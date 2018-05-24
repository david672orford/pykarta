# encoding=utf-8
# pykarta/maps/layers/tilesets_osm_vec.py
# Vector tile sets and renderers for them
# Copyright 2013--2018, Trinity College
# Last modified: 24 May 2018

# http://colorbrewer2.org/ is helpful for picking color palates for maps.

from __future__ import print_function
import os
import glob
import cairo
import math
import json
import re

from tilesets_base import tilesets, MapTilesetVector
from pykarta.maps.layers.tile_rndr_geojson import MapGeoJSONTile, json_loader
from pykarta.maps.symbols import MapSymbolSet
from pykarta.draw import \
	draw_line_label_stroked as draw_line_label, \
	draw_highway_shield, \
	centered_label as draw_centered_label, \
	poi_label as draw_poi_label, \
	polygon as draw_polygon, \
	line_string as draw_line_string, \
	stroke_with_style

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
		dedup = self.dedup
		for id, area, center, text in self.polygon_labels:
			if not text in dedup:
				# If area in square pixels is greater than that of a 100x100 pixel square,
				area = area * scale * scale
				if area > 10000:
					center = self.scale_point(center, scale)
					draw_centered_label(ctx, center[0], center[1], text, style=self.label_style)
					dedup.add(text)

tilesets.append(MapTilesetVector('osm-vector-landuse',
	tile_class=MapOsmLanduseTile,
	url_template="tiles/osm-vector-landuse/{z}/{x}/{y}.geojson", 
	attribution=u"Map © OpenStreetMap contributors",
	zoom_min=10,
	))

#-----------------------------------------------------------------------------

class MapOsmWaterwaysTile(MapGeoJSONTile):
	clip = 5
	styles = {
		"river": {
				'line-color': (0.53, 0.80, 0.98),
				'line-width': (11,0.5, 16, 7.0),
				},
		"stream": {
				'line-color': (0.53, 0.80, 0.98),
				'line-width': (11,0.25, 16, 3.0),
				},
		"canal": {
				'line-color': (0.53, 0.80, 0.98),
				'line-width': (11,0.25, 16, 2.0),
				'line-dasharray': (6,1),
				},
		"derelict_canal": {
				'line-color': (0.53, 0.80, 0.98),
				'line-width': (11,0.25, 16, 2.0),
				'line-dasharray': (1,6),
				},
		"default": {		# yellow error indicator
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
		for id, area, label_center, label_text in self.polygon_labels:
			label_center = self.scale_point(label_center, scale)
			draw_centered_label(ctx, label_center[0], label_center[1], label_text, style=self.label_style)

tilesets.append(MapTilesetVector('osm-vector-buildings',
	tile_class=MapOsmBuildingsTile,
	url_template="tiles/osm-vector-buildings/{z}/{x}/{y}.geojson", 
	attribution=u"Map © OpenStreetMap contributors",
	zoom_min=13,
	))

#-----------------------------------------------------------------------------

def RGB(r,g,b):
	return (r / 255.0, g / 255.0, b / 255.0)

#road_color = (
#	RGB(189,0,38),		# motorways
#	RGB(240,59,32),		# trunk
#	RGB(253,141,60),	# primary
#	RGB(254,204,92),	# secondary
#	RGB(255,255,178),	# tertiary
#	RGB(255,255,190),	# unclassified
#	RGB(255,255,255),	# residential
#	)
road_color = (
	RGB(227,26,28),		# motorways
	RGB(227,80,40),		# trunk
	RGB(253,141,60),	# primary
	RGB(254,204,92),	# secondary
	RGB(255,255,178),	# tertiary
	RGB(255,255,190),	# unclassified
	RGB(255,255,255),	# residential
	)

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

	# Until zoom level 14 we conflate road classes
	road_type_simplifier = {
		'trunk': 'major_road',
		'primary': 'major_road',
		'secondary': 'major_road',
		'tertiary': 'minor_road',
		'road': 'minor_road',
		'unclassified': 'minor_road',
		'residential': 'minor_road',
		'service': 'minor_road',
		}

	styles_z6_to_z10 = {
		'motorway':{
			'line-color':(0,0,0),
			'overline-color':road_color[0],
			'line-width':(6,0.08, 14,6.0),
			},
		'major_road':{
			'line-color':(0.5,0.5,0.5),
			'line-width':(6,0.03, 14,3.0),
			},
		}

	styles_z11_to_z13 = {
		'motorway':{
			'line-color':(0,0,0),
			'overline-color':road_color[0],
			'line-width':(6,0.08, 14,6.0),
			},
		'major_road':{
			'line-color':(0,0,0),
			'overline-color':road_color[1],
			'line-width':(6,0.03, 14,3.0),
			},
		'minor_road':{								# appear at z12
			'line-color':(0.5, 0.5, 0.5),			# gray texture rather than road_color[2]
			'line-width':(12,0.1, 14,1.0),
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
	styles_z14_to_z18 = {
		'motorway':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,6.0, 18,18.0),
			'overline-color':road_color[0],
			},
		'trunk':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,4.0, 18,16.0),
			'overline-color':road_color[1],
			},
		'primary':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,3.5, 18,13.0),
			'overline-color':road_color[2],
			},
		'secondary':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,3.0, 18,12.0),
			'overline-color':road_color[3],
			},
		'tertiary':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,2.0, 18,11.0),
			'overline-color':road_color[4],
			},
		'road':{	# FIXME: make different
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,1.5, 18,10.0),
			'overline-color':road_color[5],
			},
		'unclassified':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,1.5, 18,10.0),
			'overline-color':road_color[5],
			},
		'residential':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,1.5, 18,10.0),
			'overline-color':road_color[6],
			},
		'living_street':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,1.5, 18,10.0),
			'overline-dasharray':(5,1),
			'overline-color':road_color[6],
			},
		'pedestrian':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,1.5, 18,10.0),
			'overline-dasharray':(4,2),
			'overline-color':road_color[6],
			},
		'service':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,0.75, 18,6.0),
			'overline-color':road_color[6],
			},
		'abandoned':{
			'line-color':(0.0, 0.0, 0.0),			# black casing
			'line-width':(14,1.5, 18,10.0),
			'line-dasharray':(2,8),
			'overline-color':(1.0, 1.0, 1.0),		# white fill
			},
		'track':{
			'line-color': (0.75, 0.75, 0.75),
			'line-width': (14,0.75, 18,6.0),
			},
		'cycleway':{
			'line-color': (0.75, 0.5, 0.5),
			'line-width': (14,0.5, 18,5.0),
			},
		'bridleway':{
			'line-color': (0.5, 0.3, 0.3),
			'line-width': (14,0.5, 18,5.0),
			},
		'path':{
			'line-color': (0.5, 0.3, 0.3),
			'line-width': (14,0.5, 18,5.0),
			},
		'steps':{
			'line-color': (0.0, 0.0, 0.0),
			'line-width': (14,0.5, 18,5.0),
			'line-dasharray':(2,2),
			},
		'footway':{
			'line-color': (0.5, 0.3, 0.3),
			'line-width': (14,0.25, 18,3.0),
			},
		'construction':{
			'line-color': (0.5, 0.5, 0.5),
			'line-width': (14,1.5, 18,10.0),
			'line-dasharray': (10,3),
			},
		'railway':{
			'line-width': (14,2.5, 18,10.0),
			'line-color': (0.0, 0.0, 0.0),
			'line-dasharray': (1, 12),
			'overline-width': (14,0.5, 18,2.0),
			'overline-color': (0.0, 0.0, 0.0),
			},
		'aeroway':{
			'line-width': (14,6.0, 18,16.0),
			'line-color': (0.5, 0.5, 0.7),
			},
		}
	def choose_line_style(self, properties):
		#return {'line-width':1, 'line-color':(0.0, 1.0, 0.0)}

		way_type = properties.get('highway')
		if way_type is None and 'railway' in properties:
			way_type = 'railway'
		if way_type is None and 'aeroway' in properties:
			way_type = 'aeroway'
		if self.zoom >= 14:
			style = self.styles_z14_to_z18.get(way_type)
		elif self.zoom >= 11:
			style = self.styles_z11_to_z13.get(self.road_type_simplifier.get(way_type,way_type))
		else:
			style = self.styles_z6_to_z10.get(self.road_type_simplifier.get(way_type,way_type))
		if style is None:
			print("Warning: no style for:", way_type, properties)
			style = {'line-width':(0,10, 16,10), 'line-color':(0.0, 1.0, 0.0)}		# error indicator

		style = style.copy()

		# Scale road width from style. This is the width of the casing.
		line_width = self.zoom_feature(style["line-width"])

		# make link roads smaller
		if properties.get('is_link') == 'yes':
			line_width *= 0.7

		if 'overline-width' in style:
			style['overline-width'] = self.zoom_feature(style['overline-width'])
		elif 'overline-color' in style:
			style['overline-width'] = line_width * 0.9

		# At high zoom levels represent bridges by making their casings wider
		if self.zoom > 14 and properties.get('is_bridge') == 'yes':
			line_width *= 1.30

		style.update({
			'line-width': line_width,
			})

		return style

	def draw1(self, ctx, scale):
		self.start_clipping(ctx, scale)
		for id, line, name, style in self.lines:
			if 'line-width' in style:
				draw_line_string(ctx, self.scale_points(line, scale))
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
				draw_line_string(ctx, self.scale_points(line, scale))
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

	label_lines = True

	fontsizes = {
		'motorway':(12,11, 16,15),
		'primary':(12,11, 16,15),
		'trunk':(12,11, 16,15),
		'secondary':(12,10, 16,14),
		'tertiary':(12,10, 16,12),
		'residential':(12,8, 18,12),
		'unclassified':(12,8, 18,12),
		}

	abbreviations = {
		"Avenue": "Av",
		"Circle": "Cir",
		"Drive": "Dr",
		"Lane": "Ln",
		"Road": "Rd",
		"Street": "St",
		}

	def choose_line_label_text(self, properties):
		name = properties['name']
		m = re.search(r"^(.+\s)(\S+)$", name)
		if m:
			return m.group(1) + self.abbreviations.get(m.group(2),m.group(2))
		return name

	def choose_line_style(self, properties):
		if properties.get('name') is not None:
			highway = properties['highway']
			rule = self.fontsizes.get(highway, self.fontsizes['unclassified'])
			return rule
		return None

	def draw1(self, ctx, scale):
		dedup = self.dedup

		# Draw road names
		for placement in self.line_labels:
			if placement[0] not in dedup:
				draw_line_label(ctx, placement, scale)
				dedup.add(placement[0])

		# Draw highway route number shields
		for center, ref in self.line_shields:
			center = self.scale_point(center, scale)
			draw_highway_shield(ctx, center[0], center[1], ref)

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
		4: { 	# admin_level 4: state
			'line-color': (0.0, 0.0, 0.0),
			'line-width': (6, 0.25, 14, 1.0),
			'line-dasharray': (10, 5),
			},
		5: {	# admin_level 5: New York City
			'line-color': (0.0, 0.0, 0.0),
			'line-width': (6, 0.1, 14, 0.75), 
			'line-dasharray': (8, 4),
			},
		6: {	# admin_level 6: county
			'line-color': (0.0, 0.0, 0.0),
			'line-width': (6, 0.1, 14, 0.75), 
			'line-dasharray': (6, 3),
			},
		7: {	# admin_level 7: civil township (large structure in some US states)
			'line-color': (0.0, 0.0, 0.0),
			'line-width': (6, 0.1, 14, 0.75),
			'line-dasharray': (5, 3),
			},
		8: {	# admin_level 8: city or town
			'line-color': (0.0, 0.0, 0.0),
			'line-width': (6, 0.05, 14, 0.5),
			'line-dasharray': (4,2),
			},
		9: {	# admin_level 9: ward
			'line-color': (0.0, 0.0, 0.0),
			'line-width': (6, 0.02, 14, 0.25),
			'line-dasharray': (2,2),
			},
		10: {	# admin_level 10: neighborhood
			'line-color': (0.0, 0.0, 0.0),
			'line-width': (6, 0.02, 14, 0.25),
			'line-dasharray': (2,2),
			},
		}
	def choose_line_style(self, properties):
		style = self.styles.get(properties['admin_level'],None)
		if style is None:
			print("Warning: no style for admin_level %d" % properties['admin_level'])
		if style is not None:
			style = style.copy()
			for i in ("line-width", "overline-width"):
				if i in style:
					style[i] = self.zoom_feature(style[i])
		return style
	def draw1(self, ctx, scale):
		self.start_clipping(ctx, scale)
		for id, line, properties, style in reversed(self.lines):
			draw_line_string(ctx, self.scale_points(line, scale))
			stroke_with_style(ctx, style)

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
		print("Warning: no symbol for POI:", properties)
		return None
	def draw1(self, ctx, scale):
		for id, point, properties, style in self.points:
			x, y = self.scale_point(point, scale)
			renderer, label_text = style
			renderer.blit(ctx, x, y)
			if label_text is not None:
				draw_centered_label(ctx, x, y+10, label_text, style=self.label_style)

tilesets.append(MapTilesetVector('osm-vector-pois',
	tile_class=MapOsmPoisTile,
	url_template="tiles/osm-vector-pois/{z}/{x}/{y}.geojson", 
	attribution=u"Map © OpenStreetMap contributors",
	zoom_min=15,
	))

#-----------------------------------------------------------------------------

class MapOsmPlacesTile(MapGeoJSONTile):
	#sort_key = 'sort_key'
	place_label_sizes = {
		'state':    (6, 12, 16, 32),		# comes in at z5, goes out at z13
		'county':   (6, 8,  16, 18),		# comes in at z8, goes out at z10
		'city':     (6, 6,  16, 16),		# comes in at z7
		'town':     (6, 6,  16, 12),		# comes in at z10
		'village':  (6, 4,  16, 10),		# comes in at z13
		'hamlet':   (6, 4,  16, 10),
		'suburb':   (6, 4,  16, 10),
		'locality': (6, 4,  16, 10),
		}
	def choose_point_style(self, properties):
		#print("place:", properties)
		if properties.get("name") is not None:
			label_size = self.place_label_sizes.get(properties.get("place"))
			if label_size is None:
				print("Warning: unrecognized place type:", properties)
			else:
				return {
					'font-size': self.zoom_feature(label_size),
					'font-weight': 'bold',
					'color': (0.0, 0.0, 0.0),
					'halo': True,
					}
		return None
	def draw1(self, ctx, scale):
		for id, point, properties, style in self.points:
			x, y = self.scale_point(point, scale)
			place = properties["place"]
			label_text = properties['name']
			if place == "county":
				label_text = "%s County" % label_text

			if self.zoom < 14 and place == "city" or place == "town":
				ctx.new_path()
				ctx.arc(x, y, 3, 0, 2*math.pi)
				ctx.set_line_width(1.5)
				ctx.set_source_rgb(1,1,1)
				ctx.stroke_preserve()
				ctx.set_line_width(1.0)
				ctx.set_source_rgb(0,0,0)
				ctx.stroke_preserve()
				ctx.set_source_rgba(0.5,0.5,1.0)
				ctx.fill()
				draw_poi_label(ctx, x + 5, y, label_text, fontsize=style['font-size'])
			else:
				draw_centered_label(ctx, x, y, label_text, style=style)

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

