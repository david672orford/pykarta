#! /usr/bin/python
# pykarta/maps/widget_test/widget_test.py
# Last modified: 15 August 2013

import sys
sys.path.insert(1, "../../..")

import gtk
import gobject
import time

from pykarta.maps.widget import MapWidget, MapPrint
from pykarta.geometry import Point, BoundingBox
from pykarta.maps.layers import MapLayer, MapTileLayerDebug, MapLayerScale, MapLayerAttribution
from pykarta.maps.layers.vector import MapVectorLayer, \
	MapVectorMarker, \
	MapVectorLineString, \
	MapVectorPolygon, \
	MapVectorBoundingBox, \
	MapToolSelect, \
	MapToolDelete, \
	MapDrawMarker, \
	MapDrawLineString, \
	MapDrawPolygon, \
	MapDrawBoundingBox
from pykarta.maps.layers.marker import MapMarkerLayer
from pykarta.maps.layers.shapefile import MapShapefileLayer
from pykarta.maps.layers.mapquest import MapTrafficLayer

import pykarta.maps.tilesets_geojson

shapefilename = "../../../../massgis/longdisttrails/LONGDISTTRAILS_ARC_4326"

#-----------------------------------
# GUI surounding map widget
#-----------------------------------
class DemoGUI(object):
	def __init__(self, map_widget):
		window = gtk.Window()
		window.set_default_size(800, 800)
		window.connect('delete-event', lambda window, event: gtk.main_quit())
		main_box = gtk.HBox()
		window.add(main_box)

		main_box.pack_start(map_widget)
		
		main_box.pack_start(gtk.VSeparator(), False, False)
		
		button_bar = gtk.VBox()
		main_box.pack_start(button_bar, False, False, 5)

		# If the vector layer was enabled, add buttons for controlling it.
		vector_layer = map_widget.get_layer("vector")
		if vector_layer:
			tools =	(
					("Select/Drag", MapToolSelect()),
					("Drag Only", None),
					("Delete", MapToolDelete()),
					("Marker", MapDrawMarker({"label":"New Point"})),
					("Line String", MapDrawLineString()),
					("Polygon", MapDrawPolygon()),
					("BBox", MapDrawBoundingBox()),
					)
			vector_layer.set_tool(tools[0][1])
			
			tool_i = 0
			first_button = None
			for name, obj in tools:
				button = gtk.RadioButton(group=first_button, label=name)
				if first_button is None:
					first_button = button
				button_bar.pack_start(button, False, False)
				button.connect("toggled", lambda widget, i: not widget.get_active() or vector_layer.set_tool(tools[i][1]), tool_i)
				tool_i += 1
		
		# Print button
		button = gtk.Button(label="Print")
		button_bar.pack_start(button, False, False)
		button.connect("clicked", self.on_print, (window, map_widget))
		
		window.show_all()
		
	def on_print(self, widget, data):
		print "Print!"
		window, map_widget = data
		printer = MapPrint(map_widget, main_window=window)
		print printer.do_print()

#-----------------------------------
# Map widget
#-----------------------------------
def build_map_widget():
	map_widget = MapWidget(
		tile_source = "osm-default-svg",
		#tile_source=["mapquest-openaerial", "stamen-toner-labels"],
		#tile_source="bing-road",
		#tile_source=["osm-default", "osm-geojson-roads"],
		#tile_source=["osm-geojson-roads", "osm-geojson-buildings"],
		debug_level=1,
		)
	#map_widget.set_rotation(True)

	# Add test layer defined above
	#map_widget.add_layer("trivial", TrivialLayer())
	
	# Shows tile numbers and boundaries
	map_widget.add_layer("tile_debug", MapTileLayerDebug())
	
	# Traffic Jams
	#map_widget.add_layer("traffic", MapTrafficLayer())
	
	# Shapefile layer
	#map_widget.add_layer("trails", MapShapefileLayer(shapefilename))

	# POI marker layer
	#map_widget.symbols.add_symbol("Dot.svg")
	#map_widget.add_layer("marker", build_marker_layer())

	# Editable vector shapes layer	
	#map_widget.add_layer("vector", build_vector_layer())

	# Add some On Screen Display layers
	map_widget.add_osd_layer(MapLayerScale())
	map_widget.add_osd_layer(MapLayerAttribution())

	return map_widget
	
#-------------------------------------------------------------------------
# A minimal geographic layer
#-------------------------------------------------------------------------
class TrivialLayer(MapLayer):
	def do_viewport(self):
		print "Test layer: new viewport:", self.containing_map.get_bbox_degrees()
		points = (Point(42.125,-72.75), Point(42.125,-72.70), Point(42.10,-72.70))
		self.points_projected = self.containing_map.project_points(points)

	def do_draw(self, ctx):
		print "Test layer: redraw"
		ctx.set_source_rgb(0.0, 0.0, 0.0)
		ctx.set_line_width(1)
		ctx.move_to(*self.points_projected[0])
		for p in self.points_projected[1:]:
			ctx.line_to(*p)
		ctx.stroke()

#-------------------------------------------------------------------------
# Construct a vector layer and put some shapes in it
#-------------------------------------------------------------------------
def build_vector_layer():
	vector = MapVectorLayer()
	vector.add_obj(MapVectorMarker(Point(42.125, -72.73), {"label":"a house"}))
	vector.add_obj(MapVectorPolygon([Point(42.125, -72.75), Point(42.2, -72.75), Point(42.125, -72.8)]))
	vector.add_obj(MapVectorLineString([Point(42.120, -72.80), Point(42.10, -72.73), Point(42.115, -72.745)]))
	bbox = BoundingBox()
	bbox.add_point(Point(42.125, -72.70))
	bbox.add_point(Point(42.10, -72.65))
	vector.add_obj(MapVectorBoundingBox(bbox))
	return vector

#-------------------------------------------------------------------------
# Construct a marker layer and put some POI markers in it
#-------------------------------------------------------------------------
def build_marker_layer():
	markers = MapMarkerLayer()
	markers.add_marker(42.13, -72.75, "Dot", "a marker")
	markers.add_marker(42.13, -72.74, "Dot", "a marker")
	markers.add_marker(42.13, -72.73, "Dot", "a marker")
	markers.add_marker(42.13, -72.72, "Dot", "a marker")
	return markers

#-----------------------------------
# Benchmarks
#-----------------------------------

if False:
	# Benchmark projection
	# Started at 4.6 seconds
	import timeit
	point = Point(42.00, -72.00)
	points = []
	for i in range(10000):
		points.append(point)
	print timeit.timeit('map_widget.project_points(points)', number=100, setup="from __main__ import map_widget, points")

#-----------------------------------
# Startup
#-----------------------------------

gobject.threads_init()
map_widget = build_map_widget()
gui = DemoGUI(map_widget)

# Initial center and zoom level
#map_widget.set_center_and_zoom(42.125, -72.75, 12) 			# Westfield, Mass
map_widget.set_center_and_zoom(42.095823, -72.725493, 16) 	# Shaker Heights

gtk.main()

