# pykarta/draw/__init__.py
# Copyright 2013, 2014, Trinity College
# Last modified: 1 August 2014

import cairo
import math

# Add a rectangle with rounded corners to the path.
def rounded_rectangle(cr, x, y, w, h, r=20):
    # This is just one of the samples from 
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

# Add a string of line segments to the path.
def line_string(ctx, points):
	if len(points) < 1:		# empty line?
		return
	point = points[0]
	ctx.move_to(point[0], point[1])
	line_to = ctx.line_to
	map(lambda p: line_to(p[0], p[1]), points)

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
	for i in reversed(range(len(points)-1)):
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

# Stroke the path in the specified style. This was inspired by Cascadenik.
def stroke_with_style(ctx, style, width_multiplier=1.0):
	# Nobody should be using the old keys
	assert not "color" in style			# color -> line-color
	assert not "dash-pattern" in style	# dash-pattern -> line-dash
	assert not "width" in style			# width -> line-width

	ctx.set_line_cap(cairo.LINE_CAP_ROUND)

	# This stroke goes 'under' the main stroke. It can be used to put
	# a border around the main stroke or the dash pattern can be used
	# to give it wiskers.
	if 'underline-width' in style:
		ctx.set_line_width(style['underline-width'])
		ctx.set_source_rgba(*style['underline-color'])
		ctx.set_dash(style.get('underline-dash', ()))
		ctx.stroke_preserve()

	# This is the main stroke. It is always made.
	ctx.set_line_width(style.get('line-width', 1))
	ctx.set_source_rgba(*style.get('line-color', (0.0, 0.0, 0.0, 1.0)))
	ctx.set_dash(style.get('line-dash', ()))
	ctx.stroke_preserve()

	# This stroke goes over the main stroke. We can use it to run a solid
	# or dashed line down the center of the main stroke.
	if 'overline-width' in style:
		ctx.set_line_width(style['overline-width'])
		ctx.set_source_rgba(*style['overline-color'])
		ctx.set_dash(style.get('overline-dash', ()))
		ctx.stroke_preserve()

	# This whole function is pitched as a substitute for stroke(), so
	# it should clear the path.
	ctx.new_path()

# Fill a polygon according to the specified style. By default it is
# filled with transparent white. To disable filling, set fill-color
# to None in the style.
def fill_with_style(ctx, style):
	fill_color = style.get("fill-color", (1.0, 1.0, 1.0, 0.5))
	if fill_color is not None:
		ctx.set_source_rgba(*fill_color)
		ctx.fill_preserve()

# Draw circles to represent the nodes of a geometric shape. Examples of
# such nodes would be route points or a polygon vertexes.
def node_dots(ctx, points, style={}):
	diameter = style.get("diameter", 7.0)
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

def node_pluses(ctx, points, style={}):
	radius = style.get("diameter", 10) / 2.0
	underline_color = style.get("underline_color", (0.0, 0.0, 0.0, 1.0))	#(0.8, 0.2, 0.2, 1.0))
	color = style.get("color", (1.0, 1.0, 1.0, 1.0))
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

# Print a label to the upper right of a POI marker. The x coordinate passed
# should be far enough to the right of the symbol so that the label does not
# overlap it. Stroke and fill.
def poi_label(ctx, x, y, text, fontsize=8):
	# Font
	ctx.select_font_face("sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	ctx.set_font_size(fontsize)

	#extents = ctx.text_extents(text)
	#print "Extents of \"%s\":" % text, extents
	#xbearing, ybearing, width, height, xadvance, yadvance = extents
	xbearing = 0

	ctx.move_to(x - xbearing, y)
	ctx.text_path(text)
	ctx.set_line_width(fontsize / 5.0)
	ctx.set_source_rgb(1.0, 1.0, 1.0)
	ctx.stroke_preserve()
	ctx.set_source_rgb(0.0, 0.0, 0.0)
	ctx.fill()

# Place a label centered on the indicated point and just big
# enough to contain the indicated text. Stroke and fill.
def centered_label(ctx, x, y, text, fontsize=12, shield=True):
	ctx.select_font_face("sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	ctx.set_font_size(fontsize)

	ctx.new_path()

	# Text dimensions
	# See http://www.cairographics.org/manual/cairo-cairo-scaled-font-t.html#cairo-text-extents-t
	extents = ctx.text_extents(text)
	#print "Extents of \"%s\":" % text, extents
	xbearing, ybearing, width, height, xadvance, yadvance = extents
	x -= width / 2
	y -= height / 2

	if shield:
		padding = fontsize / 4
		rounded_rectangle(ctx,
			x - padding, y - padding,
			width + 2*padding, height + 2*padding,
			5		# <-- corner radius
			)
		ctx.set_line_width(1)
		ctx.set_dash(())
		ctx.set_source_rgb(0.0, 0.0, 0.0)
		ctx.stroke_preserve()
		ctx.set_source_rgb(1.0, 1.0, 1.0)
		ctx.fill()

	ctx.move_to(x - xbearing, y - ybearing)
	ctx.text_path(text)
	if not shield:
		ctx.set_source_rgb(1.0, 1.0, 1.0)
		ctx.set_line_width(fontsize / 5.0)
		ctx.stroke_preserve()
	ctx.set_source_rgb(0.0, 0.0, 0.0)
	ctx.fill()


# Draw a red X with its center at the indicated point. Stroke.
def x_marks_the_spot(ctx, x, y, radius):
	line_width = radius / 2.5
	ctx.move_to(x - radius, y - radius)
	ctx.line_to(x + radius, y + radius)
	ctx.move_to(x + radius, y - radius)
	ctx.line_to(x - radius, y + radius)
	ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	ctx.set_line_width(line_width * 2)
	ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)		# white halo
	ctx.stroke_preserve()
	ctx.set_line_width(line_width)
	#ctx.set_source_rgba(0.0, 0.7, 0.7, 1.0)	# interesting color
	ctx.set_source_rgba(0.8, 0.3, 0.3, 1.0)
	ctx.stroke()

