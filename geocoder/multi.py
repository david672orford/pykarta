#! /usr/bin/python
# pykarta/geocoder/multi.py
# Copyright 2013, 2014, Trinity College Computing Center
# Last modified: 19 October 2014

import os
from pykarta.misc import file_age_in_days, get_cachedir
from geocoder_base import GeocoderBase, GeocoderResult, GeocoderError

# Import the geocoders
from spreadsheet import GeocoderSpreadsheet
from nominatim import GeocoderNominatim
from parcel import GeocoderParcel
from google import GeocoderGoogle
from bing import GeocoderBing
from massgis import GeocoderMassGIS
from datasciencetoolkit import GeocoderDataScienceToolKit

#=============================================================================
# This geocoder is a wrapper for a list of actual geocoders. It calls them
# in sequence until one of them finds the requested information.
# It also caches the result.
#=============================================================================
class GeocoderMulti(GeocoderBase):

	def __init__(self, **kwargs):
		GeocoderBase.__init__(self, **kwargs)
		self.cache = GeocoderCache()
		self.geocoders = [
			(GeocoderSpreadsheet(**kwargs), True),
			(GeocoderNominatim(**kwargs), False),
			(GeocoderParcel(**kwargs), False),
			(GeocoderBing(**kwargs), False),
			(GeocoderGoogle(**kwargs), False),
			(GeocoderMassGIS(**kwargs), True),
			#(GeocoderDataScienceToolKit(**kwargs), True),
			]

	# Query the geocoders and cache the answers
	def FindAddr(self, address, countrycode=None, bypass_cache=False):
		self.debug("======== %s ========" % str(address))

		if not bypass_cache:
			result = self.cache.FindAddr(address, countrycode=countrycode)
			if result.coordinates is not None:
				return result

		result = GeocoderResult(address, "None")
		should_cache = False

		# Run each geocoder in turn until we find a good-quality match.
		# If all we can get is an interpolated match, take the first one.
		best = None
		i = 0
		for geocoder, stop_on_interpolated in self.geocoders:
			self.debug("Trying:", geocoder.name)
			self.progress(i, len(self.geocoders), _("Trying %s...") % geocoder.name)
			iresult = geocoder.FindAddr(address, countrycode=countrycode)
			if iresult.coordinates is not None:
				best = (geocoder, iresult)
				if stop_on_interpolated or iresult.precision != "INTERPOLATED":
					break		# good enough
			else:
				result.alternative_addresses.extend(iresult.alternative_addresses)
			self.debug("")
			i += 1

		if best is not None:
			geocoder, iresult = best
			self.debug("Best result given by %s" % geocoder.name)
			result.postal_code = iresult.postal_code
			result.coordinates = iresult.coordinates
			result.precision = iresult.precision
			result.source = iresult.source
			should_cache = geocoder.should_cache()

		# Store the result.
		if should_cache:
			self.cache.store(result)

		self.debug("\n")
		return result

	# Like FindAddr() but rather than returning the best result,
	# it returns all of the results.
	def FindAddrAll(self, address, countrycode=None):
		results = []
		for geocoder in self.geocoders:
			self.debug("====================================================")
			self.debug("Trying:", geocoder.name)
			result = geocoder.FindAddr(address, countrycode=countrycode)
			if result.coordinates is not None:
				results.append(result)
		return results

#=============================================================================
# This geocoder is used to return results from the cache.
#=============================================================================
class GeocoderCache(GeocoderBase):

	def __init__(self):
		self.cachedir = os.path.join(get_cachedir(), "geocoder")
		if not os.path.exists(self.cachedir):
			os.makedirs(self.cachedir)	

	def cachefile_name(self, address):
		formated_address = "%s %s, %s, %s %s" \
			% (address[self.f_house_number], address[self.f_street],
			  address[self.f_town], address[self.f_state], address[self.f_postal_code]
			)
		return "%s/%s" % (self.cachedir, formated_address.replace("/", "_"))

	def FindAddr(self, address, countrycode=None):	# FIXME: countrycode is ignored
		result = GeocoderResult(address, "Cache")

		cachefile_name = self.cachefile_name(address)
		cachefile_age = file_age_in_days(cachefile_name)
		if cachefile_age and cachefile_age < 30:
			fh = open(cachefile_name, "r")
			cached_answer = fh.read()
			fh.close()
			self.debug("  Using %.1f day old answer from cache." % cachefile_age)
			try:
				lines = cached_answer.splitlines()
				if len(lines) != 1:
					raise AssertionError
				lat, lon, result.precision, result.source = lines[0].split(",")
				result.coordinates = (float(lat), float(lon))
			except:
				self.debug("  Bad cache entry")

		if result.coordinates is None:
			self.debug("  No match")
		return result

	def store(self, result):
		cachefile = open(self.cachefile_name(result.query_address), "w")
		if result:	
			self.debug("  Storing new result in cache.")
			cachefile.write("%s,%s,%s,%s\n" % (repr(result.coordinates[0]), repr(result.coordinates[1]), result.precision, result.source))
		else:
			self.debug("  Storing empty result in cache.")
		cachefile.close()

#=============================================================================
# Test
#=============================================================================
if __name__ == "__main__":
	import csv
	from pykarta.formats.gpx_writer import GpxWriter

	reader = csv.reader(open("test.csv","r"))
	writer = GpxWriter(open("test.gpx","w"), "Geocoder Test")

	geocoder = GeocoderMulti()
	geocoder.debug_enabled = True

	for address in reader:
		for result in geocoder.FindAddrAll(address, countrycode="US"):
			writer.write_wpt(
				result.coordinates[0], result.coordinates[1],
				name="%s %s (%s)" % (address[0], address[1], result.source),
				sym="Pin, Red",
				)

