# pykarta/draw/labels_lines.py
# Copyright 2013--2018, Trinity College
# Last modified: 23 May 2018

import cairo
import math
import re
import pango
import pangocairo

from .shapes import svg_path

#font_family = "Ubuntu"
font_family = "sans-serif"

#============================================================================
# Find a place to place the label of a line feature such as a road.
# TODO: slide the label looking for better placement
#============================================================================

def place_line_label(line, label_text, fontsize=8, tilesize=None):
	assert len(line) >= 2

	# Estimate width of text in pixels
	width = len(label_text) * fontsize * 0.6

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

#============================================================================
# Draw a line feature label at a previously selected postion.
#============================================================================

def draw_line_label_simple(ctx, placement, scale):
	label_text, fontsize, width, middle, angle = placement
	offset = fontsize * 0.2
	ctx.select_font_face(font_family)
	ctx.set_font_size(fontsize)
	ctx.save()
	ctx.translate(middle[0]*scale, middle[1]*scale)
	ctx.rotate(angle)
	ctx.move_to(0 - width / 2, offset)
	ctx.show_text(label_text)
	ctx.restore()

def draw_line_label_stroked(ctx, placement, scale):
	label_text, fontsize, width, middle, angle = placement
	offset = fontsize * 0.2
	ctx.select_font_face(font_family)
	ctx.set_font_size(fontsize)
	ctx.save()
	ctx.translate(middle[0]*scale, middle[1]*scale)
	ctx.rotate(angle)
	ctx.move_to(0 - width / 2, offset)
	ctx.text_path(label_text)
	ctx.set_line_width(fontsize / 5.0)				# halo
	ctx.set_source_rgb(1.0, 1.0, 1.0)
	ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	ctx.stroke_preserve()
	ctx.set_source_rgb(0.0, 0.0, 0.0)				# text
	ctx.fill()
	ctx.restore()

# See: http://jcoppens.com/soft/howto/pygtk/pangocairo.en.php
def draw_line_label_pango(ctx, placement, scale):
	label_text, fontsize, width, middle, angle = placement
	offset = fontsize * 0.60
	ctx.select_font_face(font_family)
	ctx.set_font_size(fontsize)
	ctx.save()
	ctx.translate(middle[0]*scale, middle[1]*scale)
	ctx.rotate(angle)
	ctx.move_to(0 - width / 2, -offset)

	pango_ctx = pangocairo.CairoContext(ctx)
	pango_ctx.set_source_rgb(0,0,0)
	pango_layout = pango_ctx.create_layout()
	pango_layout.set_text(label_text)
	pango_layout.set_font_description(pango.FontDescription("Sans %.1f" % (fontsize * 0.7)))
	pango_ctx.update_layout(pango_layout)
	pango_ctx.show_layout(pango_layout)

	ctx.restore()

#============================================================================
# Find a place along a road for the highway shield
#============================================================================

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

#============================================================================
# Draw the text inside a generic highway shield.
#============================================================================

def draw_highway_shield(ctx, x, y, ref, size=20):
	m = re.search(r'^(\S+) (\S+)$', ref)
	if m:
		route_system, route_number = m.groups()
	else:
		route_system = None
		route_number = ref

	half_size = size / 2.0
	text_color = (0.0,0.0,0.0)
	font_size = size / 2.7
	scale = size / 48.0

	ctx.save()
	ctx.translate(x - half_size, y - half_size)
	ctx.scale(scale, scale)
	ctx.set_dash(())

	# US Interstate shield
	if route_system == "I":

		# White background (shows around edges)
		#svg_path(ctx, "M 24,-1 C 24,-1 33,5 48,2 53,40 24,49 24,49 24,49 -5,40 0,2 15,5 24,-1 24,-1 Z")
		svg_path(ctx, "M 24,-1 C 24,-1 33,5 48,2 53,40 36,46 24,49 13,46 -5,40 0,2 15,5 24,-1 24,-1 Z")
		ctx.set_line_width(0.5)
		ctx.set_source_rgb(0.0, 0.0, 0.0)
		ctx.stroke_preserve()
		ctx.set_source_rgb(1.0, 1.0, 1.0)
		ctx.fill()

		# Red head
		svg_path(ctx, "M 2,4 C 2,4 9,7 24,2 39,7 46,4 46,4 L 47,11 L 1,11 Z")
		ctx.set_source_rgb(0.69, 0.12, 0.18)
		ctx.fill()

		# Blue body
		#svg_path(ctx, "M 1,13 L 47,13 C 45,39 24,47 24,47 24,47 3,39 1,13 Z")
		svg_path(ctx, "M 1,13 L 47,13 C 45,39 36,43 24,47 11,42 3,39 1,13 Z")
		ctx.set_source_rgb(0.0, 0.25, 0.53)
		ctx.fill()

		text_color = (1.0,1.0,1.0)

	# Shield
	elif route_system == "US":
		#svg_path(ctx, "M 24,0 C 24,0 33,8 48,5 53,43 24,48 24,48 24,48 -5,43 0,5 15,8 24,0 24,0 Z")
		svg_path(ctx, "M 24,1 C 24,1 32,6 47,3 53,43 24,47 24,47 24,47 -5,43 1,3 16,6 24,1 24,1 Z")

		ctx.set_source_rgba(1.0, 1.0, 1.0, 0.5)	# white halo
		ctx.set_line_width(8)
		ctx.stroke_preserve()

		ctx.set_source_rgb(0.0, 0.0, 0.0)		# black border
		ctx.set_line_width(5)
		ctx.stroke_preserve()

		ctx.set_source_rgb(1.0, 1.0, 1.0)		# white fill
		ctx.fill()

	# Simple square
	else:
		ctx.new_path()
		ctx.rectangle(2, 2, 44, 44)

		ctx.set_source_rgba(1.0, 1.0, 1.0, 0.5)	# white halo
		ctx.set_line_width(8)
		ctx.stroke_preserve()

		ctx.set_source_rgb(0.0, 0.0, 0.0)		# black border
		ctx.set_line_width(5)
		ctx.stroke_preserve()

		ctx.set_source_rgb(1.0, 1.0, 1.0)		# white fill
		ctx.fill()

	ctx.restore()

	ctx.select_font_face(font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
	ctx.set_font_size(font_size)
	text_xbearing, text_ybearing, text_width, text_height = ctx.text_extents(route_number)[:4]
	ctx.move_to( (x - text_width / 2 - text_xbearing), (y - text_height / 2 - text_ybearing) )
	ctx.set_source_rgb(*text_color)
	ctx.show_text(route_number)

