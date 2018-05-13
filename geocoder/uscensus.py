# pykarta/geocoder/uscensus.py
# Copyright 2013--2018, Trinity College Computing Center
# Last modified: 23 April 2018

import json
import urllib
import re

from geocoder_base import GeocoderBase, GeocoderResult
from pykarta.address import disabbreviate_street, disabbreviate_placename

# https://www.census.gov/geo/maps-data/data/geocoder.html
# https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.pdf
class GeocoderUsCensus(GeocoderBase):
	url_method = "https"
	url_server = "geocoding.geo.census.gov"
	url_path = "/geocoder/locations/address"

	# Given a street address, try to find the latitude and longitude.
	def FindAddr(self, address, countrycode=None):
		result = GeocoderResult(address, "UsCensus")

		query = {
			'street': "%s %s" % (address[self.f_house_number], address[self.f_street]),
			'city': address[self.f_city],
			'state': address[self.f_state],
			'benchmark': 'Public_AR_Census2010',
			'vintage': 'Census2010_Census2010',
			'format': 'json'
			}
		response_text = self.get(self.url_path, query=query)
		response = json.loads(response_text)
		response = response['result']
		address_matches = response['addressMatches']
		self.debug(json.dumps(address_matches, indent=4, separators=(',', ': ')))

		if len(address_matches) != 1:
			self.debug("  %d matches!" % len(address_matches))
			for address_match in address_matches:
				result.alternative_addresses.append(address_match['matchedAddress'])
		else:
			matched_address = address_matches[0]['matchedAddress']
			coordinates = address_matches[0]['coordinates']
			m = re.match(r"^(\d+) ([^,]+), ([^,]+), ([A-Z][A-Z])", matched_address)
			if not m:
				self.debug("  Failed to parse matched address: %s" % matched_address)
			else:
				found_addr_list = (
					('house_number', m.group(1)),
					('street', disabbreviate_street(m.group(2))),
					('city', disabbreviate_placename(m.group(3))),
					('state', m.group(4)),
					)
				if self.result_truly_matches(address, found_addr_list):
					result.coordinates = (coordinates['y'], coordinates['x'])
					result.precision = "INTERPOLATED"
					result.postal_code = address_matches[0]['addressComponents']['zip']
				else:
					self.debug("  Inexact match")
					result.alternative_addresses.append(matched_address)

		if result.coordinates is None:
			self.debug("  No match")
		return result

if __name__ == "__main__":
	gc = GeocoderUsCensus()
	gc.debug_enabled = True
	print gc.FindAddr(["300","Summit Street","","Hartford","CT","06106"])


