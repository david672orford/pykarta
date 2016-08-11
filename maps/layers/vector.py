# pykarta/maps/layers/vector.py
# An editable vector layer
# Copyright 2013--2016, Trinity College
# Last modified: 28 April 2016

import gtk
import cairo
import math
import weakref

from pykarta.maps.layers import MapLayer
from pykarta.geometry import Point, BoundingBox, LineString, Polygon
import pykarta.draw

#============================================================================
# A container layer which can hold vector objects
#============================================================================
class MapLayerVector(MapLayer):
	def __init__(self, tool_done_cb=None, obj_modified_cb=None):
		MapLayer.__init__(self)
		self.layer_objs = []
		self.visible_objs = []
		self.dragger = None
		self.drawing_tool = None
		self.tool_done_cb = tool_done_cb
		self.obj_modified_cb = obj_modified_cb

	# Add a vector object to the vector layer
	def add_obj(self, obj):
		self.layer_objs.append(obj)
		self.set_stale()

	# Remove a vector object from the vector layer
	def remove_obj(self, obj):
		self.layer_objs.remove(obj)
		self.set_stale()

	# Raise a vector object to the top of the Z order
	def raise_obj(self, obj):
		self.layer_objs.remove(obj)
		self.layer_objs.append(obj)
		self.set_stale()

	# Remove all of the vector objects from the vector layer
	def clear(self):
		self.layer_objs = []
		self.set_stale()

	# Set the current drawing tool. Use None to deactivate.
	def set_tool(self, tool):
		#print "set_tool(%s)" % str(tool)
		self.drawing_tool = tool
		if tool is not None:
			tool.activate(weakref.proxy(self))
			self.containing_map.set_cursor(tool.cursor)
		else:
			self.containing_map.set_cursor(None)
		self.editing_off()	# also triggers redraw

	# Turn on editing for the indicated object and move it to the top.
	def edit_obj(self, obj):
		obj.set_editable(True)
		self.raise_obj(obj)

	# Disabling editing of all of the objects.
	def editing_off(self):
		for obj in self.layer_objs:
			obj.set_editable(False)
		self.redraw()

	# The drawing tools call this function when they complete an operation.
	# tool--the tool which performed the operation
	# obj--the object which it selected, deleted, or created
	# If the user supplied a callback function, it is called.
	# Default actions are also provided.
	def drawing_tool_done(self, tool, obj):
		# If there is no callback function or it returns False, do default action.
		if self.tool_done_cb is None or not self.tool_done_cb(tool, obj):
			if type(tool) is MapToolSelect:
				self.editing_off()
				obj.set_editable(True)
				self.redraw()
			elif type(tool) is MapToolDelete:
				self.remove_obj(obj)
			else:		# new object created
				self.add_obj(obj)

	# Viewport has changed
	# Figure out which objects are now visible.
	def do_viewport(self):
		map_bbox = self.containing_map.get_bbox()
		self.visible_objs = []
		for obj in self.layer_objs:
			if obj.geometry.get_bbox().overlaps(map_bbox):
				obj.project(self.containing_map)
				self.visible_objs.append(obj)
		if self.drawing_tool is not None:
			self.drawing_tool.project(self.containing_map)

	# Draw the objects selected by do_viewport().
	def do_draw(self, ctx):
		for obj in self.visible_objs:
			obj.draw(ctx)
		if self.drawing_tool is not None:
			self.drawing_tool.draw(ctx)

	# Mouse button pressed down while pointer is over map.
	# If this function takes any action in response, it returns True
	# so that the button press will not be interpreted as the start
	# of an attempt to drag the map.
	def on_button_press(self, gdkevent):
		if gdkevent.button == 1:	# left-hand button

			# If hit is near a vertex of an object with editing enabled, start dragging it.
			for obj in reversed(self.visible_objs):
				if obj._editable:
					i = obj.get_draggable_point(gdkevent)
					if i is not None:
						self.dragger = MapDragger(obj, i)
						self.containing_map.set_cursor(gtk.gdk.FLEUR)
						#break
						# We bail out here so that if the select tool is active, we will not
						# accidently select a nearby object when we move or delete a point.
						return True

			# If a drawing tool is active, send it the new point (after snapping).
			if self.drawing_tool is not None:
				x, y, pt = self.snap_search(gdkevent, None, self.drawing_tool.use_snapping, True)
				return self.drawing_tool.on_button_press(gdkevent, x, y, pt)

		return False

	# Mouse pointer moving over map
	def on_motion(self, gdkevent):
		stop_propagation = False
		if self.drawing_tool:
			x, y, pt = self.snap_search(gdkevent, None, self.drawing_tool.use_snapping, False)
			stop_propagation = self.drawing_tool.on_motion(gdkevent, x, y)
		if self.dragger:
			x, y, pt = self.snap_search(gdkevent, self.dragger.obj, self.dragger.obj.snap, False)
			self.dragger.obj.move(self.dragger.i, x, y)
			self.dragger.moved = True
			self.redraw()
			stop_propagation = True
		return stop_propagation

	# Mouse button released while pointer is over map
	def on_button_release(self, gdkevent):
		if gdkevent.button == 1:
			if self.drawing_tool:
				self.drawing_tool.on_button_release(gdkevent)
			if self.dragger:	# if mouse was down on a point,
				if self.dragger.moved:
					x, y, pt = self.snap_search(gdkevent, self.dragger.obj, self.dragger.obj.snap, True)
					self.dragger.obj.drop(self.dragger.i, pt, self.containing_map)
				else:			# clicked but not dragged
					self.dragger.obj.delete(self.dragger.i, self.containing_map)
				if self.obj_modified_cb:
					self.obj_modified_cb(self.dragger.obj)
				self.dragger = None
				self.containing_map.set_cursor(None)
				self.redraw()
		return False

	# Look for a point (belonging to a vector object) which is near the location
	# of the gdkevent. Exclude points belonging to source_obj since we do not
	# want to snap it to itself. If such a point is found, return its coordinates.
	# Otherwise return the coordinates of the event.
	#
	# If enabled is False, this function does not snapping, it just
	# returns the coordinates of the event.
	def snap_search(self, gdkevent, source_obj, enable, need_pt):
		if enable:
			for obj in self.visible_objs:
				if obj is not source_obj:	
					snap = obj.snap_search(gdkevent)
					if snap is not None:
						#print "Snap:", gdkevent.x, gdkevent.y, map(str,snap)
						x, y, pt = snap
						if need_pt:
							return (x, y, Point(pt))
						else:
							return (x, y, None)
		if need_pt:
			return (gdkevent.x, gdkevent.y, self.containing_map.unproject_point(gdkevent.x, gdkevent.y))
		else:
			return (gdkevent.x, gdkevent.y, None)

# This class describes an object and its point on which the user has
# bought the left mouse button down. If he moves the mouse before
# letting it up, the action will be considered a drag. If not, 
# we will delete the point.
class MapDragger(object):
	def __init__(self, obj, i):
		self.obj = obj			# object to which point belongs
		self.i = i				# index of its point which is dragged
		self.moved = False		# mouse motion while left button down?

#============================================================================
# The Vector Objects
# This follow GeoJSON
#============================================================================

# Base class for vector objects
class MapVectorObj(object):
	snap = True		# snap this object's points to other objects
	min_points = 0	# when to stop allowing point deletion
	unclosed = 1	# 1 for open figures, 0 for closed figures

	def __init__(self, properties):
		self._editable = False
		self.geometry = None
		self.properties = {}
		if properties is not None:
			self.properties.update(properties)

	def set_editable(self, editable):
		self._editable = editable
		self.update_phantoms()

	# Project this vector object's points to pixel space
	def project(self, containing_map):
		self.projected_points = containing_map.project_points(self.geometry.points)
		self.update_phantoms()

	# Override this to draw the object from self.projected_points.
	def draw(self, ctx):
		pass

	# Override this if you want the object to be clickable.
	# Return True if hit.
	# Test lat_lon (a Point) or gdkevent's x and y members.
	def obj_hit_detect(self, gdkevent, lat_lon):
		return False

	# Did this click hit one of the object's points? If so, return its index.
	# If a phantom point was hit, make it a real point first.
	def get_draggable_point(self, gdkevent):
		evpoint = (gdkevent.x, gdkevent.y)
		# Real points
		i = 0
		for point in self.projected_points:
			if points_close(evpoint, point):
				return i
			i += 1
		i = 0
		# Phantom points
		for point in self.phantom_points:
			if points_close(evpoint, point):
				self.projected_points.insert(i+1, self.phantom_points[i])	# make it a real point
				self.geometry.points.insert(i+1, Point(0.0, 0.0))			# FIXME: should be able to use None here
				return i+1
			i += 1
		return None

	# Is this click close to one of the object's points? If so, return that point.
	def snap_search(self, gdkevent):
		i = 0
		for point in self.projected_points:
			if points_close((gdkevent.x, gdkevent.y), point):
				return point + (self.geometry.points[i],)
			i += 1
		return None

	# Temporarily move point i of the object to the location specified by x, y.
	def move(self, i, x, y):
		#print "move:", x, y
		self.projected_points[i] = (x, y)
		self.update_phantoms()

	# Finalize the position of a moved point.
	def drop(self, i, pt, containing_map):
		#print "drop:", pt, containing_map.project_point(pt)
		self.geometry.points[i] = pt
		self.geometry.bbox = None

	# Delete point i of this object.
	def delete(self, i, containing_map):
		if len(self.geometry.points) > self.min_points:
			self.geometry.points.pop(i)
			self.geometry.bbox = None
			self.projected_points.pop(i)
			self.update_phantoms()

	# Update the locations of the intermediate points which can be dragged to add points.
	def update_phantoms(self):
		self.phantom_points = []
		if self._editable:
			i = 0
			while i < (len(self.projected_points) - self.unclosed):
				p1 = self.projected_points[i]	
				p2 = self.projected_points[(i+1)%len(self.projected_points)]
				self.phantom_points.append(( (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2))
				i += 1

# Adapter to make a point look like a one-point line. This way we
# do not have to write a lot of exceptions for the MapVectorMarker object.
class PointWrapper(object):
	def __init__(self, *args):
		self.points = [Point(*args)]
		self.bbox = None
	def get_bbox(self):
		if self.bbox is None:
			self.bbox = BoundingBox()
			self.bbox.add_points(self.points)
		return self.bbox
	def as_geojson(self):
		return self.points[0].as_geojson()

# Draws a representation of a pykarta.geometry.Point with optional label.
# Can construct a Point from point.
class MapVectorMarker(MapVectorObj):
	min_points = 1
	def __init__(self, point, properties=None, style=None):
		MapVectorObj.__init__(self, properties)
		self.geometry = PointWrapper(point)
		self.style = {}
		if style is not None:
			self.style.update(style)
		self.symbol = None
		self.label = self.style.get("label")
	def project(self, containing_map):
		MapVectorObj.project(self, containing_map)
		if self.symbol is None:
			symbol_name = self.style.get("symbol", "Dot")
			self.symbol = containing_map.symbols.get_symbol(symbol_name, "Dot")
		self.symbol_renderer = self.symbol.get_renderer(containing_map)
	def obj_hit_detect(self, gdkevent, lat_lon):
		return points_close((gdkevent.x, gdkevent.y), self.projected_points[0])
	def draw(self, ctx):
		x, y = self.projected_points[0]
		self.symbol_renderer.blit(ctx, x, y)
		if self.label:
			pykarta.draw.poi_label(ctx, x+self.symbol_renderer.label_offset, y, self.label)

# Draws a representation of a pykarta.geometry.LineString.
# Can construct a LineString from line_string.
class MapVectorLineString(MapVectorObj):
	min_points = 2
	def __init__(self, line_string, properties=None, style=None):
		MapVectorObj.__init__(self, properties)
		if isinstance(line_string, LineString):
			self.geometry = line_string
		else:
			self.geometry = LineString(line_string)
		self.style = {"line-width":1}
		if style is not None:
			self.style.update(style)
	def obj_hit_detect(self, gdkevent, lat_lon):
		testpt = (gdkevent.x, gdkevent.y)
		points = self.projected_points
		i = 0
		limit = len(points) - 1
		while i < limit:
			if pykarta.geometry.plane_lineseg_distance(testpt, points[i], points[i+1]) < 10:
				return True
			i += 1
		return False
	def draw(self, ctx):
		pykarta.draw.line_string(ctx, self.projected_points)
		if self.style.get("arrows", False):
			pykarta.draw.line_string_arrows(ctx, self.projected_points)
		pykarta.draw.stroke_with_style(ctx, self.style)
		if self._editable:
			pykarta.draw.node_pluses(ctx, self.phantom_points, style={})
			pykarta.draw.node_dots(ctx, self.projected_points, style={})
		elif False:		# FIXME: slow, not disablable
			pykarta.draw.node_dots(ctx, self.projected_points, style={"diameter":2.0,"fill-color":(0.0,0.0,0.0,1.0)})

# Draws a representation of a pykarta.geometry.Polygon.
# Can construct a Polygon from polygon.
# Holes are drawn, but editing of holes is not yet supported.
class MapVectorPolygon(MapVectorObj):
	min_points = 3
	unclosed = 0
	def __init__(self, polygon, properties=None, style=None):
		MapVectorObj.__init__(self, properties)
		if isinstance(polygon, Polygon):
			self.geometry = polygon
		else:
			self.geometry = Polygon(polygon)
		self.style = { "line-width":1 }
		if style is not None:
			self.style.update(style)
		self.label = self.style.get("label",None)
		self.label_center = None
		self.projected_label_center = None
		self.label_fontsize = None
	def set_label(self, label):
		self.label = label
	def get_label_center(self):
		if self.label_center is None:
			self.label_center = self.geometry.choose_label_center()
		return self.label_center
	def project_label_center(self, containing_map):
		if self.label:
			zoom = containing_map.get_zoom()
			if zoom > self.style.get('label-min-zoom', 8):
				self.projected_label_center = containing_map.project_point(self.get_label_center())
				self.label_fontsize = self.style.get('label-font-size', 1.0) * zoom
			else:
				self.projected_label_center = None
	def project(self, containing_map):
		MapVectorObj.project(self, containing_map)
		self.holes_projected_points = []
		for hole in self.geometry.holes:
			self.holes_projected_points.append( containing_map.project_points(hole) )
		self.project_label_center(containing_map)
	def obj_hit_detect(self, gdkevent, lat_lon):
		return self.geometry.contains_point(lat_lon)
	def draw(self, ctx):
		pykarta.draw.polygon(ctx, self.projected_points)
		for hole_points in self.holes_projected_points:
			pykarta.draw.polygon(ctx, hole_points)
		ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
		pykarta.draw.fill_with_style(ctx, self.style, preserve=True)
		pykarta.draw.stroke_with_style(ctx, self.style)
		if self._editable:
			pykarta.draw.node_pluses(ctx, self.phantom_points, style={})
			pykarta.draw.node_dots(ctx, self.projected_points, style={})
		else:
			node_dots_style = self.style.get('node-dots-style', None)
			if node_dots_style is not None:
				pykarta.draw.node_dots(ctx, self.projected_points, style=node_dots_style)
		if self.projected_label_center:
			x, y = self.projected_label_center
			pykarta.draw.centered_label(ctx, x, y, self.label, style={'font-size':self.label_fontsize})
	def drop(self, i, pt, containing_map):
		MapVectorObj.drop(self, i, pt, containing_map)
		self.label_center = None
		self.project_label_center(containing_map)
	def delete(self, i, containing_map):
		MapVectorObj.delete(self, i, containing_map)
		self.label_center = None
		self.project_label_center(containing_map)

# Draws a representation of a pykarta.geometry.BoundingBox.
class MapVectorBoundingBox(MapVectorObj):
	snap = False
	min_points = 4
	x_map = (3, 2, 1, 0)
	y_map = (1, 0, 3, 2)
	def __init__(self, bbox, properties=None, style=None):
		MapVectorObj.__init__(self, properties)
		self.orig_bbox = bbox
		self.geometry = Polygon((
			Point(bbox.max_lat, bbox.min_lon),		# NW
			Point(bbox.max_lat, bbox.max_lon),		# NE
			Point(bbox.min_lat, bbox.max_lon),		# SE
			Point(bbox.min_lat, bbox.min_lon),		# SW
			))
		self.style = {
			"line-width":1,
			"line-dasharray":(3,2)
			}
		if style is not None:
			self.style.update(style)
	def obj_hit_detect(self, gdkevent, lat_lon):
		return self.geometry.get_bbox().contains_point(lat_lon)
	def snap_search(self, gdkevent):
		# Snapping to bounding boxes does not make sense.
		return None
	def draw(self, ctx):
		pykarta.draw.polygon(ctx, self.projected_points)
		pykarta.draw.stroke_with_style(ctx, self.style)
		if self._editable:
			pykarta.draw.node_dots(ctx, self.projected_points)
	def update_phantoms(self):
		self.phantom_points = []
	def move(self, i, x, y):
		# Figure out by how much the dragged point will move.
		start_x, start_y = self.projected_points[i]
		x_dist = x - start_x
		y_dist = y - start_y
		# Move the dragged point.
		self.projected_points[i] = (x, y)
		# Move the points at the nearest corners by the same amount, each along only one axis.
		x_i = self.x_map[i]
		self.projected_points[x_i] = (self.projected_points[x_i][0] + x_dist, self.projected_points[x_i][1])
		y_i = self.y_map[i]
		self.projected_points[y_i] = (self.projected_points[y_i][0], self.projected_points[y_i][1] + y_dist)
	def drop(self, i, pt, containing_map):
		self.geometry.points[1] = pt
		self.orig_bbox.reset()
		self.orig_bbox.add_points(self.geometry.points)
		self.geometry.bbox = None	# recompute

#============================================================================
# The drawing tools
#============================================================================

# All drawing and selection tools are derived from this.
class MapToolBase(object):
	use_snapping = False
	cursor = None
	def __init__(self, style=None):
		self.style = style
		self.layer = None
	def activate(self, layer):
		self.layer = layer
		self.reset()
	def reset(self):
		pass
	def on_button_press(self, gdkevent, x, y, pt):
		return False
	def on_motion(self, gdkevent, x, y):
		return False
	def on_button_release(self, gdkevent):
		pass
	def project(self, containing_map):
		pass
	def draw(self, ctx):
		pass
	def fire_done(self, obj):
		self.layer.drawing_tool_done(self, obj)
		self.reset()

class MapToolSelect(MapToolBase):
	def __init__(self):
		MapToolBase.__init__(self)
		self.down = False
	def on_button_press(self, gdkevent, x, y, pt):
		self.down = True
		return False
	def on_motion(self, gdkevent, x, y):
		self.down = False	# this is a drag action
		return False
	def on_button_release(self, gdkevent):
		if self.down:
			lat_lon = self.layer.containing_map.unproject_point(gdkevent.x, gdkevent.y)
			if gdkevent.state & gtk.gdk.CONTROL_MASK:
				objs = self.layer.visible_objs				# bottom to top layer
			else:
				objs = reversed(self.layer.visible_objs)	# top to bottom layer
			for obj in objs:
				if obj.obj_hit_detect(gdkevent, lat_lon):
					self.fire_done(obj)
					break
			self.down = False

# The delete tool is just the select tool with a scary cursor. It derives its
# destructive power from the fact that the default tool done handler treats
# it differently.
class MapToolDelete(MapToolSelect):
	cursor = gtk.gdk.X_CURSOR

# All drawing tools are derived from this.
class MapDrawBase(MapToolBase):
	def reset(self):
		self.points = []
		self.projected_points = []
		self.hover_point = None
	def project(self, containing_map):
		self.projected_points = containing_map.project_points(self.points)
	def on_motion(self, gdkevent, x, y):
		if len(self.projected_points):
			self.hover_point = (x, y)
		self.layer.redraw()
		return False

# Place a new map marker.
class MapDrawMarker(MapDrawBase):
	use_snapping = True
	cursor = gtk.gdk.PENCIL
	def on_button_press(self, gdkevent, x, y, pt):
		self.fire_done(MapVectorMarker(pt, self.style))
		return True

class MapDrawLineString(MapDrawBase):
	use_snapping = True
	cursor = gtk.gdk.PENCIL
	def on_button_press(self, gdkevent, x, y, pt):
		self.projected_points.append((x,y))
		self.points.append(pt)
		self.hover_point = None
		if gdkevent.state & gtk.gdk.SHIFT_MASK:	# shift-click for last point
			self.fire_done(MapVectorLineString(self.points, self.style))
		self.layer.redraw()
		return True
	def draw(self, ctx):
		if len(self.projected_points) > 1:
			pykarta.draw.line_string(ctx, self.projected_points)
			pykarta.draw.stroke_with_style(ctx, {"line-width":1,"line-color":(0.0,0.0,1.0)})
		if len(self.projected_points) > 0 and self.hover_point is not None:
			pykarta.draw.node_dots(ctx, self.projected_points)
			ctx.move_to(*(self.projected_points[-1]))
			ctx.line_to(*(self.hover_point))
			pykarta.draw.stroke_with_style(ctx, {"line-width":1,"line-dasharray":(3,2)})

class MapDrawPolygon(MapDrawBase):
	use_snapping = True
	cursor = gtk.gdk.PENCIL
	def on_button_press(self, gdkevent, x, y, pt):
		done = False
		if len(self.projected_points) >= 3 and points_close((x, y), self.projected_points[0]):
			done = True
		else:	
			self.projected_points.append((x, y))
			self.points.append(pt)
			self.hover_point = None
			if gdkevent.state & gtk.gdk.SHIFT_MASK:
				done = True
		if done:
			self.fire_done(MapVectorPolygon(self.points, self.style))
		self.layer.redraw()
		return True
	def draw(self, ctx):
		if len(self.projected_points) > 1:
			pykarta.draw.line_string(ctx, self.projected_points)
			pykarta.draw.fill_with_style(ctx, {"fill-color":(1.0,1.0,1.0,0.5)}, preserve=True)
			pykarta.draw.stroke_with_style(ctx, {"line-width":1})
		if len(self.projected_points) > 0 and self.hover_point is not None:
			pykarta.draw.node_dots(ctx, self.projected_points)
			ctx.move_to(*(self.projected_points[-1]))
			ctx.line_to(*(self.hover_point))
			pykarta.draw.stroke_with_style(ctx, {"line-width":1,"line-dasharray":(3,2)})

class MapDrawBoundingBox(MapDrawBase):
	cursor = gtk.gdk.SIZING
	def on_button_press(self, gdkevent, x, y, pt):
		self.projected_points = [(x,y)]
		self.points = [pt]
		self.hover_point = None
		self.layer.redraw()
		return True
	def on_motion(self, gdkevent, x, y):
		MapDrawBase.on_motion(self, gdkevent, x, y)
		return True	# <-- prevent map motion
	def on_button_release(self, gdkevent):
		if self.hover_point is not None:
			self.projected_points.append(self.hover_point)
			self.points.append(self.layer.containing_map.unproject_points(*(self.hover_point)))
			bbox = BoundingBox()
			bbox.add_points(self.points)
			self.fire_done(MapVectorBoundingBox(bbox))
	def draw(self, ctx):
		if len(self.projected_points) > 0 and self.hover_point is not None:
			start_x, start_y = self.projected_points[0]
			hover_x, hover_y = self.hover_point
			ctx.rectangle(start_x, start_y, hover_x - start_x, hover_y - start_y)
			pykarta.draw.stroke_with_style(ctx, {"line-width":1,"line-dasharray":(3,2)})

def points_close(p1, p2, tolerance=10):
	return abs(p1[0] - p2[0]) <= tolerance and abs(p1[1] - p2[1]) <= tolerance

