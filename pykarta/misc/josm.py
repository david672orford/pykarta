# pykarta/misc/josm.py
# Copyright 2013--2023, Trinity College
# Last modified: 26 March 2023

import subprocess
from urllib.parse import urlencode
from http.client import HTTPConnection
import socket
import time

class JosmNotListening(Exception):
	pass

class Josm(object):
	def __init__(self):
		self.pid = None
		self.launch()
		self.loaded_imagery = set()

	# Send a Remote Control command to JOSM
	def send_cmd(self, command, params):
		url_path = "/%s?%s" % (command, urlencode(params))
		print("JOSM Remote Control command:", url_path)
		try:
			# Use httplib because urllib2 has proxy support which we would have to disable.
			conn = HTTPConnection("localhost:8111")
			conn.request("GET", url_path)
			resp = conn.getresponse()
			print("%s %s" % (resp.status, resp.reason))
			print(resp.read())
		except socket.error:
			raise JosmNotListening
	
	def launch(self):
		try:
			self.send_cmd("version", {})
		except JosmNotListening:
			try:
				self.pid = subprocess.Popen(["josm"])
				print("JOSM PID:", self.pid)
			except OSError:
				raise JosmNotListening
			for i in range(30):
				time.sleep(1)
				try:
					self.send_cmd("version", {})
					return
				except JosmNotListening:
					pass
			raise JosmNotListening
	
	def cmd_zoom(self, bbox):
		print("JOSM zoom to ", str(bbox))
		self.send_cmd("zoom", {
			"top": bbox.max_lat,
			"left": bbox.min_lon,
			"bottom": bbox.min_lat,
			"right": bbox.max_lon
			})
	
	def cmd_load_and_zoom(self, bbox):
		print("JOSM load data and zoom to ", bbox)
		self.send_cmd("load_and_zoom", {
			"top": bbox.max_lat,
			"left": bbox.min_lon,
			"bottom": bbox.min_lat,
			"right": bbox.max_lon
			})
	
	imagery_layers = {
		'Bing Sat': (
			('title','Bing Sat'),
			('type','bing'),
			('max_zoom','19'),
			('url','http://www.bing.com/maps'),
			)
		}

	def cmd_imagery(self, title="Bing Sat"):
		print("JOSM add imagery", title)
		if not title in self.loaded_imagery:
			params = self.imagery_layers[title]
			self.send_cmd("imagery", params)
			self.loaded_imagery.add(title)

