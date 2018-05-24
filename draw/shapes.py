# pykarta/draw/shapes.py
# Copyright 2013--2018, Trinity College
# Last modified: 23 May 2018

import cairo
import re

# Add a rectangle with rounded corners to the path.
def rounded_rectangle(cr, x, y, w, h, r=20):
    # This is "Method C" from:
    # http://www.cairographics.org/cookbook/roundedrectangles/
    #   A****BQ
    #  H      C
    #  *      *
    #  G      D
    #   F****E

    cr.move_to(x+r,y)                      # Move to A
    cr.line_to(x+w-r,y)                    # Straight line to B
    cr.curve_to(x+w,y,x+w,y,x+w,y+r)       # Curve to C, Control points are both at Q
    cr.line_to(x+w,y+h-r)                  # Move to D
    cr.curve_to(x+w,y+h,x+w,y+h,x+w-r,y+h) # Curve to E
    cr.line_to(x+r,y+h)                    # Line to F
    cr.curve_to(x,y+h,x,y+h,x,y+h-r)       # Curve to G
    cr.line_to(x,y+r)                      # Line to H
    cr.curve_to(x,y,x,y,x+r,y)             # Curve to A

# Parse a subset of the SVG path language and draw it. Design complex shapes
# using Inkscape, then paste paths into your code. Note that this supports
# only absolute coordinates. In Inkscape preferences under SVG Output change
# Path Data to Absolute. Then you can move the elements with relative paths
# and move them back. They should not have absolute paths which you can
# paste into calls to this function.
def svg_path(ctx, path):
	ctx.new_path()
	while len(path) > 0:
		#print "path:", path
		if path.startswith("M "):
			path = path[2:]
			while True:
				m = re.match(r"([\d-]+),([\d-]+) ", path)
				if m is None:
					break
				ctx.move_to(*map(int,m.groups()))
				path = path[len(m.group(0)):]
			continue
		if path.startswith("L "):
			path = path[2:]
			while True:
				m = re.match(r"([\d-]+),([\d-]+) ", path)
				if m is None:
					break
				ctx.line_to(*map(int,m.groups()))
				path = path[len(m.group(0)):]
			continue
		if path.startswith("C "):
			path = path[2:]
			while True:
				m = re.match(r"([\d-]+),([\d-]+) ([\d-]+),([\d\-]+) ([\d-]+),([\d-]+) ", path)
				if m is None:
					break
				ctx.curve_to(*map(int,m.groups()))
				path = path[len(m.group(0)):]
			continue
		if path == "Z":
			ctx.close_path()
			path = ""
			continue
		raise ValueError("Bad SVG path: \"%s\" (len=%d)" % (path, len(path)))

