# encoding=utf-8
# pykarta/geometry/util.py
# Last modified: 2 August 2013

import math

#=============================================================================
# Line simplification
#=============================================================================
def line_simplify(points, tolerance):
	stack = []
	keep = set()

	stack.append((0, len(points)-1))
	while stack:
		anchor, floater = stack.pop()
		max_dist = 0.0
		farthest = anchor + 1	# why necessary?
		#print anchor, floater
		for i in range(anchor + 1, floater):
			dist_to_seg = plane_lineseg_distance(points[i], points[anchor], points[floater])
			#print " i:", i, dist_to_seg
			if dist_to_seg > max_dist:
				max_dist = dist_to_seg
				farthest = i
		if max_dist <= tolerance:
			keep.add(anchor)
			keep.add(floater)
		else:
			stack.append((anchor, farthest))
			stack.append((farthest, floater))

	keep = list(keep)
	keep.sort()
	return [points[i] for i in keep]

#=============================================================================
# Distance on a plane
# See: http://blog.csharphelper.com/2010/03/26/find-the-shortest-distance-between-a-point-and-a-line-segment-in-c.aspx
#=============================================================================

# Distance of a point to a line segment
def plane_lineseg_distance(pt, p1, p2):
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

# Distance between two points
def plane_points_distance(p1, p2):
	dx = p1[0] - p2[0]
	dy = p1[1] - p2[1]
	return math.sqrt(dx * dx + dy * dy)

#=============================================================================
# Distance and Bearing on the Globe
#=============================================================================

# Mean radius of earth in meters
radius_of_earth = 6371000

# Compute distance (approximate) in meters from p1 to p2
# See: http://www.movable-type.co.uk/scripts/latlong.html
def points_distance_pythagorian(p1, p2):
	lat1 = math.radians(p1[0])
	lon1 = math.radians(p1[1])
	lat2 = math.radians(p2[0])
	lon2 = math.radians(p2[1])
	x = (lon2-lon1) * math.cos((lat1 + lat2)/2)		# longitudinal distance (figured at center of path)
	y = (lat2-lat1)									# latitudinal distance
	d = math.sqrt(x*x + y*y)						# Pythagerian theorem
	return d * radius_of_earth						# radians to kilometers

# Compute bearing in degress from north of p2 from p1
# See: http://www.movable-type.co.uk/scripts/latlong.html
def points_bearing(p1, p2):
	lat1 = math.radians(p1[0])
	lon1 = math.radians(p1[1])
	lat2 = math.radians(p2[0])
	lon2 = math.radians(p2[1])
	dLon = lon2 - lon1
	x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
	y = math.sin(dLon) * math.cos(lat2)
	bearing = math.atan2(y, x)
	return (math.degrees(bearing) + 360) % 360


