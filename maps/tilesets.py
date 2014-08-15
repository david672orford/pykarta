# encoding=utf-8
# pykarta/tilesets.py
# Copyright 2013, 2014, Trinity College
<<<<<<< HEAD
# Last modified: 15 August 2014
=======
# Last modified: 19 July 2014
>>>>>>> c189ca99c1047a3faa49e90287a48d04772a5908

#=============================================================================
# Known tile sets
#=============================================================================

import urllib
import json

from pykarta.maps.tilesets_obj import MapTileset, MapTilesetWMS, MapTilesets
from pykarta.misc.http import simple_urlopen
from pykarta.maps.projection import *

tilesets = MapTilesets()

#-----------------------------------------------------------------------------
# Openstreetmap.org
# See http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Tile_servers
# See http://wiki.openstreetmap.org/wiki/TMS
# See http://www.openstreetmap.org/copyright
#-----------------------------------------------------------------------------
tilesets.append(MapTileset('osm-default',
	url_template='http://tile.openstreetmap.org/{z}/{x}/{y}.png',
	attribution=u"Map © OpenStreetMap contributors",
	zoom_max=19,
	transparent=(241,238,232),
	))
tilesets.append(MapTileset('osm-cycle',
	url_template='http://tile.opencyclemap.org/cycle/{z}/{x}/{y}.png',
	attribution=u"Map © OpenStreetMap contributors",
	))
tilesets.append(MapTileset('osm-transport',
	url_template='http://tile2.opencyclemap.org/transport/{z}/{x}/{y}.png',
	attribution=u"Map © OpenStreetMap contributors",
	))
tilesets.append(MapTileset('osm-humanitarian',
	url_template='http://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
	attribution=u"Map © OpenStreetMap contributors",
	))

#-----------------------------------------------------------------------------
# Stamen's OSM maps
# See http://maps.stamen.com/
#-----------------------------------------------------------------------------

# B&W map which uses pure black and halftoning
for i in ("toner", "toner-hybrid", "toner-lite", "toner-background", "toner-labels", "toner-lines"):
	tilesets.append(MapTileset('stamen-%s' % i,
		url_template='http://tile.stamen.com/%s/{z}/{x}/{y}.png' % i,
		attribution=u"Map tiles by Stamen Design, under CC BY 3.0, data © OpenStreetMap contributors",
		zoom_min=0,
		zoom_max=20,
		saturation=0.5,
		))

# Topographic map with hill shading
for i in ("terrain", "terrain-background", "terrain-labels", "terrain-lines"):
	tilesets.append(MapTileset('stamen-%s' % i,
		url_template='http://tile.stamen.com/%s/{z}/{x}/{y}.png' % i,
		attribution=u"Map tiles by Stamen Design, under CC BY 3.0, data © OpenStreetMap contributors",
		zoom_min=4,
		zoom_max=18
		))

# Novelty map
tilesets.append(MapTileset('stamen-watercolor',
		url_template='http://tile.stamen.com/watercolor/{z}/{x}/{y}.png',
		attribution=u"Map tiles by Stamen Design, under CC BY 3.0, data © OpenStreetMap contributors",
		zoom_min=1,
		zoom_max=16
		))

#-----------------------------------------------------------------------------
# Mapbox
#-----------------------------------------------------------------------------
for i in (
		("streets", "david672orford.map-tyhg017g"),
<<<<<<< HEAD
		#("josm", "openstreetmap.map-4wvf9l0l"),
=======
		("josm", "openstreetmap.map-4wvf9l0l"),
>>>>>>> c189ca99c1047a3faa49e90287a48d04772a5908
		):
	tilesets.append(MapTileset('mapbox-%s' % i[0],
		url_template='http://a.tiles.mapbox.com/v3/%s/{z}/{x}/{y}.png' % i[1],
		attribution=u"MapBox Tiles, data © OpenStreetMap contributors",
		zoom_max=19,
		))

#-----------------------------------------------------------------------------
# Wikimedia's Toolserver
#-----------------------------------------------------------------------------
for i in ("osm-no-labels", "osm-labels-en", "osm-labels-ru", "bw-mapnik"):
	tilesets.append(MapTileset('toolserver-%s' % i,
		url_template='http://a.www.toolserver.org/tiles/%s/{z}/{x}/{y}.png' % i
	))
tilesets.append(MapTileset('toolserver-shadows',
	url_template='http://toolserver.org/~cmarqu/hill/{z}/{x}/{y}.png'
	))

#-----------------------------------------------------------------------------
# Other OSM
#-----------------------------------------------------------------------------

# http://www.openstreetbrowser.org/
tilesets.append(MapTileset('openstreetbrowser',
	url_template='http://tiles-base.openstreetbrowser.org/tiles/basemap_base/{z}/{x}/{y}.png'
	))
for i in ("places_places", "overlay_pt", "transport_pt_amenities", "leisure_leisure", "culture_religion"):
	tilesets.append(MapTileset('openstreetbrowser-%s' % i,
		url_template='http://tiles-category.openstreetbrowser.org/tiles/%s/{z}/{x}/{y}.png?50433c8a029de' % i
		))

# See http://wiki.openstreetmap.org/wiki/TopOSM
for i in (("color-relief", "contours", "features")):
	tilesets.append(MapTileset('toposm-%s' % i,
		url_template='http://a.tile.stamen.com/toposm-%s/{z}/{x}/{y}.png' % i
		))

# Öpnvkarte (also know as Openbusmap.org)
# See: http://wiki.openstreetmap.org/wiki/%C3%96pnvkarte
tilesets.append(MapTileset('opnvkarte',
	url_template='http://tile.memomaps.de/tilegen/{z}/{x}/{y}.png'
	))

# See: http://lists.openstreetmap.org/pipermail/talk/2011-June/058892.html
tilesets.append(MapTileset('geoiq-acetate',
	url_template='http://a3.acetate.geoiq.com/tiles/acetate-roads/{z}/{x}/{y}.png',
	))

#-----------------------------------------------------------------------------
# MassGIS
# http://giswebservices.massgis.state.ma.us/geoserver/wms?version=1.1.1&request=GetCapabilities
#-----------------------------------------------------------------------------

for i in (
	("base", "MassGISBasemapNoLabels1", 8, 19),
	("labels", "MassGISBasemapWithLabels2", 8, 19),
	("l3parcels", "L3Parcels", 15, 19),
	("structures", "Structures", 15, 19),
	):
	name, key, zoom_min, zoom_max = i
	tilesets.append(MapTileset('massgis-%s' % name,
		url_template='http://170.63.206.116/arcgisserver/rest/services/Basemaps/%s/MapServer/tile/{z}/{y}/{x}' % key,
		zoom_min=zoom_min,
		zoom_max=zoom_max,
		))

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

# MassGIS (hosted at Trinity College
tilesets.append(MapTileset('massgis-orthos-2009_tc',
	url_template='http://tiles.osm.trincoll.edu/cgi-bin/mapserv?' \
		+ 'mode=tile&' \
		+ 'tilemode=gmap&' \
		+ 'layers=MassGIS_2009_Orthos&' \
		+ 'tile={x}+{y}+{z}',
	attribution=u"Ortho photos courtesy of MassGIS",
	max_age_in_days=3650,
	))

#-----------------------------------------------------------------------------
# http://www.esri.com/software/arcgis/arcgis-online-map-and-geoservices/map-services
# http://services.arcgisonline.com/
#-----------------------------------------------------------------------------
tilesets.append(MapTileset('arcgis-usa-topo',
	url_template='http://services.arcgisonline.com/ArcGIS/rest/services/USA_Topo_Maps/MapServer/tile/{z}/{y}/{x}',
	zoom_min=9,
	zoom_max=15,
	# This attribution applies to zoom levels 0 thru 8 (which we have disabled).
	#attribution="© 2013 National Geographic Society, i-cubed"
	attribution="USGS"
	))
tilesets.append(MapTileset('arcgis-world-imagery',
	url_template='http://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
	zoom_min=0,
	zoom_max=19,
	attribution="Esri, DigitalGlobe, GeoEye, i-cubed, USDA, USGS, AEX, Getmapping, Aerogrid, IGN, IGP, swisstopo, and the GIS User Community"
	))
tilesets.append(MapTileset('arcgis-world-reference-overlay',
	url_template='http://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Reference_Overlay/MapServer/tile/{z}/{y}/{x}',
	zoom_min=0,
	zoom_max=13,
	attribution="Esri, DigitalGlobe, GeoEye, i-cubed, USDA, USGS, AEX, Getmapping, Aerogrid, IGN, IGP, swisstopo, and the GIS User Community"
	))
tilesets.append(MapTileset('arcgis-natgeo-world',
	url_template='http://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
	zoom_min=0,
	zoom_max=16,
	attribution="National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC",
	))
tilesets.append(MapTileset('arcgis-delorme-world-basemap',
	url_template='http://services.arcgisonline.com/ArcGIS/rest/services/Specialty/DeLorme_World_Base_Map/MapServer/tile/{z}/{y}/{x}',
	zoom_min=1,
	zoom_max=11,
	))

#-----------------------------------------------------------------------------
# Microsoft Bing map layers
# See http://www.bingmapsportal.com/
# OsmGpsMap does not document #W but implements it
# FIXME: add include=ImageryProviders to query and use result
#-----------------------------------------------------------------------------
class MapTilesetBing(MapTileset):
	def __init__(self, key, metadata_url=None, **kwargs):
		MapTileset.__init__(self, key, **kwargs)
		self.metadata_url = metadata_url
	def online_init(self):
<<<<<<< HEAD
		url = self.metadata_url.replace("{api_key}", self.api_keys["bing"])
		response = simple_urlopen(url, extra_headers=self.extra_headers)
		metadata = json.load(response)
		#print "Bing metadata:", json.dumps(metadata, indent=4, separators=(',', ': '))
		resource = metadata['resourceSets'][0]['resources'][0]
		url_template = resource['imageUrl'].replace("{subdomain}","t#R").replace("{quadkey}","#W").replace("{culture}","en-us")
		#print "Bing URL template:", url_template
		self.set_url_template(url_template)
		self.zoom_min = resource['zoomMin']
		self.zoom_max = resource['zoomMax']
		#print "Bing zoom levels: %d thru %d" % (self.zoom_min, self.zoom_max)
=======
		response = simple_urlopen(self.metadata_url, extra_headers=self.extra_headers)
		metadata = json.load(response)
		print "Bing metadata:", json.dumps(metadata, indent=4, separators=(',', ': '))
		resource = metadata['resourceSets'][0]['resources'][0]
		url_template = resource['imageUrl'].replace("{subdomain}","t#R").replace("{quadkey}","#W").replace("{culture}","en-us")
		print "Bing URL template:", url_template
		self.set_url_template(url_template)
		self.zoom_min = resource['zoomMin']
		self.zoom_max = resource['zoomMax']
		print "Bing zoom levels: %d thru %d" % (self.zoom_min, self.zoom_max)
>>>>>>> c189ca99c1047a3faa49e90287a48d04772a5908

for key, bing_key in (
	('road', 'Road'),
	('aerial', 'Aerial'),
	('aerial-with-labels', 'AerialWithLabels')
	):
	tilesets.append(MapTilesetBing('bing-%s' % key,
<<<<<<< HEAD
		metadata_url='http://dev.virtualearth.net/REST/v1/Imagery/Metadata/%s?key={api_key}' % bing_key,
=======
		metadata_url='http://dev.virtualearth.net/REST/v1/Imagery/Metadata/%s?key=%s' % (bing_key, api_keys['bing']),
>>>>>>> c189ca99c1047a3faa49e90287a48d04772a5908
		attribution="Bing"
		))

#-----------------------------------------------------------------------------
# Mapquest
#-----------------------------------------------------------------------------

# These tiles are based on open and public-domain data.
# See http://wiki.openstreetmap.org/wiki/Mapquest#MapQuest-hosted_map_tiles
# See http://developer.mapquest.com/web/products/open/map
# Supports If-Modified-Since
tilesets.append(MapTileset('mapquest-osm',
	url_template='http://otile1.mqcdn.com/tiles/1.0.0/map/{z}/{x}/{y}.jpg',
	attribution=u"Map tiles courtesy of MapQuest, data © OpenStreetMap contributors",
	))
tilesets.append(MapTileset('mapquest-openaerial',
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
	tilesets.append(MapTileset('mapquest-%s' % name,
		url_template=url_template,	
		attribution="Mapquest"
		))

#-----------------------------------------------------------------------------
# Google Maps
# See http://www.neongeo.com/wiki/doku.php?id=map_servers
# Note: As of May 2013, Google still objects to direct use of its tile
# servers, so we will not be actually using this.
#-----------------------------------------------------------------------------
<<<<<<< HEAD
#class MapTilesetGoogle(MapTileset):
#	def __init__(self, key, **kwargs):
#		MapTileset.__init__(self, key, **kwargs)
#		self.extra_headers["User-Agent"] = "Mozilla/5.0"
#		self.extra_headers["Referer"] = "http://maps.google.com/"
#
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
=======
class MapTilesetGoogle(MapTileset):
	def __init__(self, key, **kwargs):
		MapTileset.__init__(self, key, **kwargs)
		self.extra_headers["User-Agent"] = "Mozilla/5.0"
		self.extra_headers["Referer"] = "http://maps.google.com/"

tilesets.append(MapTilesetGoogle('google', 
	url_template='http://mt#R.google.com/vt/x={x}&s=&y={y}&z={z}',
	attribution = u"Map data ©2012 Google, INEGI",
	))
tilesets.append(MapTilesetGoogle('google-satellite', 
	url_template='http://khm#R.google.com/kh/v=123&x={x}&y={y}&z={z}',
	attribution = u"Map data ©2012 Google, INEGI",
	))
tilesets.append(MapTilesetGoogle('google-hybrid', 
	url_template='http://mt#R.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
	attribution = u"Map data ©2012 Google, INEGI",
	))

#-----------------------------------------------------------------------------
# Nokia OVI
# (Nokia purchased Navteq in 2007.)
# See http://www.neongeo.com/wiki/doku.php?id=map_servers
# See http://developer.here.com/ (recently discovered)
#-----------------------------------------------------------------------------
for name, key in (
	('normal', 'normal.day'),
	('normal-grey', 'normal.day.grey'),
	('normal-transit', 'normal.day.transit'),
	('satellite', 'satellite.day'),
	('terrain', 'terrain.day'),
	):
	tilesets.append(MapTileset('nokia-%s' % name, 
		url_template='http://maptile.maps.svc.ovi.com/maptiler/maptile/newest/%s/{z}/{x}/{y}/256/png8' % key,
		attribution="Nokia OVI",
		))
>>>>>>> c189ca99c1047a3faa49e90287a48d04772a5908

