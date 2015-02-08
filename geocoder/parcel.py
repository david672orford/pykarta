# pykarta/geocoder/parcel.py
# Copyright 2013, 2014, 2015, Trinity College Computing Center
# Last modified: 7 Feburary 2015

import json
import urllib

from geocoder_base import GeocoderBase, GeocoderResult

class GeocoderParcel(GeocoderBase):
	url_server = "geocoders.osm.trincoll.edu"
	url_path = "/parcel1"
	delay = 0.1

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

if __name__ == "__main__":
	import time
	gc = GeocoderParcel()
	gc.debug_enabled = True
	print gc.FindAddr(["61","Steiger Drive","","Westfield","MA","01085"])
	print gc.FindAddr(["61","Steiger Drive","","Westfield","MA","01085"])
	print gc.FindAddr(["61","Steiger Drive","","Westfield","MA","01085"])
	print gc.FindAddr(["61","Steiger Drive","","Westfield","MA","01085"])
	print gc.FindAddr(["61","Steiger Drive","","Westfield","MA","01085"])
	#time.sleep(4.9)
	#print gc.FindAddr(["63","Steiger Drive","","Westfield","MA","01085"])
	#print gc.FindAddr(["65","Steiger Drive","","Westfield","MA","01085"])


