# encoding=utf-8
# pykarta/geometry/text.py
# Copyright 2013--2018, Trinity College
# Last modified: 15 May 2018

import re
from . import Point

# Create a Point() from a text string describing a latitude and longitude
#
# Example from Wikipedia article Whitehouse: 38° 53′ 51.61″ N, 77° 2′ 11.58″ W
# \u2032 -- prime (minutes sign)
# \u2033 -- double prime (seconds sign)
# \u2019 -- single closing quote
# \u201d -- double closing quote
def PointFromText(coords_text):
	if not re.search(u'^[\(\-0-9\.°\'\u2019\u2032"\u201d\u2033NSEW, \)]+$', coords_text, flags=re.IGNORECASE):
		return None

	#print "Pasted coordinates:", coords_text

	# Make more standard
	coords_text = coords_text.upper()
	coords_text = coords_text.replace(u"(", u"")
	coords_text = coords_text.replace(u")", u"")
	
	coords_text = coords_text.replace(u"'", u"\u2032")		# ASCII single quote (apostroph) to prime
	coords_text = coords_text.replace(u"\u2019", u"\u2032")	# right single quote to prime
	coords_text = coords_text.replace(u'"', u'\u2033')		# ASCII double quote to double prime
	coords_text = coords_text.replace(u'\u201d', u'\u2033')	# right double quote to double prime

	words = _split_coords_text(coords_text)
	lat = _parse_degrees(words[0], "NS")
	lon = _parse_degrees(words[1], "EW")
	return Point(lat, lon)

def _split_coords_text(coords_text):
	m = re.match('^(\S+)\s+(\S+)$', coords_text)
	if m:
		return (m.group(1), m.group(2))

	m = re.match('^([^,]+),([^,]+)$', coords_text)
	if m:
		return (m.group(1), m.group(2))

	m = re.match('^([NS].+)([EW].+)$', coords_text)
	if m:
		return (m.group(1), m.group(2))

	m = re.match('^(.+[NS])(.+[EW])$', coords_text)
	if m:
		return (m.group(1), m.group(2))

	raise Exception("Two coordinates required")

def _parse_degrees(degrees_string, directions):
	degrees_string = degrees_string.replace(u" ", u"")			# remove spaces

	sign = 1.0
	if directions[0] in degrees_string:		# N or E
		degrees_string = degrees_string.replace(directions[0], "")
	elif directions[1] in degrees_string:	# S or W
		degrees_string = degrees_string.replace(directions[1], "")
		sign = -1.0

	# Decimal degrees signed
	m = re.search(u'^([-\d\.]+)°?$', degrees_string)
	if m:
		return float(m.group(1)) * sign

	# Degrees, minutes, seconds
	m = re.search(u'^(\d+)°(\d+)\u2032([\d\.]+)\u2033$', degrees_string)
	if m:
		degrees = int(m.group(1))
		degrees += int(m.group(2)) / 60.0
		degrees += float(m.group(3)) / 3600.0
		return degrees * sign

	m = re.search(u'^(\d+)°([\d\.]+)\u2032?$', degrees_string)
	if m:
		degrees = int(m.group(1))
		degrees += float(m.group(2)) / 60.0
		return degrees * sign

	raise Exception("Failed to parse coordinate: %s" % degrees_string)

