# pykarta/geocoder/pykarta.py
# Copyright 2013--2018, Trinity College Computing Center
# Last modified: 26 April 2018

import json
import urllib

import pykarta
from geocoder_base import GeocoderBase, GeocoderResult
from pykarta.misc.http import simple_url_split

class GeocoderPykartaBase(GeocoderBase):
	delay = 0.1
	name = "Openaddress"
	filename = "openaddress1"

	def __init__(self, **kwargs):
		GeocoderBase.__init__(self, **kwargs)
		url = "%s/geocoders/%s" (pykarta.server_url, self.filename)
		self.url_method, self.url_server, self.url_path = simple_url_split(url)

	# Given a street address, try to find the latitude and longitude.
	def FindAddr(self, address, countrycode=None):
		result = GeocoderResult(address, self.name)

		query = json.dumps([
			address[self.f_house_number],
			address[self.f_apartment_number],
			address[self.f_street],
			address[self.f_town],
			address[self.f_state],
			address[self.f_postal_code]
			])

		response_text = self.get("%s?%s" % (self.url_path, urllib.quote_plus(query)))
		feature = json.loads(response_text)
		self.debug_indented(json.dumps(feature, indent=4, separators=(',', ': ')))

		if feature is not None and feature['type'] == 'Feature':
			geometry = feature['geometry']
			assert geometry['type'] == 'Point'
			coordinates = geometry['coordinates']
			result.coordinates = (coordinates[1], coordinates[0])
			result.precision = feature['properties']['precision']

		if result.coordinates is None:
			self.debug("  No match")
		return result

	# It is worth caching the results of this geocoder?
	def should_cache(self):
		return True

class GeocoderParcel(GeocoderPykartaBase):
	name = "Parcel"
	filename = "parcel1"

class GeocoderOpenaddress(GeocoderPykartaBase):
	name = "Openaddress"
	filename = "openaddress1"

if __name__ == "__main__":
	import time
	gc = GeocoderParcel()
	gc.debug_enabled = True
	print gc.FindAddr(["6","Elm Street","","Westfield","MA","01085"])


