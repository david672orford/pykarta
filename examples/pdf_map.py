#! /usr/bin/python3

import os, sys
sys.path.insert(1, os.path.join(os.path.dirname(__file__), ".."))
import cairo
from pykarta.maps import MapCairo, MapFeedback
from pykarta.maps.layers.marker import MapLayerMarker
from pykarta.maps.layers import MapLayerScale, MapLayerAttribution

page_width = 8.5 * 72.0
page_height = 11.0 * 72.0
margin = 0.5 * 72.0
map_width = page_width - (2 * margin)
map_height = page_height - (2 * margin)

surface = cairo.PDFSurface("output.pdf", page_width, page_height)
ctx = cairo.Context(surface)

map_obj = MapCairo(
	tile_source = "osm-default",
	feedback = MapFeedback(debug_level=10),
	)
map_obj.set_size(map_width, map_height)
map_obj.set_center_and_zoom(42.125, -72.75, 13)
#map_obj.add_osd_layer(MapLayerScale())
#map_obj.add_osd_layer(MapLayerAttribution())
#map_obj.symbols.add_symbol("Dot.svg")

markers = MapLayerMarker()
map_obj.add_layer("demo-markers", markers)
markers.add_marker(42.13, -72.75, "Dot", "a marker")
markers.add_marker(42.12, -72.74, "Dot", "another marker")
markers.add_marker(42.11, -72.73, "Dot", "third marker")
markers.add_marker(42.10, -72.72, "Dot", "fourth marker")

ctx.save()
ctx.translate(margin, margin)
map_obj.draw_map(ctx)
ctx.restore()

ctx.new_path()
ctx.rectangle(margin, margin, map_width, map_height)
ctx.set_source_rgb(0.0, 0.0, 0.0)
ctx.set_line_width(0.25)
ctx.stroke()

ctx.show_page()

