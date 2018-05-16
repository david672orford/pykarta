# pykarta/server/modules/geocoder_parcel.py
# Geocoder gets addresses from the assessor's parcel map
# Last modified: 16 May 2018

import os, urllib, json, time
from pykarta.server.dbopen import dbopen
import threading

thread_data = threading.local()

def application(environ, start_response):
	stderr = environ['wsgi.errors']

	cursor, response_headers = dbopen(environ, "parcels.sqlite")
	if cursor is None:
		start_response("304 Not Modified", response_headers)
		return []

	query_string = urllib.unquote_plus(environ['QUERY_STRING'])
	#stderr.write("QUERY_STRING: %s\n" % query_string)
	house_number, apartment_number, street, town, state, postal_code = json.loads(query_string)

	# Build the query and the list of address elements to be inserted into it
	query = "SELECT centroid FROM parcel_addresses where house_number=? and street=? and city=? and state=?"
	address = [
		house_number,
		street,
		town,
		state
		]
	if postal_code != "":
		query += " and (zip=? OR zip='' OR zip IS NULL)"
		address.append(postal_code)

	# Try for an exact match
	start_time = time.time()
	cursor.execute(query, address)
	#stderr.write("elapsed: %f\n" % (time.time() - start_time))
	row = cursor.fetchone()

	# If nothing found, try a house number two lower on the chance that
	# this is the second apartment in a duplex. The assessor's map
	# supposedly lists only the lowest number in such cases.
	if row is None:
		try:
			address[0] = str(int(address[0]) - 2)
			cursor.execute(query, address)
			row = cursor.fetchone()
		except ValueError:
			pass

	# If one or the other matched,
	if row:
		geometry = json.loads(row[0])
		feature = {
			'type':'Feature',
			'geometry':geometry,
			'properties':{'precision':'LOT'}
			}	
	else:
		feature = None

	start_response("200 OK", response_headers + [
		('Content-Type', 'application/json')
		])
	stderr.write("Result: %s\n" % str(feature))
	return [json.dumps(feature)]

