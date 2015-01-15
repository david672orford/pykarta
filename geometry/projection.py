# pykarta/geometry/projection.py

import math

#=============================================================================
# Mean radius of earth in meters used in the Spherical Mercartor projection
# Spherical Mercartor in meters rather than in tiles
# http://wiki.openstreetmap.org/wiki/Mercator
#=============================================================================

radius_of_earth = 6378137.0

def project_point_mercartor(lat, lon):
	return (
		math.radians(lon) * radius_of_earth,
		math.log(math.tan(math.pi/4.0 + math.radians(lat) / 2.0)) * radius_of_earth
		)

def unproject_point_mercartor(x, y):
	return (
		math.degrees(2.0 * math.atan(math.exp(y / radius_of_earth)) - math.pi / 2.0),
		math.degrees(x / radius_of_earth)
		)

#=============================================================================
# Project to meters using sinusoidal projection.
# Use for area computations.
# See: http://stackoverflow.com/questions/4681737/how-to-calculate-the-area-of-a-polygon-on-the-earths-surface-using-python
#=============================================================================

def project_points_sinusoidal(points):
	lat_dist = math.pi * radius_of_earth / 180.0	# size of degree in meters
	return [(
		lon * lat_dist * math.cos(math.radians(lat)),
		lat * lat_dist
		) for lat, lon in points]

