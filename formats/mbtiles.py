# pykarta/formats/mbtiles.py
# Copyright 2013, 2014, Trinity College
# Last modified: 24 January 2013

import sqlite3

class MapMbtilesWriter(object):
	def __init__(self, mbtiles, metadata):
		self.conn = sqlite3.connect(mbtiles)
		self.cursor = self.conn.cursor()

		self.cursor.execute("CREATE TABLE metadata (name text, value text)")
		self.cursor.execute("CREATE UNIQUE INDEX metadata_index on metadata (name)")
		self.cursor.execute("CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob)")
		self.cursor.execute("CREATE UNIQUE INDEX tile_index on tiles (zoom_level, tile_column, tile_row)")

		for name, value in metadata.items():
			self.cursor.execute("INSERT INTO metadata (name, value) values (?, ?)", (name, value))

		self.count = 0

	def add_tile(self, zoom, x, y, tile_data):
		flipped_y = (2**zoom-1) - y
		self.cursor.execute(
			"INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data) values (?, ?, ?, ?)",
			#(zoom, x, flipped_y, sqlite3.Binary(tile_data))
			(zoom, x, flipped_y, buffer(tile_data))
			)

		self.count += 1
		if (self.count % 1000) == 0:
			self.conn.commit()

	def close(self):
		print "%d tiles saved" % self.count
		self.conn.commit()
		self.conn.close()
		self.conn = None

