# encoding=utf-8
# pykarta/maps/layers/tilesets_osm.py
# Copyright 2013--2016 Trinity College
# Last modified: 29 January 2016
#
# Openstreetmap.org raster tile sets
# This is imported by builder.py.
#
# See http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Tile_servers
# See http://wiki.openstreetmap.org/wiki/TMS
# See http://www.openstreetmap.org/copyright
#

from tilesets_base import tilesets, MapTilesetRaster

#-----------------------------------------------------------------------------
# On Openstreetmap.org
# osm-mapquest-open is defined in tilsets_mapquest.py.
#-----------------------------------------------------------------------------
tilesets.append(MapTilesetRaster('osm-default',
	url_template='http://tile.openstreetmap.org/{z}/{x}/{y}.png',
	attribution=u"Map Data: © OpenStreetMap contributors",
	zoom_max=19,
	transparent_color=(241,238,232),
	saturation=1.2,
	))
tilesets.append(MapTilesetRaster('osm-cycle',
	url_template='http://tile.opencyclemap.org/cycle/{z}/{x}/{y}.png',
	attribution=u"Map Data: © OpenStreetMap contributors",
	))
tilesets.append(MapTilesetRaster('osm-transport',
	url_template='http://tile2.opencyclemap.org/transport/{z}/{x}/{y}.png',
	attribution=u"Map Data: © OpenStreetMap contributors",
	))
tilesets.append(MapTilesetRaster('osm-humanitarian',
	url_template='http://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
	attribution=u"Map Data: © OpenStreetMap contributors",
	))

#-----------------------------------------------------------------------------
# Stamen's OSM maps
# See http://maps.stamen.com/
#-----------------------------------------------------------------------------

# B&W map which uses pure black and halftoning
for i in ("toner", "toner-hybrid", "toner-lite", "toner-background", "toner-labels", "toner-lines"):
	tilesets.append(MapTilesetRaster('stamen-%s' % i,
		url_template='http://tile.stamen.com/%s/{z}/{x}/{y}.png' % i,
		attribution=u"Map tiles by Stamen Design, under CC BY 3.0, data © OpenStreetMap contributors",
		zoom_min=0,
		zoom_max=20,
		saturation=0.5,
		))

# Topographic map with hill shading
for i in ("terrain", "terrain-background", "terrain-labels", "terrain-lines"):
	tilesets.append(MapTilesetRaster('stamen-%s' % i,
		url_template='http://tile.stamen.com/%s/{z}/{x}/{y}.jpg' % i,
		attribution=u"Map tiles by Stamen Design, under CC BY 3.0, data © OpenStreetMap contributors",
		zoom_min=4,
		zoom_max=18
		))

#-----------------------------------------------------------------------------
# Mapbox
#-----------------------------------------------------------------------------
tilesets.append(MapTilesetRaster('mapbox-streets',
	url_template='http://a.tiles.mapbox.com/v3/david672orford.map-tyhg017g/{z}/{x}/{y}.png',
	attribution=u"MapBox Tiles, data © OpenStreetMap contributors",
	zoom_max=19,
	))

#-----------------------------------------------------------------------------
# Wikimedia's Toolserver
#-----------------------------------------------------------------------------
for i in ("osm-no-labels", "hillshading", "hikebike"):	#, "osm-labels-en", "osm-labels-ru", "bw-mapnik"):
	tilesets.append(MapTilesetRaster('toolserver-%s' % i,
		url_template='http://a.tiles.wmflabs.org/%s/{z}/{x}/{y}.png' % i,
		attribution=u"Map Data: © OpenStreetMap contributors",
	))

#-----------------------------------------------------------------------------
# Other OSM
#-----------------------------------------------------------------------------

# http://korona.geog.uni-heidelberg.de/
# http://korona.geog.uni-heidelberg.de/contact.html
# Better colors and style than in osm-default
# roads--color roads layer
# roadsg--grayscale roads layer
# hybrid--semi-transparent layer
# adminb--administrative borders
for i in ("roads", "roadsg", "adminb", "hybrid"):
	tilesets.append(MapTilesetRaster('openmapsurfer-%s' % i,
		url_template='http://korona.geog.uni-heidelberg.de/tiles/%s/x={x}&y={y}&z={z}' % i,
		attribution=u"Map Data: © OpenStreetMap contributors, Rendering: GIScience Heidelberg",
		# This is the background color of openmapsurfer-roads at zoom level 13 and above.
		#transparent_color=(246,242,240),
		))

# See: http://lists.openstreetmap.org/pipermail/talk/2011-June/058892.html
tilesets.append(MapTilesetRaster('geoiq-acetate',
	url_template='http://a3.acetate.geoiq.com/tiles/acetate-roads/{z}/{x}/{y}.png',
	attribution=u"Map Data: © OpenStreetMap contributors",
	zoom_max=17,
	overzoom=True,
	))

# See http://wiki.openstreetmap.org/wiki/TopOSM
for i in (("color-relief", "contours", "features")):
	tilesets.append(MapTilesetRaster('toposm-%s' % i,
		url_template='http://a.tile.stamen.com/toposm-%s/{z}/{x}/{y}.png' % i,
		attribution=u"Map Data: © OpenStreetMap contributors",
		))

