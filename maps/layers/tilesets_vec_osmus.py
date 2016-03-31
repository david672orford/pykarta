# encoding=utf-8
# pykarta/maps/layers/tilesets_vec_osmus.py
# Vector tile sets and renderers for them
# Copyright 2013, 2014, 2015, Trinity College
# Last modified: 13 October 2015

import os
import glob
import cairo
import math

from pykarta.maps.layers.tile_rndr_geojson import RenderGeoJSON
from tilesets_base import tilesets, MapTilesetVector
from pykarta.geometry.projection import project_to_tilespace_pixel
from pykarta.maps.symbols import MapSymbolSet
import pykarta.draw

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

#-----------------------------------------------------------------------------

class RenderOsmusWater(RenderGeoJSON):
	def choose_polygon_style(self, properties):
		return { 'fill-color': (0.53, 0.80, 0.98) }

#-----------------------------------------------------------------------------

# These vector tiles do not include any building properties.
class RenderOsmusBuildings(RenderGeoJSON):
	def choose_polygon_style(self, properties):
		return  { 'fill-color': (0.8, 0.7, 0.7) }

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

#-----------------------------------------------------------------------------

tilesets.append(MapTilesetVector('osm-vector-landuse',
	url_template="http://tile.openstreetmap.us/vectiles-land-usages/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusLanduse,
	))

tilesets.append(MapTilesetVector('osm-vector-water',
	url_template="http://tile.openstreetmap.us/vectiles-water-areas/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusWater,
	))

tilesets.append(MapTilesetVector('osm-vector-buildings',
	url_template="http://tile.openstreetmap.us/vectiles-buildings/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusBuildings,
	zoom_min=13,
	))

tilesets.append(MapTilesetVector('osm-vector-roads',
	url_template="http://tile.openstreetmap.us/vectiles-highroad/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusRoads,
	))

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

tilesets.append(MapTilesetVector('osm-vector-pois',
	url_template="http://tile.openstreetmap.us/vectiles-pois/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	renderer=RenderOsmusPois,
	zoom_min=14,
	))

