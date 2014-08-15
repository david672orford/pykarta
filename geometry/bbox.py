# encoding=utf-8
# pykarta/geometry/bbox.py
# Copyright 2013, Trinity College Computing Center
# Last modified: 14 August 2013

from point import Point

# This object is used when we need to create or manipulate bounding boxes.
class BoundingBox(object):
	def __init__(self, init=None):
		if init is None:
			self.reset()
		elif isinstance(init, BoundingBox):
			self.min_lat = init.min_lat
			self.max_lat = init.max_lat
			self.min_lon = init.min_lon
			self.max_lon = init.max_lon
			self.valid = init.valid
		elif len(init) == 4:
			# Order used by Openlayers
			self.min_lon, self.min_lat, self.max_lon, self.max_lat = init
			self.valid = True
		else:
			raise ValueError

	def reset(self):
		self.min_lat = None
		self.max_lat = None
		self.min_lon = None
		self.max_lon = None
		self.valid = False

	def __str__(self):
		if self.valid:
			return "min_lon=%f max_lon=%f min_lat=%f, max_lat=%f" % (self.min_lon, self.max_lon, self.min_lat, self.max_lat)
		else:
			return "<invalid>"

	## Used only by Openlayers border editor
	#def as_rectangle(self):
	#	if self.valid:
	#		return (
	#			Point(self.min_lat, self.min_lon),	# bottom left
	#			Point(self.min_lat, self.max_lon),	# bottom right
	#			Point(self.max_lat, self.max_lon),	# top right
	#			Point(self.max_lat, self.min_lon),	# top left
	#			Point(self.min_lat, self.min_lon),	# bottom left again
	#			)
	#	else:
	#		return None

	def as_polygon(self):
		from polygon import Polygon
		if self.valid:
			return Polygon((
				Point(self.min_lat, self.min_lon),	# bottom left
				Point(self.min_lat, self.max_lon),	# bottom right
				Point(self.max_lat, self.max_lon),	# top right
				Point(self.max_lat, self.min_lon),	# top left
				))
		else:
			return None

	def _go_valid(self):
		if not self.valid:
			self.min_lat = 90
			self.max_lat = -90
			self.min_lon = 180
			self.max_lon = -180
			self.valid = True

	def add_point(self, point):
		self._go_valid()
		self.min_lat = min(self.min_lat, point.lat)
		self.max_lat = max(self.max_lat, point.lat)
		self.min_lon = min(self.min_lon, point.lon)
		self.max_lon = max(self.max_lon, point.lon)

	def add_points(self, points):
		for point in points:
			self.add_point(point)

	def add_bbox(self, bbox):
		if not isinstance(bbox, BoundingBox): raise TypeError
		self._go_valid()
		self.min_lat = min(self.min_lat, bbox.min_lat)		
		self.max_lat = max(self.max_lat, bbox.max_lat)		
		self.min_lon = min(self.min_lon, bbox.min_lon)		
		self.max_lon = max(self.max_lon, bbox.max_lon)		

	# Return the point at the center of the bounding box.
	def center(self):
		if self.valid:
			return Point( (self.max_lat + self.min_lat) / 2, (self.max_lon + self.min_lon) / 2 )
		else:
			return None

	# Does the bounding box contain the indicated point?
	def contains_point(self, point):
		return (point.lat >= self.min_lat and point.lat <= self.max_lat and point.lon >= self.min_lon and point.lon <= self.max_lon)

	# Do the bounding boxes overlap?
	def overlaps(self, other):
		if self.valid and other.valid:
			# See: http://rbrundritt.wordpress.com/2009/10/03/determining-if-two-bounding-boxes-overlap/
			# Distance between centers on horizontal and vertical axes

			#rabx = abs(self.min_lon + self.max_lon - b_left - b_right)
			rabx = abs(self.min_lon + self.max_lon - other.min_lon - other.max_lon)

			#raby = abs(self.max_lat + self.min_lat - b_top - b_bottom)
			raby = abs(self.max_lat + self.min_lat - other.max_lat - other.min_lat)

			# Sums of radii on horizontal and vertical axes
			#raxPrbx = self.max_lon - self.min_lon + b_right - b_left
			raxPrbx = self.max_lon - self.min_lon + other.max_lon - other.min_lon

			#rayPrby = self.max_lat - self.min_lat + b_top - b_bottom
			rayPrby = self.max_lat - self.min_lat + other.max_lat - other.min_lat

			if rabx <= raxPrbx and raby <= rayPrby:
				return True
		return False

	# Expand (or theoretically shrink) the bounding box around its center.
	# We used this to leave extra space around the enclosed objects.
	def scale(self, factor):
		if self.valid:
			scaled_half_width = (self.max_lon - self.min_lon) * factor / 2.0
			scaled_half_height = (self.max_lat - self.min_lat) * factor / 2.0
			center_lat, center_lon = self.center()
			self.min_lat = center_lat - scaled_half_height
			self.max_lat = center_lat + scaled_half_height
			self.min_lon = center_lon - scaled_half_width
			self.max_lon = center_lon + scaled_half_width

