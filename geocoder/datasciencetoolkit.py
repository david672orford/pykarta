# pykarta/geocoder/datasciencetoolkit.py
# Copyright 2013, 2014, 2015, Trinity College Computing Center
# Last modified: 8 February 2015

import json
import urllib

from geocoder_base import GeocoderBase, GeocoderResult
from pykarta.address import disabbreviate_street

# See http://www.datasciencetoolkit.org/developerdocs
class GeocoderDataScienceToolKit(GeocoderBase):

	def __init__(self, instance="official", **kwargs):
		GeocoderBase.__init__(self, **kwargs)
		if instance == "official":
			self.url_server = "www.datasciencetoolkit.org"
			self.url_path = "/street2coordinates"
			self.delay = 1.0		# no more than one request per second
		elif instance == "trincoll":
			self.url_server = "geocoders.osm.trincoll.edu"
			self.url_path = "/street2coordinates"
			self.delay = 0.1
		else:
			raise ValueError

	# Given a street address, try to find the latitude and longitude.
	def FindAddr(self, address, countrycode=None):
		result = GeocoderResult(address, "DSTK")

		query = "%s %s, %s, %s %s" % (
			address[self.f_house_number],
			address[self.f_street],
			address[self.f_town],
			address[self.f_state],
			address[self.f_postal_code]
			)
		#get_path = "%s/%s" % (self.url_path, urllib.quote_plus(query.encode("utf-8"), safe=""))
		#response_text = self.get(get_path)
		response_text = self.get(self.url_path, method="POST", query=json.dumps([query]))

		response = json.loads(response_text)
		response = response[query]	# keyed by sought address
		self.debug(json.dumps(response, indent=4, separators=(',', ': ')))

		if response is not None and response['street_number'] is not None:
			found_addr_list = (
				('house_number',response['street_number']),
				('street',disabbreviate_street(response['street_name'])),
				('town',response['locality']),
				('state',response['region']),
				)
			#if response['confidence'] == 1.0:
			if self.result_truly_matches(address, found_addr_list):
				result.coordinates = (response['latitude'], response['longitude'])
				result.precision = "INTERPOLATED"
			else:
				result.alternative_addresses.append(", ".join(map(lambda i: response[i], ("street_number","street_name","locality","region"))))

		if result.coordinates is None:
			self.debug("  No match")
		return result

if __name__ == "__main__":
	gc = GeocoderDataScienceToolKit(instance="trincoll")
	gc.debug_enabled = True
	print gc.FindAddr(["300","Summit Street","","Hartford","CT","06106"])

