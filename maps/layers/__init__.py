# encoding=utf-8
# pykarta/maps/layers/__init__.py
# Copyright 2013, 2014, Trinity College
# Last modified: 8 October 2014

from tilesets_base import tilesets
from pykarta.maps.layers.builder import MapLayerBuilder
from pykarta.maps.layers.tile_http import MapCacheCleaner, MapTileLayerHTTP
from pykarta.maps.layers.osd import *

# Sets of map layers for use together
map_layer_sets = {
	"osm-vector": [
			"osm-vector-landuse",
			"osm-vector-waterways",
			"osm-vector-water",
			"osm-vector-buildings",
			"osm-vector-roads",
			"osm-vector-admin-borders",
			"osm-vector-road-labels",
			"osm-vector-road-refs",
			"osm-vector-places",
			"osm-vector-pois",
			]
	}

