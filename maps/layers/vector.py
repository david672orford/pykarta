# pykarta/maps/layers/vector.py
# An editable vector layer
# Copyright 2013, 2014, Trinity College
# Last modified: 22 August 2014

import math
import gtk
import weakref

from pykarta.maps.layers import MapLayer
from pykarta.geometry import Point, BoundingBox, LineString, Polygon
import pykarta.draw

#============================================================================
# A container layer which can hold vector objects
#============================================================================
class MapVectorLayer(MapLayer):
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

	def set_tool(self, tool):
		#print "set_tool(%s)" % str(tool)
		self.drawing_tool = tool
		if tool:
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

	# The drawing tools call this when they complete an operation.
	def drawing_tool_done(self, tool, obj):
		# If there is no callback function or it returns False, do default action.
		if self.tool_done_cb is None or not self.tool_done_cb(tool, obj):
			if type(tool) is MapToolSelect:
				self.editing_off()
				obj.editable = True
				self.redraw()
			elif type(tool) is MapToolDelete:
				self.remove_obj(obj)
			else:
				self.add_obj(obj)

	# Viewport has changed
	def do_viewport(self):
		map_bbox = self.containing_map.get_bbox()
		self.visible_objs = []
		for obj in self.layer_objs:
			if obj.geometry.get_bbox().overlaps(map_bbox):
				obj.project(self.containing_map)
				self.visible_objs.append(obj)
		if self.drawing_tool:
			self.drawing_tool.project(self.containing_map)

	# Draw the objects selected by by do_viewport()
	def do_draw(self, ctx):
		for obj in self.visible_objs:
			obj.draw(ctx)
		if self.drawing_tool:
			self.drawing_tool.draw(ctx)

	# Mouse button pressed down while pointer is over map.
	# If we do anything with it, we return True so that it
	# will not be interpreted as the start of a map drag.
	def on_button_press(self, gdkevent):
		if gdkevent.button == 1:	# left-hand button

			# If hit is near a vertex of an object with editing enabled, start dragging it.
			point = Point(gdkevent.x, gdkevent.y)
			for obj in reversed(self.visible_objs):
				if obj.editable:
					i = obj.get_dragable_point(gdkevent)
					if i is not None:
						self.dragger = MapDragger(obj, i)
						self.containing_map.set_cursor(gtk.gdk.FLEUR)
						#break
						# We bail out here so that if the select tool is active, we will not
						# accidently select a nearby object when we move or delete a point.
						return True

			# If a drawing tool is active, send it the new point (after snapping).
			if self.drawing_tool:
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
			self.dragger.count += 1
			self.redraw()
			stop_propagation = True
		return stop_propagation

	# Mouse button released while pointer is over map
	def on_button_release(self, gdkevent):
		if gdkevent.button == 1:
			if self.drawing_tool:
				self.drawing_tool.on_button_release(gdkevent)
			if self.dragger:	# if mouse was down on a point,
				if self.dragger.count > 0:
					self.dragger.obj.drop(self.dragger.i, self.containing_map)
				else:
					self.dragger.obj.delete(self.dragger.i, self.containing_map)
				if self.obj_modified_cb:
					self.obj_modified_cb(self.dragger.obj)
				self.dragger = None
				self.containing_map.set_cursor(None)
				self.redraw()
		return False

	# If an object has a point near the given event position, return that point.
	# Otherwise, return the event position.
	# If enable is False, this always returns the event position.
	# The paremeter source_obj refers to the object whose point may be snapped
	# to the points of surounding objects. We use it to skip that object during
	# the search.
	def snap_search(self, gdkevent, source_obj, enable):
		if enable:
			for obj in self.visible_objs:
				if obj is not source_obj:	
					snap = obj.snap_search(gdkevent)
					if snap:
						#print "Snap!"
						return snap
		return (gdkevent.x, gdkevent.y)

class MapDragger(object):
	def __init__(self, obj, i):
		self.obj = obj
		self.i = i
		self.count = 0

#============================================================================
# The objects
# This follow GeoJSON
#============================================================================

# Base class for vector objects
class MapVectorObj(object):
	snap = True		# snap this object's points to other objects
	min_points = 0
	unclosed = 1

	def __init__(self):
		self.editable = False
		self.geometry = None

	def project(self, containing_map):
		self.projected_points = containing_map.project_points(self.geometry.points)
		self.update_phantoms()

	# Should a click at the specified location (specified in both lat, lon space
	#  and pixel space) be considered to have hit this object?
	def obj_hit_detect(self, lat_lon, gdkevent):
		pass

	# Did this click hit one of the object's points? If so, return its index.
	# If a phantom point was hit, make it a real point first.
	def get_dragable_point(self, gdkevent):
		evpoint = (gdkevent.x, gdkevent.y)
		i = 0
		for point in self.projected_points:
			if points_close(evpoint, point):
				return i
			i += 1
		i = 0
		for point in self.phantom_points:
			if points_close(evpoint, point):
				self.projected_points.insert(i+1, self.phantom_points[i])
				self.geometry.points.insert(i+1, Point(0.0, 0.0))
				return i+1
			i += 1
		return None

	# Is this click close to one of the objects points? If so, return that point.
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
		i = 0
		self.phantom_points = []
		while i < (len(self.projected_points) - self.unclosed):
			p1 = self.projected_points[i]	
			p2 = self.projected_points[(i+1)%len(self.projected_points)]
			self.phantom_points.append(( (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2))
			i += 1

class MapVectorMarker(MapVectorObj):
	min_points = 1
	def __init__(self, point, style={}):
		MapVectorObj.__init__(self)
		self.geometry = LineString((point,))
		self.style = style
		self.symbol = None
		self.label = self.style.get("label")
	def project(self, containing_map):
		MapVectorObj.project(self, containing_map)
		if self.symbol is None:
			self.symbol = containing_map.symbols.get_symbol(self.style.get("symbol","Dot"),"Dot")
		self.symbol_renderer = self.symbol.get_renderer(containing_map)
	def obj_hit_detect(self, lat_lon, gdkevent):
		return points_close((gdkevent.x, gdkevent.y), self.projected_points[0])
	def draw(self, ctx):
		x, y = self.projected_points[0]
		self.symbol_renderer.blit(ctx, x, y)
		if self.label:
			pykarta.draw.poi_label(ctx, x+self.symbol_renderer.label_offset, y, self.label)

class MapVectorLineString(MapVectorObj):
	min_points = 2
	def __init__(self, line_string, style={}):
		MapVectorObj.__init__(self)
		if isinstance(line_string, LineString):
			self.geometry = line_string
		else:
			self.geometry = LineString(line_string)
		self.style = style
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

class MapVectorPolygon(MapVectorObj):
	min_points = 3
	unclosed = 0
	def __init__(self, polygon, style={}):
		MapVectorObj.__init__(self)
		if isinstance(polygon, Polygon):
			self.geometry = polygon
		else:
			self.geometry = Polygon(polygon)
		self.style = style
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
		self.project_label_center(containing_map)
	def obj_hit_detect(self, lat_lon, gdkevent):
		return self.geometry.contains_point(lat_lon)
	def draw(self, ctx):
		pykarta.draw.polygon(ctx, self.projected_points)
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
			pykarta.draw.centered_label(ctx, x, y, self.label, fontsize=self.label_fontsize, shield=False)
	def drop(self, i, containing_map):
		MapVectorObj.drop(self, i, containing_map)
		self.label_center = None
		self.project_label_center(containing_map)
	def delete(self, i, containing_map):
		MapVectorObj.delete(self, i, containing_map)
		self.label_center = None
		self.project_label_center(containing_map)

class MapVectorBoundingBox(MapVectorObj):
	snap = False
	min_points = 4
	x_map = (3, 2, 1, 0)
	y_map = (1, 0, 3, 2)
	def __init__(self, bbox, style={}):				# FIXME: style is ignored
		MapVectorObj.__init__(self)
		self.orig_bbox = bbox
		self.geometry = Polygon((
			Point(bbox.max_lat, bbox.min_lon),		# NW
			Point(bbox.max_lat, bbox.max_lon),		# NE
			Point(bbox.min_lat, bbox.max_lon),		# SE
			Point(bbox.min_lat, bbox.min_lon),		# SW
			))
	def obj_hit_detect(self, lat_lon, gdkevent):
		return self.geometry.get_bbox().contains_point(lat_lon)
	def snap_search(self, gdkevent):
		# Snapping to bounding boxes does not make sense.
		return None
	def draw(self, ctx):
		pykarta.draw.polygon(ctx, self.projected_points)
		pykarta.draw.stroke_with_style(ctx, {"line-dash":(3,2)})
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
	def __init__(self, style={}):
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
			pykarta.draw.stroke_with_style(ctx, self.style)
		if len(self.projected_points) > 0 and self.hover_point is not None:
			pykarta.draw.node_dots(ctx, self.projected_points)
			ctx.move_to(*(self.projected_points[-1]))
			ctx.line_to(*(self.hover_point))
			pykarta.draw.stroke_with_style(ctx, {"line-dash":(3,2)})

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
			pykarta.draw.fill_with_style(ctx, self.style, preserve=True)
			pykarta.draw.stroke_with_style(ctx, self.style)
		if len(self.projected_points) > 0 and self.hover_point is not None:
			pykarta.draw.node_dots(ctx, self.projected_points)
			ctx.move_to(*(self.projected_points[-1]))
			ctx.line_to(*(self.hover_point))
			pykarta.draw.stroke_with_style(ctx, {"line-dash":(3,2)})

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
			pykarta.draw.stroke_with_style(ctx, {"line-dash":(3,2)})

def points_close(p1, p2, tolerance=10):
	return abs(p1[0] - p2[0]) <= tolerance and abs(p1[1] - p2[1]) <= tolerance

