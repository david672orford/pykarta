# encoding=utf-8
# pykarta/maps/layers/osd.py
# Copyright 2013--2021, Trinity College
# Last modified: 26 December 2021


import cairo
import math

from .base import MapLayer
from ...geometry import Point
from ...geometry.projection import radius_of_earth

#=============================================================================
# On Screen Display layers
#=============================================================================

class MapLayerCropbox(MapLayer):
	def __init__(self):
		MapLayer.__init__(self)
		self.cropbox = None

	def set_cropbox(self, cropbox):
		self.cropbox = cropbox
		self.redraw()

	def get_cropbox(self):
		return self.cropbox

	def do_draw(self, ctx):
		# width, height, margin
		if self.cropbox:
			center_x = self.containing_map.width / 2
			center_y = self.containing_map.height / 2
			half_width = self.cropbox[0] / 2 - self.cropbox[2]
			half_height = self.cropbox[1] / 2 - self.cropbox[2]
	
			# Top
			ctx.move_to(center_x - half_width - 25, center_y - half_height)
			ctx.line_to(center_x + half_width + 25, center_y - half_height)
	
			# Bottom
			ctx.move_to(center_x - half_width - 25, center_y + half_height)
			ctx.line_to(center_x + half_width + 25, center_y + half_height)
	
			# Left
			ctx.move_to(center_x - half_width, center_y - half_height - 25)
			ctx.line_to(center_x - half_width, center_y + half_height + 25)
	
			# Right
			ctx.move_to(center_x + half_width, center_y - half_height - 25)
			ctx.line_to(center_x + half_width, center_y + half_height + 25)
	
			ctx.set_source_rgb(0.0, 0.0, 0.0)
			ctx.set_line_width(1)
			ctx.stroke()

class MapLayerScale(MapLayer):
	def __init__(self):
		MapLayer.__init__(self)
		self.scale_width_min = 100
		self.scale_width_max = 300
		self.scale_width_percentage = 15
		self.scale_dimensions = None

	# Compute the dimensions for the scale indicator.
	def do_viewport(self):
		#print("Adjusting map scale indicator")
		bbox = self.containing_map.get_bbox()

		scale_width = self.containing_map.width * self.scale_width_percentage / 100
		scale_width = max(self.scale_width_min, scale_width)
		scale_width = min(self.scale_width_max, scale_width)

		# How many meters are in 180 degrees of longitude at the latitude at the center of the map?
		half_parallel_in_meters = radius_of_earth * math.pi * math.cos(math.radians(self.containing_map.lat))

		# Knowing that we can compute the width in meters of area shown in the viewport.
		viewport_width_in_meters = (bbox.max_lon - bbox.min_lon) / 180.0 * half_parallel_in_meters

		# How many meters will fit in max_width pixels?
		max_meters = viewport_width_in_meters * (float(scale_width) / float(self.containing_map.width))

		# How may digits do we have to take off to get a one digit number?
		trailing_zeros = int(math.log10(max_meters))

		# What is the maximum value of the first digit?
		first_digit_max = max_meters / math.pow(10, trailing_zeros)

		# How may pixels will each tick of the first digit cover?
		first_digit_pixels = scale_width / first_digit_max

		if trailing_zeros == 0:
			units = "meters"
		elif trailing_zeros < 3:
			units = "1" + "0" * trailing_zeros + "x meters"
		else:
			trailing_zeros -= 3
			if trailing_zeros == 0:
				units = "kilometers"
			else:
				units = "1" + "0" * trailing_zeros + "x kilometers"

		self.scale_dimensions = (scale_width, first_digit_pixels, int(first_digit_max), units)

	def do_draw(self, ctx):
		#print("Drawing map scale:", self.scale_dimensions)
		(scale_width, first_digit_pixels, first_digit_max, units) = self.scale_dimensions

		# Bottom right
		ctx.translate(self.containing_map.width - scale_width - 10, self.containing_map.height - 25)

		# Draw scale
		ctx.move_to(0, 0)						# base line
		ctx.line_to(scale_width, 0)
		for i in range(0, first_digit_max+1):	# ticks
			x = i * first_digit_pixels
			ctx.move_to(x, 0)
			ctx.line_to(x, -10)
		ctx.set_line_cap(cairo.LINE_CAP_ROUND)
		ctx.set_line_width(3)
		ctx.set_source_rgb(1.0, 1.0, 1.0)
		ctx.stroke_preserve()
		ctx.set_line_width(1)
		ctx.set_source_rgb(0.0, 0.0, 0.0)
		ctx.stroke()

		# Tick labels
		ctx.select_font_face("sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size(8)
		for i in range(0, first_digit_max+1):
			x = i * first_digit_pixels
			ctx.move_to(x-3, 9)
			ctx.text_path(str(i))

		# Description of units
		ctx.set_font_size(10)
		ctx.move_to(-3, 17)
		ctx.text_path(units)

		ctx.set_line_width(2)
		ctx.set_source_rgb(1.0, 1.0, 1.0)	# white halo
		ctx.stroke_preserve()
		ctx.set_source_rgb(0.0, 0.0, 0.0)	# black letters
		ctx.fill()

class MapLayerAttribution(MapLayer):
	def do_draw(self, ctx):
		x = 5
		y = self.containing_map.height - 5
		ctx.select_font_face("sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size(8)
		ctx.set_source_rgb(0.0, 0.0, 0.0)
		printed = set([])		# deduplicate
		for layer in self.containing_map.layers_ordered:
			attribution = layer.opts.attribution
			if attribution and attribution not in printed:
				if isinstance(attribution, cairo.ImageSurface):
					height = attribution.get_height()
					ctx.set_source_surface(attribution, x, y-height)
					ctx.paint()
					y -= height
				else:
					ctx.move_to(x, y)
					ctx.text_path(attribution)
					ctx.set_line_width(1.5)
					ctx.set_source_rgb(1.0, 1.0, 1.0)	# white halo
					ctx.stroke_preserve()
					ctx.set_source_rgb(0.0, 0.0, 0.0)	# black letters
					ctx.fill()
					y -= 10
				printed.add(attribution)

#========================================================================
# Live GPS position layer
#========================================================================

class MapLayerLiveGPS(MapLayer):
	def __init__(self):
		MapLayer.__init__(self)
		self.marker_radius = 10

		self.fix = None
		self.screen_gps_pos = None
		self.screen_gps_arrow = None
		self.onscreen = False

	# Set the position, orientation, etc. of the GPS marker.
	# In order to prevent excessive redraws, we accept the position only if at
	# least one of the following conditions is met:
	# * The position difference is at least one pixel
	# * The bearing differs by at least five degrees
	# * The length of the speed indicator will differ by at least one pixel
	def set_marker(self, fix):
		pos_threshold = 360.0 / 256.0 / (2.0 ** self.containing_map.get_zoom())
		if fix is None or self.fix is None \
				or abs(fix.lat - self.fix.lat) >= pos_threshold \
				or (abs(fix.lon - self.fix.lon) % 360.0) >= pos_threshold \
				or (fix.heading is None != self.fix.heading is None) \
				or (abs(fix.heading - self.fix.heading) % 360.0) >= 5.0 \
				or abs(fix.speed - self.fix.speed) >= 1.0:
			print("GPS marker moved")
			self.fix = fix

			# If the marker is in the viewport (or just was), refresh layer.
			now_onscreen = self.containing_map.get_bbox().contains_point(Point(fix.lat, fix.lon)) if fix else False
			if now_onscreen or self.onscreen:
				self.set_stale()
			self.onscreen = now_onscreen

	# This is called whenever the map viewport changes.
	def do_viewport(self):
		self.screen_gps_pos = None
		self.screen_gps_arrow = None
		# If GPSd has reported a result which includes location, find
		# the cooresponding pixel position on the canvas.
		if self.fix:
			self.screen_gps_pos = self.containing_map.project_point(Point(self.fix.lat, self.fix.lon))
			# If a heading was reported, prepare to draw a vector.
			if self.fix.heading is not None:
				heading = math.radians(self.fix.heading)
				# If the speed is known, make the vector proportionally longer.
				if self.fix.speed:
					arrow_length = self.marker_radius + self.fix.speed
				else:
					arrow_length = self.marker_radius
				x, y = self.screen_gps_pos
				self.screen_gps_arrow = (
					x + arrow_length * math.sin(heading),
					y - arrow_length * math.cos(heading)
					)

	# Draw or redraw layer
	def do_draw(self, ctx):
		if self.screen_gps_pos:
			x, y = self.screen_gps_pos
			ctx.arc(x, y, self.marker_radius, 0, 2*math.pi)
			ctx.set_line_width(1)
			ctx.set_source_rgb(0.0, 0.0, 0.0)
			ctx.stroke_preserve()
			ctx.set_source_rgba(0.0, 0.0, 1.0, 0.5)
			ctx.fill()

			if self.screen_gps_arrow:
				ctx.move_to(x, y)
				ctx.line_to(*self.screen_gps_arrow)
				ctx.set_line_width(2)
				ctx.set_source_rgb(0.0, 0.0, 0.0)
				ctx.stroke()

