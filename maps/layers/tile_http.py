# encoding=utf-8
# pykarta/maps/layers/tile_http.py
# Copyright 2013, 2014, Trinity College
# Last modified: 15 October 2014

import os
import errno
import random
import httplib
import threading
import time
import socket
import gobject
#import weakref

from pykarta.misc.http import http_date
from pykarta.maps.layers.base import MapTileLayer, MapRasterTile, MapCustomTile
from pykarta.misc import file_age_in_days, BoundMethodProxy, NoInet, tile_count, SaveAtomically

#=============================================================================
# TMS tile layer loaded over HTTP
#=============================================================================
class MapTileLayerHTTP(MapTileLayer):
	def __init__(self, tileset, options={}):
		MapTileLayer.__init__(self)
		self.tileset = tileset
		self.cache_enabled = tileset.layer_cache_enabled
		self.zoom_substitutions = tileset.zoom_substitutions
		self.tileset_online_init_called = False

		# For vector tiles, set up renderer.
		self.renderer = tileset.renderer
		if "renderer" in options:
			self.renderer = tileset.renderers[options["renderer"]]
		if self.renderer:
			self.draw_passes = self.renderer.draw_passes

		# How long (in milliseconds) to wait after receiving a tile
		# for the next one to arrive before redrawing
		self.tile_wait = 200

		self.downloader = None
		self.timer = None
		self.missing_tiles = {}
		self.redraw_needed = False
		self.tile_ranges = None

	# Hook set_map() so that when this layer is added to the map it
	# can create a tile downloader and set it to either syncronous mode or 
	# asyncronous mode depending on whether we are doing this for print
	# or for the screen (where lazy tile loading is disirable).
	def set_map(self, containing_map):
		MapTileLayer.set_map(self, containing_map)

		# If this tileset has not yet had a chance to download metadata and
		# we are currently online, give it that chance now.
		if not self.containing_map.offline and not self.tileset_online_init_called:
			self.tileset.online_init()
			self.tileset_online_init_called = True

		# Copy metadata from the tileset to the layer.
		self.zoom_min = self.tileset.zoom_min
		self.zoom_max = self.tileset.zoom_max
		self.overzoom = self.tileset.overzoom
		self.attribution = self.tileset.attribution

		# If we are offline, create an object which can only find tiles in the cache.
		# If we are online, create an object which can also download tiles.
		if self.containing_map.offline:
			self.downloader = MapTileCacheLoader(
				self.tileset,
				self.containing_map.tile_cache_basedir,
				#feedback=weakref.proxy(self.feedback),
				feedback=self.feedback,
				)
		else:
			self.downloader = MapTileDownloader(
				self.tileset,
				self.containing_map.tile_cache_basedir,
				#feedback=weakref.proxy(self.feedback),
				feedback=self.feedback,
				done_callback=BoundMethodProxy(self.tile_loaded_cb) if self.containing_map.lazy_tiles else None,
				)

		# The RAM cache may reflect absence of tiles. Dump it.
		self.ram_cache.clear()

	# Return the indicated tile as a Cairo surface or None
	# if it is not (yet) available.
	def load_tile(self, zoom, x, y, may_download):
		filename, pending = self.downloader.load_tile(zoom, x, y, may_download)
		if pending:
			self.missing_tiles[zoom] = self.missing_tiles.get(zoom, 0) + 1
		if filename is not None:
			if self.renderer is not None:
				return MapCustomTile(self, filename, zoom, x, y)
			else:
				try:
					return MapRasterTile(self, filename=filename)
				except:
					self.feedback.debug(1, " defective tile file: %s" % filename)
		return None

	# The tile downloader calls this when the tile has been received
	# and is waiting in the disk cache. Note that it is called from
	# the downloader thread, so we have to schedual the work
	# in the gobject event loop. We set the priority high so that
	# these messages will be delivered before redraw requests.
	def tile_loaded_cb(self, *args):
		gobject.idle_add(lambda: self.tile_loaded_cb_idle(*args), priority=gobject.PRIORITY_HIGH)
	def tile_loaded_cb_idle(self, zoom, x, y, modified):
		self.feedback.debug(2, "Tile received: %d %d,%d %s" % (zoom, x, y, str(modified)))

		# If the tile was modified, dump it from the RAM cache whether
		# it is still needed or not.
		if modified:
			self.ram_cache_invalidate(zoom, x, y)

		# If this tile is still needed.
		if self.tile_in_view(zoom, x, y):
			self.feedback.debug(5, " Still needed")

			if modified:
				self.redraw_needed = True

			# If this is the last tile we were waiting for,
			self.missing_tiles[zoom] -= 1
			if self.missing_tiles[zoom] == 0:
				self.feedback.debug(5, " All tiles in, immediate redraw")

				# If last tile arrived before timer expired,
				if self.timer is not None:
					self.feedback.debug(5, " Canceling timer")
					gobject.source_remove(self.timer)
					self.timer = None

				# If at least one tile is new or modified,
				if self.redraw_needed:
					self.redraw()
					self.redraw_needed = False

			# If some tiles still out, set a timer at the limit of or patience.
			else:
				self.feedback.debug(5, " %d tiles to go" % self.missing_tiles[zoom])
				if self.timer == None:
					self.timer = gobject.timeout_add(self.tile_wait, self.timer_expired)

	def tile_in_view(self, zoom, x, y):
		if zoom != self.int_zoom:
			return False
		if self.tile_ranges is None:
			return False
		x_range_start, x_range_end, y_range_start, y_range_end = self.tile_ranges
		return (x >= x_range_start and x <= x_range_end and y >= y_range_start and y <= y_range_end)

	# In order to avoid a redraw storm as the tiles come in we hold
	# of until either they have all arrived or a timer expires. This
	# is called when it expires.
	def timer_expired(self):
		self.feedback.debug(5, " Redraw timer expired.")
		self.redraw()
		self.timer = None
		return False

	# Load tiles into the cache in anticipation of offline use.
	def precache_tiles(self, progress, max_zoom):
		if self.tile_ranges is not None:
			downloader = MapTileDownloader(
				self.tileset,
				self.containing_map.tile_cache_basedir,
				feedback=progress,
				delay=0.1
				)
	
			# Start downloading
			x_start, x_end, y_start, y_end = self.tile_ranges
			total = tile_count(x_end-x_start+1, y_end-y_start+1, max_zoom-self.int_zoom+1)
			print "Will download %d tiles" % total
			if total > 0:
				count = 0
				for z in range(self.int_zoom, max_zoom+1):
					for x in range(x_start, x_end+1):
						for y in range(y_start, y_end+1):
							count += 1
							progress.progress(count, total,
								_("Downloading {layer} tile {count} of {total}, zoom level is {zoom}").format(layer=self.name, count=count, total=total, zoom=z)
								)
							if downloader.load_tile(z, x, y, True) is None:		# failed
								for seconds in range(10, 0, -1):
									progress.countdown(_("Retry in %d seconds...") % seconds)
									time.sleep(1.0)
					x_start *= 2
					x_end = x_end * 2 + 1
					y_start *= 2
					y_end = y_end * 2 + 1

	def reload_tiles(self):
		if self.tile_ranges is not None:
			x_range_start, x_range_end, y_range_start, y_range_end = self.tile_ranges
			zoom = self.int_zoom
			for x in range(x_range_start, x_range_end+1):
				for y in range(y_range_start, y_range_end+1):
					self.ram_cache_invalidate(zoom, x, y)
					local_filename = "%s/%s/%d/%d/%d" % (self.containing_map.tile_cache_basedir, self.tileset.key, zoom, x, y)
					try:
						os.unlink(local_filename)
					except OSError:
						pass
		self.cache_surface = None

#=============================================================================
# Download tiles using HTTP
# This uses httplib rather than urllib2 because the latter does not support
# persistent connexions.
#=============================================================================

class MapTileDownloader(object):
	def __init__(self, tileset, tile_cache_basedir, done_callback=None, feedback=None, delay=None):
		self.tileset = tileset
		self.tile_cache_basedir = tile_cache_basedir
		self.feedback = feedback
		self.done_callback = done_callback
		self.delay = delay

		if feedback is None:
			raise AssertionError

		# Should we start threads?
		self.threads = []
		if self.done_callback:		# multi-threaded mode
			self.syncer = threading.Condition()
			self.queue = []
			for i in range(3):		# number of threads
				thread = MapTileDownloaderThread(self, name="%s-%d" % (self.tileset.key, i))
				self.threads.append(thread)
				thread.start()
		else:						# syncronous mode
			self.syncer = None
			self.queue = None
			self.threads.append(MapTileDownloaderThread(self, name="%s-dummy" % self.tileset.key))

	# If the indicated tile is in the cache and is not too old, return its path
	# so that the caller can download it. If it is not, and there is no callback
	# function, download it immediately. If there is a callback function, put
	# it in the queue for a background thread the download.
	#
	# Returns:
	#  filename--None if not (yet) available
	#  pending--True if a callback is to be expected	
	def load_tile(self, zoom, x, y, may_download):
		debug_args = (self.tileset.key, zoom, x, y)
		self.feedback.debug(2, "Load tile %s %d/%d/%d" % debug_args)
		local_filename = "%s/%s/%d/%d/%d" % (self.tile_cache_basedir, self.tileset.key, zoom, x, y)
		result = None

		try:
			statbuf = os.stat(local_filename)
		except OSError:
			statbuf = None

		if statbuf is None:
			self.feedback.debug(3, " Not in cache")
		else:
			cachefile_age = (float(time.time() - statbuf.st_mtime) / 86400.0)
			self.feedback.debug(4, " Cache file age: %s" % cachefile_age)
			if cachefile_age > self.tileset.max_age_in_days:
				self.feedback.debug(3, " Old in cache")
				result = local_filename
			else:
				self.feedback.debug(3, " Fresh in cache")
				return (local_filename, False)

		# The caller may want the tile only if it is available instantly.
		# This is used when using scaled up tiles from a lower zoom level
		# to temporarily replace missing tiles.
		if not may_download:
			self.feedback.debug(2, " Caller does not want to download this tile")
			return (result, False)

		remote_filename = self.tileset.get_path(zoom, x, y)
		if self.done_callback:
			self.feedback.debug(2, " Added to queue")
			self.enqueue((zoom, x, y, local_filename, remote_filename, statbuf))
			return (result, True)
		else:
			self.feedback.debug(2, " Downloading syncronously...")
			if self.threads[0].download_tile_worker(zoom, x, y, local_filename, remote_filename, statbuf):
				if self.delay:
					time.sleep(self.delay)
				return (local_filename, False)
			else:
				return (None, False)

	# Add an item to the work queue for the background threads
	def enqueue(self, item, clear=False):
		self.syncer.acquire()
		if clear:
			while len(self.queue):
				self.queue.pop(0)
		self.queue.insert(0, item)
		if item is None:			# None is stop signal
			self.syncer.notifyAll()
		else:
			self.syncer.notify()
		self.syncer.release()

	# This tile downloader is no longer needed. Shut down the background threads.
	def __del__(self):
		#print "Destroying tile downloader..."
		if self.queue is not None:
			# Tell the threads to stop
			self.enqueue(None, clear=True)

			# Wait for them to stop
			#for thread in self.threads:
			#	self.feedback.debug(1, " Waiting for thread %s to stop..." % thread.name)
			#	thread.join()
			#self.feedback.debug(1, "All downloader threads have stopped.")
		else:
			if self.threads[0].conn is not None:
				self.threads[0].conn.close()

class MapTileDownloaderThread(threading.Thread):
	def __init__(self, parent, **kwargs):
		threading.Thread.__init__(self, **kwargs)
		self.daemon = True
		self.feedback = parent.feedback
		self.conn = None
		self.syncer = parent.syncer
		self.queue = parent.queue
		self.tileset = parent.tileset
		self.done_callback = parent.done_callback

	def run(self):
		while True:
			self.syncer.acquire()
			self.feedback.debug(3, "Thread %s is waiting..." % self.name)
			while len(self.queue) < 1:
				self.syncer.wait()
			item = self.queue[0]
			if item is not None:
				self.queue.pop(0)
			self.feedback.debug(3, "Thread %s received item: %s" % (self.name, str(item)))
			self.syncer.release()
			if item is None:				# signal to stop
				break
			while True:
				if self.download_tile_worker(*item):
					break
				self.feedback.debug(3, "Thread %s sleeping..." % self.name)
				time.sleep(10)
		if self.conn is not None:
			self.conn.close()
		self.feedback.debug(2, " Thread %s exiting..." % self.name)

	def download_tile_worker(self, zoom, x, y, local_filename, remote_filename, statbuf):
		debug_args = (self.tileset.key, zoom, x, y)
		self.feedback.debug(2, "Thread %s downloading tile %s %d/%d/%d" % ((self.name,) + debug_args))

		# Download the tile. This uses a persistent connection.
		try:
			# Send GET request
			if self.conn is None:
				hostname = self.tileset.get_hostname()
				self.feedback.debug(3, " Thread %s opening HTTP connexion to %s..." % (self.name, hostname))
				self.conn = httplib.HTTPConnection(hostname, timeout=30)
			self.feedback.debug(3, " GET %s" % remote_filename)
			hdrs = {}
			hdrs.update(self.tileset.extra_headers)
			if statbuf is not None:
				hdrs['If-Modified-Since'] = http_date(statbuf.st_mtime)
			self.conn.request("GET", remote_filename, None, hdrs)

			# Read response
			response = self.conn.getresponse()

		except socket.gaierror, msg:
			self.feedback.error(_("Tile %s/%d/%d/%d: Address lookup error: %s") % (debug_args + (msg,)))
			raise NoInet
		except socket.error, msg:
			self.feedback.error(_("Tile %s/%d/%d/%d: socket error: %s") % (debug_args + (msg,)))
			self.conn = None		# close
			return False
		except httplib.BadStatusLine:
			self.feedback.error(_("Tile %s/%d/%d/%d: BadStatusLine") % debug_args)
			self.conn = None		# close
			return False
		except httplib.ResponseNotReady:
			self.feedback.error(_("Tile %s/%d/%d/%d: no response") % debug_args)
			self.conn = None		# close
			return False

		content_length = response.getheader("content-length")
		content_type = response.getheader("content-type")
		self.feedback.debug(5, "  %s/%d/%d/%d: %d %s %s %s bytes" % (debug_args + (response.status, response.reason, content_type, str(content_length))))

		if response.status == 304:
			self.feedback.debug(1, "  %s/%d/%d/%d: not modified" % debug_args)
			response.read()					# discard
			fh = open(local_filename, "a")	# touch
			fh.close()
			modified = False

		else:
			if response.status != 200:
				self.feedback.debug(1, "  %s/%d/%d/%d: unacceptable response status: %d %s" % (debug_args + (response.status, response.reason)))
				response_body = response.read()
				if response_body != "" and content_type.startswith("text/"):
					self.feedback.debug(1, "%s" % response_body.strip())
				return True	 				# give up on tile

			if not content_type.startswith("image/") and content_type != "application/json":
				self.feedback.debug(1, "  %s/%d/%d/%d: non-image MIME type: %s" % (debug_args + (content_type,)))
				response_body = response.read()
				if content_type.startswith("text/"):
					self.feedback.debug(1, "%s" % response_body.strip())
				return True	 				# give up on tile
	
			if content_length is not None and int(content_length) == 0:
				self.feedback.debug(1, "  %s/%d/%d/%d: empty response" % debug_args)
				response.read()
				return True					# give up on tile
	
			# Make the cache directory which holds this tile, if it does not exist already.
			local_dirname = os.path.dirname(local_filename)
			if not os.path.exists(local_dirname):
				# This may fail if another thread creates.
				try:
					os.makedirs(local_dirname)
				except OSError, e:
					if e.errno != errno.EEXIST:
						raise
	
			# Save the file without there every being a partial tile written with the final name.
			cachefile = SaveAtomically(local_filename)
			try:
				cachefile.write(response.read())
			except socket.timeout:		# FIXME: socket is sometimes None. Why?
				self.feedback.debug(1, "  %s/%d/%d/%d: Socket timeout" % debug_args)
				self.feedback.error(_("Timeout during download"))
				self.conn = None		# close
				return False
			try:
				cachefile.close()
			except OSError, e:
				print "FIXME: OSError: %d" % e.errno

			modified = True
	
		# Tell the tile layer that the tile is ready so that it can redraw.
		if self.done_callback:
			try:
				self.done_callback(zoom, x, y, modified)
			except ReferenceError:
				self.feedback.debug(1, " Thread %s misses tile layer" % self.name)

		return True

#=============================================================================
# Clean the tile cache created by MapTileDownloader
#=============================================================================
class MapCacheCleaner(threading.Thread):
	def __init__(self, cache_root, scan_interval=30, max_age=180):
		threading.Thread.__init__(self, name="cache-cleaner")
		self.daemon = True
		self.cache_root = cache_root
		day = 24 * 60 * 60

		# Scan a tileset's cache if it was last scanned before this date.
		self.scan_if_before = time.time() - scan_interval * day

		# Delete tiles last used before this date.
		self.delete_if_before = time.time() - max_age * day

		# Sleep in seconds after processing each directory within a tileset's
		# cache. We do this so as not to hit the disk too hard.
		self.directory_delay = 0.2

		# Sleep in seconds after scanning each tileset.
		self.tileset_delay = 90

	def run(self):
		time.sleep(5)		# wait until after startup
		print "Cache cleaner: starting"

		tilesets = []
		tilesets_count = 0
		for tileset in os.listdir(self.cache_root):
			tilesets_count += 1
			touchfile = os.path.join(self.cache_root, tileset, ".last-cleaned")
			if os.path.exists(touchfile):
				statbuf = os.stat(touchfile)
				if statbuf.st_mtime < self.scan_if_before:
					#print "Cache cleaner: %s due for cleaning" % tileset
					tilesets.append(tileset)
				else:
					#print "Cache cleaner: %s cleaned too recently" % tileset
					pass
			else:
				#print "Cache cleaner: %s never cleaned" % tileset
				tilesets.append(tileset)
		print "Cache cleaner: %d of %d tilesets need cleaning" % (len(tilesets), tilesets_count)

		random.shuffle(tilesets)

		for tileset in tilesets:
			cachedir = os.path.join(self.cache_root, tileset)
			touchfile = os.path.join(cachedir, ".last-cleaned")

			print "Cache cleaner: cleaning %s..." % tileset
			total = 0
			deleted = 0
			for dirpath, dirnames, filenames in os.walk(cachedir, topdown=False):
				#print dirpath, dirnames, filenames
				left = 0
				for filename in filenames:
					filepath = os.path.join(dirpath, filename)
					statbuf = os.stat(filepath)
					if statbuf.st_atime < self.delete_if_before:
						deleted += 1
						os.unlink(filepath)
					else:
						left += 1
					total += 1
				for dirname in dirnames:
					path = os.path.join(dirpath, dirname)
					#print "rmdir(\"%s\")" % path
					try:
						os.rmdir(path)
					except OSError:
						#print "  Not empty"
						pass
				time.sleep(self.directory_delay)

			print "Cache cleaner: %d of %d tiles removed from %s" % (deleted, total, tileset)
			if deleted == total:
				print "Cache cleaner: removing empty cache %s..." % tileset
				if os.path.exists(touchfile):
					os.unlink(touchfile)
				os.rmdir(cachedir)
			else:
				open(touchfile, "w")

			time.sleep(self.tileset_delay)

		print "Cache cleaner: finished"

# Substitute for MapTileDownloader() for use when the map is in offline mode.
class MapTileCacheLoader(object):
	def __init__(self, tileset, tile_cache_basedir, feedback=None):
		self.tileset = tileset
		self.tile_cache_basedir = tile_cache_basedir
		self.feedback = feedback

	def load_tile(self, zoom, x, y, may_download):
		self.feedback.debug(1, "Load tile %s %d/%d/%d" % (self.tileset.key, zoom, x, y))
		local_filename = "%s/%s/%d/%d/%d" % (self.tile_cache_basedir, self.tileset.key, zoom, x, y)
		if os.path.exists(local_filename):
			return (local_filename, False)
		else:
			return (None, False)

