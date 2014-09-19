# encoding=utf-8
# pykarta/maps/layers/tilesets_base.py
# Copyright 2013, 2014, Trinity College
# Last modified: 16 September 2014

import time
import urllib

import pykarta
from pykarta.misc.http import simple_url_split
from pykarta.maps.projection import *

# A list of tile sets from which they can be retrieved
# either by key or by searching.
class MapTilesets(object):
	def __init__(self):
		self.tilesets_list = []
		self.tilesets_dict = {}

	def append(self, tileset):
		tileset.api_keys = pykarta.api_keys
		self.tilesets_list.append(tileset)
		self.tilesets_dict[tileset.key] = tileset

	# Return a member named by key.
	def __getitem__(self, key):
		assert key in self.tilesets_dict, "Tileset %s does not exist" % key
		return self.tilesets_dict[key]

	# Return the keys in their original order.
	def keys(self):
		return map(lambda i: i.key, self.tilesets_list)

# Describes a set of tiles
class MapTileset(object):
	def __init__(self, key,
			url_template=None,			# whence to get tiles
			zoom_min=0, zoom_max=18,	# zoom range covered
			overzoom=True,				# enlarge tiles if lower layer allows more zoom
			attribution=None,			# string or Cairo surface with logo or credit statement
			max_age_in_days=30,			# how long to use files from cache
			):
		self.key = key
		if url_template:
			self.set_url_template(url_template)
		else:
			self.hostname_template = None
			self.path_template = None
		self.zoom_min = zoom_min
		self.zoom_max = zoom_max
		self.overzoom = overzoom
		self.attribution = attribution
		self.max_age_in_days = max_age_in_days

		self.renderer = None
		self.layer_cache_enabled = False

		self.extra_headers = {
			"User-Agent":"PyKarta %s" % pykarta.version
			}

		# Many tile servers have four hostnames. With which will we start?
		self.server_number = int(time.time()) % 4

	def set_url_template(self, url_template):
		self.hostname_template, self.path_template = simple_url_split(url_template)

	# Override this if the tile layer requires the downloading of metadata
	# before tiles may be requested.
	def online_init(self):
		pass

	# Returns the hostname (and possibly port) from the URL
	# If the template calls for server rotation, this will handle it.
	# Each downloader thread calls this, so they will get different
	# host names.
	def get_hostname(self):
		# Get the next server number in the rotation.
		self.server_number = ((self.server_number + 1) % 4)

		return self.hostname_template.replace("#R", str(self.server_number))

	# Returns the path for the GET request to retrieve a particular tile.
	# This implements the simple case of a URL template. Override in
	# derived classes in order to support other schemes.
	def get_path(self, zoom, x, y):
		path = self.path_template

		# Basic (x, y) and zoom, Leaflet-style
		path = path.replace('{z}', str(zoom)).replace('{x}', str(x)).replace('{y}', str(y))

		# Quadtree, Osmgpsmap-style
		if path.find("#Q") != -1:
			q = "t"
			for n in range(zoom-1, -1, -1):
				digit = 0
				if (x >> n) & 1:
					digit += 1
				if (y >> n) & 1:
					digit += 2
				q += "qrts"[digit]
			path = path.replace("#Q", q)
		if path.find("#W") != -1:
			q = ""
			for n in range(zoom-1, -1, -1):
				digit = 0
				if (x >> n) & 1:
					digit += 1
				if (y >> n) & 1:
					digit += 2
				q += str(digit)
			path = path.replace("#W", q)

		return path

# Describes a set of raster tiles
class MapTilesetRaster(MapTileset):
	def __init__(self, key, 
			opacity=1.0,				# used to fade out raster tiles
			transparent_color=None,		# color to convert to transparent
			saturation=None,			# <1.0=desaturate, >1.0=increase saturation
			**kwargs
			):
		MapTileset.__init__(self, key, **kwargs)
		self.opacity = opacity
		self.transparent_color = transparent_color
		self.saturation = saturation

# Describes a set of WMS raster tiles
class MapTilesetWMS(MapTilesetRaster):
	def __init__(self, key,
			layers="",					# pass to WMS server
			styles="",					# pass to WMS server
			image_format="image/jpeg",	# pass to WMS server
			transparent=False,			# pass to WMS server
			**kwargs
			):
		MapTileset.__init__(self, key, **kwargs)
		self.wms_params = {
			'service':'WMS',
			'request':'GetMap',
			'version':'1.1.1',
			'width':256,
			'height':256,
			'srs':'EPSG:4326',
			'layers':layers,
			'styles':styles,
			'format':image_format,
			'transparent':'true' if transparent else 'false',
			}
	def get_path(self, zoom, x, y):
		nw_lat, nw_lon = unproject_from_tilespace(x, y, zoom)
		se_lat, se_lon = unproject_from_tilespace(x+1, y+1, zoom)
		query_params = {'bbox':",".join(map(str,(nw_lon, se_lat, se_lon, nw_lat)))}
		query_params.update(self.wms_params)
		path = "%s?%s" % (self.path_template, urllib.urlencode(query_params))
		print path
		return path

# Describes a set of vector tiles
class MapTilesetVector(MapTileset):
	def __init__(self, key, zoom_max=20, renderer=None, **kwargs):
		MapTileset.__init__(self, key, zoom_max=zoom_max, **kwargs)
		self.extra_headers["Accept-Encoding"] = "gzip,deflate"
		self.renderer = renderer
		self.layer_cache_enabled = True
		self.symbols = None

tilesets = MapTilesets()

