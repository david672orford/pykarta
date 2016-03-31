# encoding=utf-8
# pykarta/maps/layers/tilesets_rndr_topojson.py
# Copyright 2013, 2014, 2015, Trinity College
# Last modified: 13 October 2015

from pykarta.maps.layers.tile_rndr_geojson import RenderGeoJSON

#=============================================================================
# Base class for TopoJSON vector tile renderers
# https://github.com/mbostock/topojson/wiki
#=============================================================================

# FIXME: this unfinished
class RenderTopoJSON(RenderGeoJSON):
	def load_features(self, topojson):
		assert topojson['type'] == "Topology"
		translate = topojson['translate']
		scale = topojson['scale']
		arcs = topojson['arcs']
		objects = topojson['objects']['vectile']

