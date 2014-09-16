# pykarta/draw/labels_lines.py
# Copyright 2013, 2014, Trinity College
# Last modified: 12 September 2014

import cairo
import math

def label_line(ctx, line, label_text, fontsize=8, tilesize=None):
	assert len(line) >= 2

	#ctx.select_font_face("Sans")
	ctx.select_font_face("Ubuntu")
	ctx.set_font_size(fontsize)
	xbearing, ybearing, width, height, xadvance, yadvance = ctx.text_extents(label_text)

	# Find the length of each line segment
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
		return

	# Find the middle segment
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
			return

	# and find the angle of the middle segment
	if dx != 0:
		slope = dy/dx
		angle = math.atan(slope)
	elif dy > 0:
		angle = math.pi / 2
	else:
		angle = -math.pi / 2

	#if label_text == "Trimmer Lane":
	#	print " line:", line
	#	print " center:", i
	#	print " dx:", dx
	#	print " dy:", dy
	#	print " middle:", middle
	#	print " angle:", math.degrees(angle)

	ctx.save()
	ctx.translate(middle[0], middle[1])
	ctx.rotate(angle)
	ctx.move_to(0 - width / 2, -5)
	ctx.text_path(label_text)
	ctx.set_line_width(fontsize / 5.0)
	ctx.set_source_rgb(1.0, 1.0, 1.0)
	ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	if False:
		ctx.stroke_preserve()
		ctx.set_source_rgb(0.0, 0.0, 0.0)
		ctx.fill()
	else:
		ctx.stroke()
		ctx.set_source_rgb(0.0, 0.0, 0.0)
		ctx.move_to(0 - width / 2, -5)
		ctx.show_text(label_text)
	ctx.restore()

