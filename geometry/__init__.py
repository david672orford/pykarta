#! /usr/bin/python
# encoding=utf-8
# pykarta/geometry/__init__.py
# Copyright 2013, 2014, Trinity College
# Last modified: 4 September 2014

import math
from point import Point, Points, PointFromText, PointFromGeoJSON, Points
from bbox import BoundingBox
from util import line_simplify, plane_lineseg_distance, plane_points_distance, points_distance_pythagorian, points_bearing, radius_of_earth
from line import LineString, Route
from polygon import Polygon

#=============================================================================
# Test
#=============================================================================
if __name__ == "__main__":
	print "=== Polygon ==="

	coords = [(832,1093),(810,1121),(787,1156),(827,1173),(838,1167),(858,1157),(873,1132),(873,1107),(832,1093)]
	print "Coords:", coords
	poly = Polygon(coords)
	print "Centroid", poly.centroid()

	print "=== Bounding Box ==="
	bbox = BoundingBox()
	print "Empty:", str(bbox)
	bbox.add_point(Point(42, -72))
	bbox.add_point(Point(42.5, -73))
	print "Filled:", str(bbox)
	print "Center:", bbox.center()

	print "=== Two Points ==="
	for points in [
		[[45, -75], [45, -75]],		# same point
		[[45, -75], [45, -74]],		# one degree of longitude
		[[45, -75], [44, -75]],		# one degree of latitude
		[[45, -75], [44, -74]],		# one degree of each
		]:
		print "Points:", points
		print "Distance:", points_distance_pythagorian(*points)
		print "Bearing:", points_bearing(*points)
		print

	print "=== Formatted Latitude and Longitude ==="
	print Point(42.251, -72.251).as_str_dms()

	print "=== Points ==="
	print Points([[42.00, -72.00], [43.00, -73.00]])

	print "=== Line Segment Distance ==="
	for i in (
			((1,0), (0,0), (2,0)),
			((0,2), (0,0), (2,2)),
			((0,2), (2,2), (0,0)),
		):
		print i, ":", plane_lineseg_distance(*i)
	print

	print "=== Simplified line ==="
	line = ( (0,0), (1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (6,1), (6,2), (6,3), (6,4), (6,5), (6,6), (5,6), (4,6), (3,6), (2,6), (1,6), (0,6), (0,5), (0,4), (0,3), (0,2), (0,1), (0,0) )
	simplified = line_simplify(line, 1.0)
	print "Simplified:", simplified
	assert simplified == [(0, 0), (6, 0), (6, 6), (0, 6), (0, 0)]

