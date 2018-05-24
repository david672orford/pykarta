#! /usr/bin/python

# This file contains experimental alternative implementions of line_simplify().

import math

# Version from:
# https://gist.github.com/humanfromearth/1051247
# This ought to be faster than line_simplify(), but is actually takes
# about 75% longer.
def line_simplify_opt1(pts, tolerance):
	stack   = []
	keep    = set()
	stack.append((0, len(pts) - 1))
	while stack:
		anchor, floater = stack.pop()
	  
		# initialize line segment
		if pts[floater] != pts[anchor]:
			anchorX = float(pts[floater][0] - pts[anchor][0])
			anchorY = float(pts[floater][1] - pts[anchor][1])
			seg_len = math.sqrt(anchorX ** 2 + anchorY ** 2)
			# get the unit vector
			anchorX /= seg_len
			anchorY /= seg_len
		else:
			anchorX = anchorY = seg_len = 0.0
	
		# inner loop:
		max_dist = 0.0
		farthest = anchor + 1
		for i in range(anchor + 1, floater):
			dist_to_seg = 0.0
			# compare to anchor
			vecX = float(pts[i][0] - pts[anchor][0])
			vecY = float(pts[i][1] - pts[anchor][1])
			seg_len = math.sqrt( vecX ** 2 + vecY ** 2 )
			# dot product:
			proj = vecX * anchorX + vecY * anchorY
			if proj < 0.0:
				dist_to_seg = seg_len
			else: 
				# compare to floater
				vecX = float(pts[i][0] - pts[floater][0])
				vecY = float(pts[i][1] - pts[floater][1])
				seg_len = math.sqrt( vecX ** 2 + vecY ** 2 )
				# dot product:
				proj = vecX * (-anchorX) + vecY * (-anchorY)
				if proj < 0.0:
					dist_to_seg = seg_len
				else:  # calculate perpendicular distance to line (pythagorean theorem):
					dist_to_seg = math.sqrt(abs(seg_len ** 2 - proj ** 2))
			if max_dist < dist_to_seg:
				max_dist = dist_to_seg
				farthest = i

		if max_dist <= tolerance: # use line segment
			keep.add(anchor)
			keep.add(floater)
		else:
			stack.append((anchor, farthest))
			stack.append((farthest, floater))

	keep = list(keep)
	keep.sort()
	return [pts[i] for i in keep]

# Optimized version of above
# Takes about 20% less time than line_simplify()
def line_simplify_opt2(pts, tolerance):
	sqrt = math.sqrt	# about 5% speedup

	stack   = []
	keep    = set()
	stack.append((0, len(pts) - 1))
	while stack:
		anchor, floater = stack.pop()
		anchor_x, anchor_y = pts[anchor]
		floater_x, floater_y = pts[floater]
	  
		# initialize line segment
		if pts[floater] != pts[anchor]:
			anchorX = float(floater_x - anchor_x)
			anchorY = float(floater_y - anchor_y)
			seg_len = sqrt(anchorX ** 2 + anchorY ** 2)
			# get the unit vector
			anchorX /= seg_len
			anchorY /= seg_len
		else:
			anchorX = anchorY = seg_len = 0.0
	
		# inner loop:
		max_dist = 0.0
		farthest = anchor + 1
		for i in range(anchor + 1, floater):
			i_x, i_y = pts[i]
			dist_to_seg = 0.0
			# compare to anchor
			vecX = float(i_x - anchor_x)
			vecY = float(i_y - anchor_y)
			seg_len = sqrt( vecX ** 2 + vecY ** 2 )
			# dot product:
			proj = vecX * anchorX + vecY * anchorY
			if proj < 0.0:
				dist_to_seg = seg_len
			else: 
				# compare to floater
				vecX = float(i_x - floater_x)
				vecY = float(i_y - floater_y)
				seg_len = sqrt( vecX ** 2 + vecY ** 2 )
				# dot product:
				proj = vecX * (-anchorX) + vecY * (-anchorY)
				if proj < 0.0:
					dist_to_seg = seg_len
				else:  # calculate perpendicular distance to line (pythagorean theorem):
					dist_to_seg = sqrt(abs(seg_len ** 2 - proj ** 2))
			if max_dist < dist_to_seg:
				max_dist = dist_to_seg
				farthest = i

		if max_dist <= tolerance: # use line segment
			keep.add(anchor)
			keep.add(floater)
		else:
			stack.append((anchor, farthest))
			stack.append((farthest, floater))

	keep = list(keep)
	keep.sort()
	return [pts[i] for i in keep]

if __name__ == "__main__":
	import cProfile, pstats, io
	from pykarta.geometry.util import line_simplify
	line = ( (0,0), (1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (6,1), (6,2), (6,3), (6,4), (6,5), (6,6), (5,6), (4,6), (3,6), (2,6), (1,6), (0,6), (0,5), (0,4), (0,3), (0,2), (0,1), (0,0) )
	print "line:", line
	print "Simplified:", line_simplify(line, 1.0)
	pr = cProfile.Profile()
	pr.enable()
	for i in range(1000):
		#simplified = line_simplify(line, 1.0)
		simplified = line_simplify_opt1(line, 1.0)
		#simplified = line_simplify_opt2(line, 1.0)
	pr.disable()
	pr.print_stats()
	assert simplified == [(0, 0), (6, 0), (6, 6), (0, 6), (0, 0)]
	print

