# encoding=utf-8
# pykarta/maps/layers/tilesets_vector.py
# Vector tile sets and renders for them
# Copyright 2013, 2014, Trinity College
# Last modified: 8 October 2014

try:
	import simplejson as json
except ImportError:
	import json
import gzip
import time
import os
import glob
import cairo
import math

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

	# draw1(), draw2(), etc. should call this if they want their drawing commands
	# to be clipped to the tile borders.
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

#=============================================================================
# Base class for TopoJSON vector tile renderers
# https://github.com/mbostock/topojson/wiki
#=============================================================================

# FIXME: this unfinished
class RenderTopoJSON(RenderGeoJSON):
	def load_features(self, topojson):
		assert topojson['type'] == "Topology"
		translate = topojson['translate']
		scale = topojson['scale']
		arcs = topojson['arcs']
		vectile = topojson['objects']['vectile']
		assert vectile['type'] == "GeometryCollection"
		for feature in vectile['geometries']:		# geometries?
			print feature 

#=============================================================================
# Tile.Openstreetmap.us
# Renders OSM map from the vector tiles provided at:
#   http://openstreetmap.us/~migurski/vector-datasource/
# Configuration on Github:
#   https://github.com/migurski/OSM.us-vector-datasource
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
	label_style = {
		'font-size':10,
		'font-weight':'bold',
		'halo':False,
		'color':(0.5, 0.5, 0.5),
		}
	draw_passes = 2	# set to 2 to enable labels, 1 to disable
	label_polygons = True
	def choose_polygon_style(self, properties):
		kind = properties.get("kind", "?")
		style = self.styles.get(kind)
		if style is None:
			style = { 'fill-color': (0.90, 0.90, 0.90) }
		return style
	def draw2(self, ctx, scale):
		for id, area, center, text in self.polygon_labels:
			if not id in self.dedup:
				area = area * scale * scale
				if area > 10000:	# equivalent of 100 pixel square
					center = self.scale_point(center, scale)
					pykarta.draw.centered_label(ctx, center[0], center[1], text, style=self.label_style)
					self.dedup.add(id)

tilesets.append(MapTilesetVector('osm-vector-landuse',
	url_template="http://tile.openstreetmap.us/vectiles-land-usages/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusLanduse,
	))

#-----------------------------------------------------------------------------

class RenderOsmusWater(RenderGeoJSON):
	def choose_polygon_style(self, properties):
		return { 'fill-color': (0.53, 0.80, 0.98) }

tilesets.append(MapTilesetVector('osm-vector-water',
	url_template="http://tile.openstreetmap.us/vectiles-water-areas/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusWater,
	))

#-----------------------------------------------------------------------------

# These vector tiles do not include any building properties.
class RenderOsmusBuildings(RenderGeoJSON):
	def choose_polygon_style(self, properties):
		return  { 'fill-color': (0.8, 0.7, 0.7) }

tilesets.append(MapTilesetVector('osm-vector-buildings',
	url_template="http://tile.openstreetmap.us/vectiles-buildings/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusBuildings,
	zoom_min=12,
	))

#-----------------------------------------------------------------------------

class RenderOsmusRoads(RenderGeoJSON):
	clip = 15
	sort_key = 'sort_key'
	draw_passes = 2
	line_cap = {
		'butt':cairo.LINE_CAP_BUTT,				# default
		'square':cairo.LINE_CAP_SQUARE,
		'round':cairo.LINE_CAP_ROUND,
		}
	line_join = {
		'miter':cairo.LINE_JOIN_MITER,			# default
		'bevel':cairo.LINE_JOIN_BEVEL,
		'round':cairo.LINE_JOIN_ROUND,
		}
	# http://colorbrewer2.org/ is helpful for picking color palates
	styles = {
		'highway':{
			'line-color':(0.2, 0.3, 0.9),			# blue
			'line-width':(10,2.0, 14,10.0),
			'line-cap':'round',
			},
		'major_road':{
			'line-color':(0.8, 0.2, 0.2),			# dark red
			'line-width':(10,1.0, 14,6.0),
			'line-cap':'round',
			},
		'minor_road':{
			'line-color':(0.0, 0.0, 0.0),			# black
			'line-width':(12,0.25, 14,1.0),
			'line-cap':'round',
			},
		'rail':{
			'line-width': (12,0.5, 14,1.0),
			'line-color': (0.0, 0.0, 0.0),
			'line-dasharray': (1, 1),
			},
		}
	styles_z14 = {
		'highway':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,9.0, 18,18.0),
			'line-cap':'round',
			'overline-color':(0.2, 0.3, 0.9),		# blue
			'overline-width':(14,8.0, 18,16.0),
			'overline-cap':'round',
			},
		'major_road':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,7.0, 18,13.0),
			'line-cap':'round',
			'overline-color':(0.7, 0.0, 0.0),		# dark red
			'overline-width':(14,6.0, 18,11.0),
			'overline-cap':'round',
			},
		'major_road-secondary':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,7.0, 18,13.0),
			'line-cap':'round',
			'overline-color':(0.9, 0.3, 0.2),		# lighter red
			'overline-width':(14,6.0, 18,11.0),
			'overline-cap':'round',
			},
		'major_road-tertiary':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,7.0, 18,13.0),
			'line-cap':'round',
			'overline-color':(0.998, 0.55, 0.35),	# orange
			'overline-width':(14,6.0, 18,11.0),
			'overline-cap':'round',
			},
		'minor_road':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,4.0, 18,12.0),
			'line-cap':'round',
			'overline-color':(0.99, 0.94, 0.85),	# tan fill
			'overline-width':(14,3.0, 18,10.0),
			'overline-cap':'round',
			},
		'minor_road-residential':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,4.0, 18,12.0),
			'line-cap':'round',
			'overline-color':(1.0, 1.0, 1.0),		# white fill
			'overline-width':(14,3.0, 18,10.0),
			'overline-cap':'round',
			},
		'minor_road-service':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,2.0, 18,6.0),
			'line-cap':'round',
			'overline-color':(1.0, 1.0, 1.0),		# white fill
			'overline-width':(14,1.5, 18,5.0),
			'overline-cap':'round',
			},
		'rail':{
			'line-width': (14,3.0, 18,8.0),
			'line-color': (0.0, 0.0, 0.0),
			'line-dasharray': (1, 12),
			'overline-width': (14,1.0, 18,3.0),
			'overline-color': (0.0, 0.0, 0.0),
			},
		'path':{
			'line-color': (0.5, 0.3, 0.3),
			'line-width': (14,1.5, 18,5.0),
			},
		}
	def choose_line_style(self, properties):
		kind = properties['kind']
		highway = properties['highway']
		style = None
		if self.zoom >= 14:
			style = self.styles_z14.get("%s-%s" % (kind,highway),None)
			if style is None:
				style = self.styles_z14.get(kind,None)
		if style is None:
			style = self.styles.get(kind)
		if style is None:
			print "Warning: no style for:", properties
			style = {'line-width':(0,10, 16,10), 'line-color':(0.0, 1.0, 0.0)}		# error indicator
		style = style.copy()
		for i in ("line-width", "overline-width"):
			if i in style:
				# Scale widths to zoom level
				width = self.zoom_feature(style[i])
				# make subsidiary highways smaller
				if properties['is_link'] == 'yes':
					width /= 2
				# Accept modified style
				style[i] = width
		# Show bridges if the zoom level is high enough that the roads have casings.
		if properties['is_bridge'] == 'yes' and 'overline-width' in style:
			style['line-width'] *= 1.30
		return style
	def draw1(self, ctx, scale):
		self.start_clipping(ctx, scale)
		for id, line, name, style in self.lines:
			if 'line-width' in style:
				pykarta.draw.line_string(ctx, self.scale_points(line, scale))
				ctx.set_line_width(style['line-width'])
				ctx.set_source_rgba(*style['line-color'])
				ctx.set_dash(style.get('line-dasharray', ()))
				ctx.set_line_join(self.line_join[style.get('line-join', 'miter')])
				ctx.set_line_cap(self.line_cap[style.get('line-cap', 'butt')])
				ctx.stroke()
	def draw2(self, ctx, scale):
		self.start_clipping(ctx, scale)
		for id, line, name, style in self.lines:
			if 'overline-width' in style:
				pykarta.draw.line_string(ctx, self.scale_points(line, scale))
				ctx.set_line_width(style.get('overline-width'))
				ctx.set_source_rgba(*style.get('overline-color'))
				ctx.set_dash(style.get('overline-dasharray', ()))
				ctx.set_line_join(self.line_join[style.get('overline-join', 'miter')])
				ctx.set_line_cap(self.line_cap[style.get('overline-cap', 'butt')])
				ctx.stroke()

tilesets.append(MapTilesetVector('osm-vector-roads',
	url_template="http://tile.openstreetmap.us/vectiles-highroad/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusRoads,
	))

#-----------------------------------------------------------------------------

class RenderOsmusRoadLabels(RenderGeoJSON):
	fontsizes = {
		'motorway':(12,8, 16,14),
		'primary':(12,8, 16,14),
		'trunk':(12,8, 16,14),
		'secondary':(12,8, 16,14),
		'tertiary':(12,8, 16,12),
		'residential':(15,6, 18,12),
		'unclassified':(15,6, 18,12),
		}
	def choose_line_style(self, properties):
		if properties.get('name',"") != "":
			highway = properties['highway']
			rule = self.fontsizes.get(highway, self.fontsizes['unclassified'])
			return rule
		return None
	def draw1(self, ctx, scale):
		if self.labels is None:
			self.labels = {}
		zoom = int(self.zoom + math.log(scale, 2.0) + 0.5)
		if not zoom in self.labels:
			labels = self.labels[zoom] = []
			for id, line, properties, style in self.lines:
				label_text = properties['name']
				fontsize = self.zoom_feature(style, scale)
				placement = pykarta.draw.place_line_label(ctx, line, label_text, fontsize=fontsize, tilesize=256)
				if placement is not None:
					labels.append(placement)
		offset = self.zoom_feature((12,2.0, 16,8.0), scale)
		for placement in self.labels[zoom]:
			pykarta.draw.draw_line_label(ctx, placement, scale, offset)

tilesets.append(MapTilesetVector('osm-vector-road-labels',
	url_template="http://tile.openstreetmap.us/vectiles-skeletron/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusRoadLabels,
	zoom_min=12,
	zoom_max=16,
	zoom_substitutions={
		#14:16,
		15:16,
		},
	))

#-----------------------------------------------------------------------------

class RenderOsmusPois(RenderGeoJSON):
	label_style = {
		'font-size':8,
		}
	def __init__(self, layer, filename, zoom, x, y):
		if layer.tileset.symbols is None:
			layer.tileset.symbols = MapSymbolSet()
			path = os.path.join(os.path.dirname(__file__), "symbols")
			for symbol in glob.glob("%s/*.svg" % path):
				layer.tileset.symbols.add_symbol(symbol)
		RenderGeoJSON.__init__(self, layer, filename, zoom, x, y)
	def choose_point_style(self, properties):
		kind = properties.get("kind")
		name = properties.get("name")
		symbol = self.tileset.symbols.get_symbol(kind)
		if symbol is not None:
			renderer = symbol.get_renderer(self.containing_map)
			return (renderer, name)
		print "Warning: no symbol for POI:", properties
		return None
	def draw1(self, ctx, scale):
		for id, point, properties, style in self.points:
			x, y = self.scale_point(point, scale)
			renderer, label_text = style
			renderer.blit(ctx, x, y)
			if label_text is not None:
				pykarta.draw.centered_label(ctx, x, y+10, label_text, style=self.label_style)

tilesets.append(MapTilesetVector('osm-vector-pois',
	url_template="http://tile.openstreetmap.us/vectiles-pois/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusPois,
	zoom_min=14,
	))

#=============================================================================
# Tiles.osm.trincoll.edu
# http://tilestache.org/doc/TileStache.Goodies.VecTiles.server.html
#=============================================================================

class RenderParcels(RenderGeoJSON):
	clip = 0
	draw_passes = 2
	def __init__(self, layer, filename, zoom, x, y):
		RenderGeoJSON.__init__(self, layer, filename, zoom, x, y)
		self.labels = []
		if zoom >= 16:		# labels appear
			for id, polygon, properties, style in self.polygons:
				geojson = json.loads(properties['centroid'])
				coordinates = geojson['coordinates']
				center = project_to_tilespace_pixel(coordinates[1], coordinates[0], zoom, x, y)
				# If the label center is within this tile, use it.
				if center[0] >= 0 and center[0] < 256 and center[1] > 0 and center[1] < 256:
					self.labels.append((center, properties.get("house_number","?"), properties.get("street","?")))
	def choose_polygon_style(self, properties):
		return { "line-color": (0.0, 0.0, 0.0), "line-width": 0.25 }
	def draw2(self, ctx, scale):
		zoom = self.zoom + math.log(scale, 2.0)
		show_street = zoom >= 17.9
		for center, house_number, street in self.labels:
			center = self.scale_point(center, scale)
			if show_street:
				text = "%s %s" % (house_number, street)
			else:
				text = house_number
			pykarta.draw.centered_label(ctx, center[0], center[1], text, style={'font-size':8})

tilesets.append(MapTilesetVector('tc-parcels',
	url_template="http://tiles.osm.trincoll.edu/parcels/{z}/{x}/{y}.geojson",
	renderer=RenderParcels,
	zoom_min=16,
	zoom_max=16,
	))

#-----------------------------------------------------------------------------

class RenderTcRoadRefs(RenderGeoJSON):
	def __init__(self, layer, filename, zoom, x, y):
		RenderGeoJSON.__init__(self, layer, filename, zoom, x, y)
		self.shields = []
		dedup = set()
		for id, line, properties, style in self.lines:
			shield_text = properties['ref'].split(";")[0]
			if not shield_text in dedup:
				shield_pos = pykarta.draw.place_line_shield(line)
				if shield_pos is not None:
					self.shields.append((shield_pos, shield_text))
				dedup.add(shield_text)
	def choose_line_style(self, properties):
		return {}
	def draw1(self, ctx, scale):
		for center, shield_text in self.shields:
			center = self.scale_point(center, scale)
			pykarta.draw.generic_shield(ctx, center[0], center[1], shield_text, fontsize=8)

tilesets.append(MapTilesetVector('osm-vector-road-refs',
	url_template="http://tiles.osm.trincoll.edu/osm-vector-road-refs/{z}/{x}/{y}.json",
	renderer=RenderTcRoadRefs,
	zoom_min=10,
	zoom_max=14,
	))

#-----------------------------------------------------------------------------

class RenderWaterways(RenderGeoJSON):
	styles = {
		"river": {
				'line-color': (0.53, 0.80, 0.98),
				'line-width': (11,0.5, 16, 7.0),
				},
		"stream": {
				'line-color': (0.53, 0.80, 0.98),
				'line-width': (11,0.25, 16, 3.0),
				},
		"default": {
				'line-color': (1.00, 1.00, 0.00),
				'line-width': (11,0.25, 16, 2.0),
				},
		}
	def choose_line_style(self, properties):
		style = self.styles.get(properties['type'], self.styles['default'])
		style = style.copy()
		style['line-width'] = self.zoom_feature(style['line-width'])	
		return style

tilesets.append(MapTilesetVector('osm-vector-waterways',
	url_template="http://tiles.osm.trincoll.edu/osm-vector-waterways/{z}/{x}/{y}.json",
	renderer=RenderWaterways,
	zoom_min=11,		# at lower zooms osm-vector-water is enough
	zoom_max=16,
	))

#-----------------------------------------------------------------------------

class RenderAdminBorders(RenderGeoJSON):
	clip = 2
	sort_key = 'admin_level'
	styles = {
		4: { 	# state
			'line-color': (1.0, 1.0, 1.0),
			'line-width': (4, 1.5, 14, 3.5),
			'overline-color': (0.0, 0.0, 0.0),
			'overline-width': (4, 1.0, 14, 3.0),
			'overline-dasharray': (15, 4, 4, 4),
			},
		6: {	# county
			'line-color': (1.0, 1.0, 1.0),
			'line-width': (4, 0.9, 14, 2.5),
			'overline-color': (0.0, 0.0, 0.0),
			'overline-width': (4, 0.66, 14, 2.0), 
			'overline-dasharray': (15, 4, 4, 4),
			},
		7: {	# New York City
			'line-color': (1.0, 1.0, 1.0),
			'line-width': (4, 0.7, 14, 2.0),
			'overline-color': (0.0, 0.0, 0.0),
			'overline-width': (4, 0.55, 14, 1.5), 
			'overline-dasharray': (15, 4, 4, 4),
			},
		8: {	# town
			'line-color': (1.0, 1.0, 1.0),
			'line-width': (4, 0.4, 14, 1.5),
			'overline-color': (0.0, 0.0, 0.0),
			'overline-width': (4, 0.33, 14, 1.0),
			'overline-dasharray': (15, 4, 4, 4),
			}
		}
	def choose_polygon_style(self, properties):
		style = self.styles.get(properties['admin_level'],None)
		if style is None:
			print "Warning: no style for admin polygon:", properties
		if style is not None:
			style = style.copy()
			for i in ("line-width", "overline-width"):
				if i in style:
					style[i] = self.zoom_feature(style[i])
		return style
	def draw1(self, ctx, scale):
		self.start_clipping(ctx, scale)
		for id, polygon, properties, style in reversed(self.polygons):
			pykarta.draw.polygon(ctx, self.scale_points(polygon, scale))
			pykarta.draw.stroke_with_style(ctx, style)

tilesets.append(MapTilesetVector('osm-vector-admin-borders',
	url_template="http://tiles.osm.trincoll.edu/osm-vector-admin-borders/{z}/{x}/{y}.json",
	renderer=RenderAdminBorders,
	zoom_min=4,
	zoom_max=14,
	))

#-----------------------------------------------------------------------------

class RenderPlaces(RenderGeoJSON):
	sort_key = 'sort_key'
	sizes = {
		'state':    ( 5, 8.0,  9, 40.0),
		'county':   ( 7, 10.0, 9, 15.0),
		'city':     ( 6, 5.0, 16, 60.0),
		'town':     ( 9, 6.0, 16, 40.0),
		'village':  (13, 8.0, 16,30.0),
		'hamlet':   (13, 8.0, 16,30.0),
		'suburb':   (13, 8.0, 16,30.0),
		'locality': (13, 8.0, 16,30.0),
		}
	def choose_point_style(self, properties):
		#print "admin point:", properties
		if 'name' in properties and properties['name'] is not None:
			fontsize = self.sizes.get(properties['type'])
			if fontsize is not None:
				fontsize = self.zoom_feature(fontsize)
				if self.zoom >= 11.0:
					return {
						'font-size':fontsize,
						'color':(0.0,0.0,0.0,0.6),
						'halo':False,
						}
				else:
					return { 'font-size':fontsize }
		return None
	def draw1(self, ctx, scale):
		for id, point, properties, style in self.points:
			point = self.scale_point(point, scale)
			pykarta.draw.centered_label(ctx, point[0], point[1], properties['name'], style=style)

tilesets.append(MapTilesetVector('osm-vector-places',
	url_template="http://tiles.osm.trincoll.edu/osm-vector-places/{z}/{x}/{y}.json",
	renderer=RenderPlaces,
	zoom_min=4,
	zoom_max=14,
	))

