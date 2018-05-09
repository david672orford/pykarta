# pykarta/draw/labels_points.py
# Draw POI labels
# Copyright 2013--2018, Trinity College
# Last modified: 9 May 2018

import cairo

#font_family = "ubuntu"
font_family = "sans-serif"

font_weights = {
	'normal':cairo.FONT_WEIGHT_NORMAL,
	'bold':cairo.FONT_WEIGHT_BOLD,
	}

# Print a label to the upper right of a POI marker. The x coordinate passed
# should be far enough to the right of the symbol so that the label does not
# overlap it. Stroke and fill.
def poi_label(ctx, x, y, text, fontsize=8):
	ctx.select_font_face(font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	ctx.set_font_size(fontsize)
	#xbearing, ybearing, width, height, xadvance, yadvance = ctx.text_extents(text)
	xbearing = 0
	ctx.move_to(x - xbearing, y)
	ctx.text_path(text)
	ctx.set_line_width(fontsize / 5.0)
	ctx.set_source_rgb(1.0, 1.0, 1.0)
	ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	ctx.stroke_preserve()
	ctx.set_source_rgb(0.0, 0.0, 0.0)
	ctx.fill()

# Place a holoed label centered on the indicated point.
def centered_label(ctx, x, y, text, style=None, fontsize=None):
	assert isinstance(text, basestring)
	if style is None:
		if fontsize is not None:
			print "Warning: use of fontsize with centered_label() is deprecated"
			style = {'font-size':fontsize}
		else:
			style = {'font-size':12}
	
	font_size = style.get('font-size',12)
	font_weight = font_weights[style.get('font-weight','normal')]
	color = style.get('color',(0.0,0.0,0.0))
	halo = style.get('halo', True)

	ctx.select_font_face(font_family, cairo.FONT_SLANT_NORMAL, font_weight)
	ctx.set_font_size(font_size)
	ctx.new_path()
	extents = ctx.text_extents(text)
	xbearing, ybearing, width, height, xadvance, yadvance = extents
	x -= width / 2
	y -= height / 2
	ctx.move_to(x - xbearing, y - ybearing)		# draw text
	ctx.text_path(text)
	if halo:
		ctx.set_source_rgb(1.0, 1.0, 1.0)		# stroke halo
		ctx.set_line_width(font_size / 5.0)
		ctx.set_line_cap(cairo.LINE_CAP_ROUND)
		ctx.stroke_preserve()
	ctx.set_source_rgba(*color)					# fill text
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

