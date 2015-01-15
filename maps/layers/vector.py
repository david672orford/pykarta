# pykarta/maps/layers/vector.py
# An editable vector layer
# Copyright 2013, 2014, Trinity College
# Last modified: 18 December 2014

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
		obj.editable = True
		self.raise_obj(obj)

	# Disabling editing of all of the objects.
	def editing_off(self):
		for obj in self.layer_objs:
			obj.editable = False
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
				obj.editable = True
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
			#point = Point(gdkevent.x, gdkevent.y)		# unused?
			for obj in reversed(self.visible_objs):
				if obj.editable:
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
				x, y = self.snap_search(gdkevent, None, self.drawing_tool.use_snapping)
				return self.drawing_tool.on_button_press(x, y, gdkevent)

		return False

	# Mouse pointer moving over map
	def on_motion(self, gdkevent):
		stop_propagation = False
		if self.drawing_tool:
			x, y = self.snap_search(gdkevent, None, self.drawing_tool.use_snapping)
			stop_propagation = self.drawing_tool.on_motion(x, y, gdkevent)
		if self.dragger:
			snapped_x, snapped_y = self.snap_search(gdkevent, self.dragger.obj, self.dragger.obj.snap)
			self.dragger.obj.move(self.dragger.i, snapped_x, snapped_y, gdkevent)
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
					self.dragger.obj.drop(self.dragger.i, self.containing_map)
				else:			# clicked but not dragged
					self.dragger.obj.delete(self.dragger.i, self.containing_map)
				if self.obj_modified_cb:
					self.obj_modified_cb(self.dragger.obj)
				self.dragger = None
				self.containing_map.set_cursor(None)
				self.redraw()
		return False

	# Look for a point (belonging to a vector object) which is near
	# the location of gdkevent. Exclude points belonging to source_obj
	# since we do not want to snap it to itself.
	# If such a point is found, return its coordinates. Otherwise
	# return the coordinates of the event.
	# If enabled is False, this function does not snapping, it just
	# returns the coordinates of the event.
	def snap_search(self, gdkevent, source_obj, enable):
		if enable:
			for obj in self.visible_objs:
				if obj is not source_obj:	
					snap = obj.snap_search(gdkevent)
					if snap:
						#print "Snap!"
						return snap
		return (gdkevent.x, gdkevent.y)

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
		self.editable = False
		self.geometry = None
		self.properties = {}
		if properties is not None:
			self.properties.update(properties)

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
	def obj_hit_detect(self, lat_lon, gdkevent):
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
				self.projected_points.insert(i+1, self.phantom_points[i])
				self.geometry.points.insert(i+1, Point(0.0, 0.0))
				return i+1
			i += 1
		return None

	# Is this click close to one of the object's points? If so, return that point.
	def snap_search(self, gdkevent):
		for point in self.projected_points:
			if points_close((gdkevent.x, gdkevent.y), point):
				return point
		return False

	# Move point i of the object to the location specified by x, y.
	def move(self, i, x, y, gdkevent):
		self.projected_points[i] = (x, y)
		self.update_phantoms()

	# Finalize the position of a moved point.
	def drop(self, i, containing_map):
		self.geometry.points[i] = containing_map.unproject_point(*(self.projected_points[i]))
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
		if self.editable:
			i = 0
			while i < (len(self.projected_points) - self.unclosed):
				p1 = self.projected_points[i]	
				p2 = self.projected_points[(i+1)%len(self.projected_points)]
				self.phantom_points.append(( (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2))
				i += 1

# Adapter to make a point look like a one-point line. This way we
# do not have to write a lot of exceptions for this object.
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
	def obj_hit_detect(self, lat_lon, gdkevent):
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
	def obj_hit_detect(self, lat_lon, gdkevent):
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
		if self.editable:
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
	def obj_hit_detect(self, lat_lon, gdkevent):
		return self.geometry.contains_point(lat_lon)
	def draw(self, ctx):
		pykarta.draw.polygon(ctx, self.projected_points)
		for hole_points in self.holes_projected_points:
			pykarta.draw.polygon(ctx, hole_points)
		ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
		pykarta.draw.fill_with_style(ctx, self.style, preserve=True)
		pykarta.draw.stroke_with_style(ctx, self.style)
		if self.editable:
			pykarta.draw.node_pluses(ctx, self.phantom_points, style={})
			pykarta.draw.node_dots(ctx, self.projected_points, style={})
		else:
			node_dots_style = self.style.get('node-dots-style', None)
			if node_dots_style is not None:
				pykarta.draw.node_dots(ctx, self.projected_points, style=node_dots_style)
		if self.projected_label_center:
			x, y = self.projected_label_center
			pykarta.draw.centered_label(ctx, x, y, self.label, style={'font-size':self.label_fontsize})
	def drop(self, i, containing_map):
		MapVectorObj.drop(self, i, containing_map)
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
	def obj_hit_detect(self, lat_lon, gdkevent):
		return self.geometry.get_bbox().contains_point(lat_lon)
	def snap_search(self, gdkevent):
		# Snapping to bounding boxes does not make sense.
		return None
	def draw(self, ctx):
		pykarta.draw.polygon(ctx, self.projected_points)
		pykarta.draw.stroke_with_style(ctx, self.style)
		if self.editable:
			pykarta.draw.node_dots(ctx, self.projected_points)
	def update_phantoms(self):
		self.phantom_points = []
	def move(self, i, x, y, gdkevent):
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
	def drop(self, i, containing_map):
		self.geometry.points = containing_map.unproject_points(self.projected_points)
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
	def on_button_press(self, x, y, gdkevent):
		return False
	def on_motion(self, x, y, gdkevent):
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
	def on_button_press(self, x, y, gdkevent):
		self.down = True
		return False
	def on_motion(self, x, y, gdkevent):
		self.down = False	# this is a drag action
		return False
	def on_button_release(self, gdkevent):
		if self.down:
			lat_lon = self.layer.containing_map.unproject_point(gdkevent.x, gdkevent.y)
			for obj in reversed(self.layer.visible_objs):
				if obj.obj_hit_detect(lat_lon, gdkevent):
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
	def on_motion(self, x, y, gdkevent):
		if len(self.projected_points):
			self.hover_point = (x, y)
		self.layer.redraw()
		return False

# Place a new map marker.
class MapDrawMarker(MapDrawBase):
	use_snapping = True
	cursor = gtk.gdk.PENCIL
	def on_button_press(self, x, y, gdkevent):
		point = self.layer.containing_map.unproject_point(x, y)
		self.fire_done(MapVectorMarker(point, self.style))
		return True

class MapDrawLineString(MapDrawBase):
	use_snapping = True
	cursor = gtk.gdk.PENCIL
	def on_button_press(self, x, y, gdkevent):
		pt = (x, y)
		self.projected_points.append(pt)
		self.points.append(self.layer.containing_map.unproject_point(*pt))
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
	def on_button_press(self, x, y, gdkevent):
		done = False
		if len(self.projected_points) >= 3 and points_close((x, y), self.projected_points[0]):
			done = True
		else:	
			self.points.append(self.layer.containing_map.unproject_point(x, y))
			self.projected_points.append((x, y))
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
	def on_button_press(self, x, y, gdkevent):
		pt = (gdkevent.x, gdkevent.y)
		self.points = [self.layer.containing_map.unproject_point(*pt)]
		self.projected_points = [pt]
		self.hover_point = None
		self.layer.redraw()
		return True
	def on_motion(self, x, y, gdkevent):
		MapDrawBase.on_motion(self, x, y, gdkevent)
		return True	# <-- prevent map motion
	def on_button_release(self, gdkevent):
		if self.hover_point is not None:
			self.projected_points.append(self.hover_point)
			self.points = self.layer.containing_map.unproject_points(self.projected_points)
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

