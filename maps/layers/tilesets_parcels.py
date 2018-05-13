# encoding=utf-8
# pykarta/maps/layers/tilesets_parcel.py
# Vector tile sets and renderers for them
# Copyright 2013--2018, Trinity College
# Last modified: 13 May 2018

import math
import json

from pykarta.maps.layers.tile_rndr_geojson import MapGeoJSONTile
from tilesets_base import tilesets, MapTilesetVector
from pykarta.geometry.projection import project_to_tilespace_pixel
import pykarta.draw

class MapParcelsTile(MapGeoJSONTile):
	clip = 0
	draw_passes = 2
	def __init__(self, layer, filename, zoom, x, y):
		MapGeoJSONTile.__init__(self, layer, filename, zoom, x, y)
		self.labels = []
		if zoom >= 16:		# labels appear
			for id, polygon, properties, style in self.polygons:
				geojson = json.loads(properties['centroid'])
				coordinates = geojson['coordinates']
				center = project_to_tilespace_pixel(coordinates[1], coordinates[0], zoom, x, y)
				# If the label center is within this tile, use it.
				if center[0] >= 0 and center[0] < 256 and center[1] > 0 and center[1] < 256:
					house_number = properties.get("house_number")
					street = properties.get("street")
					if house_number and street:				# not None and not blank
						self.labels.append((center, house_number, street))
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

tilesets.append(MapTilesetVector('parcels-pykarta',
	tile_class=MapParcelsTile,
	url_template="tiles/parcels/{z}/{x}/{y}.geojson",
	zoom_min=14,
	zoom_max=16,
	))

