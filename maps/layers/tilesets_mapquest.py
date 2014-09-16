# encoding=utf-8
# pykarta/maps/layers/tilesets_mapquest.py
# Copyright 2013, 2014, Trinity College
# Last modified: 5 September 2014
#
# Mapquest
#

from tilesets_base import tilesets, MapTilesetRaster

# These tiles are based on open and public-domain data.
# See http://wiki.openstreetmap.org/wiki/Mapquest#MapQuest-hosted_map_tiles
# See http://developer.mapquest.com/web/products/open/map
# Supports If-Modified-Since
tilesets.append(MapTilesetRaster('osm-mapquest-open',		# defined in 
	url_template='http://otile1.mqcdn.com/tiles/1.0.0/map/{z}/{x}/{y}.jpg',
	attribution=u"Map tiles courtesy of MapQuest, data © OpenStreetMap contributors",
	))
tilesets.append(MapTilesetRaster('mapquest-openaerial',
	url_template='http://otile1.mqcdn.com/tiles/1.0.0/sat/{z}/{x}/{y}.jpg',
	attribution=u"Aerial tiles courtesy of MapQuest, Portions Courtesy NASA/JPL-Caltech and U.S. Depart. of Agriculture, Farm Service Agency",
	max_age_in_days=365,
	))

# These tiles may include licensed data.
# See: http://www.mapquestapi.com/
for name, url_template in (
	('map', 'http://ttiles01.mqcdn.com/tiles/1.0.0/vx/map/{z}/{x}/{y}.png'),
	('satellite', 'http://ttiles01.mqcdn.com/tiles/1.0.0/vx/sat/{z}/{x}/{y}.png'),
	('hybrid', 'http://ttiles04.mqcdn.com/tiles/1.0.0/vx/hyb/{z}/{x}/{y}.png'),
	):
	tilesets.append(MapTilesetRaster('mapquest-%s' % name,
		url_template=url_template,	
		attribution="Mapquest"
		))

