# encoding=utf-8
# pykarta/maps/layers/tilesets_vector.py
# Vector tile sets and renders for them
# Copyright 2013, 2014, Trinity College
# Last modified: 14 September 2014

try:
	import simplejson as json
except ImportError:
	import json
import gzip
import time
import os
import glob
import cairo

from tilesets_base import tilesets, MapTilesetVector
from pykarta.maps.projection import project_to_tilespace_pixel
from pykarta.geometry import Points, Polygon
import pykarta.draw
from pykarta.maps.symbols import MapSymbolSet

#=============================================================================
# Base class for GeoJSON vector tile renderers
#=============================================================================
class RenderGeoJSON(object):
	clip = None
	sort_features = False
	def __init__(self, layer, filename, zoom, x, y):
		self.timing = False
		self.elapsed_start("Parsing %s %d %d %d..." % (layer.tileset.key, zoom, x, y))
		self.layer = layer
		self.zoom = zoom
		self.x = x
		self.y = y

		try:
			f = gzip.GzipFile(filename, "rb")
			geojson = json.load(f)
		except IOError:
			f = open(filename, "r")
			geojson = json.load(f)

		assert geojson['type'] == 'FeatureCollection'

		points = self.points = []
		lines = self.lines = []
		polygons = self.polygons = []

		features = geojson['features']
		if self.sort_features:
			features = sorted(features, key=lambda feature: int(feature['properties']['sort_key']))

		for feature in features:
			assert feature['type'] == 'Feature'
			properties = feature['properties']
			geometry = feature['geometry']
			try:
				coordinates = geometry['coordinates']
			except KeyError:
				print "Broken geometry:", geometry

			if geometry['type'] == 'Point':
				style = self.choose_point_style(properties)
				if style is not None:
					point = project_to_tilespace_pixel(coordinates[1], coordinates[0], zoom, x, y)
					points.append((point, properties, style))

			elif geometry['type'] == 'LineString':
				style = self.choose_line_style(properties)
				if style is not None:
					line = map(lambda p: project_to_tilespace_pixel(p[1], p[0], zoom, x, y), coordinates)
					lines.append((line, properties, style))

			elif geometry['type'] == 'MultiLineString':
				style = self.choose_line_style(properties)
				if style is not None:
					for coordinates2 in coordinates:
						line = map(lambda p: project_to_tilespace_pixel(p[1], p[0], zoom, x, y), coordinates2)
						lines.append((line, properties, style))

			elif geometry['type'] == 'Polygon':
				style = self.choose_polygon_style(properties)
				if style is not None:
					for coordinates2 in coordinates:
						polygon = map(lambda p: project_to_tilespace_pixel(p[1], p[0], zoom, x, y), coordinates2)
						polygons.append((polygon, properties, style))

			elif geometry['type'] == 'MultiPolygon':
				style = self.choose_polygon_style(properties)
				if style is not None:
					for coordinates2 in coordinates:
						for coordinates3 in coordinates2:
							polygon = map(lambda p: project_to_tilespace_pixel(p[1], p[0], zoom, x, y), coordinates3)
							polygons.append((polygon, properties, style))

			else:
				print "Unimplemented geometry:", geometry['type'], properties

		self.elapsed()

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

	# Pass 1, draw features with clipping.
	def draw(self, ctx, scale):
		self.elapsed_start("Drawing features %s %d %d %d..." % (self.layer.tileset.key, self.zoom, self.x, self.y))
		start_time = time.time()
		if self.clip is not None:
			pad = self.clip
			ctx.new_path()
			start = 0 - pad						# slightly up and to the left
			size = 256.0 * scale + pad * 2		# width and hight of clipping rectangle
			ctx.rectangle(start, start, size, size)
			ctx.clip()
		self.draw_features(ctx, scale)
		self.elapsed()

	# Pass 2, draw labels without clipping.
	def draw2(self, ctx, scale):
		self.draw_labels(ctx, scale)

	# Override these to return something other than None for those objects
	# which you wish to render. It will be stored with the object so that
	# you can use it during the drawing stage.
	def choose_point_style(self, properties):
		raise AssertionError, "renderer %s does not expect points" % str(type(self))

	def choose_line_style(self, properties):
		raise AssertionError, "renderer %s does not expect lines" % str(type(self))

	def choose_polygon_style(self, properties):
		raise AssertionError, "renderer %s does not expect polygons" % str(type(self))

	# Override to draw the bottom layer.
	def draw_features(self, ctx, scale):
		#ctx.set_line_cap(cairo.LINE_CAP_ROUND)
		for polygon, properties, style in self.polygons:
			pykarta.draw.polygon(ctx, self.scale_points(polygon, scale))
			pykarta.draw.fill_with_style(ctx, style, preserve=True)
			pykarta.draw.stroke_with_style(ctx, style, preserve=True)
			ctx.new_path()
		for line, properties, style in self.lines:
			pykarta.draw.line_string(ctx, self.scale_points(line, scale))
			pykarta.draw.stroke_with_style(ctx, style)
		for point, properties, style in self.points:
			pykarta.draw.node_dots(ctx, [point], style=style)

	# Override to draw the top (label) layer.
	def draw_labels(self, ctx, scale):
		pass

#=============================================================================
# Openstreetmap.us
# Renders OSM map from the vector tiles provided at:
# http://openstreetmap.us/~migurski/vector-datasource/
# Though it is not advertised, this provider can also make topojson.
#=============================================================================
class RenderOsmusLanduse(RenderGeoJSON):
	styles = {
		'school': { 'fill-color': (1.0, 0.7, 0.7) },			# redish
		'playground': { 'fill-color': (1.0, 1.0, 0.7) },
		'park': { 'fill-color': (0.7, 1.0, 0.7) },				# light green
		'recreation_ground': { 'fill-color': (0.7, 1.0, 0.7) },	# light green
		'golf_course': { 'fill-color': (0.7, 1.0, 0.7) },		# light green
		'pitch': { 'fill-color': (0.6, 0.9, 0.6) },				# brown
		'forest': { 'fill-color': (0.8, 1.0, 0.8) },			# dark green
		'wood': { 'fill-color': (0.8, 1.0, 0.8) },				# dark green
		'conservation': { 'fill-color': (0.8, 1.0, 0.8) },		# dark green
		'farm': { 'fill-color': (0.9, 0.9, 0.6) },				# redish brown
		}
	def __init__(self, layer, filename, zoom, x, y):
		RenderGeoJSON.__init__(self, layer, filename, zoom, x, y)
		self.labels = []
		if zoom >= 14:
			dedup = set()
			for polygon, properties, style in self.polygons:
				center = Polygon(Points(polygon)).choose_label_center()
				kind = properties.get("kind", "?")
				name = properties.get("name", "?")
				if name is not None:
					label_text = "%s:%s" % (kind, name)
				else:
					label_text = kind
				if not label_text in dedup:
					self.labels.append((center, label_text))
					dedup.add(label_text)
	def draw_labels(self, ctx, scale):
		#for center, text in self.labels:
		#	center = self.scale_point(center, scale)
		#	pykarta.draw.centered_label(ctx, center[0], center[1], text, fontsize=8, shield=False)
		pass
	def choose_polygon_style(self, properties):
		kind = properties.get("kind", "?")
		style = self.styles.get(kind)
		if style is None:
			style = { 'fill-color': (0.90, 0.90, 0.90) }
		return style

tilesets.append(MapTilesetVector('osm-vector-landuse',
	url_template="http://tile.openstreetmap.us/vectiles-land-usages/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusLanduse,
	))

class RenderOsmusWater(RenderGeoJSON):
	def choose_polygon_style(self, properties):
		return { 'fill-color': (0.53, 0.80, 0.98) }

tilesets.append(MapTilesetVector('osm-vector-water',
	url_template="http://tile.openstreetmap.us/vectiles-water-areas/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusWater,
	))

class RenderOsmusBuildings(RenderGeoJSON):
	def choose_polygon_style(self, properties):
		return  { 'fill-color': (0.8, 0.7, 0.7) }

tilesets.append(MapTilesetVector('osm-vector-buildings',
	url_template="http://tile.openstreetmap.us/vectiles-buildings/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusBuildings,
	zoom_min=16,
	))

class RenderOsmusRoads(RenderGeoJSON):
	clip = 15
	sort_features = True
	styles = {
		'highway':{
			'line-color':(0.0, 0.0, 0.5),		# dark blue
			'line-width':(10,2.0, 14,10.0)
			},
		'major_road':{
			'line-color':(0.7, 0.2, 0.2),		# dark red
			'line-width':(10,1.0, 14,6.0),
			},
		'minor_road':{
			'line-color':(0.0, 0.0, 0.0),		# black
			'line-width':(12,0.25, 14,1.0),
			},
		}
	styles_z14 = {
		'minor_road':{
			'underline-color':(0.0, 0.0, 0.0),	# black casing
			'line-color':(1.0, 1.0, 1.0),		# white
			'line-width':(14,3.0, 18,10.0),
			'underline-width':(14,4.0, 18,12.0),
			},
		'rail':{
			'line-color':      (0.0, 0.0, 0.0),
			'underline-color': (0.0, 0.0, 0.0),
			'line-width':      (14,1.0, 18,3.0),
			'underline-width': (14,3.0, 18,8.0),
			'underline-dash':  (1, 12)
			},
		'path':{
			'line-color': (0.5, 0.3, 0.3),
			'line-width': (14,1.5, 18,5.0),
			},
		}
	def choose_line_style(self, properties):
		kind = properties['kind']
		style = None
		if self.zoom >= 14:
			style = self.styles_z14.get(kind,None)
		if style is None:
			style = self.styles.get(kind)
		if style is None:
			style = {'line-width':10, 'line-color':(0.0, 1.0, 0.0)}
		style = style.copy()
		for i in ("underline-width", "line-width", "overline-width"):
			if i in style:
				start_zoom, start_width, end_zoom, end_width = style[i]
				position = float(self.zoom - start_zoom) / float(end_zoom - start_zoom)
				width = start_width + position * (end_width - start_width)
				#if start_zoom == 14 and i == "line-width":
				#	print "style:", style[i]
				#	print "zoom:", self.zoom
				#	print "position:", position
				#	print "width:", width
				#	print
				if properties['is_link'] == 'yes' or properties['highway'] == 'service':
					width /= 2
				style[i] = width
		return style
	def draw_features(self, ctx, scale):
		ctx.set_line_cap(cairo.LINE_CAP_BUTT)
		for line, name, style in self.lines:
			if 'underline-width' in style:
				pykarta.draw.line_string(ctx, self.scale_points(line, scale))
				ctx.set_line_width(style['underline-width'])
				ctx.set_source_rgba(*style['underline-color'])
				ctx.set_dash(style.get('underline-dash', ()))
				ctx.stroke()
		ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
		for line, name, style in self.lines:
			if 'line-width' in style:
				pykarta.draw.line_string(ctx, self.scale_points(line, scale))
				ctx.set_line_width(style.get('line-width'))
				ctx.set_source_rgba(*style.get('line-color'))
				ctx.set_dash(style.get('line-dash', ()))
				ctx.stroke()
		ctx.set_line_cap(cairo.LINE_CAP_BUTT)
		for line, name, style in self.lines:
			if 'overline-width' in style:
				pykarta.draw.line_string(ctx, self.scale_points(line, scale))
				ctx.set_line_width(style['overline-width'])
				ctx.set_source_rgba(*style['overline-color'])
				ctx.set_dash(style.get('overline-dash', ()))
				ctx.stroke()

tilesets.append(MapTilesetVector('osm-vector-roads',
	url_template="http://tile.openstreetmap.us/vectiles-highroad/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusRoads,
	))

class RenderOsmusRoadLabels(RenderGeoJSON):
	def draw_features(self, ctx, scale):
		pass
	def draw_labels(self, ctx, scale):
		for line, properties, style in self.lines:
			label_text = properties['name']
			pykarta.draw.label_line(ctx, self.scale_points(line, scale), label_text, fontsize=10, tilesize=(256.0*scale))
	def choose_line_style(self, properties):
		if properties.get('name',"") != "":
			return {}
		return None

tilesets.append(MapTilesetVector('osm-vector-road-labels',
	url_template="http://tile.openstreetmap.us/vectiles-skeletron/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusRoadLabels,
	zoom_max=16,
	))

class RenderOsmusPois(RenderGeoJSON):
	def __init__(self, layer, filename, zoom, x, y):
		if layer.tileset.symbols is None:
			layer.tileset.symbols = MapSymbolSet()
			path = os.path.join(os.path.dirname(__file__), "symbols")
			for symbol in glob.glob("%s/*.svg" % path):
				layer.tileset.symbols.add_symbol(symbol)
		RenderGeoJSON.__init__(self, layer, filename, zoom, x, y)
	def draw_features(self, ctx, scale):
		pass
	def draw_labels(self, ctx, scale):
		for point, properties, style in self.points:
			x, y = self.scale_point(point, scale)
			renderer, label_text = style
			if renderer is not None:
				renderer.blit(ctx, x, y)
			else:
				pykarta.draw.poi_label(ctx, x+2, y-2, label_text, fontsize=10)
	def choose_point_style(self, properties):
		kind = properties.get("kind")
		name = properties.get("name")
		symbol = self.layer.tileset.symbols.get_symbol(kind)
		if symbol is not None:
			renderer = symbol.get_renderer(self.layer.containing_map)
			return (renderer, None)
		else:
			return (None, "%s:%s" % (kind, name))

tilesets.append(MapTilesetVector('osm-vector-pois',
	url_template="http://tile.openstreetmap.us/vectiles-pois/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusPois,
	zoom_min=14,
	))

#=============================================================================
# Mapzen
# https://github.com/mapzen/vector-datasource/wiki/Mapzen-Vector-Tile-Service
# https://github.com/mapzen/vector-datasource
#=============================================================================

class RenderMapzenPlaces(RenderOsmusPois):
	pass

tilesets.append(MapTilesetVector("osm-vector-places",
	url_template="http://vector.mapzen.com/osm/places/{z}/{x}/{y}.json",
	renderer=RenderMapzenPlaces,
	))

#=============================================================================
# DSC
#=============================================================================
class RenderTowns(RenderGeoJSON):
	clip = 2
	def choose_polygon_style(self, properties):
		return {
			"underline-width": 1,
			"underline-color": (1.0, 1.0, 1.0),
			"line-width": 1.0,
			"line-color": (0.5, 0.5, 0.5),
			"line-dash": (12, 4, 4, 4),
			}
	#def draw_labels(self, ctx, scale):
	#	for center, label in self.labels:
	#		center = self.scale_point(center, scale)
	#		pykarta.draw.centered_label(ctx, center[0], center[1], label, fontsize=8, shield=False)

tilesets.append(MapTilesetVector('dsc-towns',
	url_template="http://tiles.osm.trincoll.edu/towns/{z}/{x}/{y}.geojson",
	renderer=RenderTowns,
	zoom_max=16,
	))

class RenderParcels(RenderGeoJSON):
	clip = 2
	def __init__(self, layer, filename, zoom, x, y):
		RenderGeoJSON.__init__(self, layer, filename, zoom, x, y)
		self.labels = []
		if zoom >= 16:		# labels appear
			for polygon, properties, style in self.polygons:
				geojson = json.loads(properties['centroid'])
				coordinates = geojson['coordinates']
				center = project_to_tilespace_pixel(coordinates[1], coordinates[0], zoom, x, y)
				# If the label center is within this tile, use it.
				if center[0] >= 0 and center[0] < 256 and center[1] > 0 and center[1] < 256:
					self.labels.append((center, properties.get("house_number","?"), properties.get("street","?")))
	def choose_polygon_style(self, properties):
		return { "line-color": (0.0, 0.0, 0.0), "line-width": 0.25 }
	def draw_labels(self, ctx, scale):
		show_street = self.layer.zoom >= 17.9
		for center, house_number, street in self.labels:
			center = self.scale_point(center, scale)
			if show_street:
				text = "%s %s" % (house_number, street)
			else:
				text = house_number
			pykarta.draw.centered_label(ctx, center[0], center[1], text, fontsize=8, shield=False)

tilesets.append(MapTilesetVector('dsc-parcels',
	url_template="http://tiles.osm.trincoll.edu/parcels/{z}/{x}/{y}.geojson",
	renderer=RenderParcels,
	zoom_min=16,
	zoom_max=16,
	))
