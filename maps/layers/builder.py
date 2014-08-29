# pykarta/maps/layers/builder.py
# Copyright 2013, 2014, Trinity College
# Last modified: 21 August 2014

from tileset_defs import tilesets
import tileset_defs_raster
import tileset_defs_vector

def MapLayerBuilder(layer_name):
	if layer_name == "osm-default-svg":
		from pykarta.maps.layers.osm_svg import MapLayerSVG
		layer_obj = MapLayerSVG(layer_name, extra_zoom=2.0)
	elif layer_name.startswith("screen-"):
		from pykarta.maps.layers.screen import MapScreenLayer
		layer_obj = MapScreenLayer(float(layer_name[7:]))
	elif layer_name == "mapquest-traffic":
		from pykarta.maps.layers.mapquest import MapTrafficLayer
		MapTrafficLayer()
	elif layer_name == "tile-debug":
		from pykarta.maps.layers.tile_debug import MapTileLayerDebug
		layer_obj = MapTileLayerDebug()
	elif layer_name.endswith(".mbtiles"):
		from pykarta.maps.layers.tile_mbtiles import MapTileLayerMbtiles
		layer_obj = MapTileLayerMbtiles(layer_name)
	elif layer_name.endswith(".geojson"):
		from pykarta.maps.layers.geojson import MapGeoJSONLayer
		layer_obj = MapGeoJSONLayer(layer_name)
	elif layer_name.endswith(".shp"):
		from pykarta.maps.layers.shapefile import MapShapefileLayer
		layer_obj = MapShapefileLayer(layer_name)
	else:
		from pykarta.maps.layers.tile_http import MapTileLayerHTTP
		layer_name = layer_name.split(",")
		tileset = tilesets[layer_name[0]]
		options = {}
		for option in layer_name[1:]:
			name, sep, value = option.partition("=")
			options[name] = value
		layer_obj = MapTileLayerHTTP(tileset, options)
	return layer_obj
	
