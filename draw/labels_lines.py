# pykarta/draw/labels_lines.py
# Copyright 2014, Trinity College
# Last modified: 20 August 2014

import cairo
import math

def label_line(ctx, line, label_text, fontsize=8):
	assert len(line) >= 2

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

	if middle[0] < 0 or middle[0] > 256 or middle[1] < 0 or middle[1] > 256:
		return

	# and find the angle of the middle segment
	if dx != 0:
		slope = dy/dx
		angle = math.atan(slope)
	elif dy > 0:
		angle = math.pi / 2
	else:
		angle = -math.pi / 2

	if label_text == "Trimmer Lane":
		print " line:", line
		print " center:", i
		print " dx:", dx
		print " dy:", dy
		print " middle:", middle
		print " angle:", math.degrees(angle)

	ctx.save()
	ctx.translate(middle[0], middle[1])
	ctx.rotate(angle)
	ctx.select_font_face("Sans")
	ctx.set_font_size(fontsize)
	xbearing, ybearing, width, height, xadvance, yadvance = ctx.text_extents(label_text)
	ctx.move_to(0 - width / 2, -5)
	ctx.text_path(label_text)
	ctx.set_line_width(fontsize / 5.0)
	ctx.set_source_rgb(1.0, 1.0, 1.0)
	ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	ctx.stroke_preserve()
	ctx.set_source_rgb(0.0, 0.0, 0.0)
	ctx.fill()
	ctx.restore()

