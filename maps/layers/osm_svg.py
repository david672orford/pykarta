# encoding=utf-8
# pykarta/maps/layers/osm_svg.py
# Copyright 2013--2018, Trinity College
# Last modified: 22 October 2018

import os
import math
import re
#import gzip

from pykarta.maps.layers.base import MapLayer
from pykarta.misc.http import simple_urlopen
from pykarta.misc import file_age_in_days, SaveAtomically

#try:
#	import rsvg
#except:
import pykarta.fallback.rsvg as rsvg

#=============================================================================
# Experimental layer which exports a map in SVG format from openstreetmap.org
# This is intended for printing.
#=============================================================================
class MapLayerSVG(MapLayer):
	url_template = "https://render.openstreetmap.org/cgi-bin/export?bbox=%f,%f,%f,%f&scale=%d&format=svg"

	xlate = {
		# Brown Buildings
		"fill:rgb(74.72549%,66.27451%,66.27451%)": "fill:rgb(0%,100%,0%)",
	
		# Blue outline of highway=motorway
		"stroke:rgb(46.666667%,53.333333%,63.137255%)": "stroke:rgb(0%,0%,0%)",
		# Blue center highway=motorway
		"stroke:rgb(53.72549%,64.313725%,79.607843%)": "stroke:rgb(0%,0%,100%)",
	
		# Reddish outline of highway=primary
		"stroke:rgb(77.254902%,48.235294%,49.411765%)": "stroke:rgb(0%,0%,0%)",
		# Reddish center of highway=primary
		"stroke:rgb(86.666667%,62.352941%,62.352941%)": "stroke:rgb(90%,50%,50%)",
	
		# Orange outline of highway=secondary
		"stroke:rgb(80%,63.137255%,41.568627%)": "stroke:rgb(0%,0%,0%)",
		# Orange center of highway=secondary
		"stroke:rgb(97.647059%,83.921569%,66.666667%)": "stroke:rgb(100%,70%,50%)",
	
		# Outline of highway=tertiary
	    "stroke:rgb(77.647059%,77.647059%,54.117647%)": "stroke:rgb(0%,0%,0%)",
		# Pale yellow center of highway=tertiary
		"stroke:rgb(97.254902%,97.254902%,72.941176%)": "stroke:rgb(100%,100%,70%)",
	
		# White center of highway=residential, also white of holos
	    #"stroke:rgb(100%,100%,100%)": "stroke:rgb(100%,0%,0%)",
		# Gray border of highway=residential
		"stroke:rgb(73.333333%,73.333333%,73.333333%)": "stroke:rgb(0%,0%,0%)",
		}

	def __init__(self, source, extra_zoom=1.0):
		if source != "osm-default-svg":
			raise ValueError

		MapLayer.__init__(self)
		self.source = source
		self.extra_zoom = extra_zoom
		self.attribution = u"Map © OpenStreetMap contributors"

		self.svg = None
		self.svg_scale = None

		self.rgb_pattern = re.compile(r"(fill|stroke):rgb\([0-9\.]+%,[0-9\.]+%,[0-9\.]+%\)")
	
	def set_map(self, containing_map):
		MapLayer.set_map(self, containing_map)
		self.cache_dir = os.path.join(self.containing_map.tile_cache_basedir, self.source)
		if not os.path.exists(self.cache_dir):
			os.makedirs(self.cache_dir)

	def do_viewport(self):
		print "SVG layer: new viewport"
		bbox = self.containing_map.get_bbox()
		zoom = self.containing_map.get_zoom()

		# What a reading of http://svn.openstreetmap.org/applications/rendering/mapnik/zoom-to-scale.txt suggests:
		#scale = int(559082264.028 / math.pow(2, zoom) / self.extra_zoom + 0.5)

		# Determined by trial and error, produces map with expected pixel size
		scale = int(698000000 / math.pow(2, zoom) / self.extra_zoom + 0.5)

		print "SVG layer: scale:", scale
		cachefile = os.path.join(self.cache_dir, "%f_%f_%f_%f_%d.svg" % (bbox.min_lon, bbox.min_lat, bbox.max_lon, bbox.max_lat, scale))
		cachefile_age = file_age_in_days(cachefile)

		# Download the SVG file if we do not have it already in the cache.
		if cachefile_age is None or cachefile_age > 30:
			self.feedback.progress(0, 2, _("Requesting SVG file"))

			# FIXME: gzip compression not supported
			# See: http://love-python.blogspot.com/2008/07/accept-encoding-gzip-to-make-your.html?m=1
			url = self.url_template % (bbox.min_lon, bbox.min_lat, bbox.max_lon, bbox.max_lat, scale)
			response = simple_urlopen(url, extra_headers={'Cookie':'_osm_totp_token=384781'})

			content_type = response.getheader("content-type")
			if content_type != "image/svg+xml":
				raise AssertionError("Unsupported content-type: %s" % content_type)

			content_length = int(response.getheader("content-length"))
			print "content-length:", content_length

			content_encoding = response.getheader("content-encoding")
			#if content_encoding != "gzip":
			#	raise AssertionError("Unsupported content-encoding: %s" % content_encoding)

			fh = SaveAtomically(cachefile)
			count = 0
			while True:
				self.containing_map.feedback.progress(float(count) / float(content_length), 2, _("Downloading SVG file"))
				data = response.read(0x10000)
				if data == "":
					break
				fh.write(data)
				count += len(data)
			fh.close()

		# Load the SVG file into memory.
		self.svg = rsvg.Handle()
		#ifh = gzip.GzipFile(cachefile, "r")	
		ifh = open(cachefile, "r")	
		for line in ifh:
			# remove background color
			if line.startswith("<rect"):
				continue

			# Alter colors
			line = self.rgb_pattern.sub(lambda m: self.xlate.get(m.group(0),m.group(0)), line)

			self.svg.write(line)			# FIXME: error checking is missing
		if not self.svg.close():
			raise AssertionError("Failed to load SVG file: %s" % cachefile)

		print "SVG layer: map dimensions:", self.containing_map.width, self.containing_map.height
		width, height = self.svg.get_dimension_data()[:2]
		print "SVG layer: SVG image dimensions:", width, height
		self.svg_scale = float(self.containing_map.width) / float(width)
		print "SVG layer: svg_scale:", self.svg_scale
		print "done"

	def do_draw(self, ctx):
		print "draw"
		self.containing_map.feedback.progress(1, 2, _("Rendering SVG file"))
		ctx.scale(self.svg_scale, self.svg_scale)
		self.svg.render_cairo(ctx)

