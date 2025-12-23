#! /usr/bin/python
# Copyright 2011, 2014, Trinity College Computing Center
# Reader and writer for OSM XML files
# Written by David Chappell
# Last modified: 1 August 2014

import xml.sax
from .osm_objs import OsmNode, OsmWay, OsmRelation, OsmRelationMember

class OsmReader(xml.sax.handler.ContentHandler):
	def __init__(self, fh, keep_deleted=False):
		self.keep_deleted = keep_deleted
		self.nodes = []
		self.nodes_by_id = {}
		self.ways = []
		self.ways_by_id = {}
		self.relations = []

		self.thing = None
		self.way = None
		self.relation = None

		# Parse the input file. The callback functions are in this object.
		parser = xml.sax.make_parser()
		parser.setContentHandler(self)
		parser.parse(fh)

		# Go back and replace the node id numbers with the
		# cooresponding node objects.
		for way in self.ways:
			for nd in way.node_ids:
				way.nodes.append(self.nodes_by_id[nd])
	
		# Go back and replace the member references with the
		# cooresponding node and way objects.
		for relation in self.relations:
			for member in relation.members:
				if member.type == 'node':
					member.ref = self.nodes_by_id[member.ref]
				elif member.type == 'way':
					member.ref = self.ways_by_id[member.ref]
				else:
					raise AssertionError("Missing case")
	
	def startElement(self, name, attrs):
		if name == 'tag':
			self.thing.osm_tags[attrs.get('k')] = attrs.get('v')
		elif name == 'node':
			node = OsmNode(float(attrs.get('lat')), float(attrs.get('lon')), {})
			node.id = int(attrs.get('id'))
			if self.keep_deleted or attrs.get('action') != 'delete':
				self.nodes.append(node)
				self.nodes_by_id[node.id] = node
			self.thing = node
		elif name == 'way':
			self.way = OsmWay()
			self.way.id = int(attrs.get('id'))
			self.way.node_ids = []
			if self.keep_deleted or attrs.get('action') != 'delete':
				self.ways.append(self.way)
				self.ways_by_id[self.way.id] = self.way
			self.thing = self.way
		elif name == 'nd':
			assert self.way is not None
			ref = int(attrs.get('ref'))
			self.way.node_ids.append(ref)
		elif name == 'relation':
			self.relation = OsmRelation()
			self.relation.id = int(attrs.get('id'))
			if self.keep_deleted or attrs.get('action') != 'delete':
				self.relations.append(self.relation)
			self.thing = self.relation
		elif name == 'member':
			assert self.relation is not None
			member = OsmRelationMember(attrs.get("type"), attrs.get("role"), int(attrs.get("ref")))
			self.relation.append(member)
			
	def endElement(self, name):
		if name == 'node':
			self.node = self.thing = None
		elif name == 'way':
			self.way = self.thing = None
		elif name == 'relation':
			self.relation = self.thing = None

