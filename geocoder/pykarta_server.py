# pykarta/geocoder/pykarta_server.py
# Copyright 2013--2018, Trinity College Computing Center
# Last modified: 15 May 2018

from __future__ import print_function
import json
try:
	from urllib import quote_plus
except ImportError:
	from urllib.parse import quote_plus

import pykarta
from .geocoder_base import GeocoderBase, GeocoderResult
from pykarta.misc.http import simple_url_split

class GeocoderPykartaBase(GeocoderBase):
	delay = 0.1
	geocoder_source_name = None
	geocoder_basename = None

	def __init__(self, **kwargs):
		GeocoderBase.__init__(self, **kwargs)
		url = "%s/geocoders/%s" % (pykarta.server_url, self.geocoder_basename)
		self.url_method, self.url_server, self.url_path = simple_url_split(url)

	# Given a street address, try to find the latitude and longitude.
	def FindAddr(self, address, countrycode=None):
		result = GeocoderResult(address, self.geocoder_source_name)

		query = json.dumps([
			address[self.f_house_number],
			address[self.f_apartment],
			address[self.f_street],
			address[self.f_city],
			address[self.f_state],
			address[self.f_postal_code]
			])

		response_text = self.get("%s?%s" % (self.url_path, quote_plus(query)))
		feature = json.loads(response_text.decode("ASCII"))
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
	geocoder_source_name = "Parcel"
	geocoder_basename = "parcel"

class GeocoderOpenAddresses(GeocoderPykartaBase):
	geocoder_source_name = "OpenAddresses"
	geocoder_basename = "openaddresses"

if __name__ == "__main__":
	import time
	for gc in (GeocoderParcel(), GeocoderOpenAddresses()):
		gc.debug_enabled = True
		print(type(gc))
		print(gc.FindAddr(["6","Elm Street","","Westfield","MA","01085"]))
		print()


