#! /usr/bin/python
# pykarta/maps/examples/widget_simple.py
# Last modified: 4 September 2014

import sys
sys.path.insert(1, "../..")

import gtk
import gobject
from pykarta.maps.widget import MapWidget
from pykarta.maps.layers.marker import MapLayerMarker
from pykarta.maps.layers import MapLayerScale, MapLayerAttribution

gobject.threads_init()

window = gtk.Window()
window.set_default_size(800, 800)
window.connect('delete-event', lambda window, event: gtk.main_quit())

map_widget = MapWidget(
	tile_source = "osm-default",
	debug_level=0,
	)

window.add(map_widget)
window.show_all()

# The map has a set of SVG symbols which can be used by marker layers.
# The set starts empty. This loads one symbol which we will use in
# the marker layer which we create below.
map_widget.symbols.add_symbol("Dot.svg")

# Add a layer with some map markers	
markers = MapLayerMarker()
map_widget.add_layer("demo-markers", markers)
markers.add_marker(42.13, -72.75, "Dot", "a marker")
markers.add_marker(42.12, -72.74, "Dot", "another marker")
markers.add_marker(42.11, -72.73, "Dot", "third marker")
markers.add_marker(42.10, -72.72, "Dot", "fourth marker")

# Add some On Screen Display layers
map_widget.add_osd_layer(MapLayerScale())
map_widget.add_osd_layer(MapLayerAttribution())
	
# Initial center and zoom level
map_widget.set_center_and_zoom(42.125, -72.75, 13)

# Run GTK+ main loop
gtk.main()
