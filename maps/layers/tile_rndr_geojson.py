# encoding=utf-8
# pykarta/maps/layers/tile_rndr_geojson.py
# Base class for GeoJSON vector tile renderers
# Copyright 2013--2018, Trinity College
# Last modified: 15 May 2018

from __future__ import print_function
try:
	import simplejson as json
except ImportError:
	import json
import gzip
import os
import math
import time

from pykarta.geometry.projection import project_to_tilespace_pixel
from pykarta.geometry import Polygon
import pykarta.draw

def json_loader(filename):
	try:
		f = gzip.GzipFile(filename, "rb")
		parsed_json = json.load(f)
	except IOError:
		f = open(filename, "r")
		parsed_json = json.load(f)
	return parsed_json

def _project_to_tilespace_pixels(coordinates, zoom, xtile, ytile):
	return map(lambda p: project_to_tilespace_pixel(p[1], p[0], zoom, xtile, ytile), coordinates)

# This is twice as fast as the above.
def project_to_tilespace_pixels(coordinates, zoom, xtile, ytile):
	n = 2.0 ** zoom
	nx2 = 2.0 / n
	nx360 = 360.0 / n
	radians = math.radians
	log = math.log
	tan = math.tan
	cos = math.cos
	pi = math.pi
	return [
		(
			((lon + 180.0) / nx360 - xtile) * 256.0,
			(((1.0 - log(tan(radians(lat)) + (1 / cos(radians(lat)))) / pi) / nx2) - ytile) * 256.0
			)
		for lon, lat in coordinates]

# Base class for a tile which renders GeoJSON
class MapGeoJSONTile(object):
	draw_passes = 1										# draw1(), override for draw2(), etc.
	clip = None
	sort_key = None
	label_polygons = False
	def __init__(self, layer, filename, zoom, x, y, data=None):
		self.timing_load = True							# Option: Time the loading routines and print the results
		self.timing_draw = False						# Option: Time the drawing routines and print the results
		self.tileset = layer.tileset					# Note that we do not keep a reference to layer
		self.containing_map = layer.containing_map		# itself since that would be circular.
		self.dedup = layer.dedup
		self.style_cache = layer.style_cache
		self.zoom = zoom
		self.x = x
		self.y = y
		self.labels = {}								# labels indexed by zoom level

		if self.timing_load:
			self._elapsed_start("Parsing %s %s %d %d %d..." % (layer.tileset.key, type(self).__name__, zoom, x, y))
		if data is not None:
			parsed_json = data
		else:
			parsed_json = json_loader(filename)

		self._load_features(parsed_json)

		if self.label_polygons:
			polygon_labels = self.polygon_labels = []
			if zoom >= 13:
				for id, polygon, properties, style in self.polygons:
					if not id in self.dedup:
						label_text = self.choose_polygon_label_text(properties)
						if label_text is not None:
							polygon_obj = Polygon(polygon)
							area = polygon_obj.area()
							center = polygon_obj.choose_label_center()
							#label_text = "%s(%s)" % (label_text, id)		# for debugging
							polygon_labels.append((id, area, center, label_text))
						self.dedup.add(id)

		if self.timing_load:
			self._elapsed()

	def choose_polygon_label_text(self, properties):
		return properties.get('name')

	# This code is broken out of __init__() strictly for the sake of readability.
	def _load_features(self, geojson):
		points = self.points = []
		lines = self.lines = []
		polygons = self.polygons = []

		assert geojson['type'] == 'FeatureCollection'
		features = geojson['features']
		if self.sort_key is not None:
			features = sorted(features, key=lambda feature: feature['properties'][self.sort_key])

		for feature in features:
			assert feature['type'] == 'Feature'
			id = feature.get('id', None)
			properties = feature['properties']
			geometry = feature['geometry']

			if geometry["type"] == 'GeometryCollection':
				geometries = geometry["geometries"]
			else:
				geometries = [geometry]

			for geometry in geometries:
				geometry_type = geometry['type']
	
				try:
					coordinates = geometry['coordinates']
				except KeyError:
					print("Warning: broken geometry:", feature)
					continue
	
				if geometry_type == 'Point':
					style = self.choose_point_style(properties)
					if style is not None:
						point = project_to_tilespace_pixel(coordinates[1], coordinates[0], self.zoom, self.x, self.y)
						points.append((id, point, properties, style))
					continue
	
				if geometry_type == 'LineString':
					style = self.choose_line_style(properties)
					if style is not None:
						line = project_to_tilespace_pixels(coordinates, self.zoom, self.x, self.y)
						lines.append((id, line, properties, style))
					continue
	
				if geometry_type == 'MultiLineString':
					style = self.choose_line_style(properties)
					if style is not None:
						for coordinates2 in coordinates:
							line = project_to_tilespace_pixels(coordinates2, self.zoom, self.x, self.y)
							lines.append((id, line, properties, style))
					continue
	
				if geometry_type == 'Polygon':
					style = self.choose_polygon_style(properties)
					if style is not None:
						for coordinates2 in coordinates:
							polygon = project_to_tilespace_pixels(coordinates2, self.zoom, self.x, self.y)
							polygons.append((id, polygon, properties, style))
					continue
	
				if geometry_type == 'MultiPolygon':
					style = self.choose_polygon_style(properties)
					if style is not None:
						for coordinates2 in coordinates:
							for coordinates3 in coordinates2:
								polygon = project_to_tilespace_pixels(coordinates3, self.zoom, self.x, self.y)
								polygons.append((id, polygon, properties, style))
					continue
	
				print("Warning: unimplemented geometry type:", feature)

	# Performance timer
	def _elapsed_start(self, message):
		print(" %s" % message, end="")
		self.start_time = time.time()

	def _elapsed(self):
		stop_time = time.time()
		elapsed_time = (stop_time - self.start_time) * 1000
		print(" (%.3f ms)" % elapsed_time)

	# Override these to return something other than None for those objects
	# which you wish to render. It will be stored with the object so that
	# you can use it during the drawing stage.
	def choose_point_style(self, properties):
		print("Warning: renderer %s did not expect points in tile %d %d %d" % (type(self).__name__, self.zoom, self.x, self.y))
		return None

	def choose_line_style(self, properties):
		print("Warning: renderer %s did not expect lines in tile %d %d %d" % (type(self).__name__, self.zoom, self.x, self.y))
		return None

	def choose_polygon_style(self, properties):
		print("Warning: renderer %s did not expect polygons in tile %d %d %d" % (type(self).__name__, self.zoom, self.x, self.y))
		return None

	# The layer calls this when it is time to draw the tile. If self.draw_passes
	# is more than one, then it will be called once for each pass. All tiles are
	# drawn at each pass before any tile is draw at the next pass.
	def draw(self, ctx, scale, draw_pass):
		if self.timing_draw:
			self._elapsed_start("Drawing %s %s %d %d %d, pass %d..." % (self.tileset.key, type(self).__name__, self.zoom, self.x, self.y, draw_pass))
		getattr(self,"draw%d" % (draw_pass+1))(ctx, scale)
		if self.timing_draw:
			self._elapsed()

	# Very simply implementation of drawing. Override in derived classes
	# if you want something fancier.
	def draw1(self, ctx, scale):
		self.start_clipping(ctx, scale)
		for id, polygon, properties, style in self.polygons:
			pykarta.draw.polygon(ctx, self.scale_points(polygon, scale))
			pykarta.draw.fill_with_style(ctx, style, preserve=True)
			pykarta.draw.stroke_with_style(ctx, style, preserve=True)
			ctx.new_path()
		for id, line, properties, style in self.lines:
			pykarta.draw.line_string(ctx, self.scale_points(line, scale))
			pykarta.draw.stroke_with_style(ctx, style)
		for id, point, properties, style in self.points:
			pykarta.draw.node_dots(ctx, [point], style=style)

	# draw1(), draw2(), etc. should call this if they want their drawing
	# commands to be clipped to the tile borders.
	def start_clipping(self, ctx, scale):
		if self.clip is not None:
			pad = self.clip
			ctx.new_path()
			start = 0 - pad						# slightly up and to the left
			size = 256.0 * scale + pad * 2		# width and height of clipping rectangle
			ctx.rectangle(start, start, size, size)
			ctx.clip()

	@staticmethod
	def scale_point(point, scale):
		return (point[0] * scale, point[1] * scale)

	@staticmethod
	def scale_points(points, scale):
		return map(lambda point: (point[0]*scale,point[1]*scale), points)

	# Use the supplied rule to determine the width of a feature
	# at the current zoom level.
	def zoom_feature(self, rule, scale=None):
		zoom = self.zoom
		if scale is not None:
			zoom += math.log(scale, 2.0)
		start_zoom, start_width, end_zoom, end_width = rule
		position = float(zoom - start_zoom) / float(end_zoom - start_zoom)
		width = start_width + position * (end_width - start_width)
		if width < 0.1:
			print("Warning: rules %s yields width of %f at zoom %f" % (str(rule), width, zoom))
		return width


