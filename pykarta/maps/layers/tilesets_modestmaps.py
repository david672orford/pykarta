# encoding=utf-8
# pykarta/maps/layers/tilesets_modestmaps.py
# Copyright 2013--2021, Trinity College
# Last modified: 26 December 2021

from .tilesets_base import tilesets, MapTilesetRaster

tilesets.append(MapTilesetRaster('modestmaps-bluemarble',
	url_template='http://s3.amazonaws.com/com.modestmaps.bluemarble/{z}-r{y}-c{x}.jpg',
	attribution="NASA",
	zoom_min=0,
	zoom_max=9,
	))


