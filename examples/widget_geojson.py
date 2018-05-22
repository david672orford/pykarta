#! /usr/bin/python
# pykarta/examples/widget_geojson.py
# Simple GeoJSON editor
# Last modified: 21 May 2018

import os
import sys
sys.path.insert(1, "../..")

import gtk
import gobject
import time

from pykarta.maps.widget import MapWidget, MapPrint
from pykarta.maps.layers import MapLayerScale, MapLayerAttribution
from pykarta.maps.layers.vector import \
	MapToolSelect, \
	MapToolDelete, \
	MapDrawMarker, \
	MapDrawLineString, \
	MapDrawPolygon, \
	MapDrawBoundingBox
from pykarta.maps.layers.geojson import MapLayerGeoJSON

class DemoGUI(object):
	def __init__(self):
		window = gtk.Window()
		window.set_default_size(800, 600)
		window.connect('delete-event', lambda window, event: gtk.main_quit())
		main_box = gtk.HBox()
		window.add(main_box)

		# Create the map widget
		self.map_widget = MapWidget(
			debug_level=0,
			)
		main_box.pack_start(self.map_widget)

		# Load a marker symbol	
		self.map_widget.symbols.add_symbol("Dot.svg")

		# Add editable vector shapes layer	
		vector_layer = MapLayerGeoJSON()
		self.map_widget.add_layer("vector", vector_layer)

		if os.path.exists("test.geojson"):
			with open("test.geojson", "r") as fh:
				vector_layer.load_geojson(fh)
	
		# Add some On Screen Display layers
		self.map_widget.add_osd_layer(MapLayerScale())
		self.map_widget.add_osd_layer(MapLayerAttribution())

		main_box.pack_start(gtk.VSeparator(), False, False)

		# Add some controls
		button_bar = gtk.VBox()
		main_box.pack_start(button_bar, False, False, 5)

		tools =	(
				("Select/Drag", MapToolSelect()),
				("Drag Only", None),
				("Delete", MapToolDelete()),
				("Marker", MapDrawMarker({"label":"New Point"})),
				("Line String", MapDrawLineString()),
				("Polygon", MapDrawPolygon()),
				("BBox", MapDrawBoundingBox()),
				)
		tool_i = 0
		first_button = None
		for name, obj in tools:
			button = gtk.RadioButton(group=first_button, label=name)
			if first_button is None:
				first_button = button
			button_bar.pack_start(button, False, False)
			button.connect("toggled", lambda widget, i: not widget.get_active() or vector_layer.set_tool(tools[i][1]), tool_i)
			tool_i += 1
		
		vector_layer.set_tool(tools[0][1])

		# Add a Print button
		button = gtk.Button(label="Print")
		button_bar.pack_start(button, False, False)
		button.connect("clicked", self.on_print, window)

		# Add a Save button
		button = gtk.Button(label="Save")
		button_bar.pack_start(button, False, False)
		button.connect("clicked", self.on_save)
		
		window.show_all()

	def set_center_and_zoom(self, lat, lon, zoom):
		self.map_widget.set_center_and_zoom(lat, lon, zoom)
		
	def on_print(self, widget, window):
		print "Print!"
		printer = MapPrint(self.map_widget, main_window=window)
		print printer.do_print()

	def on_save(self, widget):
		print "Save!"
		vector_layer = self.map_widget.get_layer("vector")
		with open("test_saved.geojson", "w") as fh
			vector_layer.save_geojson(fh)
	
#-----------------------------------
# Startup
#-----------------------------------

gobject.threads_init()

gui = DemoGUI()

gui.set_center_and_zoom(42.125, -72.75, 12) 			# Westfield, Mass

gtk.main()

