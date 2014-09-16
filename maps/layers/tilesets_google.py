# encoding=utf-8
# pykarta/maps/layers/tilesets_google.py
# Copyright 2013, 2014, Trinity College
# Last modified: 3 September 2014
#
#
# Google Maps
# See http://www.neongeo.com/wiki/doku.php?id=map_servers
# Note: As of May 2013, Google objects to direct use of its tile
# servers, so we will not be actually using this.
#

from tilesets_base import tilesets, MapTileset

class MapTilesetGoogle(MapTilesetRaster):
	def __init__(self, key, **kwargs):
		MapTileset.__init__(self, key, **kwargs)
		self.extra_headers["User-Agent"] = "Mozilla/5.0"
		self.extra_headers["Referer"] = "http://maps.google.com/"

#tilesets.append(MapTilesetGoogle('google', 
#	url_template='http://mt#R.google.com/vt/x={x}&s=&y={y}&z={z}',
#	attribution = u"Map data ©2012 Google, INEGI",
#	))
#tilesets.append(MapTilesetGoogle('google-satellite', 
#	url_template='http://khm#R.google.com/kh/v=123&x={x}&y={y}&z={z}',
#	attribution = u"Map data ©2012 Google, INEGI",
#	))
#tilesets.append(MapTilesetGoogle('google-hybrid', 
#	url_template='http://mt#R.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
#	attribution = u"Map data ©2012 Google, INEGI",
#	))

