#! /usr/bin/python
import sys
sys.path.insert(1, "../..")
import gobject
import gtk
from pykarta.geometry import Point
from pykarta.maps.widget import MapWidget
gobject.threads_init()
window = gtk.Window()
window.set_default_size(800, 800)
window.connect('delete-event', lambda window, event: gtk.main_quit())
map_widget = MapWidget()
map_widget.set_center_and_zoom(42.125, -72.75, 12)
window.add(map_widget)
window.show_all()

# Make a bunch of points
point = Point(42.00, -72.00)
points = []
for i in range(10000):
	points.append(point)

# Benchmark projection
# Started at 4.6 seconds
import timeit
print "Starting..."
print timeit.timeit('map_widget.project_points(points)', number=100, setup="from __main__ import map_widget, points")

