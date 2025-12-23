# pykarta/server/modules/tiles_parcels.py
# Produce GeoJSON tiles from parcel boundaries stored in a Spatialite database
# Last modified: 19 October 2019


import os, json, re, gzip, io
from pykarta.geometry.projection import unproject_from_tilespace
from pykarta.server.dbopen import dbopen

def app(environ, start_response):
	stderr = environ['wsgi.errors']

	m = re.match(r'^/(\d+)/(\d+)/(\d+)\.geojson$', environ['PATH_INFO'])
	assert m, environ['PATH_INFO']
	zoom = int(m.group(1))
	x = int(m.group(2))
	y = int(m.group(3))
	stderr.write("Parcel tile (%d, %d) at zoom %d...\n" % (x, y, zoom))
	assert zoom <= 16

	cursor, response_headers = dbopen(environ, "parcels.sqlite")
	if cursor is None:
		start_response("304 Not Modified", response_headers)
		return []

	p1 = unproject_from_tilespace(x - 0.05, y - 0.05, zoom)
	p2 = unproject_from_tilespace(x + 1.05, y + 1.05, zoom)
	bbox = 'BuildMBR(%f,%f,%f,%f,4326)' % (p1[1], p1[0], p2[1], p2[0])

	geometry = "Intersection(Geometry,{bbox})".format(bbox=bbox)
	if zoom < 16:
		geometry = "SimplifyPreserveTopology({geometry},{simplification})".format(
			geometry=geometry,
			simplification = 360.0 / (2.0 ** zoom) / 256.0		# one pixel
			)
	else:
		#stderr.write("Not simplified\n")
		pass

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
	with gzip.open(out, mode='wt') as fo:
		json.dump(geojson, fo)

	start_response("200 OK", response_headers + [
		('Content-Type', 'application/json'),
		('Content-Encoding', 'gzip'),
		])
	return [out.getvalue()]

if __name__ == "__main__":
	def dummy_start_response(code, headers):
		print(code, headers)
	print(app({
		'PATH_INFO': "/16/19525/24300.geojson",
		}, dummy_start_response))
 
