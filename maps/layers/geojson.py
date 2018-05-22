# pykarta/maps/layers/geojson.py
# Copyright 2014--2018, Trinity College
# Last modified: 21 May 2018
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
from pykarta.geometry import GeometryFromGeoJSON

class MapLayerGeoJSON(MapLayerVector):
	def __init__(self, filename=None):
		MapLayerVector.__init__(self)

		if filename is not None:
			fh = open(filename, "r")
			self.load_geojson(fh)
			fh.close()

	def load_geojson(self, fh):
		geojson = json.load(fh)

		if geojson.get('type') != 'FeatureCollection':
			raise TypeError("File is not in GeoJSON format")

		self.style = geojson.get('properties',{}).get('style',{})

		layer1 = []
		layer2 = []

		for feature in geojson['features']:
			if feature.get('type') != 'Feature':
				raise TypeError("Member of GeoJSON FeatureCollection is not a Feature")
			properties = feature['properties']
			geometry = feature['geometry']
			geometry_type = geometry['type']

			if geometry_type == 'Point':
				point = GeometryFromGeoJSON(geometry)
				style = {'label': properties.get('name','')}
				obj = MapVectorMarker(point, properties=properties, style=style)
				layer1.append(obj)
			elif geometry_type == 'LineString':
				linestring = GeometryFromGeoJSON(geometry)
				obj = MapVectorLineString(linestring, properties=properties)
				layer2.append(obj)
			elif geometry_type == 'Polygon':
				polygon = GeometryFromGeoJSON(geometry)
				style = {
					'label':properties.get('name',''),
					'fill-color': None,
					}
				style.update(self.style)
				obj = MapVectorPolygon(polygon, properties=properties, style=style)
				layer2.append(obj)
			else:
				raise ValueError("Geometries of type %s not supported" % geometry['type'])

		for obj in layer1 + layer2:
			self.add_obj(obj)

	def save_geojson(self, fh):
		features = []

		for obj in self.layer_objs:
			features.append({
				'type':'Feature',
				'properties': obj.properties,
				'geometry': obj.geometry.as_geojson(),
				})

		fh.write(json.dumps(
			{
			'type': "FeatureCollection",
			'features': features,
			},
			separators=(',',':')
			))

