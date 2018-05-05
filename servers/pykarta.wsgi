#! /usr/bin/python
# pykarta/servers/pykarta.wsgi

import re, os

from pykarta.servers.modules.not_found import application as app_not_found
from pykarta.servers.modules.hello import application as app_hello

from pykarta.servers.modules.geocoder_parcel import application as app_geocoder_parcel
from pykarta.servers.modules.geocoder_openaddresses import application as app_geocoder_openaddresses

from pykarta.servers.modules.tiles_parcels import application as app_tiles_parcels
from pykarta.servers.modules.tiles_osm_vec import application as app_tiles_osm_vec

routes = {
		'geocoders/parcel': app_geocoder_parcel,
		'geocoders/openaddresses': app_geocoder_openaddresses,
		'tiles/parcels': app_tiles_parcels,
		'tiles': app_tiles_osm_vec,
		'hello': app_hello,
		}

def application(environ, start_response):
	stderr = environ['wsgi.errors']
	stderr.write("\n")

	environ['DATADIR'] = os.environ['HOME'] + "/geo_data/processed"

	m = re.match(r'^/([^/]+)/([^/]+)(.*)$', environ['PATH_INFO'])
	if not m:
		stderr.write("Parse failed: %s\n" % environ['PATH_INFO'])
		app = app_not_found
	else:
		stderr.write("groups: %s %s %s\n" % m.groups())
		app = routes.get("%s/%s" % (m.group(1), m.group(2)))
		if app is not None:
			environ['SCRIPT_NAME'] += ("/%s/%s" % (m.group(1), m.group(2)))
			environ['PATH_INFO'] = m.group(3)
		else:
			app = routes.get(m.group(1))
			if app is not None:
				environ['SCRIPT_NAME'] += ("/%s" % m.group(1))
				environ['PATH_INFO'] = ("/%s%s" % (m.group(2), m.group(3)))
			else:
				app = app_not_found
	return app(environ, start_response)

if __name__ == "__main__":
	#from wsgiref.simple_server import make_server
	#httpd = make_server('', 8000, application)
	#print("Serving HTTP on port 8000...")
	#httpd.serve_forever()
	from werkzeug.serving import run_simple
	run_simple('localhost', 8000, application, threaded=True)

