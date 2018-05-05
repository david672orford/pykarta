# utils_rsvg_ctypes.py
# Last modified: 2 May 2018

import sys
import ctypes
import gobject

# See: http://cairographics.org/cookbook/librsvgpython/
# See: http://cairographics.org/cairo_rsvg_and_python_in_windows/
# https://stackoverflow.com/questions/6142757/error-with-python-ctypes-and-librsvg
# https://developer.gnome.org/rsvg/2.42/rsvg-RsvgHandle.html

if sys.platform == "win32":
	librsvg    = ctypes.CDLL("librsvg-2-2.dll")
	libgobject = ctypes.CDLL("libgobject-2.0-0.dll")
elif sys.platform == "darwin":
	# Don"t forget to set DYLD_FALLBACK_LIBRARY_PATH.
	librsvg    = ctypes.CDLL("librsvg-2.2.dylib")
	libgobject = ctypes.CDLL("libgobject-2.0.dylib")
elif sys.platform.startswith("linux"):
	librsvg    = ctypes.CDLL("librsvg-2.so.2")
	libgobject = ctypes.CDLL("libgobject-2.0.so.0")
else:
	raise Exception("No case for platform %s" % sys.platform)

class RsvgError(Exception):
	pass

class RsvgDimensionData(ctypes.Structure):
	_fields_ = [("width", ctypes.c_int),
	            ("height", ctypes.c_int),
	            ("em", ctypes.c_double),
	            ("ex", ctypes.c_double)]

class PycairoContext(ctypes.Structure):
	_fields_ = [("PyObject_HEAD", ctypes.c_byte * object.__basicsize__),
	            ("ctx", ctypes.c_void_p),
	            ("base", ctypes.c_void_p)]

class GError(ctypes.Structure):
	_fields_ = [("domain", ctypes.c_uint32), ("code", ctypes.c_int), ("message", ctypes.c_char_p)]

# Boilerplate code to convert a C GObject to a Python GObject
# From: http://faq.pygtk.org/index.py?req=show&file=faq23.041.htp
class PyGObjectCPAI(object):
	class _PyGObject_Functions(ctypes.Structure):
	    _fields_ = [
			('register_class',
				ctypes.PYFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p,
				ctypes.c_int, ctypes.py_object,
				ctypes.py_object)),
			('register_wrapper',
				ctypes.PYFUNCTYPE(ctypes.c_void_p, ctypes.py_object)),
			('register_sinkfunc',
				ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.c_void_p)),
			('lookupclass',
				ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.c_int)),
			('newgobj',
				ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.c_void_p)),
			]
	def __init__(self):
		PyCObject_AsVoidPtr = ctypes.pythonapi.PyCObject_AsVoidPtr
   		PyCObject_AsVoidPtr.restype = ctypes.c_void_p
	   	PyCObject_AsVoidPtr.argtypes = [ctypes.py_object]
		addr = PyCObject_AsVoidPtr(ctypes.py_object(gobject._PyGObject_API))
		self._api = self._PyGObject_Functions.from_address(addr)
	def pygobject_new(self, addr):
		return self._api.newgobj(addr)

libgobject.g_type_init()

librsvg.rsvg_handle_new_from_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.POINTER(GError))]
librsvg.rsvg_handle_new_from_file.restype = ctypes.c_void_p

librsvg.rsvg_handle_new.argtypes = []
librsvg.rsvg_handle_new.restype = ctypes.c_void_p

librsvg.rsvg_handle_render_cairo.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
librsvg.rsvg_handle_render_cairo.restype = ctypes.c_bool

librsvg.rsvg_handle_get_dimensions.argtypes = [ctypes.c_void_p, ctypes.POINTER(RsvgDimensionData)]

librsvg.rsvg_handle_write.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.POINTER(GError))]
librsvg.rsvg_handle_write.restype = ctypes.c_bool

librsvg.rsvg_handle_close.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.POINTER(GError))]
librsvg.rsvg_handle_close.restype = ctypes.c_bool

librsvg.rsvg_handle_get_pixbuf.argtypes = [ctypes.c_void_p]
librsvg.rsvg_handle_get_pixbuf.restype = ctypes.c_void_p

class Handle():
	def __init__(self, path=None):
		self.path = path
		if path is not None:
			error = ctypes.POINTER(GError)()
			self.handle = librsvg.rsvg_handle_new_from_file(path, error)
			if self.handle is None:
				raise RsvgError(error.contents.message)
		else:
			self.handle = librsvg.rsvg_handle_new()

	def write(self, data):
		error = ctypes.POINTER(GError)()
		return librsvg.rsvg_handle_write(self.handle, data, len(data), error)

	def close(self):
		error = ctypes.POINTER(GError)()
		return librsvg.rsvg_handle_close(self.handle, error)

	def get_dimension_data(self):
		svgDim = RsvgDimensionData()
		librsvg.rsvg_handle_get_dimensions(self.handle, ctypes.byref(svgDim))
		return (svgDim.width, svgDim.height)	# FIXME: what about em and ex?

	def render_cairo(self, ctx):
		ctx.save()
		z = PycairoContext.from_address(id(ctx))
		librsvg.rsvg_handle_render_cairo(self.handle, z.ctx)
		ctx.restore()

	def get_pixbuf(self):
		pixbuf = librsvg.rsvg_handle_get_pixbuf(self.handle)
		capi = PyGObjectCPAI()
		return capi.pygobject_new(pixbuf)

