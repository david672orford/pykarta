#! /usr/bin/python
# pykarta/geocoder/nominatim.py
# Copyright 2013--2018, Trinity College Computing Center
# Last modified: 20 May 2018

from __future__ import print_function

import xml.etree.cElementTree as ET
import json

from pykarta.geocoder.geocoder_base import GeocoderBase, GeocoderResult, GeocoderError
from pykarta.address import abbreviate_state
from pykarta.geometry import Point, Polygon, BoundingBox

# See http://wiki.openstreetmap.org/wiki/Nominatim
class GeocoderNominatim(GeocoderBase):

	url_method = "https"
	url_server = "nominatim.openstreetmap.org"
	url_path = "/search"
	url_path_reverse = "/reverse"
	delay = 1.0	# one request per second

	xlate = {
		'road': 'street',
		'postcode': 'postal_code',
		}

	#-------------------------------------------------------------------
	# Given a street address, try to find the latitude and longitude.
	#-------------------------------------------------------------------
	def FindAddr(self, address, countrycode=None):
		result = GeocoderResult(address, "Nominatim")
	
		query_hash = {
			'format': 'xml',
			'addressdetails': '1',
			'polygon': '1',
			# For 2071 Riverdale Street, West Springfield, MA 01089 including the ZIP code makes the results worse.
			#'q': "%s %s, %s, %s %s" % (address[self.f_house_number], address[self.f_street], address[self.f_city], address[self.f_state], address[self.f_postal_code])
			'q': (u"%s %s, %s, %s" % (address[self.f_house_number], address[self.f_street], address[self.f_city], address[self.f_state])).encode("utf-8")
			}
		if countrycode is not None:
			query_hash['countrycodes'] = countrycode

		resp_text = self.get(self.url_path, query=query_hash)
		#print(resp_text)
		try:
			tree = ET.XML(resp_text)
		except:
			self.debug("  Invalid response")
			return result

		# Examine the condidate matches
		for place in tree.findall("place"):
			self.debug("  Candidate: %s" % place.get("display_name"))
			osm_type = (place.get("osm_type"), place.get("class"), place.get("type"))
			self.debug("    osm_type: %s" % str(osm_type))

			found_address_list = []
			found_address_dict = {}
			for i in list(place):
				comp_type = i.tag
				comp_name = i.text
				comp_type = self.xlate.get(comp_type, comp_type)
				if comp_type == "state":
					comp_name = abbreviate_state(comp_name)
				self.debug("    %s: %s" % (comp_type, comp_name))
				found_address_list.append((comp_type, comp_name))
				found_address_dict[comp_type] = comp_name

			if self.result_truly_matches(address, found_address_list):
				self.debug("  Match")
				result.coordinates = (float(place.get('lat')), float(place.get('lon')))
				if osm_type == ("node","place","house"):
					result.precision = "ENTRANCE"
				elif osm_type == ("way","building","yes"):
					result.precision = "ROOF"
				else:							# TIGER interpolation?
					result.precision = "INTERPOLATED"
				break
			else:
				self.debug("    (Partial match)")
				result.add_alternative_address(found_address_dict)

		if result.coordinates is None:
			self.debug("  No match")
		return result

	#-------------------------------------------------------------------
	# Given an address down to street level, try to find the street and
	# return a polygon which encloses it which can be used for
	# highlighting it on a map.	
	#-------------------------------------------------------------------
	def FindStreet(self, street, city, state, countrycode=None):
		self.debug("Search for: %s, %s, %s" % (street, city, state))

		query_hash = {
			'format': 'xml',
			'polygon': '1',
			'addressdetails': '1',
			'q': "%s,%s,%s" % (street, city, state)
			}
		if countrycode != None:
			query_hash['countrycodes'] = countrycode

		resp_text = self.get(self.url_path, query=query_hash)
		#print(resp_text)
		tree = ET.XML(resp_text)

		# Examine the candidate matches
		# FIXME: we should combine the component parts of a road
		answer = None
		for place in tree.findall("place"):
			self.debug("  Candidate: %s" % place.get("display_name"))
			osm_type = place.get("osm_type")
			self.debug("    osm_type: %s" % osm_type)
			osm_class = place.get("class")
			self.debug("    class: %s" % osm_class)

			found_address = []
			for i in list(place):
				self.debug("    %s: %s" % (i.tag, i.text))
				found_address.append([i.tag, i.text])

			if self.result_city_matches(city, found_address) and osm_type == "way" and osm_class == "highway":
				self.debug("  Match")
				bbox = self.place_bbox(place)
				answer = {
					'lat' : float(place.get('lat')),
					'lon' : float(place.get('lon')),
					'bbox' : bbox,
					'polygon' : self.place_polygon(place, bbox),
					'highway' : place.get('type'),
					'display_name' : place.get('display_name')
					}
				break

		self.debug("")
		return answer

	#-------------------------------------------------------------------
	# Given a city and state name, try to find information about it.
	#-------------------------------------------------------------------
	def FindCity(self, city, state, countrycode=None):
		self.debug("Search for: %s, %s" % (city, state))

		query_hash = {
			'format': 'xml',
			'polygon': '1',
			'addressdetails': '1',
			'q': "%s,%s" % (city, state)
			}
		if countrycode != None:
			query_hash['countrycodes'] = countrycode

		resp_text = self.get(self.url_path, query=query_hash)
		#print(resp_text)
		tree = ET.XML(resp_text)

		# Examine the candidate matches
		answer_boundary = None
		answer_place = None
		for place in tree.findall("place"):
			self.debug("  Candidate: %s" % place.get("display_name"))
			place_class = place.get('class')
			self.debug("    class: %s" % place_class)
			self.debug("    type: %s" % place.get('type'))
			self.debug("    boundingbox: %s" % str(place.get('boundingbox')))
			county = None
			for i in list(place):
				self.debug("    %s: %s" % (i.tag, i.text))
				if i.tag == "county":
					county = i.text
			bbox = self.place_bbox(place)
			answer = {
				'lat' : float(place.get('lat')),
				'lon' : float(place.get('lon')),
				'polygon': self.place_polygon(place, bbox),
				'bbox' : bbox,
				'county': county
				}
			if place_class == 'boundary':		# city border
				answer_boundary = answer
			elif place_class == 'place':		# city center
				answer_place = answer	

		if answer_boundary:
			return answer_boundary
		else:
			return answer_place		# may be None

	#-------------------------------------------------------------------
	# Find the address (likely without house number) closest to the 
	# indicated latitude and longitude.
	#-------------------------------------------------------------------
	def Reverse(self, lat, lon):
		self.debug("Search for: (%f, %f)" % (lat, lon))

		resp_text = self.get(self.url_path_reverse, query={
			'format': 'xml',
			'zoom': '18',
			'addressdetails': '1',
			'lat': repr(lat),
			'lon': repr(lon),
			})
		#print(resp_text)
		tree = ET.XML(resp_text)

		address = tree.find("addressparts")
		if address:
			self.debug("  Answer:")
			parts = {}
			for i in list(address):
				self.debug("    %s = %s" % (i.tag, i.text))
				parts[i.tag] = i.text
			return parts
		else:
			self.debug("  Not found")
			return None

	@staticmethod
	def place_bbox(place):
		min_lat, max_lat, min_lon, max_lon = map(lambda i: float(i), (place.get('boundingbox')).split(','))
		return BoundingBox((min_lon, min_lat, max_lon, max_lat))

	@staticmethod
	def place_polygon(place, bbox):
		polygonpoints = place.get('polygonpoints')
		if polygonpoints is not None:
			return Polygon(map(lambda i: Point(float(i[1]), float(i[0])), json.loads(polygonpoints)[:-1]))

		# Sometime around January 2011 Nominatim stopped returning polygons for some objects.
		# If there is no polygon, make one out of the bounding box.
		else:
			p = BoundingBox(bbox)
			p.scale(1.05)
			return p.as_polygon()

#=============================================================================
# Tests
# Covers things not covered in multi.py tests.
#=============================================================================
if __name__ == "__main__":
	import os
	import sys

	nominatim = GeocoderNominatim()
	nominatim.debug_enabled = True

	action = sys.argv[1] if len(sys.argv) >= 2 else None
	if action == "FindStreet":
		#result = nominatim.FindStreet("Falley Drive", "Westfield", "MA", countrycode="US")
		result = nominatim.FindStreet("Union Street", "Westfield", "MA", countrycode="US")
		print(result)

	elif action == "FindTown":
		result = nominatim.FindTown("Feeding Hills", "MA", countrycode="US")
		print(result)

	elif action == "Reverse":
		result = nominatim.Reverse(42.103923797607422, -72.634140014648438)
		print(result)

	else:
		#print(nominatim.FindAddr(["300","Summit Street","","Hartford","CT","06106"]))		# amenity point
		#print(nominatim.FindAddr(["15","Steiger Drive","","Westfield","MA","01085"]))		# non-existent address
		#print(nominatim.FindAddr(["151","Steiger Drive","","Westfield","MA","01085"]))		# address on building outline
		#print(nominatim.FindAddr(["11","Steiger Drive","","Westfield","MA","01085"]))		# address on building entrance
		print(nominatim.FindAddr(["11","Steiger Street","","Westfield","MA","01085"]))		# street name incorrect

