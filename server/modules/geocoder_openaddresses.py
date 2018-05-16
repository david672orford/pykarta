# pykarta/server/modules/geocoder_openaddresses.py
# Geocoder gets addresses from the Openaddresses project.
# Last modified: 16 May 2018

import os, urllib, json, time, re
from pykarta.server.dbopen import dbopen
import threading

thread_data = threading.local()

def application(environ, start_response):
	stderr = environ['wsgi.errors']

	cursor, response_headers = dbopen(environ, "openaddresses.sqlite")
	if cursor is None:
		start_response("304 Not Modified", response_headers)
		return []

	query_string = urllib.unquote_plus(environ['QUERY_STRING'])
	house_number, apartment_number, street, city, state, postal_code = json.loads(query_string)

	# Build the query template
	query_template = "SELECT longitude, latitude FROM addresses where {house} and street=? and city=? and region=?"
	address_base = [
		street,
		city,
		state
		]
	if postal_code is not None and postal_code != "":
		query_template += " and (postal_code=? or postal_code is null)"
		address_base.append(postal_code)

	# Result of SQL queries go here.
	row = None

	# If the apartment number is specified in the address, try a search with the exact house number and apartment number.
	if apartment_number:
		cursor.execute(query_template.replace("{house}", "apartment_number=? and house_number=?"), [apartment_number, house_number] + address_base)
		row = cursor.fetchone()

	# If the previous search was not performed or did not produce anything, try without the apartment number.
	if row is None:
		# Try for an exact match 
		#start_time = time.time()
		cursor.execute(query_template.replace("{house}", "house_number=?"), [house_number] + address_base)
		#stderr.write("elapsed: %f\n" % (time.time() - start_time))
		row = cursor.fetchone()

	# If nothing found, look for an entry which gives a range of house numbers which includes this one.
	if row is None and re.match(r'^\d+$', house_number):
		house_number = int(house_number)
		cursor.execute(query_template.replace("{house}", "house_number_start <= ? and house_number_end >= ?"), [house_number, house_number] + address_base)
		row = cursor.fetchone()

	# If we got a match, insert the latitude and longitude into a GeoJSON point object.
	if row:
		feature = {
			'type':'Feature',
			'geometry':{'type':'Point', 'coordinates':[row[0], row[1]]},
			'properties':{'precision':'ROOF'}
			}	
	else:
		feature = None

	start_response("200 OK", response_headers + [
		('Content-Type', 'application/json')
		])
	stderr.write("Result: %s\n" % str(feature))
	return [json.dumps(feature)]

