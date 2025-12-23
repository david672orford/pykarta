# encoding=utf-8
#=============================================================================
# pykarta/maps/base.py
# Copyright 2013--2021, Trinity College
# Last modified: 26 December 2021
#=============================================================================


import os
import sys
import math
import cairo
import weakref

from pykarta.geometry import Point, BoundingBox
from pykarta.geometry.projection import project_to_tilespace, unproject_from_tilespace
import pykarta.maps.symbols
from pykarta.maps.layers import MapLayerBuilder, map_layer_sets, MapCacheCleaner
import pykarta.misc

cache_cleaner_thread = None

#=============================================================================
# Common code for both the map widget and the map printer
#=============================================================================
class MapBase(object):
	lazy_tiles = False			# Load tiles asyncronously?
	print_mode = False			# Need higher resolution?

	def __init__(self, tile_source="osm-default", tile_cache_basedir=None, feedback=None, debug_level=0, offline=False):
		if tile_cache_basedir is not None:
			self.tile_cache_basedir = tile_cache_basedir
		else:
			self.tile_cache_basedir = os.path.join(pykarta.misc.get_cachedir(), "map_tiles")

		# If the user has not supplied a custom MapFeedback object,
		# create a generic one for him.
		if feedback is not None:
			self.feedback = feedback
		else:
			self.feedback = MapFeedback(debug_level=debug_level)
		self.feedback.debug(1, "__init__")

		self.offline = offline

		# Default Settings
		self.zoom_min = 0		# at level 0 the whole Earth fits on one tile
		self.zoom_max = 18
		self.zoom_step = 0.2

		# Initial State
		self.lat = 0.0
		self.lon = 0.0
		self.zoom = 4
		self.width = None
		self.height = None
		self.previous_dimensions = [None, None]		# for detecting size changes
		self.rotate = False
		self.symbols = pykarta.maps.symbols.MapSymbolSet()
		self.zoom_cb = None
		self.layers_group_1 = []
		self.layers_group_2 = []
		self.layers_ordered = []
		self.layers_byname = {}
		self.layers_osd = []
		self.updated_viewport = True
		self.top_left_pixel = None

		if tile_source is not None:
			self.feedback.debug(1, "Initial tile source: %s" % repr(tile_source))
			self.set_tile_source(tile_source)

		global cache_cleaner_thread
		if cache_cleaner_thread is None:
			self.feedback.debug(1, "Starting cache cleaner thread...")
			cache_cleaner_thread = MapCacheCleaner(self.tile_cache_basedir)
			cache_cleaner_thread.start()

	# When the map goes out of scope, check the layers to see whether
	# they will go out of scope too. Warn if they won't.
	def __del__(self):
		self.feedback.debug(1, "deallocated")

		# Our reference, plus the reference created by the test, plus the two
		# that we clear in the next step should be the only ones.
		for layer in self.layers_ordered:
			self.feedback.debug(1, "layer %s has %d extra reference(s)" % (layer.name, sys.getrefcount(layer)-4))

		# Layers will have references to feedback, so drop them before testing.
		self.layers_byname = {}
		self.layers_ordered = []

		# Our reference, plus the reference created by the test should be the only ones.
		self.feedback.debug(1, "self.feedback has %d extra reference(s)" % (sys.getrefcount(self.feedback)-2))

	# This must be called whenever the center point, the zoom level,
	# or the window size changes.
	def _viewport_changed(self):
		if self.width is not None:	# if not too soon,

			# Find the location of the top-left pixel in tilespace. We will use
			# this to convert other coordinates from tilespace to drawing
			# area space.
			x, y = project_to_tilespace(self.lat, self.lon, self.zoom)
			self.top_left_pixel = (
				x - (self.width  / 2.0 / 256.0),
				y - (self.height / 2.0 / 256.0),
				)
			#print("Map top left:", self.top_left_pixel)
	
			self.queue_draw()

		self.updated_viewport = True

	#------------------------------------------------------------------------
	# Public methods: widget
	#------------------------------------------------------------------------

	# Noop here, but overridden in Gtk widget
	def queue_draw(self):
		pass

	#------------------------------------------------------------------------
	# Public Methods: Projection
	#------------------------------------------------------------------------

	# Convert a position in latitude and longitude into a pixel position measured
	# from the top-left corner of the widget's current drawing area.
	def project_point(self, point):
		x, y = project_to_tilespace(point.lat, point.lon, self.zoom)
		return (int((x - self.top_left_pixel[0]) * 256), int((y - self.top_left_pixel[1]) * 256))

	# Apply project_point() to a list of points
	def project_points(self, points):
		return list(map(self.project_point, points))

	# Take a list of points which have already been passed through
	# project_to_tilespace() return a new list with them converted
	# to coordinates according to the current viewport.
	def scale_points(self, projected_points):
		n = 2 ** self.zoom
		return list([(int((p[0] * n - self.top_left_pixel[0]) * 256), int((p[1] * n - self.top_left_pixel[1]) * 256)) for p in projected_points])

	# Convert screen coordinates to latitude and longitude.
	# Returns: (lat, lon)
	def unproject_point(self, x, y):
		tile_x = self.top_left_pixel[0] + x / 256.0
		tile_y = self.top_left_pixel[1] + y / 256.0
		return Point(unproject_from_tilespace(tile_x, tile_y, self.zoom))
	def unproject_points(self, points):
		result = []
		for point in points:
			result.append(self.unproject_point(*point))
		return result

	#------------------------------------------------------------------------
	# Public Methods: Viewport
	#------------------------------------------------------------------------

	# Move map by the indicated number of pixels.
	# More positive y is more south, more positive x is more east.
	#
	# NOTE: This functions works in the same way as scroll() in Osmgpsmap,
	# however the Osmgpsmap docs incorrectly state that positive is north or east.
	def scroll(self, x, y):
		self.feedback.debug(1, "scroll(x=%d, y=%d)" % (x, y))
		if x == 0.0 and y == 0.0:
			return
		center_x = self.width / 2.0
		center_y = self.height / 2.0
		center = self.unproject_point(center_x + x, center_y + y)
		self.set_center(center.lat, center.lon)

	# Return the bounding box of the visible map.
	def get_bbox(self):
		p1 = self.unproject_point(0, 0)
		p2 = self.unproject_point(self.width, self.height)
		bbox = BoundingBox()
		bbox.add_point(p1)
		bbox.add_point(p2)
		return bbox

	# Unconditionally zoom to a specified level.
	def set_zoom(self, zoom):
		self.feedback.debug(1, "set_zoom(%f)" % zoom)
		zoom = min(max(zoom, self.zoom_min), self.zoom_max)
		if zoom != self.zoom:	# if changed,
			self.zoom = zoom
			if self.zoom_cb:
				self.zoom_cb(zoom)
			self._viewport_changed()
		return zoom

	# Get current zoom level of map.
	# The levels start at 0 (furthest out) and go to 16 or 18.
	def get_zoom(self):
		return self.zoom

	# Zoom in in or out one step
	def zoom_in(self):
		self.feedback.debug(1, "zoom in")
		return self._set_zoom_rounded(self.zoom + self.zoom_step)
	def zoom_out(self):
		self.feedback.debug(1, "zoom out")
		return self._set_zoom_rounded(self.zoom - self.zoom_step)
	def _set_zoom_rounded(self, zoom):
		return self.set_zoom(int((zoom + 0.001) / self.zoom_step) * self.zoom_step)

	# Supply a function to be called each time the zoom level changes. This can
	# be used to display the zoom level somewhere in the user interface.
	def set_zoom_cb(self, function):
		self.zoom_cb = function
		self.zoom_cb(self.zoom)

	# Scroll (but do not zoom) the map so that the indicated point is in the center.
	def set_center(self, lat, lon):
		self.feedback.debug(1, "set_center(%f, %f)" % (lat, lon))

		# This projection does not go all the way to the poles.
		lat = min(85.0, max(-85.0, lat))

		# wrap at 180 degrees
		if lon > 180.0:
			lon -= 360.0
		elif lon < -180.0:
			lon += 360.0

		if lat != self.lat or lon != self.lon:
			self.lat = lat
			self.lon = lon
			self._viewport_changed()

	# Move the map only if the difference will be more than the indicated
	# number of pixels. This can be used to move the map to the position
	# of a GPS fix without quickly running down the battery on portable
	# devices due to position jitter.
	# FIXME: This implementation does not take into account the difference
	# in size between a degree of latitude and a degree of longitude.
	def set_center_damped(self, lat, lon, pixels=1.0):
		pos_threshold = 360.0 / 256.0 / (2.0 ** self.zoom) / pixels
		if abs(lat - self.lat) >= pos_threshold or (abs(lon - self.lon) % 360.0) >= pos_threshold:
			#print("Damped map move")
			self.set_center(lat, lon)

	# Return the current center point and zoom level of the map.
	# returns: (lat, lon, zoom)
	def get_center_and_zoom(self):
		return (self.lat, self.lon, self.zoom)

	# lat, lon, zoom
	def set_center_and_zoom(self, lat, lon, zoom):
		self.feedback.debug(1, "set_center_and_zoom(%f, %f, %d)" % (lat, lon, zoom))
		self.set_center(lat, lon)
		self.set_zoom(zoom)

	# Like above but will not zoom out if the map is already zoomed in furthur than indicated.
	def set_center_and_zoom_in(self, lat, lon, minzoom):
		self.feedback.debug(1, "set_center_and_zoom_in(%f, %f, %d)" % (lat, lon, minzoom))
		zoom = max(self.get_zoom(), minzoom)
		self.set_center_and_zoom(lat, lon, zoom)

	# Zoom and position the map to show a particular area defined by bounding box.
	def zoom_to_extent(self, bbox, padding=10, rotate_ok=False):
		self.feedback.debug(1, "zoom_to_extent(bbox, padding=%d, rotate_ok=%s)" % (padding, str(rotate_ok)))
		center = bbox.center()
		if center:		# If there is at least one point in the bbox,

			# Center on the bounding box and zoom to an arbitrarily selected level.
			lat, lon = center
			self.set_center_and_zoom(lat, lon, 16)

			# Figure out the size of the bounding box in pixels at this zoom level.
			p1 = Point(bbox.max_lat, bbox.min_lon)	# top left
			p2 = Point(bbox.min_lat, bbox.max_lon)	# bottom right
			p1x, p1y = self.project_point(p1)
			p2x, p2y = self.project_point(p2)
			width = (p2x - p1x)
			height = (p2y - p1y)

			# Avoid division by zero
			width = max(width, 1)
			height = max(height, 1)

			self.feedback.debug(1, " extent pixel dimensions: %f x %f" % (width, height))
			self.feedback.debug(1, " map pixel dimensions: %f x %f" % (self.width, self.height))
			if rotate_ok:
				if self.rotate:
					page_landscape = self.height > self.width
				else:
					page_landscape = self.width > self.height
				extent_landscape = width > height
				print(" extent_landscape:", extent_landscape)
				print(" page_landscape:", page_landscape)
				self.set_rotation(extent_landscape != page_landscape and self.oblongness(width, height) > 0.1)

			x_zoom_diff = math.log(float(width) / float(self.width - 2*padding), 2)
			y_zoom_diff = math.log(float(height) / float(self.height - 2*padding), 2)
			#print("x_zoom_diff:", x_zoom_diff)
			#print("y_zoom_diff:", y_zoom_diff)
			self.set_zoom(16 - max(x_zoom_diff, y_zoom_diff))

	@staticmethod
	def oblongness(width, height):
		smaller_dimension = min(width, height)
		larger_dimension = max(width, height)
		result = float(larger_dimension - smaller_dimension) / float(smaller_dimension)
		print(" oblongness:", width, height, result)
		return result

	# If the indicated point is not within the viewport, zoom out
	# (if necessary) and reposition the map so that both it and 
	# most of what was already visible are visible.
	#
	# FIXME: These are both a bit of a hack. For example, we have to
	# avoid calling zoom_to_extent() if the point is well within the
	# viewport since otherwise the center would creap. This is probably
	# due to the differences between the lat, lon center and the 
	# projected center.
	def make_visible(self, lat, lon):
		self.feedback.debug(1, "make_visible(%f, %f)" % (lat, lon))
		bbox = BoundingBox(self.get_bbox())
		bbox.scale(0.9)
		point = Point(lat, lon)
		if not bbox.contains_point(point):
			bbox.add_point(point)
			self.zoom_to_extent(bbox)

	# Same as above, but for polygon
	def make_visible_polygon(self, points):
		self.feedback.debug(1, "make_visible_polygon(%s)" % str(points))
		bbox = BoundingBox(init=self.get_bbox())
		bbox.scale(0.9)
		count = 0
		for point in points:
			if not bbox.contains_point(point):
				bbox.add_point(point)
				count += 1
		if count:
			self.zoom_to_extent(bbox)

	# This is called by the MapWidget and MapPrint subclasses to change
	# to match the size of the provided drawing surface.
	def set_size(self, width, height):
		self.feedback.debug(1, "set_size(%d, %d)" % (int(width), int(height)))
		if self.previous_dimensions != (width, height):
			if self.rotate:
				self.width, self.height = height, width
			else:
				self.width, self.height = width, height
			self.previous_dimensions = (width, height)
			self._viewport_changed()

	# Should the map be rotated 90 degrees in order to better show the desired region?
	def set_rotation(self, rotate):
		self.feedback.debug(1, "set_rotation(%s)" % str(rotate))
		if rotate != self.rotate:
			self.rotate = rotate
			self.width, self.height = self.height, self.width
			self._viewport_changed()

	#------------------------------------------------------------------------
	# Public Methods: Layers
	#------------------------------------------------------------------------

	# Called to inform active (top) layer that the drawing tool has been changed.
	# (This is for certain vector layers.)
	def set_tool(self, tool):
		return self.layers_ordered[len(self.layers_ordered)-1].set_tool(tool)

	# Add a layer to this map
	def add_layer(self, layer_name, layer_obj, group=3):
		""" add a layer object to the map """
		self.feedback.debug(1, "add_layer(\"%s\", ...)" % layer_name)
		assert not layer_name in self.layers_byname, "layer already added"

		layer_obj.name = layer_name

		# Tell the layer that we are adding it to the map
		layer_obj.set_map(weakref.proxy(self))

		# Actually add the layer to the map.
		self.layers_byname[layer_name] = layer_obj
		if group == 1:
			self.layers_ordered.insert(len(self.layers_group_1), layer_obj)
			self.layers_group_1.append(layer_name)
		elif group == 2:
			self.layers_ordered.insert(len(self.layers_group_1) + len(self.layers_group_2), layer_obj)
			self.layers_group_2.append(layer_name)
		else:
			self.layers_ordered.append(layer_obj)

		# If this is the first layer in group 1, let it determine
		# the min and max zoom levels.
		if group == 1 and self.layers_group_1[0] == layer_name:
			self._inspect_base_layer(layer_obj)

		# This layer has not yet been drawn
		layer_obj.set_stale()
		layer_obj.redraw()			# FIXME: may be redundant

		return layer_obj

	# This is called on the base layer so that we can bring the map
	# into its max zoom limits.
	def _inspect_base_layer(self, layer_obj):
		try:
			self.zoom_min = layer_obj.zoom_min
			self.zoom_max = layer_obj.zoom_max
		except:
			self.zoom_min = 0
			self.zoom_max = 18
		self.set_zoom(self.zoom)        # bring zoom within limits

	def get_layer(self, layer_name):
		""" retrieve the layer object for the named layer """
		return self.layers_byname.get(layer_name)

	def remove_layer(self, layer_name):
		""" removed the named layer from the map """
		self.feedback.debug(1, "remove_layer(\"%s\")" % layer_name)
		assert(layer_name in self.layers_byname)
		layer_obj = self.layers_byname[layer_name]
		del self.layers_byname[layer_name]
		if layer_name in self.layers_group_1:
			self.layers_group_1.remove(layer_name)
		if layer_name in self.layers_group_2:
			self.layers_group_2.remove(layer_name)
		self.layers_ordered.remove(layer_obj)
		self.queue_draw()
		return layer_obj

	# This raises the named layer to the top and tells it to enable editing.
	def raise_layer_to_top(self, layer_name):
		self.feedback.debug(1, "raise_layer_to_top(\"%s\")" % layer_name)
		layer_obj = self.layers_byname[layer_name]
		i = self.layers_ordered.index(layer_obj)
		if i != (len(self.layers_ordered)-1):		# if not already on top

			# Tell the layer currently on top that we are taking its active tool away.
			self.layers_ordered[len(self.layers_ordered)-1].set_tool(None)

			# Remove the layer and put it back at the end.
			self.layers_ordered.pop(i)
			self.layers_ordered.append(layer_obj)

			self.queue_draw()

	# Add an On Screen Display layer.
	def add_osd_layer(self, layer_obj):
		self.feedback.debug(1, "add_osd_layer(%s)" % str(layer_obj))
		layer_obj.set_map(weakref.proxy(self))
		self.layers_osd.append(layer_obj)
		layer_obj.set_stale()
		return layer_obj

	# Convenience function
	# Replace the base layer or layers with the layers named in
	# tile_source (which may be either a list or a string).
	def set_tile_source(self, tile_source):
		self.feedback.debug(1, "set_tile_source(%s)" % str(tile_source))

		# Accept either a string or a list of strings.
		#if isinstance(tile_source, basestring):
		if isinstance(tile_source, str):
			tile_source = [tile_source]

		# Expand layer sets into their component layers.
		temp = []
		for layer_name in tile_source:
			if layer_name in map_layer_sets:
				temp.extend(map_layer_sets[layer_name])
			else:
				temp.append(layer_name)
		tile_source = temp

		# If this is a different tile source...
		if self.layers_group_1 != tile_source:
			# Remove the existing base layers.
			for layer_name in self.layers_group_1[:]:
				self.remove_layer(layer_name)

			# Create and add the new layers.
			for layer_name in tile_source:
				layer_obj = MapLayerBuilder(layer_name)
				self.add_layer(layer_name, layer_obj, group=1)
			self.base_layer_names = tile_source

			# Bring zoom within limits defined by bottom layer.
			self.set_zoom(self.zoom)

	# Change the offline mode of the map.
	# The layers must be informed.
	def set_offline(self, offline):
		if offline != self.offline:
			self.offline = offline
			i = 0
			for layer in self.layers_ordered:
				# Retrigger layer setup
				layer.set_map(layer.containing_map)
				# Layer setup may have retrieved max zoom.
				if i == 0:
					self._inspect_base_layer(layer)
				i += 1
		self.queue_draw()

#=============================================================================
# This encapsulates debugging and progress indication so that we can
# pass them as a single object to the threads.
#
# You can customize the display of this information either by:
# 1) Creating your own instance of this object, configurating the callback
#    handlers, and passing that to the map object constructor
# 2) Creating a derived class and passing that to the map object
#    constructor
#=============================================================================
class MapFeedback(object):
	def __init__(self, debug_level=1, debug_callback=None, progress_callback=None):
		self.debug_level = debug_level
		self.debug_callback = pykarta.misc.BoundMethodProxy(debug_callback) if debug_callback else None
		self.progress_callback = pykarta.misc.BoundMethodProxy(progress_callback) if progress_callback else None

		self.step = 0
		self.steps = 1

	def __del__(self):
		print("Map: feedback deallocated")

	def debug(self, level, message):
		if self.debug_callback:
			self.debug_callback(level, message)
		elif level <= self.debug_level:
			print("Map:", message)

	def error(self, message):
		if self.progress_callback:
			self.progress_callback(None, None, message)
		else:
			print("Map Error:", message)

	def progress_step(self, step=0, steps=1):
		self.step = step
		self.steps = steps

	def progress(self, finished, total, message):
		if self.progress_callback:
			fraction = (self.step / float(self.steps)) + float(finished) / float(total) / float(self.steps)
			self.progress_callback(fraction, 1.0, message)
		else:
			print("Map Progress: %f of %f: %s" % (finished, total, message))

#=============================================================================
# Map which can be drawn directly on a Cairo context. This is used when
# generating PDF files or when printing.
#=============================================================================
class MapCairo(MapBase):
	print_mode = True

	def draw_map(self, ctx):
		self.feedback.debug(1, "draw_map(ctx)")

		if not isinstance(ctx, cairo.Context):
			raise TypeError
		assert(self.width is not None and self.height is not None)

		ctx.save()

		if self.rotate:
			ctx.rotate(math.pi / -2.0)					# 90 degrees counter clockwise
			ctx.translate(-self.width, 0)

		ctx.rectangle(0, 0, self.width, self.height)
		ctx.clip()

		finished = 0
		for layer in self.layers_ordered:
			self.feedback.progress_step(finished, len(self.layers_ordered))
			self.feedback.debug(2, "drawing layer: %s" % str(layer))
			layer.do_viewport()
			ctx.save()
			layer.do_draw(ctx)
			ctx.restore()
			finished += 1

		for layer in self.layers_osd:
			self.feedback.debug(2, "drawing layer: %s" % str(layer))
			layer.do_viewport()
			ctx.save()
			layer.do_draw(ctx)
			ctx.restore()

		ctx.restore()

