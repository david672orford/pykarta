# encoding=utf-8
# pykarta/maps/layers/tilesets_vec_tc.py
# Vector tile sets and renderers for them
# Copyright 2013, 2014, 2015, Trinity College
# Last modified: 13 October 2015

import math
import json

from pykarta.maps.layers.tile_rndr_geojson import RenderGeoJSON
from tilesets_base import tilesets, MapTilesetVector
from pykarta.geometry.projection import project_to_tilespace_pixel
import pykarta.draw

#=============================================================================
# Tiles.osm.trincoll.edu
# http://tilestache.org/doc/TileStache.Goodies.VecTiles.server.html
#=============================================================================

class RenderTcParcels(RenderGeoJSON):
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
	renderer=RenderTcParcels,
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

class RenderTcWaterways(RenderGeoJSON):
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
	renderer=RenderTcWaterways,
	zoom_min=11,		# at lower zooms osm-vector-water is enough
	zoom_max=16,
	))

#-----------------------------------------------------------------------------

class RenderTcAdminBorders(RenderGeoJSON):
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
	url_template="http://tiles.osm.trincoll.edu/osm-vector-admin-borders/{z}/{x}/{y}.json",
	renderer=RenderTcAdminBorders,
	zoom_min=4,
	zoom_max=14,
	))

#-----------------------------------------------------------------------------

class RenderTcPlaces(RenderGeoJSON):
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
	renderer=RenderTcPlaces,
	zoom_min=4,
	zoom_max=14,
	))

