# pykarta/maps/layers/geojson.py
# Copyright 2014--2018, Trinity College
# Last modified: 14 May 2018
#
# Preliminary implementation of an extension to the vector layer which can
# load GeoJSON data from file handles and save the whole layer to a file
# handle as GeoJSON.
#
# Current Limitations:
# * the loader only works if the top level object is a FeatureCollection
# * properties are not preserved
# * nested FeatureCollections are not supported
# * GeomemtryCollections are loaded as individual objects
# * MultiLineString is not supported yet
# * MultiPolygon is loaded as multiple polygons
#

import json
from pykarta.maps.layers.vector import MapLayerVector, MapVectorMarker, MapVectorLineString, MapVectorPolygon
from pykarta.geometry import Point, PointFromGeoJSON, LineStringFromGeoJSON, PolygonFromGeoJSON

class MapLayerGeoJSON(MapLayerVector):
	def __init__(self, filename=None):
		MapLayerVector.__init__(self)

		if filename is not None:
			fh = open(filename, "r")
			self.load_geojson(fh)
			fh.close()

	def load_geojson(self, fh):
		geojson = json.load(fh)

		assert geojson['type'] == 'FeatureCollection'

		self.style = geojson.get('properties',{}).get('style',{})

		self.layer1 = []
		self.layer2 = []

		for feature in geojson['features']:
			assert feature['type'] == "Feature"
			properties = feature['properties']
			geometry = feature['geometry']

			if geometry['type'] == "GeometryCollection":
				for sub_geometry in geometry['geometries']:
					self._add_geojson_geometry(sub_geometry, properties)
			else:
				self._add_geojson_geometry(geometry, properties)

		for obj in self.layer1 + self.layer2:
			self.add_obj(obj)
	
	def _add_geojson_geometry(self, geometry, properties):
		if geometry['type'] == 'Point':
			point = PointFromGeoJSON(geometry)
			style = {'label': properties.get('name','')}
			marker = MapVectorMarker(point, properties=properties, style=style)
			self.layer1.append(marker)
		elif geometry['type'] == 'LineString':
			linestring = LineStringFromGeoJSON(geometry)
			obj = MapVectorLineString(linestring, properties=properties)
			self.layer2.append(obj)
		elif geometry['type'] == 'Polygon':
			self._add_geojson_polygon(geometry, properties)
		elif geometry['type'] == 'MultiPolygon':
			for coordinates in geometry['coordinates']:
				sub_geo = {
					"type": "Polygon",
					"coordinates": coordinates,
					}
				self._add_geojson_polygon(sub_geo, properties)
		else:
			raise ValueError("Geometries of type %s not supported" % geometry['type'])

	def _add_geojson_polygon(self, geometry, properties):
		polygon = PolygonFromGeoJSON(geometry)
		style = {
			'label':properties.get('name',''),
			'fill-color': None,
			}
		style.update(self.style)
		obj = MapVectorPolygon(polygon, properties=properties, style=style)
		self.layer2.append(obj)

	def save_geojson(self, fh):
		features = []

		for obj in self.layer_objs:
			features.append({
				'type':'Feature',
				'properties':obj.properties,
				'geometry': obj.geometry.as_geojson(),
				})

		fh.write(json.dumps(
			{
			'type': "FeatureCollection",
			'features': features,
			},
			separators=(',',':')
			))

