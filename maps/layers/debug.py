# encoding=utf-8
# pykarta/maps/layers/svg.py
# Copyright 2013, 2014, Trinity College
# Last modified: 9 May 2014

from pykarta.maps.layers.base import MapTileLayer
import cairo

# This layer draws tile outlines and puts z/x/y in the top left hand corner.
class MapTileLayerDebug(MapTileLayer):
	def do_draw(self, ctx):
		ctx.scale(self.tile_scale_factor, self.tile_scale_factor)
		ctx.set_line_width(1)
		ctx.set_source_rgb(1.0, 0.0, 0.0)
		ctx.select_font_face("sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size(12)
		for tile in self.tiles:
			zoom, x, y, xpixoff, ypixoff = tile
			ctx.save()
			ctx.translate(xpixoff, ypixoff)
			ctx.rectangle(0, 0, 256, 256)
			ctx.stroke()
			ctx.move_to(10, 22)
			ctx.show_text("%d/%d/%d" % (zoom, x, y))
			ctx.restore()

