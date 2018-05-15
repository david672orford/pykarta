# encoding=utf-8
# pykarta/geometry/__init__.py
# Copyright 2013--2018, Trinity College
# Last modified: 15 May 2018

from __future__ import print_function
import math
from .distance import plane_lineseg_distance
from .projection import project_points_sinusoidal

#=============================================================================
# Create an appropriate geometry object from a GeoJSON geometry
#=============================================================================

def GeometryFromGeoJSON(geojson):
	geometry_type = geojson["type"]
	if geometry_type == "Point":
		return Point(geometry=geojson)
	if geometry_type == "MultiPoint":
		return MultiPoint(geometry=geojson)
	if geometry_type == "LineString":
		return LineString(geometry=geojson)
	if geometry_type == "MultiLineString":
		return MultiLineString(geometry=geojson)
	if geometry_type == "Polygon":
		return Polygon(geometry=geojson)
	if geometry_type == "MultiPolygon":
		return MultiPolygon(geometry=geojson)
	if geometry_type == "GeometryCollection":
		return GeometryCollection(geometry=geojson)
	raise TypeError, geometry_type

class GeometryCollection(object):
	def __init__(self, geometry=None):
		assert geometry["type"] == "GeometryCollection"
		self.geometries = []
		for sub_geometry in geometry["geometries"]:
			self.geometries.append(GeometryFromGeoJSON(sub_geometry))
		self.bbox = None

	def get_bbox(self):
		if self.bbox is None:
			self.bbox = BoundingBox()
			for geometry in self.geometries:
				self.bbox.add_bbox(geometry.get_bbox())
		return self.bbox

	def as_geojson(self):
		geometries = []
		for geometry in self.geometries:
			geometries.append(geometry.as_geojson())
		return { "type":"GeometryCollection", "geometries":geometries }

#=============================================================================
# Geographic Points
# The latitude and longitude can either be referred to as
# .lat and .lon or as [0] and [1] respectively.
#=============================================================================

class Point(object):
	__slots__ = ['lat', 'lon']
	def __init__(self, lat=None, lon=None, geometry=None):
		if geometry is not None:	# Point({"type":"Point","coordinates":[lon, lat]})
			assert geometry['type'] == "Point"
			self.lon, self.lat = geometry["coordinates"]
		elif lon is None:
			if lat is None:			# Point()
				self.lat = None
				self.lon = None
			else:					# Point([lat, lon])
				self.lat, self.lon = lat
		else:						# Point(lat, lon)
			self.lat = lat
			self.lon = lon

	# Allow access as to a list of two coordinates
	def __getitem__(self, index):
		if index == 0:
			return self.lat
		elif index == 1:
			return self.lon
		else:
			raise IndexError

	def __str__(self):
		return "(%f, %f)" % (self.lat, self.lon)

	def __eq__(self, other):
		return self.lat == other.lat and self.lon == other.lon

	def __len__(self):
		return 2

	def as_str_decimal(self):
		"Convert to string in degrees with decimal point"
		return str(self)

	def as_str_dms(self):
		"Convert to string in degrees, minutes and seconds."
		return ( u"(%s, %s)" % (
				u"%s%02d°%02d'%04.1f\"" % self._dms_split(self.lat, "N", "S"),
				u"%s%03d°%02d'%04.1f\"" % self._dms_split(self.lon, "E", "W")
				)
			)

	def as_str_dm(self):
		"Convert to string degrees, minutes with decimal point."
		return ( u"(%s, %s)" % (
				u"%s%02d°%06.3f'" % self._dm_split(self.lat, "N", "S"),
				u"%s%03d°%06.3f'" % self._dm_split(self.lon, "E", "W")
				)
			)
	
	def _dm_split(self, degrees, positive, negative):
		hemisphere = positive if degrees > 0.0 else negative
		degrees = abs(degrees)
		degrees,minutes = divmod(degrees*60,60)
		return (hemisphere, degrees, minutes)

	# Split degrees to degrees, minutes, and seconds	
	def _dms_split(self, degrees, positive, negative):
		hemisphere = positive if degrees > 0.0 else negative
		degrees = abs(degrees)
		minutes,seconds = divmod(degrees*3600,60)
		degrees,minutes = divmod(minutes,60)
		return (hemisphere, degrees, minutes, seconds)
	
	def as_geojson_position(self):
		return [self.lon, self.lat]

	def as_geojson(self):
		return { "type":"Point","coordinates":(self.lon, self.lat) }

# Convert an array of points (presumably expressed as (lat, lon)) to Point objects.
class MultiPoint(object):
	def __init__(self, points=None, geometry=None):
		if geometry is not None:
			assert geometry["type"] == "MultiPoint"
			points = map(lambda p: Point(p[1],p[0]), geometry['coordinates'])
		elif points is not None:
			points = map(Point, points)
		else:
			points = []
		self.bbox = None
	def get_bbox(self):
		if self.bbox is None:
			self.bbox = BoundingBox()
			self.bbox.add_points(self.points)
		return self.bbox
	def as_geojson(self):
		return { "type":"MultiPoint", "coordinates": map(lambda p: p.as_geojson_position(), self.points) }

#=============================================================================
# Strings of Geographic Points
#=============================================================================

class LineString(MultiPoint):
	def __init__(self, points=None, geometry=None):
		if geometry is not None:
			assert geometry["type"] == "LineString"
			points = map(lambda p: Point(p[1],p[0]), geometry['coordinates'])
			MultiPoint.__init__(self, points)
		else:
			MultiPoint.__init__(self, points, geometry)
	def as_geojson(self):
		return { "type":"LineString", "coordinates": map(lambda p: p.as_geojson_position(), self.points) }

class MultiLineString(object):
	def __init__(self, linestrings=None, geometry=None):
		if geometry is not None:
			assert geometry["type"] == "MultiLineString"
			self.linestrings = []
			for coordinates in geometry['coordinates']:
				self.linestrings.append(LineString(geometry={"type":"LineString", "coordinates": coordinates}))
		else:
			self.linestrings = linestrings
		self.bbox = None

	def get_bbox(self):
		if self.bbox is None:
			self.bbox = BoundingBox()
			for linestring in self.linestrings:
				self.bbox.add_bbox(linestring.get_bbox())
		return self.bbox

	def as_geojson(self):
		coordinates = []
		for linestring in self.linestrings:
			coordinates.append(linestring.as_geojson()['coordinates'])
		return { "type":"LineString", "coordinates":coordinates }

#=============================================================================
# Polygon object
#
# List of points passed to the constructor should name each point only
# once. The first point should _not_ be repeated as the last point.
#
# All of the calculations assume a rectangular grid. In other words,
# they ignore projection.
#
# For now calculations ignore holes. All we do is store them.
#=============================================================================

class Polygon(MultiPoint):
	def __init__(self, points=None, geometry=None):
		MultiPoint.__init__(self)
		if geometry is not None:
			assert geometry['type'] == 'Polygon', geometry['type']
			rings = []
			for sub_poly in geometry['coordinates']:
				points = list(map(lambda p: Point(p[1], p[0]), sub_poly))
				assert len(points) >= 4, "not enough points for a polygon"
				assert points[0] == points.pop(-1), "polygon is not closed"
				rings.append(points)
			self.points = rings[0]
			self.holes = rings[1:]
		elif points is not None:
			self.points = map(Point, points)
			self.holes = []
		else:
			self.points = []
			self.holes = []

	# Methods area() and centroid() came from:
	# http://local.wasp.uwa.edu.au/~pbourke/geometry/polyarea/
	# We have shortened them up.
	def area(self, project=False):
		"Area of polygon in square degrees unless project=True when it is in square meters"
		if project:		# project to meters first?
			points = project_points_sinusoidal(self.points)
		else:
			points = self.points
		area=0
		j=len(points)-1
		for i in range(len(points)):
			p1=points[i]
			p2=points[j]
			area += (p1[0]*p2[1])
			area -= p1[1]*p2[0]
			j=i
		area /= 2;
		return math.fabs(area)	# is often negative

	def centroid(self):
		x=0
		y=0
		j=len(self.points)-1;
		for i in range(len(self.points)):
			p1=self.points[i]
			p2=self.points[j]
			f=p1[0]*p2[1]-p2[0]*p1[1]
			x+=(p1[0]+p2[0])*f
			y+=(p1[1]+p2[1])*f
			j=i
		f=self.area()*6
		if(f == 0):
			return self.points[0]
		else:
			return Point(x/f, y/f)

	# See:
	# http://www.faqs.org/faqs/graphics/algorithms-faq/ (section 2.03)
	# http://www.ecse.rpi.edu/Homepages/wrf/Research/Short_Notes/pnpoly.html
	def contains_point(self, testpt):
		"Return True if the polygon contains the indicated point"
		if not self.get_bbox().contains_point(testpt):
			return False

		inPoly = False
		i = 0
		j = len(self.points) - 1
		while i < len(self.points):
			verti = self.points[i]
			vertj = self.points[j]
			if ( ((verti.lat > testpt.lat) != (vertj.lat > testpt.lat)) \
					and \
					(testpt.lon < (vertj.lon - verti.lon) * (testpt.lat - verti.lat) / (vertj.lat - verti.lat) + verti.lon) ):
				inPoly = not inPoly
			j = i
			i += 1

		return inPoly

	def choose_label_center(self):
		"Try 81 possible label positions and choose the one farthest from the polygon's border"
		assert len(self.points) >= 3
		bbox = self.get_bbox()
		lat_step = (bbox.max_lat - bbox.min_lat) / 10.0
		lon_step = (bbox.max_lon - bbox.min_lon) / 10.0
		largest_distance = 0
		largest_distance_point = None
		for y in range(1,10):
			lat = bbox.min_lat + lat_step * y
			for x in range(1,10):
				lon = bbox.min_lon + lon_step * x
				point = Point(lat, lon)
				if self.contains_point(point):
					distance = self.distance_to(point, largest_distance)
					if distance is not None and distance > largest_distance:
						largest_distance = distance
						largest_distance_point = point
		if largest_distance_point is not None:
			return largest_distance_point
		else:	# for some unknown pathological case
			return self.centroid()

	def distance_to(self, point, low_abort=None):
		"Find the distance from <point> to the nearest segment of the polygon"
		shortest = None
		i = 0
		while i < len(self.points):
			p1 = self.points[i]
			p2 = self.points[(i+1) % len(self.points)]
			distance = plane_lineseg_distance(point, p1, p2)
			if shortest is None or distance < shortest:
				shortest = distance
			if low_abort is not None and distance < low_abort:
				return None
			i += 1
		return shortest

	def as_geojson(self):
		coordinates = []
		for poly in [self.points] + self.holes:
			points = self.points[:]
			points.append(points[0])		# close polygon
			coordinates.append(map(lambda p: p.as_geojson_position(), points))
		return { "type":"Polygon", "coordinates": coordinates }

class MultiPolygon(object):
	def __init__(self, polygons=None, geometry=None):
		if geometry is not None:
			assert geometry["type"] == "MultiPolygon"
			self.polygons = []
			for coordinates in geometry['coordinates']:
				self.polygons.append(Polygon(geometry={"type":"Polygon", "coordinates": coordinates}))
		else:
			self.polygons = polygons
		self.bbox = None

	def get_bbox(self):
		if self.bbox is None:
			self.bbox = BoundingBox()
			for polygon in self.polygons:
				self.bbox.add_bbox(polygon.get_bbox())
		return self.bbox

	def as_geojson(self):
		coordinates = []
		for polygon in self.polygons:
			coordinates.append(polygon.as_geojson()['coordinates'])
		return { "type":"Polygon", "coordinates":coordinates }

#=============================================================================
# Bounding Boxes
#=============================================================================

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

#=============================================================================
# Tests
#=============================================================================

if __name__ == "__main__":
	p = PolygonFromGeoJSON({
		'type': 'Polygon',
		'coordinates': [
			[[-71.0, 42.0], [-70.0, 42.0], [-71.0, 41.0], [-71.0, 42.0]],
			[[-70.9, 41.9], [-70.1, 41.9], [-70.9, 41.1], [-70.9, 41.9]] 
			]
		})
	print(p.as_geojson())

