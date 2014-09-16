# pykarta/formats/tiledir.py
# Copyright 2013, 2014, Trinity College
# Last modified: 2 September 2014

import os

class MapTiledirWriter(object):
	def __init__(self, output_dir):
		self.output_dir = output_dir
	def add_tile(self, x, y, zoom, tile_data):
		dirname = "%s/%d/%d" % (self.output_dir, zoom, x)
		filename = "%s/%d.png" % (dirname, y)
		if not os.path.exists(dirname):
			os.makedirs(dirname)
		f = open(filename, "wb")
		f.write(tile_data)
		f.close()
	def close(self):
		pass

