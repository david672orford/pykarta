import os
import csv

class FIPS(object):
	def __init__(self):
		reader = csv.reader(open(os.path.join(os.path.dirname(__file__), "national_county.txt")))
		self.county2fips = county2fips = {}
		self.fips2county = fips2county = {}
		for state, state_fips, county_fips, county, mystery_code in reader:
			if state == "State":
				continue
			state_fips = int(state_fips)
			county_fips = int(county_fips)
			county2fips[(state, county)] = (state_fips, county_fips)
			fips2county[(state_fips, county_fips)] = (state, county)

