#! /usr/bin/python
# pykarta/examples/widget_vector.py
# Last modified: 12 May 2018

import sys
sys.path.insert(1, "../..")

import gtk
import gobject
from pykarta.maps.widget import MapWidget
from pykarta.maps.layers import MapLayerScale, MapLayerAttribution
from pykarta.geometry import Point, Polygon, BoundingBox
from pykarta.maps.layers.vector import \
	MapLayerVector, \
	MapVectorMarker, \
	MapVectorLineString, \
	MapVectorPolygon, \
	MapVectorBoundingBox

gobject.threads_init()

window = gtk.Window()
window.set_default_size(800, 800)
window.connect('delete-event', lambda window, event: gtk.main_quit())

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

vector.add_obj(MapVectorLineString(Polygon([Point(42.120, -72.80), Point(42.10, -72.73), Point(42.115, -72.745)])))

vector.add_obj(MapVectorPolygon(Polygon([Point(42.125, -72.75), Point(42.2, -72.75), Point(42.125, -72.8)])))

vector.add_obj(MapVectorPolygon(Polygon(
		[Point(42.0, -72.0), Point(42.0, -71.0), Point(41.0, -72.0), Point(42.0, -72.0)],
		[[	Point(41.9, -71.9),
			Point(41.9, -71.2),
			Point(41.2, -71.9),
			Point(41.9, -71.9)]]
		), style={'fill-color':(1.0,1.0,1.0,0.5)})) 

bbox = BoundingBox()
bbox.add_point(Point(42.125, -72.70))
bbox.add_point(Point(42.10, -72.65))
vector.add_obj(MapVectorBoundingBox(bbox))

# Add some On Screen Display layers
map_widget.add_osd_layer(MapLayerScale())
map_widget.add_osd_layer(MapLayerAttribution())
	
# Initial center and zoom level
map_widget.set_center_and_zoom(42.125, -72.75, 12)

# Run GTK+ main loop
gtk.main()
