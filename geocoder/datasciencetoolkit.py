# pykarta/geocoder/datasciencetoolkit.py
# Copyright 2013, 2014, Trinity College Computing Center
# Last modified: 9 October 2014

import json
import urllib

from geocoder_base import GeocoderBase, GeocoderResult
from pykarta.address import disabbreviate_street

# See http://www.datasciencetoolkit.org/developerdocs
class GeocoderDataScienceToolKit(GeocoderBase):
	url_server = "www.datasciencetoolkit.org"
	url_path = "/street2coordinates"
	delay = 1.0		# no more than one request per second

	# Given a street address, try to find the latitude and longitude.
	def FindAddr(self, address, countrycode=None):
		result = GeocoderResult(address, "DSTK")

		query = "%s %s, %s, %s %s" \
				% (address[self.f_house_number], address[self.f_street],
				  address[self.f_town], address[self.f_state], address[self.f_postal_code])
		get_path = "%s/%s" % (self.url_path, urllib.quote_plus(query))

		response_text = self.get(get_path)

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

