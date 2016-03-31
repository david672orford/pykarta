# encoding=utf-8
# pykarta/maps/layers/tile_geojson.py
# Base class for GeoJSON vector tile renderers
# Copyright 2013, 2014, 2015, Trinity College
# Last modified: 13 October 2015

try:
	import simplejson as json
except ImportError:
	import json
import gzip
import os
import math
import time

from pykarta.geometry.projection import project_to_tilespace_pixel
from pykarta.geometry import Points, Polygon
import pykarta.draw

class RenderGeoJSON(object):
	clip = None
	sort_key = None
	draw_passes = 1
	label_polygons = False
	def __init__(self, layer, filename, zoom, x, y):
		self.timing = False
		self.tileset = layer.tileset					# Note that we do not keep a reference to layer
		self.containing_map = layer.containing_map		# itself since that would be circular.
		self.dedup = layer.dedup
		self.zoom = zoom
		self.x = x
		self.y = y
		self.labels = None

		self.elapsed_start("Parsing %s %d %d %d..." % (layer.tileset.key, zoom, x, y))

		try:
			f = gzip.GzipFile(filename, "rb")
			parsed_json = json.load(f)
		except IOError:
			f = open(filename, "r")
			parsed_json = json.load(f)

		self.load_features(parsed_json)

		if self.label_polygons:
			polygon_labels = self.polygon_labels = []
			if zoom >= 13:
				for id, polygon, properties, style in self.polygons:
					name = properties.get("name")
					if name is not None:
						polygon_obj = Polygon(Points(polygon))
						area = polygon_obj.area()
						center = polygon_obj.choose_label_center()
						polygon_labels.append((id, area, center, name))

		self.elapsed()

	def load_features(self, geojson):
		assert geojson['type'] == 'FeatureCollection'

		points = self.points = []
		lines = self.lines = []
		polygons = self.polygons = []

		features = geojson['features']
		if self.sort_key is not None:
			features = sorted(features, key=lambda feature: feature['properties'][self.sort_key])

		for feature in features:
			assert feature['type'] == 'Feature'
			id = feature.get('id', None)
			properties = feature['properties']
			geometry = feature['geometry']
			try:
				coordinates = geometry['coordinates']
			except KeyError:
				print "Warning: broken geometry:", geometry

			if geometry['type'] == 'Point':
				style = self.choose_point_style(properties)
				if style is not None:
					point = project_to_tilespace_pixel(coordinates[1], coordinates[0], self.zoom, self.x, self.y)
					points.append((id, point, properties, style))

			elif geometry['type'] == 'LineString':
				style = self.choose_line_style(properties)
				if style is not None:
					line = map(lambda p: project_to_tilespace_pixel(p[1], p[0], self.zoom, self.x, self.y), coordinates)
					lines.append((id, line, properties, style))

			elif geometry['type'] == 'MultiLineString':
				style = self.choose_line_style(properties)
				if style is not None:
					for coordinates2 in coordinates:
						line = map(lambda p: project_to_tilespace_pixel(p[1], p[0], self.zoom, self.x, self.y), coordinates2)
						lines.append((id, line, properties, style))

			elif geometry['type'] == 'Polygon':
				style = self.choose_polygon_style(properties)
				if style is not None:
					for coordinates2 in coordinates:
						polygon = map(lambda p: project_to_tilespace_pixel(p[1], p[0], self.zoom, self.x, self.y), coordinates2)
						polygons.append((id, polygon, properties, style))

			elif geometry['type'] == 'MultiPolygon':
				style = self.choose_polygon_style(properties)
				if style is not None:
					for coordinates2 in coordinates:
						for coordinates3 in coordinates2:
							polygon = map(lambda p: project_to_tilespace_pixel(p[1], p[0], self.zoom, self.x, self.y), coordinates3)
							polygons.append((id, polygon, properties, style))

			else:
				print "Warning: unimplemented geometry:", geometry['type'], properties

	def elapsed_start(self, message):
		if self.timing:
			print message
			self.start_time = time.time()

	def elapsed(self):
		if self.timing:
			stop_time = time.time()
			elapsed_time = int((stop_time - self.start_time) * 1000 + 0.5)
			print " %d ms" % elapsed_time

	@staticmethod
	def scale_point(point, scale):
		return (point[0] * scale, point[1] * scale)

	@staticmethod
	def scale_points(points, scale):
		return map(lambda point: (point[0]*scale,point[1]*scale), points)

	def zoom_feature(self, rule, scale=None):
		zoom = self.zoom
		if scale is not None:
			zoom += math.log(scale, 2.0)
		start_zoom, start_width, end_zoom, end_width = rule
		position = float(zoom - start_zoom) / float(end_zoom - start_zoom)
		width = start_width + position * (end_width - start_width)
		return width

	# Override these to return something other than None for those objects
	# which you wish to render. It will be stored with the object so that
	# you can use it during the drawing stage.
	def choose_point_style(self, properties):
		print "Warning: renderer %s did not expect points in tile %d %d %d" % (str(type(self)), self.zoom, self.x, self.y)
		return None

	def choose_line_style(self, properties):
		print "Warning: renderer %s did not expect lines in tile %d %d %d" % (str(type(self)), self.zoom, self.x, self.y)
		return None

	def choose_polygon_style(self, properties):
		print "Warning: renderer %s did not expect polygons in tile %d %d %d" % (str(type(self)), self.zoom, self.x, self.y)
		return None

	# Draw and redraw
	def draw(self, ctx, scale, draw_pass):
		self.elapsed_start("Drawing %s %d %d %d, pass %d..." % (self.tileset.key, self.zoom, self.x, self.y, draw_pass))
		start_time = time.time()
		getattr(self,"draw%d" % (draw_pass+1))(ctx, scale)
		self.elapsed()

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

	# Override to draw the bottom layer.
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

