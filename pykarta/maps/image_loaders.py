# pykarta/maps/image_loaders.py
# Last modified: 26 March 2023
#
# Use GDK to load PNG and JPEG images into new Cairo surfaces.
# We do not use cairo.ImageSurface.create_from_png() because even after
# the file is loaded, the surface works very slowly. This greatly slows
# down map drawing.
#

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GdkPixbuf
import cairo

def surface_from_pixbuf(pixbuf):
	surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, pixbuf.get_width(), pixbuf.get_height())
	ctx = cairo.Context(surface)
	Gdk.cairo_set_source_pixbuf(ctx, pixbuf, 0, 0)
	ctx.paint()
	return surface

def pixbuf_from_file(filename):
	return GdkPixbuf.Pixbuf.new_from_file(filename)

def pixbuf_from_file_data(data):
	loader = GdkPixbuf.PixbufLoader()
	loader.write(data)
	loader.close()
	return loader.get_pixbuf()

def surface_from_file(filename):
	return surface_from_pixbuf(pixbuf_from_file(filename))

def surface_from_file_data(data):
	return surface_from_pixbuf(pixbuf_from_file_data(data))

