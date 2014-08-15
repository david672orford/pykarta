# encoding=utf-8
# pykarta/maps/layers/base.py
# Copyright 2013, 2014, Trinity College
# Last modified: 12 May 2014

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
# Objects to represent loaded tiles
#=============================================================================

# Used for raster image tiles
class MapRasterTile(object):
	def __init__(self, filename=None, data=None, transparent=None, saturation=None):
		if filename is not None:
			pixbuf = pixbuf_from_file(filename)
		elif data is not None:
			pixbuf = pixbuf_from_file_data(data)
		else:
			raise AssertionError

		# See http://www.pygtk.org/pygtk2reference/class-gdkpixbuf.html
		if transparent is not None:
			pixbuf = pixbuf.add_alpha(True, *transparent)
		if saturation is not None:
			pixbuf.saturate_and_pixelate(pixbuf, saturation, False)

		self.tile_surface = surface_from_pixbuf(pixbuf)

	# Draw a 265x265 unit tile at position (xpixoff, ypixoff).
	def draw(self, ctx, xpixoff, ypixoff, opacity):
		ctx.set_source_surface(self.tile_surface, xpixoff, ypixoff)
		ctx.paint_with_alpha(opacity)

# Used for vector tiles
class MapCustomTile(object):
	def __init__(self, filename, zoom, x, y, custom_renderer_class):
		#print "New Custom Tile:", filename
		self.sig = filename
		self.renderer = custom_renderer_class(filename, zoom, x, y)
	def draw(self, ctx, xpixoff, ypixoff, opacity):
		#print "Draw Custom Tile:", self.sig
		self.renderer.draw(ctx, xpixoff, ypixoff, opacity)

#=============================================================================
# Base of all tile layers
#=============================================================================
class MapTileLayer(MapLayer):
	def __init__(self):
		MapLayer.__init__(self)
		self.ram_cache = OrderedDict()
		self.ram_cache_max = 1000
		self.zoom_min = 0
		self.zoom_max = 99
		self.tiles = []
		self.tile_scale_factor = None
		self.int_zoom = None
		self.tile_ranges = None

	def __del__(self):
		print "Map: tile layer %s destroyed" % self.name

	# Called whenever viewport changes
	def do_viewport(self):
		#print "New tiles viewport..."
		lat, lon, zoom = self.containing_map.get_center_and_zoom()
		tile_size = 256
		half_width_in_pixels = self.containing_map.width / 2.0
		half_height_in_pixels = self.containing_map.height / 2.0

		if type(zoom) == int:
			self.int_zoom = zoom
			self.tile_scale_factor = 1.0
		else:
			self.int_zoom = int(zoom + 0.5)
			self.tile_scale_factor = math.pow(2, zoom) / (1 << self.int_zoom)
		#print "zoom:", zoom
		#print "int_zoom:", self.int_zoom
		#print "tile_scale_factor:", self.tile_scale_factor

		# In print mode, try to double the resolution by using tiles
		# for one zoom level higher and scaling them down.
		if self.containing_map.print_mode and self.int_zoom < self.zoom_max:
			if self.tile_scale_factor is None:
				self.tile_scale_factor = 1.0
			self.int_zoom += 1
			self.tile_scale_factor /= 2.0

		# Make a list of the tiles to use used and their positions on the screen.
		self.tiles = []
		self.tile_ranges = None
		if self.int_zoom >= self.zoom_min and self.int_zoom <= self.zoom_max:
			center_tile_x, center_tile_y = project_to_tilespace(lat, lon, self.int_zoom)

			# Find out how many tiles (and factions thereof) are required to reach the edges.
			half_width_in_tiles = half_width_in_pixels / (float(tile_size) * self.tile_scale_factor)
			half_height_in_tiles = half_height_in_pixels / (float(tile_size) * self.tile_scale_factor)

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
			xpixoff = (half_width_in_pixels - (center_tile_x - x_range_start) * tile_size * self.tile_scale_factor) / self.tile_scale_factor
			starting_ypixoff = (half_height_in_pixels - (center_tile_y - y_range_start) * tile_size * self.tile_scale_factor) / self.tile_scale_factor
			tile_size *= 0.998		# shave slightly less than 1/2 pixel in order to prevent rounding gaps between tiles
			for x in range(x_range_start, x_range_end + 1):
				ypixoff = starting_ypixoff
				for y in range(y_range_start, y_range_end + 1):
					#print " Tile:", x, y, xpixoff, ypixoff
					self.tiles.append((self.int_zoom, x % (1 << self.int_zoom), y, xpixoff, ypixoff))
					ypixoff += tile_size
				xpixoff += tile_size

			self.tile_ranges = (x_range_start, x_range_end, y_range_start, y_range_end)

	# Called whenever redrawing required
	def do_draw(self, ctx):
		#print "Draw tiles..."
		ctx.scale(self.tile_scale_factor, self.tile_scale_factor)

		progress = 1
		for tile in self.tiles:
			if not self.containing_map.lazy_tiles:
				numtiles = len(self.tiles)
				self.containing_map.feedback.progress(progress, numtiles, _("Downloading {layername} tile {progress} of {numtiles}").format(layername=self.name, progress=progress, numtiles=numtiles))
			zoom, x, y, xpixoff, ypixoff = tile

			tile = self.load_tile_cached(zoom, x, y, True)
			if tile is not None:
				tile.draw(ctx, xpixoff, ypixoff, self.opacity)

			else:
				for lower_zoom in range(zoom-1, self.zoom_min-1, -1):
					zoom_diff = zoom - lower_zoom
					bigger_tile = self.load_tile_cached(lower_zoom, x >> zoom_diff, y >> zoom_diff, False)
					if bigger_tile != None:
						ctx.save()
						ctx.translate(xpixoff, ypixoff)
						ctx.rectangle(0, 0, 256, 256)
						ctx.clip()
						scale = 1 << zoom_diff
						pixels = 256 >> zoom_diff
						mask = scale - 1
						ctx.scale(scale, scale)
						bigger_tile.draw(ctx, -(pixels * (x & mask)), -(pixels * (y & mask)), self.opacity)
						ctx.restore()
						break

			progress += 1

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


