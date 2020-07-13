# encoding=utf-8
# pykarta/maps/layers/tile_debug.py
# Copyright 2013--2018, Trinity College
# Last modified: 9 May 2014

from pykarta.maps.layers.base import MapTileLayer
import cairo

# This layer draws tile outlines and puts z/x/y in the top left hand corner.
class MapTileLayerDebug(MapTileLayer):
	def __init__(self):
		MapTileLayer.__init__(self, None)		# None is the tile class
	def do_draw(self, ctx):
		ctx.set_line_width(1)
		ctx.set_source_rgb(1.0, 0.0, 0.0)
		ctx.select_font_face("sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size(12)
		for tile in self.tiles:
			zoom, x, y, xpixoff, ypixoff = tile
			ctx.save()
			ctx.translate(xpixoff, ypixoff)
			ctx.scale(self.tile_scale_factor, self.tile_scale_factor)
			ctx.rectangle(0, 0, 256, 256)
			ctx.stroke()
			ctx.move_to(10, 22)
			ctx.show_text("%d/%d/%d" % (zoom, x, y))
			ctx.restore()

