# pykarta/geometry/projection.py
# Last modified: 3 February 2015

from math import radians, degrees, exp, log, tan, cos, sinh, atan, pi

#=============================================================================
# Web Mercator tiles
#=============================================================================

# Convert latitude and longitude to tile coordinates. The whole part of the
# x and y coordinates indicates the tile number. The fractional part
# indicates the position within the tile.
def project_to_tilespace(lat, lon, zoom):
	lat_rad = radians(lat)
	n = 2.0 ** zoom
	xtile = (lon + 180.0) / 360.0 * n
	ytile = (1.0 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2.0 * n
	return (xtile, ytile)

# Converts tile coordinates back to latitude and longitude
def unproject_from_tilespace(xtile, ytile, zoom):
	n = 2.0 ** zoom
	lon = xtile / n * 360.0 - 180.0
	lat = degrees(atan(sinh(pi * (1 - 2 * ytile / n))))
	return (lat, lon)

# Convert latitude and longitude to a pixel position within the
# coordinate space of a particular tile. Note that the pixel
# position itself could well be outside the tile.
def project_to_tilespace_pixel(lat, lon, zoom, xtile, ytile):
	xtile2, ytile2 = project_to_tilespace(lat, lon, zoom)
	return ((xtile2 - xtile) * 256.0, (ytile2 - ytile) * 256.0)

#=============================================================================
# Spherical Mercartor in meters rather than in tiles
# http://wiki.openstreetmap.org/wiki/Mercator
#=============================================================================

radius_of_earth = 6378137.0			 # Mean radius of earth in meters 

def project_point_mercartor(lat, lon):
	return (
		radians(lon) * radius_of_earth,
		log(tan(pi/4.0 + radians(lat) / 2.0)) * radius_of_earth
		)

def unproject_point_mercartor(x, y):
	return (
		degrees(2.0 * atan(exp(y / radius_of_earth)) - pi / 2.0),
		degrees(x / radius_of_earth)
		)

#=============================================================================
# Project to meters using sinusoidal projection.
# Use for area computations.
# See: http://stackoverflow.com/questions/4681737/how-to-calculate-the-area-of-a-polygon-on-the-earths-surface-using-python
#=============================================================================

def project_points_sinusoidal(points):
	lat_dist = pi * radius_of_earth / 180.0	# size of degree in meters
	return [(
		lon * lat_dist * cos(radians(lat)),
		lat * lat_dist
		) for lat, lon in points]

