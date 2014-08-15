# pykarta/maps/layers/geojson.py
# Copyright 2014, Trinity College
# Last modified: 21 July 2014

import json
from pykarta.maps.layers.vector import MapVectorLayer, MapVectorMarker, MapVectorLineString, MapVectorPolygon
from pykarta.geometry.point import Point, PointFromGeoJSON
from pykarta.geometry.line import LineStringFromGeoJSON
from pykarta.geometry.polygon import PolygonFromGeoJSON

class MapGeoJSONLayer(MapVectorLayer):
	def __init__(self, filename):
		MapVectorLayer.__init__(self)
		self.tolerance = 0.001

		fh = open(filename, "r")
		geojson_featurecollection = json.load(fh)
		fh.close()

		assert geojson_featurecollection['type'] == 'FeatureCollection'

		self.style = geojson_featurecollection.get('properties',{}).get('style',{})

		self.layer1 = []
		self.layer2 = []

		for feature in geojson_featurecollection['features']:
			self.add_feature(feature)

		for obj in self.layer1 + self.layer2:
			self.add_obj(obj)

	def add_feature(self, feature):
		assert feature['type'] == "Feature"
		properties = feature['properties']
		#print properties
		feature_name = properties.get('name', '')
		geometry = feature['geometry']
		if geometry['type'] == "GeometryCollection":
			for sub_geometry in geometry['geometries']:
				self.add_geometry(sub_geometry, feature_name)
		else:
			self.add_geometry(geometry, feature_name)
	
	def add_geometry(self, geometry, name):
		if geometry['type'] == 'Point':
			self.layer1.append(MapVectorMarker(PointFromGeoJSON(geometry), style={'label':name}))
		elif geometry['type'] == 'LineString':
			linestring = LineStringFromGeoJSON(geometry)
			obj = MapVectorLineString(linestring)
			self.layer2.append(obj)
		elif geometry['type'] == 'Polygon':
			self.add_polygon(geometry, name)
		elif geometry['type'] == 'MultiPolygon':
			for coordinates in geometry['coordinates']:
				sub_geo = {
					"type": "Polygon",
					"coordinates": coordinates,
					}
				self.add_polygon(sub_geo, name)
		else:
			raise ValueError("Geometries of type %s not supported" % geometry['type'])

	def add_polygon(self, geometry, name):
		polygon = PolygonFromGeoJSON(geometry)
		polygon.simplify(self.tolerance, debug=True)
		style = {
			'label':name,
			'fill-color': None,
			}
		style.update(self.style)
		obj = MapVectorPolygon(polygon, style=style)
		self.layer2.append(obj)


