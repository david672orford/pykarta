#! /usr/bin/python

import sys
sys.path.insert(1, "../..")
import pyapp.i18n
from pykarta.maps import MapCairo
import cairo

width = 256
height = 256
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
ctx = cairo.Context(surface)

map_obj = MapCairo(tile_source = "osm-vector-roads")
map_obj.set_size(width, height)
map_obj.set_center_and_zoom(41.76733880383798, -72.6796251074755, 15.3)
map_obj.draw_map(ctx)

surface.write_to_png("vector_tile_benchmark.png")
