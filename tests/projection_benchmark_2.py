#! /usr/bin/python

from __future__ import print_function
import sys
sys.path.insert(1, "../..")
import math

from pykarta.geometry.projection import project_to_tilespace_pixel

# Make a bunch of points
point = (-72.00, 42.00)
points = []
for i in range(10000):
	points.append(point)

def project_to_tilespace_pixels(coordinates, zoom, xtile, ytile):
	points = map(lambda p: project_to_tilespace_pixel(p[1], p[0], zoom, xtile, ytile), coordinates)
	return list(points)

def optimized_project_to_tilespace_pixels(coordinates, zoom, xtile, ytile):
	n = 2.0 ** zoom
	nx2 = 2.0 / n
	nx360 = 360.0 / n
	radians = math.radians
	log = math.log
	tan = math.tan
	cos = math.cos
	pi = math.pi
	return [
		(
			((lon + 180.0) / nx360 - xtile) * 256.0,
			(((1.0 - log(tan(radians(lat)) + (1 / cos(radians(lat)))) / pi) / nx2) - ytile) * 256.0
			)
		for lon, lat in coordinates]

print(project_to_tilespace_pixels([[-72.765, 42.123]], 14, 4880, 6074))
print(optimized_project_to_tilespace_pixels([[-72.765, 42.123]], 14, 4880, 6074))

# Benchmark projection
import timeit

# Hatter: 500,000 points/second
print("Starting control test...")
seconds = timeit.timeit('project_to_tilespace_pixels(points, 0, 0, 0)', number=100, setup="from __main__ import project_to_tilespace_pixels, points")
print("%d points/second" % (len(points) * 100 / seconds))

print("Starting optimized test...")
seconds = timeit.timeit('optimized_project_to_tilespace_pixels(points, 0, 0, 0)', number=100, setup="from __main__ import optimized_project_to_tilespace_pixels, points")
print("%d points/second" % (len(points) * 100 / seconds))

