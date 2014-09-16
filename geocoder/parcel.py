# pykarta/geocoder/parcel.py
# Copyright 2013, 2014, Trinity College Computing Center
# Last modified: 16 September 2014

import json
import urllib

from geocoder_base import GeocoderBase, GeocoderResult

class GeocoderParcel(GeocoderBase):
	def __init__(self, **kwargs):
		GeocoderBase.__init__(self, **kwargs)
		self.url_server = "geocoders.osm.trincoll.edu"
		self.url_path = "/parcel1"
		self.delay = 0.1	# ten requests per second

	# Given a street address, try to find the latitude and longitude.
	def FindAddr(self, address, countrycode=None):
		result = GeocoderResult(address, "Parcel")

		query = json.dumps([
			address[self.f_house_number],
			address[self.f_street],
			address[self.f_town],
			address[self.f_state],
			address[self.f_postal_code]
			])

		feature = json.loads(self.get("%s?%s" % (self.url_path, urllib.quote_plus(query))))
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

if __name__ == "__main__":
	gc = GeocoderParcel()
	gc.debug_enabled = True
	print gc.FindAddr(["61","Steiger Drive","","Westfield","MA","01085"])
	#print gc.FindAddr(["63","Steiger Drive","","Westfield","MA","01085"])


