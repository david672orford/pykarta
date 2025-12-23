# pykarta/format/geojson_writer.py
# Copyright 2011--2017, David Chappell
# Last modified: 11 May 2017

import json

class GeojsonWriter(object):
	def __init__(self, writable_object):
		self.writable_object = writable_object
		self.features = []
		self.properties = {}
		self.saved = False

	def __del__(self):
		if not self.saved:
			self.save()

	def save(self):
		self.saved = True
		fh = self.writable_object
		self.write(fh)
		fh.close()

	def save_js(self, varname):
		self.saved = True
		fh = self.writable_object
		fh.write("var %s = " % varname)
		self.write(fh)
		fh.write(";\n")
		fh.close()

	def write(self, fh):
		json.dump(
			{
			'type': "FeatureCollection",
			'properties': self.properties,
			'features': self.features,
			}, fh, indent=1, separators=(',',':'))

	def __str__(self):
		return json.dumps(
			{
			'type': "FeatureCollection",
			'features': self.features,
			}, separators=(',',':'))

	def add_point(self, lat, lon, properties={}):
		self.features.append(
			{
			'type': "Feature",
			'geometry': {
				'type': "Point",
				'coordinates': [lon, lat],
				},
			'properties': properties,
			})

	# Simple polygon
	def add_polygon(self, vertexes, properties={}):
		assert type(vertexes[0][0]) is float
		self.features.append(
			{
			'type': "Feature",
			'geometry': {
				'type': "Polygon",
				'coordinates': [[[i[1], i[0]] for i in vertexes]],
				},
			'properties': properties,
			})

	def add_linestring(self, vertexes, properties={}):
		self.features.append(
			{
			'type': "Feature",
			'geometry': {
				'type': "LineString",
				'coordinates': [[i[1], i[0]] for i in vertexes],
				},
			'properties': properties,
			})

