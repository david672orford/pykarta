#! /usr/bin/python
# Simple WMS server for PyKarta
# Copyright 2014, Trinity College
# Last modified: 8 October 2014

# References:
# * https://github.com/mapnik/OGCServer
# * http://developer.tomtom.com/docs/read/map_toolkit/web_services/wms/GetCapabilities

from werkzeug.wrappers import Request, Response
import cairo
import StringIO
import math
import sys
sys.path.insert(1, "../..")
from pykarta.maps import MapCairo
from pykarta.geometry.projection import unproject_point_mercartor, radius_of_earth

capabilities_response = """
<!DOCTYPE WMT_MS_Capabilities SYSTEM "http://schemas.opengis.net/wms/1.1.1/WMS_MS_Capabilities.dtd">
<WMT_MS_Capabilities version="1.1.1">
	<Service>
		<Name>OGC:WMS</Name>
	</Service>
	<Capability>
		<Request>
			<GetCapabilities>
				<Format>application/vnd.ogc.wms_xml</Format>
				<DCPType>
					<HTTP>
						<Get>
							<OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple" xlink:href="http://localhost:8080/wms?"/>
						</Get>
					</HTTP>
				</DCPType>
			</GetCapabilities>
			<GetMap>
				<Format>image/png</Format>
				<DCPType>
					<HTTP>
						<Get>
							<OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple" xlink:href="http://localhost:8080/wms?"/>
						</Get>
					</HTTP>
				</DCPType>
			</GetMap>
		</Request>
		<Exception>
			<Format>application/vnd.ogc.se_xml</Format>
		</Exception>
		<Layer>
			<Title>OSM Rendered by PyKarta</Title>
			<SRS>EPSG:3857</SRS>
			<LatLonBoundingBox minx="-180" miny="-85.0511287798" maxx="180" maxy="85.0511287798"/>
			<BoundingBox SRS="EPSG:3857" minx="-20037508.34" miny="-20037508.34" maxx="20037508.34" maxy="20037508.34"/>
			<Layer queryable="0" opaque="1">
				<Name>osm-vector</Name>
				<Title>OSM Rendered by PyKarta</Title>
				<BoundingBox SRS="EPSG:4326" minx="-180.0" miny="-85.0511287798" maxx="180.0" maxy="85.0511287798"/>
				<ScaleHint min="0" max="124000"/>
			</Layer>
		</Layer>
	</Capability>
</WMT_MS_Capabilities>
"""

@Request.application
def application(request):
	assert request.args.get("SERVICE") == "WMS"
	wms_request = request.args.get("REQUEST")
	if wms_request == "GetCapabilities":
		response_body = capabilities_response
		return Response(response_body, mimetype='application/vnd.ogc.wms_xml')
	elif wms_request == "GetMap":
		srs = request.args.get("SRS")
		assert srs == "EPSG:3857"
		bbox = request.args.get("BBOX")
		height = int(request.args.get("HEIGHT"))
		width = int(request.args.get("WIDTH"))

		min_x, min_y, max_x, max_y = map(float, bbox.split(","))
		center_x = (min_x + max_x) / 2.0
		center_y = (min_y + max_y) / 2.0
		print "center:", center_x, center_y
		center_lat, center_lon = unproject_point_mercartor(center_x, center_y)
		print "center:", center_lat, center_lon

		width_in_tiles = width / 256.0
		print "width_in_tiles:", width_in_tiles
		bbox_width_in_meters = max_x - min_x
		print "bbox_width_in_meters:", bbox_width_in_meters
		meters_per_tile = bbox_width_in_meters / width_in_tiles
		print "meters_per_tile:", meters_per_tile
		zoom = math.log(radius_of_earth * math.pi * 2.0 / meters_per_tile, 2)
		print "zoom:", zoom

		map_obj = MapCairo(tile_source="osm-vector")
		map_obj.set_size(width, height)
		map_obj.set_center_and_zoom(center_lat, center_lon, zoom)

		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
		ctx = cairo.Context(surface)
		map_obj.draw_map(ctx)

		sio = StringIO.StringIO()
		surface.write_to_png(sio)
		return Response(sio.getvalue(), mimetype='image/png')
	else:
		raise AssertionError("request %s not supported" % request)

if __name__ == "__main__":
	from werkzeug.serving import run_simple
	import __builtin__
	__builtin__.__dict__['_'] = lambda text: text
	run_simple("localhost", 8080, application)

