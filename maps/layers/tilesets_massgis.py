# encoding=utf-8
# pykarta/maps/layers/tilesets_massgis.py
# Copyright 2013, 2014, Trinity College
# Last modified: 5 September 2014
#
# See http://giswebservices.massgis.state.ma.us/geoserver/wms?version=1.1.1&request=GetCapabilities

from tilesets_base import tilesets, MapTilesetRaster, MapTilesetWMS

# MassGIS tile server
for i in (
	("base", "MassGISBasemapNoLabels1", 8, 19),
	("base-with-labels", "Base_Streets_with_Labels", 8, 19),
	("base-with-labels2", "MassGISBasemapWithLabels2", 8, 19),
	("l3parcels", "L3Parcels", 15, 19),
	("structures", "Structures", 15, 19),
	):
	name, key, zoom_min, zoom_max = i
	tilesets.append(MapTilesetRaster('massgis-%s' % name,
		#url_template='http://170.63.206.116/arcgisserver/rest/services/Basemaps/%s/MapServer/tile/{z}/{y}/{x}' % key,
		url_template='http://gisprpxy.itd.state.ma.us/tiles/Basemaps_%s/{z}/{y}/{x}.jpg' % key,
		zoom_min=zoom_min,
		zoom_max=zoom_max,
		))

# MassGIS WMS server
# http://giswebservices.massgis.state.ma.us/geoserver/wms?service=WMS&version=1.1.1&request=GetCapabilities
for i in (
	("orthos-199X", 'massgis:GISDATA.IMG_BWORTHOS', 'image/jpeg', False),
	("orthos-2001", 'massgis:GISDATA.IMG_COQ2001', 'image/jpeg', False),
	("orthos-2005", 'massgis:GISDATA.IMG_COQ2005', 'image/jpeg', False),
	("orthos-2009", 'massgis:GISDATA.IMG_COQ2009_30CM', 'image/jpeg', False),
	('usgs-topos', 'massgis:GISDATA.IMG_USGSQUADM', 'image/jpeg', False),
	('urban-boundaries', 'massgis:GISDATA.MA2000URBBND_POLY', 'image/png', True),
	('fishing', 'massgis:GISDATA.OFBA_PT', 'image/png', True),
	):
	name, layers, image_format, transparent = i
	tilesets.append(MapTilesetWMS('massgis-%s' % name,
		url_template='http://giswebservices.massgis.state.ma.us/geoserver/wms',
		layers=layers,
		image_format=image_format,
		transparent=transparent,
		))

