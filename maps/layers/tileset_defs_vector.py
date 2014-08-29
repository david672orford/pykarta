# encoding=utf-8
# pykarta/maps/tileset_defs_vector.py
# Copyright 2013, 2014, Trinity College
# Last modified: 27 August 2014

#=============================================================================
# Vector tile sets
# This is imported by builder.py.
# Renders OSM map from the vector tiles provided at:
# http://openstreetmap.us/~migurski/vector-datasource/
# and
# https://github.com/mapzen/vector-datasource/wiki/Mapzen-Vector-Tile-Service
#=============================================================================

try:
	import simplejson as json
except ImportError:
	import json
import gzip
import time
import os
import glob
import cairo
from tileset_defs import tilesets
from tileset_objs import MapTileset
from pykarta.maps.projection import project_to_tilespace_pixel
import pykarta.draw
from pykarta.geometry import Points, Polygon
from pykarta.maps.symbols import MapSymbolSet

def scale_point(point, scale):
	return (point[0] * scale, point[1] * scale)

def scale_points(points, scale):
	return map(lambda point: (point[0]*scale,point[1]*scale), points)

class OsmRenderGeoJSON(object):
	draws = set()
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

		for feature in geojson['features']:
			assert feature['type'] == 'Feature'
			properties = feature['properties']
			geometry = feature['geometry']
			coordinates = geometry['coordinates']

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
					# FIXME: inner polygons not implemented
					polygon = map(lambda p: project_to_tilespace_pixel(p[1], p[0], zoom, x, y), coordinates[0])
					polygons.append((polygon, properties, style))

			elif geometry['type'] == 'MultiPolygon':
				style = self.choose_polygon_style(properties)
				if style is not None:
					for coordinates2 in coordinates:
						# FIXME: inner polygons not implemented
						polygon = map(lambda p: project_to_tilespace_pixel(p[1], p[0], zoom, x, y), coordinates2[0])
						polygons.append((polygon, properties, style))

			else:
				print "Unimplemented geometry:", geometry['type'], properties

		myclass = type(self).__name__
		assert "points" in self.draws or len(self.points) == 0, "%s does not expect points" % myclass
		assert "lines" in self.draws or len(self.lines) == 0, "%s does not expect lines" % myclass
		assert "polygons" in self.draws or len(self.polygons) == 0, "%s does not expect polygons" % myclass

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

	# Pass 1, draw features with clipping.
	def draw(self, ctx, scale, opacity):
		self.elapsed_start("Drawing features %s %d %d %d..." % (self.layer.tileset.key, self.zoom, self.x, self.y))
		start_time = time.time()
		# FIXME: Why does clipping cause weird gaps at tile boundaries?
		#ctx.rectangle(-10, -10, 266*scale, 266*scale)			# allow a little overlap
		#ctx.clip()
		self.draw_features(ctx, scale)
		self.elapsed()

	# Pass 2, draw labels without clipping.
	def draw2(self, ctx, scale):
		self.draw_labels(ctx, scale)

	def choose_point_style(self, properties):
		return None

	def choose_line_style(self, properties):
		return None

	def choose_polygon_style(self, properties):
		return None

	def draw_features(self, ctx, scale):
		pass

	def draw_labels(self, ctx, scale):
		pass

#===========================================================================
# Openstreetmap.us
#===========================================================================
class OsmRenderGeoJSONLanduse(OsmRenderGeoJSON):
	draws = set(["polygons"])
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
		OsmRenderGeoJSON.__init__(self, layer, filename, zoom, x, y)
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
					self.labels.append(((center[0], center[1]), label_text))
					dedup.add(label_text)
	def draw_features(self, ctx, scale):
		for polygon, properties, style in self.polygons:
			pykarta.draw.polygon(ctx, scale_points(polygon, scale))
			ctx.set_source_rgba(*style.get('fill-color', (0.0, 0.0, 0.0)))
			ctx.fill()
	def draw_labels(self, ctx, scale):
		for center, label in self.labels:
			center = scale_point(center, scale)
			pykarta.draw.centered_label(ctx, center[0], center[1], label, fontsize=8, shield=False)
	def choose_polygon_style(self, properties):
		kind = properties.get("kind", "?")
		style = self.styles.get(kind)
		if style is None:
			style = { 'fill-color': (0.90, 0.90, 0.90) }
		return style

class OsmRenderGeoJSONWater(OsmRenderGeoJSON):
	draws = set(["polygons"])
	def draw_features(self, ctx, scale):
		for polygon, properties, style in self.polygons:
			pykarta.draw.polygon(ctx, scale_points(polygon, scale))
			ctx.set_source_rgb(*style.get('fill-color'))
			ctx.fill()
	def choose_polygon_style(self, properties):
		return { 'fill-color': (0.53, 0.80, 0.98) }

class OsmRenderGeoJSONBuildings(OsmRenderGeoJSON):
	draws = set(["polygons"])
	def draw_features(self, ctx, scale):
		for polygon, properties, style in self.polygons:
			pykarta.draw.polygon(ctx, scale_points(polygon, scale))
			ctx.set_source_rgb(*style.get('fill-color'))
			ctx.fill()
	def choose_polygon_style(self, properties):
		return  { 'fill-color': (0.8, 0.7, 0.7) }

class OsmRenderGeoJSONRoads(OsmRenderGeoJSON):
	draws = set(["lines"])
	styles = {
		'highway':{
			'overline-color':(0.0, 0.0, 0.5),		# dark blue
			'overline-width':2,
			},
		'major_road':{
			'overline-color':(0.7, 0.0, 0.0),		# dark red
			'overline-width':1,
			},
		'minor_road':{
			'line-color':(0.0, 0.0, 0.0),
			'line-width':0.5,
			},
		'rail':{
			'line-color':(0.5, 0.0, 0.0),
			'line-width':1,
			'line-dash':(12,4)
			},
		}
	styles_z14 = {
		'highway':{
			'overline-color':(0.0, 0.0, 0.5),		# dark blue
			'overline-width':5,
			},
		'major_road':{
			'overline-color':(0.7, 0.0, 0.0),		# dark red
			'overline-width':3,
			},
		'minor_road':{
			'underline-color':(0.0, 0.0, 0.0),
			'underline-width':3.0,
			'line-color':(1.0, 1.0, 1.0),
			'line-width':2.0,
			},
		'path':{
			'line-color':(0.5, 0.3, 0.3),
			'line-width':1.0,
			},
		'rail':{
			'line-color':(0.5, 0.0, 0.0),
			'line-width':3,
			'line-dash':(12,4)
			},
		}
	styles_z16 = {
		'highway':{
			'overline-color':(0.0, 0.0, 0.5),		# dark blue
			'overline-width':8,
			},
		'major_road':{
			'overline-color':(0.7, 0.0, 0.0),		# dark red
			'overline-width':6,
			},
		'minor_road':{
			'underline-color':(0.0, 0.0, 0.0),
			'underline-width':4.0,
			'line-color':(1.0, 1.0, 1.0),
			'line-width':3.0,
			},
		'path':{
			'line-color':(0.5, 0.3, 0.3),
			'line-width':2.0,
			},
		'rail':{
			'line-color':(0.5, 0.0, 0.0),
			'line-width':5,
			'line-dash':(12,4)
			},
		}
	def draw_features(self, ctx, scale):
		ctx.set_line_cap(cairo.LINE_CAP_ROUND)
		for line, name, style in self.lines:
			if 'underline-width' in style:
				pykarta.draw.line_string(ctx, scale_points(line, scale))
				ctx.set_line_width(style['underline-width'])
				ctx.set_source_rgba(*style['underline-color'])
				ctx.set_dash(style.get('underline-dash', ()))
				ctx.stroke()
		for line, name, style in self.lines:
			if 'line-width' in style:
				pykarta.draw.line_string(ctx, scale_points(line, scale))
				ctx.set_line_width(style.get('line-width'))
				ctx.set_source_rgba(*style.get('line-color'))
				ctx.set_dash(style.get('line-dash', ()))
				ctx.stroke()
		for line, name, style in self.lines:
			if 'overline-width' in style:
				pykarta.draw.line_string(ctx, scale_points(line, scale))
				ctx.set_line_width(style['overline-width'])
				ctx.set_source_rgba(*style['overline-color'])
				ctx.set_dash(style.get('overline-dash', ()))
				ctx.stroke()
	def choose_line_style(self, properties):
		kind = properties['kind']
		style = None
		if self.zoom >= 14:
			style = self.styles_z14.get(kind)
		elif self.zoom >= 16:
			style = self.styles_z16.get(kind)
		else:
			style = self.styles.get(kind)
		if style is None:
			#print properties
			return {'line-width':10, 'line-color':(0.0, 1.0, 0.0)}
		return style

class OsmRenderGeoJSONRoadLabels(OsmRenderGeoJSON):
	draws = set(["lines"])
	def draw_labels(self, ctx, scale):
		for line, properties, style in self.lines:
			label_text = properties['name']
			pykarta.draw.label_line(ctx, scale_points(line, scale), label_text)
	def choose_line_style(self, properties):
		if properties.get('name',"") != "":
			return {}
		return None

class OsmRenderGeoJSONPois(OsmRenderGeoJSON):
	draws = set(["points"])
	def __init__(self, layer, filename, zoom, x, y):
		if layer.tileset.symbols is None:
			layer.tileset.symbols = MapSymbolSet()
			path = os.path.join(os.path.dirname(__file__), "symbols")
			for symbol in glob.glob("%s/*.svg" % path):
				layer.tileset.symbols.add_symbol(symbol)
		OsmRenderGeoJSON.__init__(self, layer, filename, zoom, x, y)
	def draw_labels(self, ctx, scale):
		for point, properties, style in self.points:
			x, y = scale_point(point, scale)
			renderer = style
			renderer.blit(ctx, x, y)
			name = properties.get("name")
			kind = properties.get("kind")
			label_text = "%s:%s" % (kind, name)
			pykarta.draw.poi_label(ctx, x+2, y-2, label_text, fontsize=10)
	def choose_point_style(self, properties):
		kind = properties.get("kind")
		renderer = self.layer.tileset.symbols.get_symbol(kind, default="Dot").get_renderer(self.layer.containing_map)
		return renderer

class MapTilesetVector(MapTileset):
	def __init__(self, key, **kwargs):
		MapTileset.__init__(self, key, **kwargs)
		self.extra_headers["Accept-Encoding"] = "gzip,deflate"
		self.attribution=u"Map © OpenStreetMap contributors"
		self.layer_cache_enabled = True,
		self.symbols = None

tilesets.append(MapTilesetVector('osm-vector-landuse',
	url_template="http://tile.openstreetmap.us/vectiles-land-usages/{z}/{x}/{y}.json", 
	renderer = OsmRenderGeoJSONLanduse,
	))
tilesets.append(MapTilesetVector('osm-vector-water',
	url_template="http://tile.openstreetmap.us/vectiles-water-areas/{z}/{x}/{y}.json", 
	renderer = OsmRenderGeoJSONWater,
	))
tilesets.append(MapTilesetVector('osm-vector-buildings',
	url_template="http://tile.openstreetmap.us/vectiles-buildings/{z}/{x}/{y}.json", 
	renderer = OsmRenderGeoJSONBuildings,
	zoom_min=16,
	))
tilesets.append(MapTilesetVector('osm-vector-roads',
	url_template="http://tile.openstreetmap.us/vectiles-highroad/{z}/{x}/{y}.json", 
	renderer = OsmRenderGeoJSONRoads,
	))
tilesets.append(MapTilesetVector('osm-vector-road-labels',
	url_template="http://tile.openstreetmap.us/vectiles-skeletron/{z}/{x}/{y}.json", 
	renderer = OsmRenderGeoJSONRoadLabels,
	))
tilesets.append(MapTilesetVector('osm-vector-pois',
	url_template="http://tile.openstreetmap.us/vectiles-pois/{z}/{x}/{y}.json", 
	renderer = OsmRenderGeoJSONPois,
	zoom_min=14,
	))

# DSC
class RenderParcels(OsmRenderGeoJSON):
	draws = set(["polygons"])
	def draw_features(self, ctx, scale):
		for polygon, properties, style in self.polygons:
			pykarta.draw.polygon(ctx, scale_points(polygon, scale))
			ctx.set_source_rgb(0.0, 0.0, 0.0)
			ctx.set_line_width(0.25)
			ctx.stroke()
	def choose_polygon_style(self, properties):
		return "dummy_value";

tilesets.append(MapTilesetVector('massgis-l3parcels-vector',
	url_template="http://127.0.0.1:8080/parcels-westfield/{z}/{x}/{y}.geojson",
	renderer = RenderParcels,
	zoom_min=12,
	))


