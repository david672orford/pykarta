# pykarta/geometry/simplify.py
# Last modified: 8 October 2014

from util import plane_lineseg_distance

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

