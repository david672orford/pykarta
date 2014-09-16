#! /usr/bin/python
# pykarta/maps/examples/widget_basic.py
# Last modified: 4 September 2014

import sys
sys.path.insert(1, "../..")

import gtk
import gobject
from pykarta.maps.widget import MapWidget
from pykarta.maps.layers import MapLayerBuilder, MapLayerScale, MapLayerAttribution

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
		
# Shows tile numbers and boundaries
map_widget.add_layer("tile_debug", MapLayerBuilder("tile-debug"))

# Add some On Screen Display layers
map_widget.add_osd_layer(MapLayerScale())
map_widget.add_osd_layer(MapLayerAttribution())
	
# Initial center and zoom level
map_widget.set_center_and_zoom(42.125, -72.75, 12)

# Run GTK+ main loop
gtk.main()
