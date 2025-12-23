# encoding=utf-8
# pykarta/maps/layers/tilesets_osm.py
# Copyright 2013--2025 Trinity College
#
# Tile sets based on free data from Openstreetmap.org
# This is imported by builder.py.
#
# http://wiki.openstreetmap.org/wiki/Tile_servers
# See http://wiki.openstreetmap.org/wiki/TMS
# See http://www.openstreetmap.org/copyright (attribution requirements)
#

from .tilesets_base import tilesets, MapTilesetRaster

#-----------------------------------------------------------------------------
# Renderings offered on Openstreetmap.org
#-----------------------------------------------------------------------------

tilesets.append(MapTilesetRaster("osm-default",
	url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
	attribution="Map Data: © OpenStreetMap contributors",
	zoom_max=19,
	transparent_color=(241,238,232),
	saturation=1.2,
	))

# https://osm.rrze.fau.de/
# Double-resolution rendering of the default style
tilesets.append(MapTilesetRaster("osm-default-hd", 
	# Direct
	url_template="http://a.osm.rrze.fau.de/osmhd/{z}/{x}/{y}.png",
	# Proxied thru Pykarta Server
	#url_template="tiles/osm-default-hd/{z}/{x}/{y}.png",
	attribution="© OpenStreetMap contributors",
	zoom_max=19,
	transparent_color=(242,239,233),
	saturation=1.2,
	))

#-----------------------------------------------------------------------------
# From https://layers.openstreetmap.fr
#-----------------------------------------------------------------------------

# "CyclOSM" on Openstreetmap.org
tilesets.append(MapTilesetRaster("osm-cyclosm",
	url_template="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
	attribution="Map Data: © OpenStreetMap contributors",
	))

# "Humanitarian" on Openstreetmap.org
tilesets.append(MapTilesetRaster("osm-humanitarian",
	url_template="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
	attribution="Map Data: © OpenStreetMap contributors",
	))

#-----------------------------------------------------------------------------
# From Thunderforest
# Tiles are free, but styles are closed-source.
# Styles "cycle" and "transport" featured on Openstreetmap.org
#-----------------------------------------------------------------------------

for style in ("cycle","transport","landscape","outdoors","transport-dark","pioneer","mobile-atlas","neighbourhood"):
	tilesets.append(MapTilesetRaster("osm-thunderforest-%s" % style,
		url_template="https://{s}.tile.thunderforest.com/%s/{z}/{x}/{y}@2x.png?apikey={api_key}" % style,
		attribution="Map: © Thunderforest, Data: © OpenStreetMap contributors",
		api_key_name="thunderforest",
		))

#-----------------------------------------------------------------------------
# Stamen's OSM maps
# See http://maps.stamen.com/
#-----------------------------------------------------------------------------

## B&W map which uses pure black and halftoning
#for i in ("toner", "toner-hybrid", "toner-lite", "toner-background", "toner-labels", "toner-lines"):
#	tilesets.append(MapTilesetRaster("osm-stamen-%s" % i,
#		url_template="http://{s}.tile.stamen.com/%s/{z}/{x}/{y}.png" % i,
#		subdomains="abcd",
#		attribution="Map tiles by Stamen Design, under CC BY 3.0, data © OpenStreetMap contributors",
#		zoom_min=0,
#		zoom_max=20,
#		saturation=0.5,
#		))
#
## Topographic map with hill shading
#for i in ("terrain", "terrain-background", "terrain-labels", "terrain-lines", "terrain-classic"):
#	tilesets.append(MapTilesetRaster("osm-stamen-%s" % i,
#		url_template="http://{s}.tile.stamen.com/%s/{z}/{x}/{y}.png" % i,
#		subdomains="abcd",
#		attribution="Map tiles by Stamen Design, under CC BY 3.0, data © OpenStreetMap contributors",
#		zoom_min=4,
#		zoom_max=18
#		))
#
## http://wiki.openstreetmap.org/wiki/TopOSM
## Now run on Stamen servers
#for name, ext in (("color-relief", "jpg"), ("contours", "png"), ("features", "png")):
#	tilesets.append(MapTilesetRaster("osm-toposm-%s" % name,
#		url_template="http://{s}.tile.stamen.com/toposm-%s/{z}/{x}/{y}.%s" % (name, ext),
#		attribution="Map Data: © OpenStreetMap contributors",
#		))

#-----------------------------------------------------------------------------
# Other renderings of OSM data
#-----------------------------------------------------------------------------

# OpenMapSurfer
# http://korona.geog.uni-heidelberg.de/ (slippy map)
# http://korona.geog.uni-heidelberg.de/contact.html (terms of use)
# Better colors and style than in osm-default
# roads--color roads layer
# roadsg--grayscale roads layer
# hybrid--semi-transparent layer
# adminb--administrative borders
# NOTE: not updated since 2016; kept for sake of aerial view
for i in ("roads", "roadsg", "adminb", "hybrid"):
	tilesets.append(MapTilesetRaster("osm-openmapsurfer-%s" % i,
		url_template="http://korona.geog.uni-heidelberg.de/tiles/%s/x={x}&y={y}&z={z}" % i,
		attribution="Map Data: © OpenStreetMap contributors, Rendering: GIScience Heidelberg",
		# This is the background color of openmapsurfer-roads at zoom level 13 and above.
		#transparent_color=(246,242,240),
		))

# https://opentopomap.org/about
tilesets.append(MapTilesetRaster("osm-opentopomap",
	url_template="https://a.tile.opentopomap.org/{z}/{x}/{y}.png",
	attribution="Kartendaten: © OpenStreetMap-Mitwirkende, SRTM | Kartendarstellung: © OpenTopoMap (CC-BY-SA)",
	))

# http://www.waymarkedtrails.org/
for i in ("hiking","cycling"):
	tilesets.append(MapTilesetRaster("osm-waymarkedtrails-%s" % i,
		url_template="https://tile.waymarkedtrails.org/%s/{z}/{x}/{y}.png" % i,
		attribution="Map Data: © OpenStreetMap contributors",
		))

# https://wiki.openstreetmap.org/wiki/Carto_(Company)
# https://carto.com/location-data-services/basemaps/
# URLs from:
#  https://wiki.openstreetmap.org/wiki/Tile_servers
for i in ("light","dark"):
	tilesets.append(MapTilesetRaster("osm-carto-%s" % i,
		url_template="https://cartodb-basemaps-{s}.global.ssl.fastly.net/%s_all/{z}/{x}/{y}.png" % i,
		attribution="Map tiles by Carto, under CC BY 3.0. Data by OpenStreetMap, under ODbL.",
		))

# Mapbox (broken)
tilesets.append(MapTilesetRaster("osm-mapbox-streets",
	#url_template="http://a.tiles.mapbox.com/v3/david672orford.map-tyhg017g/{z}/{x}/{y}.png",
	url_template="https://api.mapbox.com/v4/david672orford.map-tyhg017g/{z}/{x}/{y}.png",
	attribution="MapBox Tiles, data © OpenStreetMap contributors",
	zoom_max=19,
	))

