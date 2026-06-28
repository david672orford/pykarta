import os
import time
import sys

from platformdirs import PlatformDirs

# Exception raised when it seems the Internet connexion is down.
class NoInet(Exception):
	pass

# Return the name of a directory where PyKarta may store cache files.
def get_cachedir():
	app_name = "PyKarta"
	dirs = PlatformDirs(app_name, appauthor=False)
	return dirs.user_cache_dir

# How many days ago was this file modified?
def file_age_in_days(filename):
	try:
		stat_result = os.stat(filename)
	except OSError:
		return None
	return (float(time.time() - stat_result.st_mtime) / 86400.0)

# The weakref module is unable to create a reference to a bound method. This can.
if sys.version_info >= (3,0):
	from weakref import WeakMethod
	class BoundMethodProxy:
		def __init__(self, bound_method):
			self.m = WeakMethod(bound_method)
		def __call__(self, *args, **kwargs):
			return self.m()(*args, **kwargs)
else:
	import weakref
	import new
	class BoundMethodProxy(object):
		def __init__(self, bound_method):
			self.im_self_ref = weakref.ref(bound_method.__self__)
			self.__func__ = bound_method.__func__
			self.__self__.__class__ = bound_method.__self__.__class__
		def __call__(self, *args, **kwargs):
			obj = self.im_self_ref()
			if obj is None:
				raise ReferenceError
			return new.instancemethod(self.__func__, obj, self.__self__.__class__)(*args, **kwargs)

# How many tiles are covered by a rectangle of the indicated size (in tiles)
# taken to the indicated number of zoom levels?
def tile_count(width, height, zoom_levels):
	total = 0
	for z in range(zoom_levels):
		total += (width * height)
		width *= 2
		height *= 2
	return total

# TODO: backport from Pyapp
# Take the data from the handle and write it to the indicated file.
# The file does not receive the indicted name until it is complete.
class SaveAtomically(object):
	def __init__(self, filename, backup=False):
		self.filename = filename
		self.backup = backup

		# MS-DOS naming scheme
		#(base, ext) = os.path.splitext(self.filename)
		#self.tempname = "%s.tmp" % base
		#self.backname = "%s.bak" % base

		# Unix naming scheme
		self.tempname = "%s.tmp" % self.filename
		self.backname = "%s~" % self.filename

		self.fh = open(self.tempname, 'wb')

	def write(self, data):
		self.fh.write(data)

	def close(self):
		self.fh.close()
		if os.path.exists(self.filename):
			if self.backup:
				if os.path.exists(self.backname):
					os.remove(self.backname)
				os.rename(self.filename, self.backname)
			else:
				os.unlink(self.filename)
		os.rename(self.tempname, self.filename)

