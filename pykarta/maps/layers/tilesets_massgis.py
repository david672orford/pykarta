# encoding=utf-8
# pykarta/maps/layers/tilesets_massgis.py
# Copyright 2013--2021, Trinity College
# Last modified: 26 December 2021

from .tilesets_base import tilesets, MapTilesetRaster, MapTilesetWMS

# MassGIS WMS server
# http://giswebservices.massgis.state.ma.us/geoserver/wms?service=WMS&version=1.1.1&request=GetCapabilities
for name, layers, image_format, transparent in (
	('usgs-topos', 'massgis:GISDATA.IMG_USGSQUADM', 'image/jpeg', False),
	('urban-boundaries', 'massgis:GISDATA.MA2000URBBND_POLY', 'image/png', True),
	('fishing', 'massgis:GISDATA.OFBA_PT', 'image/png', True),
	):
	tilesets.append(MapTilesetWMS(
		'massgis-%s' % name,
		url_template='http://giswebservices.massgis.state.ma.us/geoserver/wms',
		layers=layers,
		image_format=image_format,
		transparent=transparent,
		))

# Arcgis server for MassGIS
for name, layers, zoom_min, zoom_max in (
	("l3parcels", "MassGIS_Level3_Parcels", 15, 18),
	("orthos-199X", "BW_Orthos_Tile_Package", 0, 19),
	("orthos-2001", "orthos2001_tile_package", 0, 19),
	("orthos-2005", "orthos2005_tile_package", 0, 19),
	("orthos-2009", "coq0809_from_sids_package", 0, 19),
	("orthos-2014", "USGS_Orthos_2013_2014", 0, 20),
	):
	tilesets.append(MapTilesetRaster(
		'massgis-%s' % name,
		url_template='http://tiles1.arcgis.com/tiles/hGdibHYSPO59RG1h/arcgis/rest/services/%s/MapServer/tile/{z}/{y}/{x}' % layers,
		zoom_min=zoom_min,
		zoom_max=zoom_max,
		))

