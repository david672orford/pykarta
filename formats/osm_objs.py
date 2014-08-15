# Copyright 2011, 2014, Trinity College Computing Center
# Objects to represent data in OSM XML files
# Written by David Chappell
# Last modified: 2 August 2014

class OsmTags(dict):
	def __init__(self, items):
		dict.__init__(self)
		if items is not None:
			self.update(items)

	def is_tagged(self, name, value):
		return self.get(name, None) == value

	def __str__(self):
		text = ""
		for name, value in self.items():
			text += ' <tag k="%s" v="%s"/>\n' % (self._encode(name), self._encode(value))
		return text

	def _encode(self, text):
		text = text.replace('&', '&amp;')
		text = text.replace('<', '&lt;')
		text = text.replace('>', '&gt;')
		return text

class OsmObj(object):
	def __init__(self, osm_tags):
		self.id = None
		self.osm_tags = OsmTags(osm_tags)

class OsmNode(OsmObj):
	def __init__(self, lat, lon, osm_tags):
		OsmObj.__init__(self, osm_tags)
		assert type(lat) == float
		assert type(lon) == float
		self.lat = lat
		self.lon = lon

	def __str__(self):
		text = "<node id='%d' lat='%s' lon='%s'>\n" % (self.id, repr(self.lat), repr(self.lon))
		text += str(self.osm_tags)
		text += "</node>\n"
		return text

class OsmWay(OsmObj):
	def __init__(self, nodes=None, osm_tags=None):
		OsmObj.__init__(self, osm_tags)
		self.nodes = [] if nodes is None else nodes

	def __str__(self):
		text = '<way id="%d">\n' % self.id
		for node in self.nodes:
			text += ' <nd ref="%d"/>\n' % node.id
		text += str(self.osm_tags)
		text += "</way>\n"
		return text

	def append(self, point):
		self.nodes.append(point)

class OsmRelation(OsmObj):
	def __init__(self, members=None, osm_tags=None):
		OsmObj.__init__(self, osm_tags)
		self.members = [] if members is None else members

	def append(self, new_member):
		self.members.append(new_member)

	def __str__(self):
		text = "<relation id='%d'>\n" % self.id
		text += str(self.osm_tags)
		for member in self.members:
			text += str(member)
		text += "</relation>\n";
		return text

	def append(self, new_member):
		self.members.append(new_member)

class OsmRelationMember(object):
	def __init__(self, type, role, ref):
		self.type = type
		self.role = role
		self.ref = ref

	def __str__(self):
		return " <member type='%s' role='%s' ref='%d' />\n" % (self.type, self.role, self.ref.id)

