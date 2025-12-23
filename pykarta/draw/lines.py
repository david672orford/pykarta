# pykarta/draw/lines.py
# Copyright 2013--2022, Trinity College
# Last modified: 2 January 2022

import cairo
import math

# Add a string of line segments to the path.
def line_string(ctx, points):
	if len(points) < 1:		# empty line?
		return
	ctx.move_to(*points[0])
	line_to = ctx.line_to
	for point in points[1:]:
		line_to(*point)

# Add a line with arrows showing direction to the path.
def route(ctx, points):
	line_string(ctx, points)
	line_string_arrows(ctx, points)

# Add a simple polygon to the path.
def polygon(ctx, points):
	line_string(ctx, points)
	ctx.close_path()

# Add arrow heads to show direction of travel.
# We work backwards from the end so as to have the best
# change of placing an arrowhead at or near the end of 
# the line. This looks better.
def line_string_arrows(ctx, points, line_width=1):
	arrow_min_interval = 50
	arrow_running_distance = arrow_min_interval
	# Note that if the len(points) is < 2 there will be no iterations. This is good.
	for i in reversed(list(range(len(points)-1))):
		p1 = points[i]
		p2 = points[i+1]
		width = p2[0] - p1[0]
		height = p2[1] - p1[1]
		distance = math.sqrt(width*width + height*height)
		arrow_running_distance += distance
		if arrow_running_distance > arrow_min_interval and distance > 20:
			barb1, barb2 = arrowhead_barbs(p1, p2, arrow_length=line_width * 5.0)
			ctx.move_to(*barb1)
			ctx.line_to(*p2)
			ctx.line_to(*barb2)
			arrow_running_distance = 0
	
# Compute positions of the barb points of an arrow drawn at the end 
# of a line.
# See: http://kapo-cpp.blogspot.com/2008/10/drawing-arrows-with-cairo.html
def arrowhead_barbs(start_point, end_point, arrow_length=15, arrow_angle_degrees=20):
	start_x, start_y = start_point	
	end_x, end_y = end_point
	arrow_angle = math.radians(arrow_angle_degrees)
	angle = math.atan2(end_y - start_y, end_x - start_x) + math.pi
	x1 = end_x + arrow_length * math.cos(angle - arrow_angle)
	y1 = end_y + arrow_length * math.sin(angle - arrow_angle)
	x2 = end_x + arrow_length * math.cos(angle + arrow_angle)
	y2 = end_y + arrow_length * math.sin(angle + arrow_angle)
	return [[x1, y1], [x2, y2]]

# Draw circles to represent the nodes of a geometric shape. Examples of
# such nodes would be route points or a polygon vertexes.
def node_dots(ctx, points, style={}):
	diameter = style.get("diameter", 8.0)
	stroke_color = style.get("border-color", (0.0, 0.0, 0.0, 1.0))
	fill_color = style.get("fill-color", (1.0, 1.0, 1.0, 1.0))

	for x, y in points:
		ctx.new_path()
		ctx.arc(x, y, diameter/2.0, 0, 2*math.pi)

		ctx.set_line_width(1.5)
		ctx.set_source_rgba(*stroke_color)
		ctx.stroke_preserve()

		ctx.set_source_rgba(*fill_color)
		ctx.fill()

# Draw plus signs to represent the possibility of adding an intermediate
# point by dragging.
def node_pluses(ctx, points, style={}):
	radius = style.get("diameter", 10) / 2.0
	underline_color = style.get("underline-color", (0.0, 0.0, 0.0, 1.0))	#(0.8, 0.2, 0.2, 1.0))
	color = style.get("line-color", (1.0, 1.0, 1.0, 1.0))
	line_width = style.get("line-width", 1)
	ctx.new_path()
	for x, y in points:
		ctx.move_to(x-radius, y)
		ctx.line_to(x+radius, y)
		ctx.move_to(x, y-radius)
		ctx.line_to(x, y+radius)
	ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	ctx.set_line_width(4.0)
	ctx.set_source_rgba(*underline_color)
	ctx.stroke_preserve()
	ctx.set_line_width(2.0)
	ctx.set_source_rgba(*color)
	ctx.stroke()

