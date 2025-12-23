#! /usr/bin/python3
# pykarta/examples/widget_vector.py
# Last modified: 25 March 2023

import sys
sys.path.insert(1, "../..")

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from pykarta.maps.widget import MapWidget
from pykarta.maps.layers import MapLayerScale, MapLayerAttribution
from pykarta.geometry import Point, LineString, Polygon, BoundingBox
from pykarta.maps.layers.vector import \
	MapLayerVector, \
	MapVectorMarker, \
	MapVectorLineString, \
	MapVectorPolygon, \
	MapVectorBoundingBox

window = Gtk.Window()
window.set_default_size(800, 800)
window.connect('delete-event', Gtk.main_quit)

map_widget = MapWidget(
	#tile_source = "osm-default",
	tile_source = "osm-vector",
	debug_level=0,
	)

window.add(map_widget)
window.show_all()
		
# The map has a set of SVG symbols which can be used by marker layers.
# The set starts empty. This loads one symbol which will be used by
# the vector layer which we create below to display markers.
map_widget.symbols.add_symbol("Dot.svg")

# Vector layer
vector = MapLayerVector()
map_widget.add_layer("vector-doodles", vector)

vector.add_obj(MapVectorMarker(Point(42.125, -72.73), {"label":"a house"}))

vector.add_obj(MapVectorLineString(LineString([
	Point(42.130, -72.70),
	Point(42.150, -72.69),
	Point(42.160, -72.65)
	]), style={"line-color": (0.0, 0.0, 1.0), "line-width": 3}))

vector.add_obj(MapVectorPolygon(Polygon([Point(42.125, -72.75), Point(42.2, -72.75), Point(42.125, -72.8)])))

# FIXME: This is off-screen
vector.add_obj(MapVectorPolygon(Polygon(
		points=[
			Point(42.1, -72.8),
			Point(42.1, -72.7),
			Point(42.0, -72.7),
			Point(42.1, -72.8)
			],
		holes=[[
			Point(42.09, -72.78),
			Point(42.09, -72.71),
			Point(42.02, -72.71),
			Point(42.09, -72.78)]]
		), style={'fill-color':(0.0,1.0,0.0,0.5)})) 

bbox = BoundingBox()
bbox.add_point(Point(42.125, -72.65))
bbox.add_point(Point(42.10, -72.60))
vector.add_obj(MapVectorBoundingBox(bbox))

# Add some On Screen Display layers
map_widget.add_osd_layer(MapLayerScale())
map_widget.add_osd_layer(MapLayerAttribution())
	
# Initial center and zoom level
map_widget.set_center_and_zoom(42.125, -72.70, 12)

# Run GTK+ main loop
Gtk.main()
