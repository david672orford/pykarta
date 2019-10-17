# pykarta/servers/dbopen.py
# Last modified: 17 October 2019

from email.utils import formatdate, parsedate_tz, mktime_tz
import os, time
import sqlite3
import threading

class Databases(threading.local):
	def __init__(self):
		self.databases = {}

databases = Databases()

def dbopen(environ, db_basename):
	stderr = environ['wsgi.errors']

	if not db_basename in databases.databases:
		db_filename = os.path.join(environ["DATADIR"], db_basename)
		stderr.write("Opening database %s...\n" % db_filename)
		stderr.write("db_filename: %s\n" % db_filename)
		conn = sqlite3.connect(db_filename)
		conn.enable_load_extension(True)
		conn.load_extension("mod_spatialite")
		conn.enable_load_extension(False)
		conn.row_factory = sqlite3.Row
		databases.databases[db_basename] = (conn.cursor(), int(os.path.getmtime(db_filename)))
	(cursor, last_modified) = databases.databases[db_basename]

	time_now = time.time()
	response_headers = [
		('Date', formatdate(time_now, usegmt=True)),
        ('Last-Modified', formatdate(last_modified, usegmt=True)),
		('Cache-Control', 'public,max-age=86400'),
		]

	if_modified_since = environ.get("HTTP_IF_MODIFIED_SINCE")
	if if_modified_since is not None:
		stderr.write("If-Modified-Since: %s\n" % if_modified_since)
		stderr.write("Last-Modified: %s\n" % formatdate(last_modified, usegmt=True))
		if_modified_since = mktime_tz(parsedate_tz(if_modified_since))
		if last_modified <= if_modified_since:
			stderr.write("304 Not Modified\n")
			return (None, response_headers)

	return (cursor, response_headers)

