#-----------------------------------------------------------------------------
# Westfield GIS
# We try to retrieve tiles from a service which is not intended to 
# provide tiles. They do not stitch together well. This appears to
# be because the Westfield does not use the same projection as we do.
#-----------------------------------------------------------------------------

from pykarta.maps.tilesets_obj import MapTileset
from pykarta.maps.tilesets import tilesets

# See: http://resources.esri.com/help/9.3/arcgisserver/apis/rest/
# See: http://gis.cityofwestfield.org/ArcGIS/rest/services/WestfieldAGS/MapServer
class MapTilesetWestfield(MapTileset):
	def __init__(self, key, layers="", transparent=True, image_format=None, **kwargs):
		MapTileset.__init__(self, key, **kwargs)
		self.rest_params = {
			'transparent':'true' if transparent else 'false',
			#'bboxSR':'2249',
			'f':'image',
			'format':image_format,	# "jpg", "png"
			#'dpi':'96',
			'layers':'show:%s' % layers,
			'size':'256,256',
			'imageSR':'2249',
			}
		import pyproj
		self.project = pyproj.Proj("+init=EPSG:2249")
	def get_path(self, zoom, x, y):
		nw_lat, nw_lon = unproject_from_tilespace(x, y, zoom)
		se_lat, se_lon = unproject_from_tilespace(x+1, y+1, zoom)
		print "In degrees:", str((nw_lon, se_lat, se_lon, nw_lat))

		nw_x, nw_y = self.project(nw_lon, nw_lat)
		se_x, se_y = self.project(se_lon, se_lat)
		print "In meters:", str((nw_x, se_y, se_x, nw_y))

		to_feet = 3.280839895
		nw_y *= to_feet
		se_y *= to_feet
		nw_x *= to_feet
		se_x *= to_feet
		print "In feet:", str((nw_x, se_y, se_x, nw_y))

		x_offset = 135710.0
		nw_x += x_offset
		se_x += x_offset

		y_offset = -2245.0
		nw_y += y_offset
		se_y += y_offset

		query_params = {'bbox':",".join(map(str, (nw_x, se_y, se_x, nw_y)))}
		print query_params

		query_params.update(self.rest_params)
		path = "%s?%s" % (self.path_template, urllib.urlencode(query_params))
		print path
		print
		return path

tilesets.append(MapTilesetWestfield('westfieldgis-parcels',
	url_template='http://gis.cityofwestfield.org/ArcGIS/rest/services/WestfieldAGS/MapServer/export',
	layers='42',
	image_format="png"
	))
tilesets.append(MapTilesetWestfield('westfieldgis-orthos-1940',
	url_template='http://gis.cityofwestfield.org/ArcGIS/rest/services/WestfieldAGS/MapServer/export',
	layers='94',
	image_format="jpg"
	))
tilesets.append(MapTilesetWestfield('westfieldgis-orthos-1969',
	url_template='http://gis.cityofwestfield.org/ArcGIS/rest/services/WestfieldAGS/MapServer/export',
	layers='101',
	image_format="jpg"
	))


