#! /usr/bin/python

# See http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/

import pyproj

p1 = pyproj.Proj(init='epsg:4326')
p2 = pyproj.Proj(init='epsg:3857')
x, y = pyproj.transform(p1, p2, -180.0, 0.0)
print x / 40000000 + 0.5, 0.5 - y / 40000000

