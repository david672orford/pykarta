# encoding=utf-8
# pykarta/geometry/point.py
# Last modified: 14 July 2014

import re

# A geographic points
# The latitude and longitude can either be referred to as
# .lat and .lon or as [0] and [1] respectively.
class Point(object):
	__slots__ = ['lat', 'lon']
	def __init__(self, *args):
		if len(args) == 0:			# Point()
			self.lat = None
			self.lon = None
		elif len(args) == 1:		# Point(point)
			self.lat = args[0][0]
			self.lon = args[0][1]
		elif len(args) == 2:		# Point(lat, lon)
			self.lat = args[0]
			self.lon = args[1]
		else:
			raise Exception("Invalid arguments:", args)

	# This is what allows old functions to consume these objects.
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

	# Convert to string in degress with decimal point
	def as_str_decimal(self):
		return str(self)

	# Convert to string in degrees, minutes and seconds.
	def as_str_dms(self):
		return ( u"(%s, %s)" % (
				u"%s%02d°%02d'%04.1f\"" % self._dms_split(self.lat, "N", "S"),
				u"%s%03d°%02d'%04.1f\"" % self._dms_split(self.lon, "E", "W")
				)
			)
	
	def _dms_split(self, degrees, positive, negative):
		hemisphere = positive if degrees > 0.0 else negative
		degrees = abs(degrees)
		minutes,seconds = divmod(degrees*3600,60)
		degrees,minutes = divmod(minutes,60)
		return (hemisphere, degrees, minutes, seconds)
	
	# Convert to string degrees, minutes with decimal point.
	def as_str_dm(self):
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

	def as_geojson_position(self):
		return (self.lon, self.lat)

	def as_geojson(self):
		return {"type":"Point","coordinates":(self.lon, self.lat)}

# Create a Point() from a text string describing a latitude and longitude
#
# Example from Wikipedia article Whitehouse: 38° 53′ 51.61″ N, 77° 2′ 11.58″ W
# \u2032 -- prime (minutes sign)
# \u2033 -- double prime (seconds sign)
# \u2019 -- single closing quote
# \u201d -- double closing quote
def PointFromText(coords_text):
	if not re.search(u'^[\(\-0-9\.°\'\u2019\u2032"\u201d\u2033NSEW, \)]+$', coords_text, flags=re.IGNORECASE):
		return None

	print "Pasted coordinates:", coords_text

	# Make more standard
	coords_text = coords_text.upper()
	coords_text = coords_text.replace(u"(", u"")
	coords_text = coords_text.replace(u")", u"")
	coords_text = coords_text.replace(u" ", u"")				# remove spaces
	coords_text = coords_text.replace(u"'", u"\u2032")		# ASCII single quote (apostroph) to prime
	coords_text = coords_text.replace(u"\u2019", u"\u2032")	# right single quote to prime
	coords_text = coords_text.replace(u'"', u'\u2033')		# ASCII double quote to double prime
	coords_text = coords_text.replace(u'\u201d', u'\u2033')	# right double quote to double prime

	words = _split_coords_text(coords_text)
	lat = _parse_degrees(words[0], "NS")
	lon = _parse_degrees(words[1], "EW")
	return Point(lat, lon)

def _split_coords_text(coords_text):
	m = re.match('^([^,]+),([^,]+)$', coords_text)
	if m:
		return (m.group(1), m.group(2))

	m = re.match('^([NS].+)([EW].+)$', coords_text)
	if m:
		return (m.group(1), m.group(2))

	m = re.match('^(.+[NS])(.+[EW])$', coords_text)
	if m:
		return (m.group(1), m.group(2))

	raise Exception("Two coordinates required")

def _parse_degrees(degrees_string, directions):
	sign = 1.0
	if directions[0] in degrees_string:		# N or E
		degrees_string = degrees_string.replace(directions[0], "")
	elif directions[1] in degrees_string:	# S or W
		degrees_string = degrees_string.replace(directions[1], "")
		sign = -1.0

	# Decimal degrees signed
	m = re.search(u'^([-\d\.]+)°?$', degrees_string)
	if m:
		return float(m.group(1)) * sign

	# Degrees, minutes, seconds
	m = re.search(u'^(\d+)°(\d+)\u2032([\d\.]+)\u2033$', degrees_string)
	if m:
		degrees = int(m.group(1))
		degrees += int(m.group(2)) / 60.0
		degrees += float(m.group(3)) / 3600.0
		return degrees * sign

	m = re.search(u'^(\d+)°([\d\.]+)\u2032?$', degrees_string)
	if m:
		degrees = int(m.group(1))
		degrees += float(m.group(2)) / 60.0
		return degrees * sign

	raise Exception("Failed to parse coordinate: %s" % degrees_string)

def PointFromGeoJSON(geojson):
	if geojson['type'] != 'Point':
		raise ValueError("Not a GeoJSON point")
	coordinates = geojson['coordinates']
	return Point(coordinates[1], coordinates[0])

# Convert an array of points (presumably expressed as (lat, lon)) to Point objects.
def Points(points):
	return map(Point, points)

# Extract the "coordinates" member from a decoded GeoJSON object
def PointsFromGeoJSON(geojson):
	points = geojson['coordinates']
	if geojson['type'] == "LineString":
		pass
	elif geojson['type'] == "Polygon":
		if len(points) != 0:
			raise ValueError("Only simple polygons are supported")
		points = points[0]				# take outer polygon
		if len(points) < 1 or points[0] != points[-1]:
			raise ValueError("Points do not form a LinearRing")
		points.pop(-1)					# discard last vertex
	else:
		raise ValueError("GeoJSON type %s not supported" % geojson['type'])
	return map(lambda p: Point(p[1], p[0]), points)

