# Produce GeoJSON tiles from parcel boundaries stored in a Spatialite database
# Last modified: 4 May 2018

from __future__ import print_function
import os, json, re, gzip, io
from email.utils import formatdate
from pyspatialite import dbapi2 as db
from pykarta.geometry.projection import unproject_from_tilespace
import threading

thread_data = threading.local()

def application(environ, start_response):
	stderr = environ['wsgi.errors']

	cursor = getattr(thread_data, 'cursor', None)
	if cursor is None:
		db_filename = environ["DATADIR"] + "/parcels.sqlite"
		thread_data.last_modified = formatdate(os.path.getmtime(db_filename), usegmt=True)
		conn = db.connect(db_filename)
		conn.row_factory = db.Row
		cursor = conn.cursor()
		thread_data.cursor = cursor

	m = re.match(r'^/(\d+)/(\d+)/(\d+)\.geojson$', environ['PATH_INFO'])
	assert m, environ['PATH_INFO']
	zoom = int(m.group(1))
	x = int(m.group(2))
	y = int(m.group(3))
	stderr.write("Parcel tile (%d, %d) at zoom %d...\n" % (x, y, zoom))
	assert zoom <= 16

	p1 = unproject_from_tilespace(x - 0.05, y - 0.05, zoom)
	p2 = unproject_from_tilespace(x + 1.05, y + 1.05, zoom)
	bbox = 'BuildMBR(%f,%f,%f,%f,4326)' % (p1[1], p1[0], p2[1], p2[0])

	geometry = "Intersection(Geometry,{bbox})".format(bbox=bbox)
	if zoom < 16:
		geometry = "SimplifyPreserveTopology({geometry},{simplification})".format(
			geometry=geometry,
			simplification = 360.0 / (2.0 ** zoom) / 256.0
			)
	else:
		print("Not simplified")

	query = """SELECT rowid as __id__, AsGeoJSON({geometry}) as __geometry__, house_number, street, centroid
		FROM parcels
		WHERE MBRIntersects({bbox}, Geometry)
		AND ROWID IN ( SELECT ROWID FROM SpatialIndex WHERE f_table_name = 'parcels' AND search_frame = {bbox} )
		""".format(geometry=geometry, bbox=bbox)

	cursor.execute(query)

	features = []
	for row in cursor:
		if row['__geometry__'] is None:
			continue
		row = dict(row)
		feature = {
			'type': 'Feature',
			'id': row.pop("__id__"),
			'geometry': json.loads(row.pop("__geometry__")),
			'properties': row,
			}
		features.append(feature)
	stderr.write("Found %d feature(s)\n" % len(features))

	geojson = {
		'type': 'FeatureCollection',
		'features': features,
		}

	# Convert to JSON and compress
	out = io.BytesIO()
	with gzip.GzipFile(fileobj=out, mode='w') as fo:
		json.dump(geojson, fo)
	geojson = out.getvalue()

	start_response("200 OK", [
		('Content-Type', 'application/json'),
		('Content-Encoding', 'gzip'),
		('Last-Modified', thread_data.last_modified,
		])
	return [geojson]

if __name__ == "__main__":
	def dummy_start_response(code, headers):
		print(code, headers)
	print(application({
		'PATH_INFO': "/16/19525/24300.geojson",
		}, dummy_start_response))
 
