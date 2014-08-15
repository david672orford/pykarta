# encoding=utf-8
# pykarta/maps/layers/screen.py
# Copyright 2013, 2014, Trinity College
# Last modified: 28 July 2014

from pykarta.maps.layers.base import MapLayer

class MapScreenLayer(MapLayer):
	def __init__(self, opacity):
		MapLayer.__init__(self)
		self.opacity = opacity
	def do_draw(self, ctx):
		ctx.rectangle(0, 0, self.containing_map.width, self.containing_map.height)
		ctx.set_source_rgba(1.0, 1.0, 1.0, self.opacity)
		ctx.fill()

