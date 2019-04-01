# encoding=utf-8
# pykarta/maps/layers/tilesets_base.py
# Copyright 2013--2019, Trinity College
# Last modified: 1 April 2019

import time
from urllib import urlencode
from urlparse import urlparse

import pykarta
from pykarta.geometry.projection import unproject_from_tilespace
from pykarta.maps.layers.base import MapRasterTile

# A list of tile sets from which they can be retrieved
# either by key or by searching.
class MapTilesets(object):
	def __init__(self):
		self.tilesets_list = []
		self.tilesets_dict = {}

	def append(self, tileset):
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
	def __init__(self,
			key,						# name of this tileset
			tile_class,					# class which represents a loaded tile
			url_template=None,			# whence to get tiles
			subdomains="abc",
			zoom_min=0, zoom_max=18,	# zoom range covered
			overzoom=True,				# enlarge tiles if lower layer allows more zoom
			attribution=None,			# string or Cairo surface with logo or credit statement
			max_age_in_days=30,			# how long to use files from cache
			api_key_name=None
			):
		self.key = key
		self.tile_class = tile_class
		self.url_template = None
		if url_template:
			self.set_url_template(url_template)
		self.subdomains = subdomains
		self.zoom_min = zoom_min
		self.zoom_max = zoom_max
		self.overzoom = overzoom
		self.attribution = attribution
		self.max_age_in_days = max_age_in_days
		self.api_key_name = api_key_name
		self.api_key = None
		self.saturation = None			# FIXME: only implemented for raster
		self.opacity = None				# FIXME: only implemented for raster

		self.renderer = None
		self.layer_cache_enabled = False
		self.zoom_substitutions = None

		self.extra_headers = {
			"User-Agent":"PyKarta %s" % pykarta.version
			}

		# Start the server number somewhere random. This will be
		# constrained to the set of self.subdomains before it is used.
		self.server_number = int(time.time())

	def late_init(self):
		if self.api_key_name is not None:
			self.api_key = pykarta.api_keys[self.api_key_name]

		# If the tileset URL template does not specify a server, it is relative
		# to the root of the Pykarta tile server.
		if self.url_template is not None and self.url_template.netloc == "":
			server_url = urlparse(pykarta.server_url)
			if server_url.path.endswith("/"):
				path = (server_url.path + self.url_template.path)
			else:
				path = (server_url.path + "/" + self.url_template.path)
			self.url_template = self.url_template._replace(
				scheme = server_url.scheme,
				netloc = server_url.netloc,
				path = path
				)

	# Override this if the layer needs Internet access to complete initialization.
	def online_init(self):
		pass

	# The URL template shows us how to make the URLs for downloading tiles.
	def set_url_template(self, url_template):
		self.url_template = urlparse(url_template)

	# Returns the hostname (and possibly port) from the URL template.
	# If the template calls for server rotation, this will handle it.
	# Each downloader thread calls this, so they will get different
	# host names.
	def get_hostname(self):
		self.server_number = ((self.server_number + 1) % len(self.subdomains))
		return self.url_template.netloc.replace("{s}", self.subdomains[self.server_number])

	# Returns the path for the GET request to retrieve a particular tile.
	# This implements the simple case of a URL template. Override in
	# derived classes in order to support other schemes.
	def get_path(self, zoom, x, y):
		path = self.url_template.path
		if self.url_template.query:
			path = "%s?%s" % (path, self.url_template.query)

		if self.api_key:
			path = path.replace("{api_key}", self.api_key)

		# Basic (x, y) and zoom, Leaflet-style
		path = path.replace('{z}', str(zoom)).replace('{x}', str(x)).replace('{y}', str(y))

		## Quadtree (#Q in OsmGpsMap)
		#if path.find("{Q}") != -1:
		#	q = "t"
		#	for n in range(zoom-1, -1, -1):
		#		digit = 0
		#		if (x >> n) & 1:
		#			digit += 1
		#		if (y >> n) & 1:
		#			digit += 2
		#		q += "qrts"[digit]
		#	path = path.replace("{Q}", q)

		# Quadtree (#W in OsmGpsMap)
		if path.find("{quadkey}") != -1:
			q = ""
			for n in range(zoom-1, -1, -1):
				digit = 0
				if (x >> n) & 1:
					digit += 1
				if (y >> n) & 1:
					digit += 2
				q += str(digit)
			path = path.replace("{quadkey}", q)

		return path

# Describes a set of TMS raster tiles
class MapTilesetRaster(MapTileset):
	def __init__(self, key, 
			opacity=1.0,				# used to fade out raster tiles
			transparent_color=None,		# color to convert to transparent
			saturation=None,			# <1.0=desaturate, >1.0=increase saturation
			**kwargs
			):
		MapTileset.__init__(self, key, MapRasterTile, **kwargs)
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
		MapTilesetRaster.__init__(self, key, **kwargs)
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
		path = "%s?%s" % (self.url_template.path, urlencode(query_params))
		return path

# Describes a set of vector tiles
class MapTilesetVector(MapTileset):
	def __init__(self, key, tile_class, zoom_max=16, renderer=None, zoom_substitutions=None, **kwargs):
		MapTileset.__init__(self, key, tile_class, zoom_max=zoom_max, **kwargs)
		self.extra_headers["Accept-Encoding"] = "gzip,deflate"
		self.zoom_substitutions = zoom_substitutions
		self.layer_cache_enabled = True
		self.symbols = None

tilesets = MapTilesets()

