# encoding=utf-8
# pykarta/maps/layers/base.py
# Copyright 2013, 2014, Trinity College
# Last modified: 18 September 2014

import math
import cairo

try:
	from collections import OrderedDict
except ImportError:
	from pykarta.fallback.ordereddict import OrderedDict

from pykarta.maps.image_loaders import surface_from_pixbuf, pixbuf_from_file, pixbuf_from_file_data
from pykarta.maps.projection import *

#=============================================================================
# Base of all map layers
#=============================================================================
class MapLayer(object):
	def __init__(self):
		self.name = None
		self.containing_map = None
		self.stale = False
		self.attribution = None
		self.cache_enabled = False
		self.cache_surface = None

	# Called automatically when the layer is added to the container.
	# It is called again if offline mode is entered or left so that the layer
	# can make any necessary adjustments.
	def set_map(self, containing_map):
		self.containing_map = containing_map

	# Mark layer so that at next redraw its do_viewport() will be called.
	# If the layer has already been added to a map, request a redraw.
	def set_stale(self):
		if not self.stale:
			self.stale = True
			self.redraw()

	# Ask the map to ask this layer to redraw itself.
	def redraw(self):
		if self.containing_map is not None:
			self.containing_map.queue_draw()
		self.cache_surface = None

	# Overridden in editable vector layers
	def set_tool(self, tool):
		pass

	# The viewport has changed. Select objects or tiles and
	# determine their positions.
	def do_viewport(self):
		pass

	# Draw the objects selected and positioned by do_viewport()
	def do_draw(self, ctx):
		pass

	# MapWidget actually calls this instead of calling do_draw() directly.
	def do_draw_cached(self, ctx):
		if self.cache_enabled:
			if self.cache_surface is None:
				self.cache_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.containing_map.width, self.containing_map.height)
				cache_ctx = cairo.Context(self.cache_surface)
				cache_ctx.set_line_join(ctx.get_line_join())
				cache_ctx.set_line_cap(ctx.get_line_cap())
				self.do_draw(cache_ctx)
			else:
				#print "cached"
				pass
			ctx.set_source_surface(self.cache_surface, 0, 0)
			ctx.paint()
		else:
			self.do_draw(ctx)

	# Mouse button pressed down while pointer is over map
	def on_button_press(self, gdkevent):
		return False

	# Mouse button released while pointer is over map
	def on_button_release(self, gdkevent):
		return False

	# Mouse pointer moving over map
	def on_motion(self, gdkevent):
		return False

#=============================================================================
# Base of all tile layers
#=============================================================================
class MapTileLayer(MapLayer):
	def __init__(self):
		MapLayer.__init__(self)
		self.zoom_min = 0
		self.zoom_max = 99
		self.ram_cache_max = 1000
		self.renderer = None
		self.overzoom = False
		self.draw_passes = 1

		self.ram_cache = OrderedDict()
		self.tiles = []
		self.tile_scale_factor = None
		self.zoom = None
		self.int_zoom = None
		self.tile_size = None
		self.tile_ranges = None			# used for precaching

	#def __del__(self):
	#	print "Map: tile layer %s destroyed" % self.name

	# Called whenever viewport changes
	def do_viewport(self):
		#print "New %s tiles viewport..." % self.name

		lat, lon, self.zoom = self.containing_map.get_center_and_zoom()
		self.int_zoom = int(self.zoom + 0.5)		# round to int
		self.tile_scale_factor = math.pow(2, self.zoom) / (1 << self.int_zoom)
		#print "zoom:", self.zoom, self.int_zoom, self.tile_scale_factor

		# If there is no renderer (which means we are using raster tiles)
		# and this map is in print mode (which means higher resolution is needed)
		# and tiles are available at a higher zoom level, then use them instead
		# and scale them down.
		if self.renderer is None and self.containing_map.print_mode and self.int_zoom < self.zoom_max:
			self.int_zoom += 1
			self.tile_scale_factor /= 2.0

		# If the map is zoomed in furthur than this layer goes (which can happen
		# if it is not the first layer), then enlarge the tiles.
		if self.overzoom:
			while self.int_zoom > self.zoom_max:
				self.int_zoom -= 1
				self.tile_scale_factor *= 2.0

		# How many units on the output device (pixels on a screen) will
		# the tile be scaled to cover?
		self.tile_size = 256.0 * self.tile_scale_factor

		# remove gaps due to rounding errors
		#self.tile_scale_factor *= 1.0025
		self.tile_scale_factor *= 1.0027

		# Make a list of the tiles to use used and their positions on the screen.
		self.tiles = []
		self.tile_ranges = None
		if self.int_zoom >= self.zoom_min and self.int_zoom <= self.zoom_max:
			center_tile_x, center_tile_y = project_to_tilespace(lat, lon, self.int_zoom)

			half_width_in_pixels = self.containing_map.width / 2.0
			half_height_in_pixels = self.containing_map.height / 2.0

			# Find out how many tiles (and factions thereof) are required to reach the edges.
			half_width_in_tiles = half_width_in_pixels / float(self.tile_size)
			half_height_in_tiles = half_height_in_pixels / float(self.tile_size)

			# Find the first and last tile row and column which will be at least
			# partially visible inside the viewport.
			x_range_start = int(center_tile_x - half_width_in_tiles)
			x_range_end = int(center_tile_x + half_width_in_tiles + 1)
			y_range_start = int(center_tile_y - half_height_in_tiles)
			y_range_end = int(center_tile_y + half_height_in_tiles + 1)

			# Eliminate tiles that are off the 'edge of the world' at the top
			# or the bottom. (Those that hang off at the left and right will
			# be wrapped around.)
			max_tile_coord = (1 << self.int_zoom) - 1
			y_range_start = max(0, min(max_tile_coord, y_range_start))
			y_range_end = max(0, min(max_tile_coord, y_range_end))

			# Step through the tiles in the grid appending them to a list of
			# those which do_draw() will render.
			# FIXME: in screen mode make sure that the values of xpixoff and ypixoff
			# are always integers.
			xpixoff = (half_width_in_pixels - (center_tile_x - x_range_start) * self.tile_size)
			starting_ypixoff = (half_height_in_pixels - (center_tile_y - y_range_start) * self.tile_size)
			for x in range(x_range_start, x_range_end + 1):
				ypixoff = starting_ypixoff
				for y in range(y_range_start, y_range_end + 1):
					#print " Tile:", x, y, xpixoff, ypixoff
					self.tiles.append((self.int_zoom, x % (1 << self.int_zoom), y, xpixoff, ypixoff))
					ypixoff += self.tile_size
				xpixoff += self.tile_size

			self.tile_ranges = (x_range_start, x_range_end, y_range_start, y_range_end)

	# Called whenever redrawing required
	def do_draw(self, ctx):
		#print "Draw %s tiles..." % self.name

		# Load tiles
		progress = 1
		tile_objs = []
		for zoom, x, y, xpixoff, ypixoff in self.tiles:

			# If this map blocks until all of the tiles are loaded, display progress.
			if not self.containing_map.lazy_tiles:
				numtiles = len(self.tiles)
				self.containing_map.feedback.progress(progress, numtiles, _("Downloading {layername} tile {progress} of {numtiles}").format(layername=self.name, progress=progress, numtiles=numtiles))

			# Load the tile if it is already cached.
			# Request that it be loaded in the background.
			tile_obj = (
				self.load_tile_cached(zoom, x, y, True),
				None, None, None, None
				)

			# Tile not loaded? Search for a lower zoom tile which will do.
			if tile_obj[0] is None:
				for lower_zoom in range(zoom-1, self.zoom_min-1, -1):
					zoom_diff = zoom - lower_zoom
					bigger_tile = self.load_tile_cached(lower_zoom, x >> zoom_diff, y >> zoom_diff, False)
					if bigger_tile is not None:
						subtile_scale_factor = 1 << zoom_diff
						subtile_mask = subtile_scale_factor - 1
						x_adj = -(self.tile_size * (x & subtile_mask))
						y_adj = -(self.tile_size * (y & subtile_mask))
						tile_obj = (None, bigger_tile, subtile_scale_factor, x_adj, y_adj)
						break

			tile_objs.append(tile_obj)
			progress += 1

		# Draw tiles
		for draw_pass in range(self.draw_passes):
			i = 0
			for zoom, x, y, xpixoff, ypixoff in self.tiles:
				#print zoom, x, y, xpixoff, ypixoff
				ctx.save()
				ctx.translate(xpixoff, ypixoff)
	
				tile, bigger_tile, subtile_scale_factor, x_adj, y_adj = tile_objs[i]
	
				if tile is not None:
					tile.draw(ctx, self.tile_scale_factor, draw_pass)
				elif bigger_tile is not None:
					ctx.rectangle(-1, -1, self.tile_size+2, self.tile_size+2)
					ctx.clip()
					ctx.translate(x_adj, y_adj)
					bigger_tile.draw(ctx, self.tile_scale_factor * subtile_scale_factor, draw_pass)
	
				ctx.restore()
				tile_objs.append(tile)
				i += 1

	# This wraps load_tile() and caches the most recently used tiles in RAM.
	def load_tile_cached(self, zoom, x, y, may_download):
		#print "Tile:", zoom, x, y, may_download
		key = (zoom, x, y)
		try:
			result = self.ram_cache.pop(key)	# will reinsert below
			#print " cache hit"
		except KeyError:
			#print " cache miss"
			result = self.load_tile(zoom, x, y, may_download)
			if result == None and not may_download:
				return None
			if len(self.ram_cache) > self.ram_cache_max:		# trim cache?
				self.ram_cache.popitem(last=False)
		self.ram_cache[key] = result
		return result

	def ram_cache_invalidate(self, zoom, x, y):
		try:
			self.ram_cache.pop((zoom, x, y))
		except KeyError:
			print "cache_invalidate(): not in cache", zoom, x, y

	# Return the indicated tile as a Cairo surface. If it is not yet
	# available, return None.
	def load_tile(self, zoom, x, y, may_download):
		return None

#=============================================================================
# Objects to represent loaded tiles
#=============================================================================

# Used for raster image tiles
class MapRasterTile(object):
	def __init__(self, layer, filename=None, data=None):
		if filename is not None:
			pixbuf = pixbuf_from_file(filename)
		elif data is not None:
			pixbuf = pixbuf_from_file_data(data)
		else:
			raise AssertionError

		self.opacity = layer.tileset.opacity

		# See http://www.pygtk.org/pygtk2reference/class-gdkpixbuf.html
		transparent_color = layer.tileset.transparent_color
		if transparent_color is not None:
			pixbuf = pixbuf.add_alpha(True, *transparent_color)

		saturation = layer.tileset.saturation
		if saturation is not None:
			pixbuf.saturate_and_pixelate(pixbuf, saturation, False)

		self.tile_surface = surface_from_pixbuf(pixbuf)

	# Draw a 265x265 unit tile at position (xpixoff, ypixoff).
	def draw(self, ctx, scale, draw_pass):
		ctx.scale(scale, scale)
		ctx.set_source_surface(self.tile_surface, 0, 0)
		ctx.paint_with_alpha(self.opacity)

# Used for vector tiles
class MapCustomTile(object):
	def __init__(self, layer, filename, zoom, x, y):
		self.renderer = layer.renderer(layer, filename, zoom, x, y)
	def draw(self, ctx, scale, draw_pass):
		self.renderer.draw(ctx, scale, draw_pass)

