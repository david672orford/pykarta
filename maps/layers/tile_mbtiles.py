# encoding=utf-8
# pykarta/maps/layers/tile_mbtiles.py
# Copyright 2013--2018, Trinity College
# Last modified: 4 May 2018

from pykarta.maps.layers.base import MapTileLayer, MapRasterTile, MapTileError
from pykarta.maps.layers.tilesets_base import MapTilesetRaster

#=============================================================================
# Mbtiles tile layer
# http://mapbox.com/developers/mbtiles/
#=============================================================================
class MapTileLayerMbtiles(MapTileLayer):
	def __init__(self, mbtiles_filename):
		MapTileLayer.__init__(self, MapRasterTile)

		import sqlite3
		self.conn = sqlite3.connect(mbtiles_filename)
		self.cursor = self.conn.cursor()

		self.tileset = MapTilesetRaster(mbtiles_filename,
			zoom_min = int(self.fetch_metadata_item('minzoom', 0)),
			zoom_max = int(self.fetch_metadata_item('maxzoom', 99)),
			attribution = self.fetch_metadata_item('attribution', ''),
			)

		self.opts.zoom_min = self.tileset.zoom_min
		self.opts.zoom_max = self.tileset.zoom_max
		self.opts.attribution = self.tileset.attribution

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
			try:
				return self.tile_class(self, None, zoom, x, y, data=result[0])
			except MapTileError as e:
				self.feedback.debug(1, " %s" % str(e))
		return None

