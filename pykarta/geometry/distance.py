# encoding=utf-8
# pykarta/geometry/distance.py
# Last modified: 14 May 2018

import math

#=============================================================================
# Distance on a plane
# See: http://blog.csharphelper.com/2010/03/26/find-the-shortest-distance-between-a-point-and-a-line-segment-in-c.aspx
#=============================================================================

def plane_points_distance(p1, p2):
	"Distance between two points on a plane"
	dx = p1[0] - p2[0]
	dy = p1[1] - p2[1]
	return math.sqrt(dx * dx + dy * dy)

def plane_lineseg_distance(pt, p1, p2):
	"Distance of a point to a line segment on a plane"
	dx = float(p2[0] - p1[0])
	dy = float(p2[1] - p1[1])

	# Zero-length line segment?
	if dx == 0.0 and dy == 0.0:
		return plane_points_distance(p1, pt)

	# How far along the line segment is the closest point?
	# 0.0 means it is opposite p1
	# 1.0 means it is opposite p2
	t = ((pt[0] - p1[0]) * dx + (pt[1] - p1[1]) * dy) / (dx * dx + dy * dy)

	if t < 0.0:		# before start point?
		return plane_points_distance(p1, pt)
	elif t > 1.0:	# after end point?
		return plane_points_distance(p2, pt)
	else:
		closest = (p1[0] + t * dx, p1[1] + t * dy);
		return plane_points_distance(closest, pt)

#=============================================================================
# Distance and Bearing on the Globe
#=============================================================================

# Mean radius of earth in meters used in the Spherical Mercartor projection
radius_of_earth = 6378137.0

# See: http://www.movable-type.co.uk/scripts/latlong.html
def points_distance_pythagorian(p1, p2):
	"Compute distance (approximate) in meters from p1 to p2"
	lat1 = math.radians(p1[0])
	lon1 = math.radians(p1[1])
	lat2 = math.radians(p2[0])
	lon2 = math.radians(p2[1])
	x = (lon2-lon1) * math.cos((lat1 + lat2)/2)		# longitudinal distance (figured at center of path)
	y = (lat2-lat1)									# latitudinal distance
	d = math.sqrt(x*x + y*y)						# Pythagerian theorem
	return d * radius_of_earth						# radians to kilometers

# See: http://www.movable-type.co.uk/scripts/latlong.html
def points_bearing(p1, p2):
	"Compute bearing in degress from north of p2 from p1"
	lat1 = math.radians(p1[0])
	lon1 = math.radians(p1[1])
	lat2 = math.radians(p2[0])
	lon2 = math.radians(p2[1])
	dLon = lon2 - lon1
	x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
	y = math.sin(dLon) * math.cos(lat2)
	bearing = math.atan2(y, x)
	return (math.degrees(bearing) + 360) % 360

