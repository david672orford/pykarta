# encoding=utf-8
# pykarta/maps/layers/tile_rndr_geojson.py
# Base class for GeoJSON vector tile renderers
# Copyright 2013--2018, Trinity College
# Last modified: 24 May 2018

from __future__ import print_function
try:
	import simplejson as json
except ImportError:
	import json
import gzip
import os
import math
import time
import re

from pykarta.geometry.projection import project_to_tilespace_pixel
from pykarta.geometry import Polygon
from pykarta.draw import place_line_label, place_line_shield, polygon as draw_polygon, line_string as draw_line_string, line_string as draw_line_string, stroke_with_style, fill_with_style

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
	draw_passes = 1					# draw1(), override for draw2(), etc.
	clip = None						# None for no clipping, or number of pixels beyond tile border
	sort_key = None

	label_lines = False
	label_polygons = False

	timing_load = True				# Option: Time the loading routines and print the results
	timing_draw = False				# Option: Time the drawing routines and print the results

	def __init__(self, layer, filename, zoom, x, y, data=None):
		self.zoom = zoom								# zoom, x, y of tile to load
		self.x = x
		self.y = y

		self.tileset = layer.tileset
		self.dedup = layer.dedup
		self.containing_map = layer.containing_map

		self.points = []
		self.lines = []
		self.polygons = []

		self.line_labels = []
		self.line_shields = []
		self.polygon_labels = []

		# Load the data, uncompress it, and parse the JSON into Python objects
		if self.timing_load:
			self._elapsed_start("Parsing %s %s %d %d %d..." % (layer.tileset.key, type(self).__name__, zoom, x, y))
		if data is not None:
			parsed_json = data
		else:
			parsed_json = json_loader(filename)

		if self.timing_load:
			self._elapsed()

		# Interpret the JSON (now in the form of Python dicts and lists) as GeoJSON
		self.load_geojson(parsed_json)

		if self.label_lines:

			# Place text labels along lines
			labels = self.line_labels
			for id, line, properties, style in self.lines:
				label_text = self.choose_line_label_text(properties)
				fontsize = self.zoom_feature(style)
				placement = place_line_label(line, label_text, fontsize=fontsize, tilesize=256)
				if placement is not None:
					labels.append(placement)

			# Place the highway shields
			tile_level_dedup = set()
			shields = self.line_shields
			for id, line, properties, style in self.lines:
				for ref in self.get_highway_refs(properties):
					if not ref in tile_level_dedup:
						# FIXME: should place all of them
						shield_pos = place_line_shield(line)
						if shield_pos is not None:
							shields.append((shield_pos, ref))
						tile_level_dedup.add(ref)

		if self.label_polygons:
			polygon_labels = self.polygon_labels
			if zoom >= 13:
				for id, polygon, properties, style in self.polygons:
					label_text = self.choose_polygon_label_text(properties)
					if label_text is not None:
						# See ../tests/polyton_labeling_test.py for an example where this fails.
						#polygon_obj = Polygon(polygon)
						#area = polygon_obj.area()
						#label_center = polygon_obj.choose_label_center()

						# For now we will compute a bounding box and put the label at the center.
						min_x = 255
						max_x = 0
						min_y = 255
						max_y = 0
						for x, y in polygon:
							min_x = min(min_x, x)
							max_x = max(max_x, x)
							min_y = min(min_y, y)
							max_y = max(max_y, y)
						area = ((max_x - min_x) * (max_y - min_y))
						label_center = ((max_x + min_x) / 2, (max_y + min_y) / 2)

						polygon_labels.append((id, area, label_center, label_text))

	def get_highway_refs(self, properties):
		for ref in re.split(r'\s*;\s*', properties.get('ref','')):
			if ref != "":
				yield ref

	def choose_line_label_text(self, properties):
		return properties.get('name')

	def choose_polygon_label_text(self, properties):
		return properties.get('name')

	def load_geojson(self, geojson):
		points = self.points
		lines = self.lines
		polygons = self.polygons

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
			draw_polygon(ctx, self.scale_points(polygon, scale))
			fill_with_style(ctx, style, preserve=True)
			stroke_with_style(ctx, style, preserve=True)
			ctx.new_path()
		for id, line, properties, style in self.lines:
			draw_line_string(ctx, self.scale_points(line, scale))
			stroke_with_style(ctx, style)
		for id, point, properties, style in self.points:
			draw_node_dots(ctx, [point], style=style)

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


