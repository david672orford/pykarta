#! /usr/bin/python3
# pykarta/examples/widget_basic.py
# How to display a simple map in Gtk widget
# Last modified: 25 March 2023

import sys, os
sys.path.insert(1, "../..")

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pykarta
from pykarta.maps.widget import MapWidget
from pykarta.maps.layers import MapLayerBuilder, MapLayerScale, MapLayerAttribution

pykarta.server_url = os.environ.get('PYKARTA_SERVER_URL', pykarta.server_url)

window = Gtk.Window()
window.set_default_size(800, 800)
window.connect('delete-event', Gtk.main_quit)

map_widget = MapWidget(
	tile_source = "osm-default",
	#tile_source = "osm-vector",
	#tile_source = "osm-vector-roads",
	#tile_source = "osm-vector-road-labels",
	debug_level=10,
	)

window.add(map_widget)
window.show_all()
		
# Shows tile numbers and boundaries
map_widget.add_layer("tile_debug", MapLayerBuilder("tile-debug"))

# Add some On Screen Display layers
map_widget.add_osd_layer(MapLayerScale())
map_widget.add_osd_layer(MapLayerAttribution())
	
# Initial center and zoom level
map_widget.set_center_and_zoom(42.125, -72.75, 12)

# Run GTK main loop
Gtk.main()

