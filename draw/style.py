# pykarta/draw/style.py
# Copyright 2013, 2014, Trinity College
# Last modified: 18 September 2014
#
# This module has functions to stroke lines and fill polygons using style
# attributes borrowed from Cascadenik. See:
# https://github.com/mapnik/Cascadenik/wiki/Dictionary

import cairo

# Stroke the path in the specified style. This was inspired by Cascadenik.
def stroke_with_style(ctx, style, preserve=False):
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
		color = style['underline-color']
		if len(color) == 4:
			ctx.set_source_rgba(*color)
		else:
			ctx.set_source_rgb(*color)
		ctx.set_dash(style.get('underline-dasharray', ()))
		ctx.stroke_preserve()

	# This is the main stroke.
	if 'line-width' in style:
		ctx.set_line_width(style['line-width'])
		color = style.get('line-color', (0.0, 0.0, 0.0))
		if len(color) == 4:
			ctx.set_source_rgba(*color)
		else:
			ctx.set_source_rgb(*color)
		ctx.set_dash(style.get('line-dasharray', ()))
		ctx.stroke_preserve()

	# This stroke goes over the main stroke. We can use it to run a solid
	# or dashed line down the center of the main stroke.
	if 'overline-width' in style:
		ctx.set_line_width(style['overline-width'])
		color = style['overline-color']
		if len(color) == 4:
			ctx.set_source_rgba(*color)
		else:
			ctx.set_source_rgb(*color)
		ctx.set_dash(style.get('overline-dasharray', ()))
		ctx.stroke_preserve()

	# This whole function is pitched as a substitute for stroke(), so
	# it should clear the path.
	if not preserve:
		ctx.new_path()

# Fill a polygon according to the specified style. By default it is
# filled with transparent white. To disable filling, set fill-color
# to None in the style.
def fill_with_style(ctx, style, preserve=False):
	fill_color = style.get("fill-color")
	if fill_color is not None:
		if len(fill_color) == 4:
			ctx.set_source_rgba(*fill_color)
		else:
			ctx.set_source_rgb(*fill_color)
		if preserve:
			ctx.fill_preserve()
		else:
			ctx.fill()


