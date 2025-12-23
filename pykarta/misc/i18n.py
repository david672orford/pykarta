try:
	import pyapp.i18n
except ImportError:
	import builtins
	builtins.__dict__['_'] = lambda text: text
