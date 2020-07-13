# pykarta/maps/tilegen.py
# Copyright 2013--2017, Trinity College
# Last modified: 3 February 2015

import cairo
import os
import StringIO
import re

from pykarta.maps import MapBase
from pykarta.geometry import BoundingBox
from pykarta.misc import tile_count
import pyapp.i18n
from pykarta.geometry.projection import project_to_tilespace, unproject_from_tilespace

# This is a Pykarta map object which produces map tiles as its output.
# But rather than stitch them together on a Cairo surface, it saves
# them to a tile store using a tile store object provided by the caller.
class MapTilegen(MapBase):
	def __init__(self, writer, **kwargs):
		kwargs['tile_source'] = None
		MapBase.__init__(self, **kwargs)
		self.writer = writer
		self.re_blank_surface = re.compile('^\0+$')

	# Render a single object and store it in the tile store.
	def render_tile(self, x, y, zoom):
		self.top_left_pixel = (x, y)
		self.zoom = zoom
		self.width = 256
		self.height = 256
		self.lat, self.lon = unproject_from_tilespace(x + 0.5, y + 0.5, zoom)

		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 256, 256)
		ctx = cairo.Context(surface)

		for layer in self.layers_ordered:
			layer.do_viewport()
			layer.do_draw(ctx)

		surface.flush()
		data = surface.get_data()
		if self.re_blank_surface.match(data):
			return None
		else:
			sio = StringIO.StringIO()
			surface.write_to_png(sio)
			return sio.getvalue()

	# Render all of the tiles required to cover the sum of the bounding
	# boxes of all of the layers.
	def render_tiles(self, zoom_start, zoom_stop):
		bbox = BoundingBox()
		for layer in self.layers_ordered:
			bbox.add_bbox(layer.get_bbox())

		x_start, y_start = map(int, project_to_tilespace(bbox.max_lat, bbox.min_lon, zoom_start))
		x_stop, y_stop = map(int, project_to_tilespace(bbox.min_lat, bbox.max_lon, zoom_start))
		total = tile_count(x_stop-x_start+1, y_stop-y_start+1, zoom_stop-zoom_start+1)

		count = 0
		for zoom in range(zoom_start, zoom_stop+1):
			x_start, y_start = map(int, project_to_tilespace(bbox.max_lat, bbox.min_lon, zoom))
			x_stop, y_stop = map(int, project_to_tilespace(bbox.min_lat, bbox.max_lon, zoom))
			for x in range(x_start-1, x_stop+2):
				for y in range(y_start-1, y_stop+2):
					#print "render_tile(%d, %d, %d)" % (x, y, zoom)
					if (count % 73) == 0:	# 73 speeds things while letting all of the digits change
						self.feedback.progress(count, total, _("Rending tile {count} of {total}").format(count=count, total=total))
					tile_data = self.render_tile(x, y, zoom)
					if tile_data is not None:
						self.writer.add_tile(zoom, x, y, tile_data)
					#else:
					#	print " blank tile"
					count += 1

# Test
if __name__ == "__main__":
	from pykarta.maps.layers.marker import MapMarkerLayer
	from pykarta.formats.tiledir import MapTiledirWriter
	from pykarta.formats.mbtiles import MapMbtilesWriter
	#writer = MapTiledirWriter("map_tilegen_test")
	writer = MapMbtilesWriter(
		"tilegen_test.mbtiles",
		{
		'name':'test',
		'description':'test tileset',
		'version':'1.0',
		'type':'overlay',
		'format':'png',
		})
	generator = MapTilegen(writer)
	generator.symbols.add_symbol("layers/symbols/Dot.svg")
	layer = MapMarkerLayer()
	generator.add_layer("markers", layer)
	layer.add_marker(42.12, -72.75, "First POI")
	layer.add_marker(42.13, -72.752, "Second POI")
	generator.render_tiles(12, 16)
	writer.close()


