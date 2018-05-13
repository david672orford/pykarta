#! /usr/bin/python
# pykarta/examples/widget_custom_layer.py
# Last modified: 12 May 2018

import sys
sys.path.insert(1, "../..")

import gtk
import gobject
from pykarta.maps.widget import MapWidget
from pykarta.maps.layers import MapLayer, MapLayerScale, MapLayerAttribution
from pykarta.geometry import Point

# A minimal geographic layer
class TrivialLayer(MapLayer):

	def do_viewport(self):
		print "Test layer: new viewport:", self.containing_map.get_bbox()
		# Project three points into tilespace
		points = (Point(42.125,-72.75), Point(42.125,-72.70), Point(42.10,-72.70))
		self.points_projected = self.containing_map.project_points(points)

	def do_draw(self, ctx):
		print "Test layer: redraw"
		# Use Cairo to draw a line between the three points
		ctx.set_source_rgb(0.0, 0.0, 0.0)
		ctx.set_line_width(1)
		ctx.move_to(*self.points_projected[0])
		for p in self.points_projected[1:]:
			ctx.line_to(*p)
		ctx.stroke()

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
		
# Add custom layer defined above.
map_widget.add_layer("trivial", TrivialLayer())
	
# Add some On Screen Display layers
map_widget.add_osd_layer(MapLayerScale())
map_widget.add_osd_layer(MapLayerAttribution())
	
# Initial center and zoom level
map_widget.set_center_and_zoom(42.125, -72.75, 12)

# Run GTK+ main loop
gtk.main()

