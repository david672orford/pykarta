# encoding=utf-8
# pykarta/maps/tilesets_geojson.py
# Last modified: 5 September 2013

import json
from pykarta.maps.tilesets_obj import MapTileset
from pykarta.maps.tilesets import tilesets
import pykarta.draw
from pykarta.maps.projection import project_to_tilespace_pixel

class RenderRoads(object):
	styles = {
		'highway':{
			'line-color':(0.0, 0.0, 0.5, 1.0),		# dark blue
			'line-width':4,
			},
		'major_road':{
			'line-color':(0.0, 0.5, 0.0, 1.0),		# dark green
			'line-width':4,
			},
		'minor_road':{
			'line-color':(0.0, 0.0, 0.0, 1.0),
			'line-width':1.5,
			},
		'rail':{
			'line-color':(0.5, 0.0, 0.0, 1.0),
			'line-width':2,
			'line-dash':(12,4)
			},
		'path':{
			'line-color':(0.5, 0.3, 0.3, 1.0),
			'line-width':1,
			},
		}

	def __init__(self, filename, zoom, x, y):
		f = open(filename, "rb")
		geojson = json.load(f)
		assert geojson['type'] == 'FeatureCollection'

		lines = []
		for feature in geojson['features']:
			assert feature['type'] == 'Feature'
			geometry = feature['geometry']
			if geometry['type'] == 'LineString':
				line = map(lambda p: project_to_tilespace_pixel(p[1], p[0], zoom, x, y), geometry['coordinates'])
				lines.append((line, self.choose_style(feature['properties'])))
			elif geometry['type'] == 'MultiLineString':
				for coordinates in geometry['coordinates']:
					line = map(lambda p: project_to_tilespace_pixel(p[1], p[0], zoom, x, y), coordinates)
					lines.append((line, self.choose_style(feature['properties'])))
			else:
				print "Unused:", geometry['type']

		self.lines = lines
		self.width_multiplier = max((zoom - 10.0) / 3.0, 1.0)

	def draw(self, ctx, xpixoff, ypixoff, opacity):
		ctx.save()
		ctx.translate(xpixoff, ypixoff)
		lines = self.lines
		for line, style in lines:
			pykarta.draw.line_string(ctx, line)
			pykarta.draw.stroke_with_style(ctx, style, self.width_multiplier)
		ctx.restore()

	def choose_style(self, properties):
		kind = properties['kind']
		style = self.styles.get(kind)
		if style is None:
			print properties
			return {'width':5, 'color':(1.0, 0.0, 0.0, 1.0)}
		return style

class RenderBuildings(object):
	style = {
		'fill-color': (0.5, 0.5, 0.5, 1.0)
		}

	def __init__(self, filename, zoom, x, y):
		f = open(filename, "rb")
		geojson = json.load(f)
		assert geojson['type'] == 'FeatureCollection'

		polygons = []
		for feature in geojson['features']:
			assert feature['type'] == 'Feature'
			geometry = feature['geometry']
			if geometry['type'] == 'Polygon':
				polygon = map(lambda p: project_to_tilespace_pixel(p[1], p[0], zoom, x, y), geometry['coordinates'][0])
				polygons.append(polygon)
		print "%d polygons" % len(polygons)
		self.polygons = polygons

	def draw(self, ctx, xpixoff, ypixoff, opacity):
		ctx.save()
		ctx.translate(xpixoff, ypixoff)
		polygons = self.polygons
		for polygon in polygons:
			pykarta.draw.polygon(ctx, polygon)
			pykarta.draw.fill_with_style(ctx, self.style)
		ctx.restore()

# http://openstreetmap.us/~migurski/vector-datasource/
tilesets.append(MapTileset('osm-geojson-roads',
	url_template="http://tile.openstreetmap.us/vectiles-highroad/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	custom_renderer_class = RenderRoads,
	layer_cache_enabled = True,
	))
tilesets.append(MapTileset('osm-geojson-buildings',
	url_template="http://tile.openstreetmap.us/vectiles-buildings/{z}/{x}/{y}.json", 
	attribution=u"Map © OpenStreetMap contributors",
	custom_renderer_class = RenderBuildings,
	layer_cache_enabled = True,
	))

