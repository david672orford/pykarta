# encoding=utf-8
# pykarta/maps/layers/tilesets_osm_vec.py
# Vector tile sets and renderers for them
# Copyright 2013--2018, Trinity College
# Last modified: 9 May 2018

# http://colorbrewer2.org/ is helpful for picking color palates

import os
import glob
import cairo
import math

from tilesets_base import tilesets, MapTilesetVector
from pykarta.maps.layers.tile_rndr_geojson import MapGeoJSONTile, json_loader
from pykarta.maps.symbols import MapSymbolSet
import pykarta.draw

#-----------------------------------------------------------------------------

class MapOsmLanduseTile(MapGeoJSONTile):
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
		landuse = properties.get("landuse", "?")
		style = self.styles.get(landuse, { 'fill-color': (0.90, 0.90, 0.90) })
		return style
	def draw2(self, ctx, scale):
		for id, area, center, text in self.polygon_labels:
			area = area * scale * scale
			if area > 10000:	# equivalent of 100 pixel square
				center = self.scale_point(center, scale)
				pykarta.draw.centered_label(ctx, center[0], center[1], text, style=self.label_style)

tilesets.append(MapTilesetVector('osm-vector-landuse',
	tile_class=MapOsmLanduseTile,
	url_template="tiles/osm-vector-landuse/{z}/{x}/{y}.geojson", 
	attribution=u"Map © OpenStreetMap contributors",
	zoom_min=10,
	))

#-----------------------------------------------------------------------------

class MapOsmWaterwaysTile(MapGeoJSONTile):
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
		style = self.styles.get(properties['waterway'], self.styles['default'])
		style = style.copy()
		style['line-width'] = self.zoom_feature(style['line-width'])	
		return style

tilesets.append(MapTilesetVector('osm-vector-waterways',
	tile_class=MapOsmWaterwaysTile,
	url_template="tiles/osm-vector-waterways/{z}/{x}/{y}.geojson",
	zoom_min=11,		# at lower zooms osm-vector-water is enough
	zoom_max=16,
	))

#-----------------------------------------------------------------------------

class MapOsmWaterTile(MapGeoJSONTile):
	def choose_polygon_style(self, properties):
		return { 'fill-color': (0.53, 0.80, 0.98) }

tilesets.append(MapTilesetVector('osm-vector-water',
	tile_class=MapOsmWaterTile,
	url_template="tiles/osm-vector-water/{z}/{x}/{y}.geojson", 
	attribution=u"Map © OpenStreetMap contributors",
	zoom_min=4,
	))

#-----------------------------------------------------------------------------

# These vector tiles do not include any building properties.
class MapOsmBuildingsTile(MapGeoJSONTile):
	label_polygons = True
	draw_passes = 2
	label_style = {
		'font-size':8,
		'font-weight':'normal',
		'halo':False,
		'color':(0.5, 0.5, 0.5),
		}
	def choose_polygon_style(self, properties):
		return  { 'fill-color': (0.8, 0.7, 0.7) }
	def choose_polygon_label_text(self, properties):
		return properties.get('addr:housenumber')
	def draw2(self, ctx, scale):
		for id, area, center, text in self.polygon_labels:
			center = self.scale_point(center, scale)
			pykarta.draw.centered_label(ctx, center[0], center[1], text, style=self.label_style)

tilesets.append(MapTilesetVector('osm-vector-buildings',
	tile_class=MapOsmBuildingsTile,
	url_template="tiles/osm-vector-buildings/{z}/{x}/{y}.geojson", 
	attribution=u"Map © OpenStreetMap contributors",
	zoom_min=13,
	))

#-----------------------------------------------------------------------------

class MapOsmRoadsTile(MapGeoJSONTile):
	clip = 15
	sort_key = 'z_order'
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

	road_type_simplifier = {						# until zoom level 14
		'trunk': 'major_road',
		'primary': 'major_road',
		'secondary': 'major_road',
		'tertiary': 'minor_road',
		'road': 'minor_road',
		'unclassified': 'minor_road',
		'residential': 'minor_road',
		'service': 'minor_road',
		}
	styles = {
		'motorway':{
			#'line-color':(0.2, 0.3, 0.9),			# blue
			'line-color':(0.3, 0.45, 1.0),			# blue
			'line-width':(6,0.25, 14,8.0),
			'line-cap':'round',
			},
		'major_road':{
			#'line-color':(0.8, 0.2, 0.2),			# dark red
			'line-color':(0.9, 0.3, 0.3),			# dark red
			'line-width':(6,0.15, 14,5.0),
			'line-cap':'round',
			},
		'minor_road':{								# appear at z12
			'line-color':(0.4, 0.4, 0.4),			# grey
			'line-width':(12,0.2, 14,2.0),
			'line-cap':'round',
			},
		'railway':{
			'line-width': (12,0.5, 14,1.0),
			'line-color': (0.0, 0.0, 0.0),
			'line-dasharray': (1, 1),
			},
		'aeroway':{
			'line-width': (12,1.0, 14,2.0),
			'line-color': (0.5, 0.5, 0.7),
			},
		}

	# https://wiki.openstreetmap.org/wiki/Key:highway
	styles_z14 = {
		'motorway':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,8.0, 18,18.0),
			'line-cap':'round',
			#'overline-color':(0.2, 0.3, 0.9),		# blue
			'overline-color':(0.4, 0.6, 1.0),		# blue
			'overline-width':(14,6.0, 18,14.0),
			'overline-cap':'round',
			},
		'trunk':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,7.0, 18,16.0),
			'line-cap':'round',
			#'overline-color':(0.7, 0.0, 0.0),		# dark red
			'overline-color':(0.8, 0.0, 0.0),		# dark red
			'overline-width':(14,6.0, 18,14.0),
			'overline-cap':'round',
			},
		'primary':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,6.0, 18,13.0),
			'line-cap':'round',
			#'overline-color':(0.7, 0.0, 0.0),		# dark red
			'overline-color':(0.8, 0.0, 0.0),		# dark red
			'overline-width':(14,5.0, 18,11.0),
			'overline-cap':'round',
			},
		'secondary':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,5.0, 18,12.0),
			'line-cap':'round',
			'overline-color':(0.9, 0.3, 0.2),		# lighter red
			'overline-width':(14,4.0, 18,10.0),
			'overline-cap':'round',
			},
		'tertiary':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,4.0, 18,11.0),
			'line-cap':'round',
			'overline-color':(0.998, 0.55, 0.35),	# orange
			'overline-width':(14,3.5, 18,9.0),
			'overline-cap':'round',
			},
		'road':{	# FIXME: make different
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,3.0, 18,10.0),
			'line-cap':'round',
			'overline-color':(1.0, 1.0, 1.0),		# white fill
			'overline-width':(14,2.5, 18,8.0),
			'overline-cap':'round',
			},
		'unclassified':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,3.0, 18,10.0),
			'line-cap':'round',
			'overline-color':(0.99, 0.94, 0.85),	# tan fill
			'overline-width':(14,2.5, 18,8.0),
			'overline-cap':'round',
			},
		'residential':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,3.0, 18,10.0),
			'line-cap':'round',
			'overline-color':(1.0, 1.0, 1.0),		# white fill
			'overline-width':(14,2.5, 18,8.0),
			'overline-cap':'round',
			},
		'living_street':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,3.0, 18,10.0),
			'line-cap':'round',
			'line-dasharray':(2,10),
			'overline-color':(1.0, 1.0, 1.0),		# white fill
			'overline-width':(14,2.5, 18,8.0),
			'overline-cap':'round',
			},
		'pedestrian':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,3.0, 18,10.0),
			'line-cap':'round',
			'line-dasharray':(4,10),
			'overline-color':(1.0, 1.0, 1.0),		# white fill
			'overline-width':(14,2.5, 18,8.0),
			'overline-cap':'round',
			},
		'service':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,2.0, 18,6.0),
			'line-cap':'round',
			'overline-color':(1.0, 1.0, 1.0),		# white fill
			'overline-width':(14,1.75, 18,5.0),
			'overline-cap':'round',
			},
		'abandoned':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,3.0, 18,10.0),
			'line-cap':'round',
			'line-dasharray':(2,8),
			'overline-color':(1.0, 1.0, 1.0),		# white fill
			'overline-width':(14,2.5, 18,8.0),
			'overline-cap':'round',
			},
		'track':{
			'line-color': (0.75, 0.75, 0.75),
			'line-width': (14,1.5, 18,5.0),
			},
		'cycleway':{
			'line-color': (0.75, 0.5, 0.5),
			'line-width': (14,1.5, 18,5.0),
			},
		'bridleway':{
			'line-color': (0.5, 0.3, 0.3),
			'line-width': (14,1.5, 18,5.0),
			},
		'path':{
			'line-color': (0.5, 0.3, 0.3),
			'line-width': (14,1.5, 18,5.0),
			},
		'steps':{
			'line-color': (0.0, 0.0, 0.0),
			'line-width': (14,1.5, 18,5.0),
			'line-dasharray':(2,2),
			},
		'footway':{
			'line-color': (0.5, 0.3, 0.3),
			'line-width': (14,1.0, 18,3.0),
			},
		'construction':{
			'line-color': (0.5, 0.5, 0.5),
			'line-width': (14,2.0, 18,6.0),
			'line-dasharray': (10,3),
			},
		'railway':{
			'line-width': (14,3.0, 18,8.0),
			'line-color': (0.0, 0.0, 0.0),
			'line-dasharray': (1, 12),
			'overline-width': (14,1.0, 18,3.0),
			'overline-color': (0.0, 0.0, 0.0),
			},
		'aeroway':{
			'line-width': (14,6.0, 18,16.0),
			'line-color': (0.5, 0.5, 0.7),
			},
		}
	def choose_line_style(self, properties):
		style = self.style_cache.get((self.zoom, properties))
		if style is not None:
			return style	

		way_type = properties.get('highway')
		if way_type is None and 'railway' in properties:
			way_type = 'railway'
		if way_type is None and 'aeroway' in properties:
			way_type = 'aeroway'
		style = None
		if self.zoom >= 14:
			style = self.styles_z14.get(way_type)
		if style is None:
			style = self.styles.get(self.road_type_simplifier.get(way_type,way_type))
		if style is None:
			print "Warning: no style for:", way_type, properties
			style = {'line-width':(0,10, 16,10), 'line-color':(0.0, 1.0, 0.0)}		# error indicator
		style = style.copy()
		for i in ("line-width", "overline-width"):
			if i in style:
				# Scale widths to zoom level
				width = self.zoom_feature(style[i])
				# make motorway entrance and exit ramps smaller
				if properties.get('is_link') == 'yes':
					width *= 0.7
				# Accept modified style
				style[i] = width
		# Show bridges if the zoom level is high enough that the roads have casings.
		if properties.get('is_bridge') == 'yes' and 'overline-width' in style:
			style['line-width'] *= 1.30
		
		self.style_cache[(self.zoom, properties)] = style
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
	tile_class=MapOsmRoadsTile,
	url_template="tiles/osm-vector-roads/{z}/{x}/{y}.geojson", 
	attribution=u"Map © OpenStreetMap contributors",
	zoom_min=6,
	))

#-----------------------------------------------------------------------------

class MapOsmRoadLabelsTile(MapGeoJSONTile):
	fontsizes = {
		'motorway':(12,8, 16,14),
		'primary':(12,8, 16,14),
		'trunk':(12,8, 16,14),
		'secondary':(12,8, 16,14),
		'tertiary':(12,8, 16,12),
		'residential':(15,6, 18,12),
		'unclassified':(15,6, 18,12),
		}
	def __init__(self, layer, filename, zoom, x, y, data=None):
		MapGeoJSONTile.__init__(self, layer, filename, zoom, x, y, data)

		# Place the highway shields
		self.shields = []
		dedup = set()		# dedup only within tile
		for id, line, properties, style in self.lines:
			ref = properties.get('ref')
			if ref is not None:
				shield_text = ref.split(";")[0]
				if not shield_text in dedup:
					shield_pos = pykarta.draw.place_line_shield(line)
					if shield_pos is not None:
						self.shields.append((shield_pos, shield_text))
					dedup.add(shield_text)

	def choose_line_style(self, properties):
		if properties.get('name') is not None:
			highway = properties['highway']
			rule = self.fontsizes.get(highway, self.fontsizes['unclassified'])
			return rule
		return None

	def draw1(self, ctx, scale):

		# Place the road labels for the current zoom level (if it has not been done yet)
		zoom = int(self.zoom + math.log(scale, 2.0) + 0.5)
		if not zoom in self.labels:
			labels = self.labels[zoom] = []
			for id, line, properties, style in self.lines:
				name = properties['name']
				if not name in self.dedup:
					fontsize = self.zoom_feature(style, scale)
					placement = pykarta.draw.place_line_label(ctx, line, name, fontsize=fontsize, tilesize=256)
					if placement is not None:
						labels.append(placement)
					self.dedup.add(name)

		# Draw road names
		offset = self.zoom_feature((10,2.0, 16,8.0), scale)
		for placement in self.labels[zoom]:
			pykarta.draw.draw_line_label(ctx, placement, scale, offset)

		# Draw highway route number shields
		for center, shield_text in self.shields:
			center = self.scale_point(center, scale)
			pykarta.draw.generic_shield(ctx, center[0], center[1], shield_text, fontsize=10)

tilesets.append(MapTilesetVector('osm-vector-road-labels',
	tile_class=MapOsmRoadLabelsTile,
	url_template="tiles/osm-vector-road-labels/{z}/{x}/{y}.geojson", 
	attribution=u"Map © OpenStreetMap contributors",
	zoom_min=10,
	zoom_max=16,
	zoom_substitutions={
		#14:16,
		15:16,
		},
	))

#-----------------------------------------------------------------------------

class MapOsmAdminBordersTile(MapGeoJSONTile):
	clip = 2
	sort_key = 'admin_level'
	# http://wiki.openstreetmap.org/wiki/United_States_admin_level
	styles = {
		4: { 	# state
			'line-color': (1.0, 1.0, 1.0),
			'line-width': (4, 1.5, 14, 3.5),
			'overline-color': (0.0, 0.0, 0.0),
			'overline-width': (4, 1.0, 14, 3.0),
			'overline-dasharray': (15, 4, 4, 4),
			},
		5: {	# New York City (was 7)
			'line-color': (1.0, 1.0, 1.0),
			'line-width': (4, 1.0, 14, 3.0),
			'overline-color': (0.0, 0.0, 0.0),
			'overline-width': (4, 0.75, 14, 2.5), 
			'overline-dasharray': (15, 4, 4, 4),
			},
		6: {	# county
			'line-color': (1.0, 1.0, 1.0),
			'line-width': (4, 0.9, 14, 2.5),
			'overline-color': (0.0, 0.0, 0.0),
			'overline-width': (4, 0.66, 14, 2.0), 
			'overline-dasharray': (15, 4, 4, 4),
			},
		7: {	# town (larger than city?!), township, unincorporated community
			'line-color': (1.0, 1.0, 1.0),
			'line-width': (4, 0.6, 14, 2.0),
			'overline-color': (0.0, 0.0, 0.0),
			'overline-width': (4, 0.50, 14, 1.5),
			'overline-dasharray': (15, 4, 4, 4),
			},
		8: {	# city or village
			'line-color': (1.0, 1.0, 1.0),
			'line-width': (4, 0.4, 14, 1.5),
			'overline-color': (0.0, 0.0, 0.0),
			'overline-width': (4, 0.33, 14, 1.0),
			'overline-dasharray': (15, 4, 4, 4),
			},
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
	tile_class=MapOsmAdminBordersTile,
	url_template="tiles/osm-vector-admin-borders/{z}/{x}/{y}.geojson",
	zoom_min=4,
	zoom_max=16,
	))

#-----------------------------------------------------------------------------

class MapOsmPoisTile(MapGeoJSONTile):
	label_style = {
		'font-size':8,
		}
	def __init__(self, layer, filename, zoom, x, y, data=None):
		if layer.tileset.symbols is None:
			layer.tileset.symbols = MapSymbolSet()
			path = os.path.join(os.path.dirname(__file__), "symbols")
			for symbol in glob.glob("%s/*.svg" % path):
				layer.tileset.symbols.add_symbol(symbol)
		MapGeoJSONTile.__init__(self, layer, filename, zoom, x, y, data)
	def choose_point_style(self, properties):
		amenity = properties.get("amenity")
		symbol = self.tileset.symbols.get_symbol(amenity)
		if symbol is not None:
			renderer = symbol.get_renderer(self.containing_map)
			label_text = properties.get("name") if self.zoom >= 16 else None
			return (renderer, label_text)
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
	tile_class=MapOsmPoisTile,
	url_template="tiles/osm-vector-pois/{z}/{x}/{y}.geojson", 
	attribution=u"Map © OpenStreetMap contributors",
	zoom_min=14,
	))

#-----------------------------------------------------------------------------

class MapOsmPlacesTile(MapGeoJSONTile):
	#sort_key = 'sort_key'
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
			fontsize = self.sizes.get(properties['place'])
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
	tile_class=MapOsmPlacesTile,
	url_template="tiles/osm-vector-places/{z}/{x}/{y}.geojson",
	zoom_min=4,
	zoom_max=14,
	))

#-----------------------------------------------------------------------------

class MapOsmTile(object):
	draw_passes = 12
	tile_classes = (
		("landuse", MapOsmLanduseTile),
		("waterways", MapOsmWaterwaysTile),
		("water", MapOsmWaterTile),
		("buildings", MapOsmBuildingsTile),
		("roads", MapOsmRoadsTile),
		("admin-borders", MapOsmAdminBordersTile),
		("road-labels", MapOsmRoadLabelsTile),
		("places", MapOsmPlacesTile),
		("pois", MapOsmPoisTile),
		)
	def __init__(self, layer, filename, zoom, x, y, data=None):
		parsed_json = json_loader(filename)
		self.passes = []
		for layer_name, tile_class in self.tile_classes:
			layer_data = parsed_json.get(layer_name)
			if layer_data is not None:
				tile = tile_class(layer, None, zoom, x, y, data=layer_data)
			else:
				tile = None
			for i in range(tile_class.draw_passes):
				self.passes.append((tile, i))
		assert len(self.passes) == self.draw_passes
	def draw(self, ctx, scale, draw_pass):
		tile, i = self.passes[draw_pass]
		if tile is not None:
			tile.draw(ctx, scale, i)

tilesets.append(MapTilesetVector('osm-vector',
	tile_class=MapOsmTile,
	url_template="tiles/osm-vector/{z}/{x}/{y}.geojson",
	zoom_min=4,
	zoom_max=16,
	))

