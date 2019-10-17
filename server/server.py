#! /usr/bin/python
# pykarta/server/server.py
# Server for use of PyKarta appliations. Provides geocoding and vector map tiles.
# Last modified: 17 October 2019

import re, os

try:
	import pykarta
except ImportError:
	import sys
	sys.path.insert(1, "../..")

# Import data data provider modules
from pykarta.server.modules.not_found import application as app_not_found
from pykarta.server.modules.geocoder_parcel import application as app_geocoder_parcel
from pykarta.server.modules.geocoder_openaddresses import application as app_geocoder_openaddresses
from pykarta.server.modules.tiles_parcels import application as app_tiles_parcels
from pykarta.server.modules.tiles_osm_vec import application as app_tiles_osm_vec

# Map paths to data provider modules
routes = {
		'geocoders/parcel': app_geocoder_parcel,
		'geocoders/openaddresses': app_geocoder_openaddresses,
		'tiles/parcels': app_tiles_parcels,
		'tiles': app_tiles_osm_vec,
		None: app_not_found,
		}

# WSGI application
def application(environ, start_response):
	stderr = environ['wsgi.errors']

	# In production the server administrator will have set DATADIR.
	if not 'DATADIR' in environ:
		# During testing we use this.
		environ['DATADIR'] = os.environ['HOME'] + "/geo_data/processed"

	# /tiles/<tileset>/
	# /geocoders/<geocoder>/
	m = re.match(r'^/([^/]+)/([^/]+)(.*)$', environ['PATH_INFO'])
	if not m:
		stderr.write("Parse failed: %s\n" % environ['PATH_INFO'])
		app = routes[None]
	else:
		# Level 2 mounts such as /tiles/parcels/
		app = routes.get("%s/%s" % (m.group(1), m.group(2)))
		if app is not None:
			environ['SCRIPT_NAME'] += ("/%s/%s" % (m.group(1), m.group(2)))
			environ['PATH_INFO'] = m.group(3)
		else:
			# Level 1 mounts such as /tiles/
			app = routes.get(m.group(1))
			if app is not None:
				environ['SCRIPT_NAME'] += ("/%s" % m.group(1))
				environ['PATH_INFO'] = ("/%s%s" % (m.group(2), m.group(3)))
			else:
				app = routes[None]
	return app(environ, start_response)

if __name__ == "__main__":
	import sys
	sys.path.insert(1, "../..")
	from werkzeug.serving import run_simple
	run_simple('localhost', 8000, application, threaded=True)

