# pykarta/geometry/polygon.py
# Last modified: 21 July 2014

#=============================================================================
# Simple (no holes) Polygons
#
# The first point should not be repeated. The polygon is assumed to be closed.
#
# All of the calculations assume a rectangular grid. In other words, they
# ignore projection.
#=============================================================================

from point import Point
from line import LineString
from util import plane_lineseg_distance, line_simplify

# FIXME: bad things will happen if the Polygon has fewer than three points
# and we try to choose a label center.

class Polygon(LineString):

	# Methods area() and centroid() came from:
	# http://local.wasp.uwa.edu.au/~pbourke/geometry/polyarea/
	# We have shortened them up.
	def area(self):
		area=0
		j=len(self.points)-1
		for i in range(len(self.points)):
			p1=self.points[i]
			p2=self.points[j]
			area+= (p1[0]*p2[1])
			area-=p1[1]*p2[0]
			j=i
		area/=2;
		return area;

	def centroid(self):
		print self.points
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
		return Point(x/f, y/f)

	# See:
	# http://www.faqs.org/faqs/graphics/algorithms-faq/ (section 2.03)
	# http://www.ecse.rpi.edu/Homepages/wrf/Research/Short_Notes/pnpoly.html
	def contains_point(self, testpt):
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

	# Try 81 possible label positions starting just inside the polygon's
	# bounding box. Return the one which is farthest from the polygon's
	# border.
	def choose_label_center(self):
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
		points = self.points[:]
		points.append(points[0])
		return {"type":"Polygon", "coordinates": [map(lambda p: p.as_geojson_position(), points)]}

	def simplify(self, tolerance, debug=False):
		before_count = len(self.points)
		new_points = line_simplify(self.points, tolerance)
		after_count = len(new_points)
		if debug:
			print "Reduced %s points to %s" % (before_count, after_count)
		if after_count >= 3:
			self.points = new_points

def PolygonFromGeoJSON(geometry):
	assert geometry['type'] == 'Polygon', geometry['type']
	assert len(geometry['coordinates']) == 1, len(geometry['coordinates'])
	points = map(lambda p: Point(p[1], p[0]), geometry['coordinates'][0])
	assert len(points) >= 4
	redundant_point = points.pop(-1)
	assert points[0] == redundant_point
	return Polygon(points)

