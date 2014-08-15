#! /usr/bin/python
# Copyright 2011, 2014, Trinity College Computing Center
# Reader and writer for OSM XML files
# Written by David Chappell
# Last modified: 7 August 2014

from osm_objs import OsmNode, OsmWay

class OsmWriter:
	def __init__(self, writable_object, creator):
		self.fh = writable_object
		self.creator = creator
		self.nodes = []
		self.nodes_by_id = {}
		self.nodes_by_coords = {}
		self.ways = []
		self.ways_by_id = {}
		self.relations = []
		self.relations_by_id = {}
		self.lowest_id = 0			# JOSM uses one counter for both nodes and ways, so must be OK
		self.saved = False

	def _id_assigner(self, obj):
		if obj.id is None:
			self.lowest_id -= 1
			obj.id = self.lowest_id
		elif obj.id < self.lowest_id:
			self.lowest_id = obj.id

	def __del__(self):
		if not self.saved:
			self.save()

	def save(self):
		self.saved = True
		self.fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
		self.fh.write('<osm version="0.6" generator="%s">\n' % self.creator)
		for node in self.nodes:
			self.fh.write(str(node))
		for way in self.ways:
			self.fh.write(str(way))
		for relation in self.relations:
			self.fh.write(str(relation))
		self.fh.write('</osm>\n')

	def append_node(self, node):
		self._id_assigner(node)
		if node.id in self.nodes_by_id:
			assert self.nodes_by_id[node.id] is node
		else:
			self.nodes.append(node)
			self.nodes_by_id[node.id] = node
			self.nodes_by_coords[(node.lat, node.lon)] = node
		return node

	def append_way(self, way):
		self._id_assigner(way)
		if way.id in self.ways_by_id:
			assert self.ways_by_id[way.id] is way
		else:
			self.ways.append(way)
			self.ways_by_id[way.id] = way
			for node in way.nodes:
				self.append_node(node)
		return way

	def append_relation(self, relation):
		self._id_assigner(relation)
		if relation.id in self.relations_by_id:
			assert self.relations_by_id[relation.id] is relation
		else:
			self.relations.append(relation)
			self.relations_by_id[relation.id] = relation
			for member in relation.members:
				if member.type == "node":
					self.append_node(member.ref)
				elif member.type == "way":
					self.append_way(member.ref)
				else:
					raise AssertionError, "Missing case"
		return relation

	def new_node_deduper(self, lat, lon, osm_tags=None):
		node = self.nodes_by_coords.get((lat, lon), None)
		if node is not None:
			if osm_tags is not None:
				node.osm_tags.update(osm_tags)	
		else:
			node = OsmNode(lat, lon, osm_tags)
		return node

	def new_node(self, lat, lon, osm_tags=None):
		node = self.new_node_deduper(lat, lon, osm_tags)
		return self.append_node(node)

	def new_way(self, coordinates, osm_tags=None):
		nodes = []
		for coordinate in coordinates:
			node = self.new_node_deduper(coordinates[0], coordinates[1])
			nodes.append(node)
		return self.append_way(OsmWay(nodes, osm_tags))

if __name__ == "__main__":
	import sys
	osm = OsmWriter(sys.stdout, "OsmWriter test")
	osm.add_node(42.0, -72.0, {'name':'smith'})
	osm.add_node(42.0, -72.0, {'addr:housenumber':'12'})
	osm.add_way([
		[42.0, -72.0],
		[43.0, -72.0],
		[43.0, -71.0],
		[42.0, -72.0]
		])
	osm.save()

