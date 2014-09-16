# pykarta/draw/labels_points.py
# Copyright 2013, 2014, Trinity College
# Last modified: 12 September 2014

import cairo
from shapes import rounded_rectangle

# Print a label to the upper right of a POI marker. The x coordinate passed
# should be far enough to the right of the symbol so that the label does not
# overlap it. Stroke and fill.
def poi_label(ctx, x, y, text, fontsize=8):
	# Font
	#ctx.select_font_face("sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	ctx.select_font_face("ubuntu", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	ctx.set_font_size(fontsize)

	#extents = ctx.text_extents(text)
	#print "Extents of \"%s\":" % text, extents
	#xbearing, ybearing, width, height, xadvance, yadvance = extents
	xbearing = 0

	ctx.move_to(x - xbearing, y)
	ctx.text_path(text)
	ctx.set_line_width(fontsize / 5.0)
	ctx.set_source_rgb(1.0, 1.0, 1.0)
	ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	ctx.stroke_preserve()
	ctx.set_source_rgb(0.0, 0.0, 0.0)
	ctx.fill()

# Place a label centered on the indicated point. If shield is True, a
# box will be drawn around it. The box will be just big enough to contain
# the indicated text. Strokes and fills.
def centered_label(ctx, x, y, text, fontsize=12, shield=True):
	#ctx.select_font_face("sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	ctx.select_font_face("ubuntu", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
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
		ctx.set_line_cap(cairo.LINE_CAP_ROUND)
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


