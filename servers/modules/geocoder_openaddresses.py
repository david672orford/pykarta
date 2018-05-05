# pykarta/servers/modules/geocoder_openaddresses.py
# Geocoder gets addresses from the MassGIS assessor's parcel map
# Last modified: 4 May 2018

import os, urllib, json, time, re
from pyspatialite import dbapi2 as db
import threading

thread_data = threading.local()

def application(environ, start_response):
	stderr = environ['wsgi.errors']

	cursor = getattr(thread_data, 'cursor', None)
	if cursor is None:
		db_filename = environ["DATADIR"] + "/openaddresses.sqlite"
		conn = db.connect(db_filename)
		cursor = conn.cursor()
		thread_data.cursor = cursor

	query_string = urllib.unquote_plus(environ['QUERY_STRING'])
	#stderr.write("QUERY_STRING: %s\n" % query_string)
	house_number, apartment_number, street, town, state, postal_code = json.loads(query_string)

	# Build the query and the list of address elements to be inserted into it
	query = "SELECT longitude, latitude FROM addresses where house_number=? and street=? and town=? and state=?"
	address = [
		house_number,
		street,
		town,
		state
		]
	if postal_code is not None and postal_code != "":
		query += " and (postal_code=? or postal_code is null)"
		address.append(postal_code)

	# Try for an exact match
	#start_time = time.time()
	cursor.execute(query, address)
	#stderr.write("elapsed: %f\n" % (time.time() - start_time))
	row = cursor.fetchone()

	# If nothing found, look for a number range that matches.
	if row is None and re.match(r'^\d+$', house_number):
		query = query.replace(" house_number=? ", " house_number_start <= ? and house_number_end >= ? ")
		house_number = int(house_number)
		address = [house_number, house_number] + address[1:]
		cursor.execute(query, address)
		row = cursor.fetchone()

	# If one or the other matched,
	if row:
		feature = {
			'type':'Feature',
			'geometry':{'type':'Point', 'coordinates':[row[0], row[1]]},
			'properties':{'precision':'ROOF'}
			}	
	else:
		feature = None

	start_response("200 OK", [('Content-Type', 'application/json')])
	stderr.write("Result: %s\n" % str(feature))
	return [json.dumps(feature)]

