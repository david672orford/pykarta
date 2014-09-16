# encoding=utf-8
# pykarta/maps/layers/tile_mbtiles.py
# Copyright 2013, 2014, Trinity College
# Last modified: 5 September 2014

from pykarta.maps.layers.base import MapTileLayer, MapRasterTile
from pykarta.maps.layers.tilesets_base import MapTilesetRaster

#=============================================================================
# Mbtiles tile layer
# http://mapbox.com/developers/mbtiles/
#=============================================================================
class MapTileLayerMbtiles(MapTileLayer):
	def __init__(self, mbtiles_filename):
		MapTileLayer.__init__(self)
		import sqlite3
		self.conn = sqlite3.connect(mbtiles_filename)
		self.cursor = self.conn.cursor()

		self.tileset = MapTilesetRaster(mbtiles_filename,
			zoom_min = int(self.fetch_metadata_item('minzoom', 0)),
			zoom_max = int(self.fetch_metadata_item('maxzoom', 99)),
			attribution = self.fetch_metadata_item('attribution', ''),
			)

		self.zoom_min = self.tileset.zoom_min
		self.zoom_max = self.tileset.zoom_max
		self.attribution = self.tileset.attribution

	def fetch_metadata_item(self, name, default):
		self.cursor.execute("select value from metadata where name = ?", (name,))
		result = self.cursor.fetchone()
		if result is not None:
			#print "%s=%s" % (name, result[0])
			return result[0]
		else:
			return default

	# Return the indicated tile as a Cairo surface or None.
	def load_tile(self, zoom, x, y, may_download):
		y = (2**zoom-1) - y
		self.cursor.execute("select tile_data from tiles where zoom_level = ? and tile_column = ? and tile_row = ?", (zoom, x, y))
		result = self.cursor.fetchone()
		if result is not None:
			if self.renderer:
				raise AssertionError("Not yet implemented")
			else:
				try:
					return MapRasterTile(self, data=result[0])
				except:
					pass
		return None

