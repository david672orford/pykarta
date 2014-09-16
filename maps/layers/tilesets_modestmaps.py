# encoding=utf-8
# pykarta/maps/layers/tilesets_modestmaps.py
# Copyright 2013, 2014, Trinity College
# Last modified: 5 September 2014

from tilesets_base import tilesets, MapTilesetRaster

tilesets.append(MapTilesetRaster('modestmaps-bluemarble',
	url_template='http://s3.amazonaws.com/com.modestmaps.bluemarble/{z}-r{y}-c{x}.jpg',
	attribution=u"NASA",
	zoom_min=0,
	zoom_max=9,
	))


