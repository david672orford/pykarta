# pykarta/geometry/route.py
# Copyright 2013--2018, Trinity College
# Last modified: 15 May 2018

from __future__ import print_function
import math
from . import LineString
from .distance import points_distance_pythagorian, points_bearing

#=============================================================================
# Route--a LineString with additional self-analysis abilities
#=============================================================================

class Route(LineString):
	def __init__(self, points=None, geometry=None):
		LineString.__init__(self, points, geometry)
		self.update()

	def update(self):
		self.distances = []
		self.bearings = []
		for i in range(len(self.points) - 1):
			p1 = self.points[i]
			p2 = self.points[i+1]
			self.distances.append(points_distance_pythagorian(p1, p2))
			self.bearings.append(points_bearing(p1, p2))

	# Return travel distance in meters along route to reach poi_point. 
	def routeDistance(self, poi_point, debug=False):
		running_route_distance = 0
		closest_excursion_distance = None		# distance to closest (possibly extended) route segment
		closest_route_distance = None			# distance from start if above turns out to be closest

		# Step through the segments of this route.
		# self.points[i] -- the current point
		# self.bearings[i] -- the direction of the route segment which starts here
		# self.distances[i] -- the length of the route segment which starts here
		for i in range(len(self.points) - 1):

			# Bearing in degrees of corse from current point to this poi
			poi_bearing = points_bearing(self.points[i], poi_point)

			# Link of direct line from current point to POI
			# We will use this as the hypotenus of a right triangle. The adjacent side
			# will run along the route segment that starts at the current point (though
			# it may extend furthur).
			poi_hyp_length = points_distance_pythagorian(self.points[i], poi_point)

			# The angle in degrees between the route segment that starts at this point
			# and the direct line to the POI from this point
			relative_bearing = (poi_bearing - self.bearings[i] + 360) % 360

			if debug:
				print("  From point %d POI is at %f degrees, %f meters away." % (i, poi_bearing, poi_hyp_length))
				print("    Relative bearing %f degrees" % (relative_bearing))

			# If the direct line to the POI does not point behind us,
			if relative_bearing <= 90.0 or relative_bearing >= 270.0:

				# Compute the lengths of the sides of the right triangle. We do not
				# care on which side of the route the POI lies.
				relative_bearing_radians = math.radians(relative_bearing)
				opposite = math.fabs(poi_hyp_length * math.sin(relative_bearing_radians))
				adjacent = math.fabs(poi_hyp_length * math.cos(relative_bearing_radians))

				# How far will we need to move off of the route to read the POI?
				# We do not know where the road to the POI lies, so we use
				# an arbitrary route.
				# We start with the amount that the POI is off to one side.
				# If it lies beyond the end of the current segment, we add the 
				# amount by which we would need to extend the segment in order
				# to reach it.
				excursion = opposite
				if adjacent > self.distances[i]:
					excursion += (adjacent - self.distances[i])
				if debug:
					print("    Opposite %f meters" % (opposite))
					print("    Adjacent %f meters" % (adjacent))
					print("    Excursion %f meters" % (excursion))

				# If the excursion from the route is the smallest yet, save it.
				if not closest_excursion_distance or excursion < closest_excursion_distance:
					closest_excursion_distance = excursion
					# The distance to the POI is the length of all route segments
					# that are already behind us plus the distance from this point 
					# of the point where we would leave the route in order to reach
					# the POI.
					closest_route_distance = running_route_distance + min(adjacent, self.distances[i])
					if debug:
						print("    (Closest yet at %f meters)" % closest_route_distance)

			# Keep a running total of the length of route segments that are behind us.
			running_route_distance += self.distances[i]

		return closest_route_distance		# may be None

