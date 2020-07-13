# encoding=utf-8
# pykarta/maps/layers/tilesets_arcgis.py
# Copyright 2013, 2014, Trinity College
# Last modified: 3 September 2014
#
# http://www.esri.com/software/arcgis/arcgis-online-map-and-geoservices/map-services
# http://services.arcgisonline.com/
#

from tilesets_base import tilesets, MapTilesetRaster

tilesets.append(MapTilesetRaster('arcgis-usa-topo',
	url_template='http://services.arcgisonline.com/ArcGIS/rest/services/USA_Topo_Maps/MapServer/tile/{z}/{y}/{x}',
	zoom_min=9,
	zoom_max=15,
	# This attribution applies to zoom levels 0 thru 8 (which we have disabled).
	#attribution="© 2013 National Geographic Society, i-cubed"
	attribution="USGS"
	))
tilesets.append(MapTilesetRaster('arcgis-world-imagery',
	url_template='http://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
	zoom_min=0,
	zoom_max=19,
	attribution="Esri, DigitalGlobe, GeoEye, i-cubed, USDA, USGS, AEX, Getmapping, Aerogrid, IGN, IGP, swisstopo, and the GIS User Community"
	))
tilesets.append(MapTilesetRaster('arcgis-world-reference-overlay',
	url_template='http://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Reference_Overlay/MapServer/tile/{z}/{y}/{x}',
	zoom_min=0,
	zoom_max=13,
	attribution="Esri, DigitalGlobe, GeoEye, i-cubed, USDA, USGS, AEX, Getmapping, Aerogrid, IGN, IGP, swisstopo, and the GIS User Community"
	))
tilesets.append(MapTilesetRaster('arcgis-natgeo-world',
	url_template='http://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
	zoom_min=0,
	zoom_max=16,
	attribution="National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC",
	))
tilesets.append(MapTilesetRaster('arcgis-delorme-world-basemap',
	url_template='http://services.arcgisonline.com/ArcGIS/rest/services/Specialty/DeLorme_World_Base_Map/MapServer/tile/{z}/{y}/{x}',
	zoom_min=1,
	zoom_max=11,
	))

