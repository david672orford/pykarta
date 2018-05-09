from email.utils import formatdate, parsedate_tz, mktime_tz
import os, time
from pyspatialite import dbapi2 as db
import threading

thread_data = threading.local()

def dbopen(environ, db_basename):
	stderr = environ['wsgi.errors']

	cursor = getattr(thread_data, 'cursor', None)
	if cursor is None:
		db_filename = os.path.join(environ["DATADIR"], db_basename)
		thread_data.last_modified = int(os.path.getmtime(db_filename))
		conn = db.connect(db_filename)
		conn.row_factory = db.Row
		cursor = conn.cursor()
		thread_data.cursor = cursor

	time_now = time.time()
	response_headers = [
		('Date', formatdate(time_now, usegmt=True)),
        ('Last-Modified', formatdate(thread_data.last_modified, usegmt=True)),
		('Cache-Control', 'public,max-age=86400'),
		]

	if_modified_since = environ.get("HTTP_IF_MODIFIED_SINCE")
	if if_modified_since is not None:
		stderr.write("If-Modified-Since: %s\n" % if_modified_since)
		stderr.write("Last-Modified: %s\n" % formatdate(thread_data.last_modified, usegmt=True))
		if_modified_since = mktime_tz(parsedate_tz(if_modified_since))
		if thread_data.last_modified <= if_modified_since:
			stderr.write("304 Not Modified\n")
			return (None, response_headers)

	return (cursor, response_headers)

