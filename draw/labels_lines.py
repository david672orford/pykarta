# pykarta/draw/labels_lines.py
# Copyright 2013--2018, Trinity College
# Last modified: 15 May 2018

import cairo
import math

from shapes import rounded_rectangle

#font_family = "Ubuntu"
font_family = "sans-serif"

# Find a place to place the label of a line feature such as a road.
# TODO: slide the label looking for better placement
def place_line_label(ctx, line, label_text, fontsize=8, tilesize=None):
	assert len(line) >= 2

	ctx.select_font_face(font_family)
	ctx.set_font_size(fontsize)
	xbearing, ybearing, width, height, xadvance, yadvance = ctx.text_extents(label_text)

	# Find the length of each line segment and the total length
	distances = []
	total_distance = 0
	for i in range(len(line)-1):
		p1 = line[i]
		p2 = line[i+1]
		dx = p2[0] - p1[0]
		dy = p2[1] - p1[1]
		distance = math.sqrt(dx * dx + dy * dy)
		distances.append(distance)
		total_distance += distance

	# If it won't fit, bail out
	if total_distance < width:
		return None

	# Find the middle segment (in terms of distance)
	countdown = total_distance / 2
	i = 0
	for distance in distances:
		countdown -= distance
		if countdown < 0:
			break
		i += 1
	p1 = line[i]
	p2 = line[i+1]

	# Find the middle of the middle segment
	dx = p2[0] - p1[0]
	dy = p2[1] - p1[1]
	middle = (p1[0] + dx/2, p1[1] + dy/2)

	# If the middle is not inside the tile, bail out
	if tilesize is not None:
		if middle[0] < 0 or middle[0] > tilesize or middle[1] < 0 or middle[1] > tilesize:
			return None

	# and find the angle of the middle segment
	if dx != 0:
		slope = dy/dx
		angle = math.atan(slope)
	elif dy > 0:
		angle = math.pi / 2
	else:
		angle = -math.pi / 2

	return (label_text, fontsize, width, middle, angle)

# Draw a line feature label at a previously selected postion.
def draw_line_label(ctx, placement, scale, offset):
	label_text, fontsize, width, middle, angle = placement
	ctx.select_font_face(font_family)
	ctx.set_font_size(fontsize)
	ctx.save()
	ctx.translate(middle[0]*scale, middle[1]*scale)
	ctx.rotate(angle)
	ctx.move_to(0 - width / 2, -offset)
	ctx.text_path(label_text)
	ctx.set_line_width(fontsize / 5.0)
	ctx.set_source_rgb(1.0, 1.0, 1.0)
	ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	if False:
		ctx.stroke_preserve()
		ctx.set_source_rgb(0.0, 0.0, 0.0)
		ctx.fill()
	else:	# may give us hinting
		ctx.stroke()
		ctx.set_source_rgb(0.0, 0.0, 0.0)
		ctx.move_to(0 - width / 2, -offset)
		ctx.show_text(label_text)
	ctx.restore()

# Find a place along a road for the highway shield
def place_line_shield(line):
	longest_distance = 0.0
	longest_distance_center = None
	for i in range(len(line)-1):
		p1 = line[i]
		p2 = line[i+1]
		dx = p2[0] - p1[0]
		dy = p2[1] - p1[1]
		distance = math.sqrt(dx * dx + dy * dy)
		#print p1, p2, distance
		if distance > longest_distance:
			center = (p1[0] + dx/2.0, p1[1] + dy/2.0)
			if min(center[0],center[1]) >= 0 and max(center[0],center[1]) < 256:	# if within tile
				longest_distance = distance
				longest_distance_center = center
	return longest_distance_center

# Draw the text inside a generic highway shield.
def generic_shield(ctx, x, y, text, fontsize=12):
	ctx.select_font_face(font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	ctx.set_font_size(fontsize)
	extents = ctx.text_extents(text)
	xbearing, ybearing, width, height, xadvance, yadvance = extents

	x -= width / 2
	y -= height / 2
	padding_left_right = fontsize / 4
	padding_top_bottom = fontsize / 2

	# White shield with black edging
	ctx.new_path()
	rounded_rectangle(ctx,
		x - padding_left_right, y - padding_top_bottom,
		width + 2*padding_left_right, height + 2*padding_top_bottom,
		r=fontsize		# <-- corner radius
		)

	#ctx.set_line_width(3)
	#ctx.set_dash(())
	#ctx.set_source_rgb(1.0, 1.0, 1.0)
	#ctx.stroke_preserve()

	ctx.set_line_width(1)						# black border
	ctx.set_dash(())
	ctx.set_source_rgb(0.0, 0.0, 0.0)
	ctx.stroke_preserve()

	ctx.set_source_rgb(1.0, 1.0, 1.0)
	ctx.fill()
	# Text
	ctx.move_to(x - xbearing, y - ybearing)
	ctx.text_path(text)
	ctx.set_source_rgb(0.0, 0.0, 0.0)
	ctx.fill()

