# encoding=utf-8
# pykarta/maps/layers/tilesets_vec_mapzen.py
# Vector tile sets and renders for them
# Copyright 2013, 2014, 2015, Trinity College
# Last modified: 13 October 2015

import glob
import cairo
import math

from pykarta.maps.layers.tile_rndr_topojson import RenderTopoJSON
from tilesets_base import tilesets, MapTilesetVector
from pykarta.maps.symbols import MapSymbolSet
from pykarta.geometry.projection import project_to_tilespace_pixel
import pykarta.draw

#=============================================================================
# Mapzen
# https://mapzen.com/projects/vector-tiles/
# https://github.com/mapzen/vector-datasource
#=============================================================================

class RenderMapzen(RenderTopoJSON):
	pass

tilesets.append(MapTilesetVector('osm-mapzen',
	url_template="http://vector.mapzen.com/all/{z}/{x}/{y}.topojson?api_key={api_key}", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderMapzen,
	))

