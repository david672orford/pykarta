# pykarta/geocoder/geocoder_base.py
# Copyright 2013, 2014, 2015, Trinity College Computing Center
# Last modified: 6 February 2015

import threading
import httplib
import socket
import errno
import urllib
import time
import sys
import pykarta
from pykarta.misc import NoInet

# Thread in which the HTTP GET runs
class GetThread(threading.Thread):
	def __init__(self, geocoder, path, kwargs):
		threading.Thread.__init__(self)
		self.geocoder = geocoder
		self.path = path
		self.kwargs = kwargs
		self.result = None
		self.exception = None
		self.daemon = True
	def run(self):
		try:
			self.result = self.geocoder.get_blocking(self.path, **(self.kwargs))
		except Exception as e:
			self.exception = e

class GeocoderBase:

	# Offsets into the address array passed to FindAddr()
	f_house_number = 0
	f_street = 1
	f_apartment = 2
	f_town = 3
	f_state = 4
	f_postal_code = 5

	url_server = None
	url_path = None
	conn = None					# HTTP connexion to server
	delay = 1.0					# minimum time between requests
	retry_limit = 5				# how many times to retry failed request
	retry_delay = 10			# delay in seconds between retries
	timeout = 30

	def __init__(self, progress_dialog=None, debug=False):
		self.progress_dialog = progress_dialog
		self.debug_enabled = debug
		self.name = self.__class__.__name__
		self.last_request_time = 0
		self.last_progress_part = 0

	def debug(self, *args):
		if self.debug_enabled:
			string_list = []
			for i in args:
				string_list.append(i)
			sys.stderr.write(" ".join(string_list))
			sys.stderr.write("\n")

	def debug_indented(self, text):
		if self.debug_enabled:
			for line in text.split('\n'):
				sys.stderr.write("    %s\n" % line)

	def progress(self, part, whole, message):
		if self.progress_dialog:
			self.progress_dialog.sub_progress(part, whole, message)
		self.last_progress_part = part

	def progress_bump(self, bump):
		if self.progress_dialog:
			self.progress_dialog.bump(bump)

	# Send an HTTP query to the geocoder server.
	# Calls get_blocking() which is defined below.
	# Runs it in a thread so as to keep the GUI refreshed while waiting.
	# Handles retries.
	def get(self, path, **kwargs):
		assert self.url_server is not None
		retry = 0
		while True:
			try:
				thread = GetThread(self, path, kwargs)
				thread.start()
				bump = 0.0
				while thread.isAlive():
					self.progress_bump(bump)
					thread.join(0.2)
					bump += 0.1
				if thread.exception is not None:
					raise thread.exception
				return thread.result
			except GeocoderError as e:
				self.debug("  %s" % str(e))
				self.conn = None		# close connexion
				retry += 1
				if e.retryable and retry <= self.retry_limit:
					countdown = self.retry_delay
					while countdown > 0:
						time.sleep(1)
						self.progress(None, None, "%s failed, retry %d in %d seconds." % (self.name, retry, countdown))
						countdown -= 1
				else:
					raise e

	# This is the function which actually sends the HTTP query.
	def get_blocking(self, path, query=None, method="GET", content_type=None):
		try:
			message_body = None
			if query is not None:
				if method == "GET":
					path = path + "?" + urllib.urlencode(query)
				elif method == "POST":
					message_body = query
			self.debug("  %s %s" % (method, path))

			remaining_delay = self.last_request_time + self.delay - time.time()
			self.debug("    remaining_delay: %f" % remaining_delay)
			if remaining_delay > 0:
				time.sleep(remaining_delay)
			self.last_request_time = time.time()

			for attempt in (1, 2):
				if self.conn is None:
					self.debug("  Opening HTTP connexion to %s..." % self.url_server)
					self.conn = httplib.HTTPConnection(self.url_server, timeout=self.timeout)

				# Send the HTTP request
				# We could use self.conn.request() here, but then we would have
				# to build the headers hash, and that would take about the same
				# amount of code.
				self.conn.putrequest(method, path)
				self.conn.putheader("User-Agent", "PyKarta %s" % pykarta.version)
				if method == "POST":
					self.conn.putheader("Content-Length", len(message_body))
				if content_type is not None:
					self.conn.putheader("Content-Type", content_type)
				self.conn.endheaders(message_body=message_body)

				# Read the HTTP status line. If it is empty, assume the connection
				# was persistent, but the server disconnected it and try again
				# immediately.
				try:
					http_resp = self.conn.getresponse()
				except httplib.BadStatusLine as e:
					if attempt == 1:
						self.debug("  Server disconnected.")
						self.conn = None
						continue
					else:
						line = e.args[0].strip()
						raise GeocoderError("HTTP server sent bad response: %s" % line)

				# Does the server think it suceeded?
				self.debug("    %s %s" % (http_resp.status, http_resp.reason))
				if http_resp.status != 200:
					raise GeocoderError("HTTP %s failed: %d %s" % (method, http_resp.status, http_resp.reason), retryable=False)

				# Read the HTTP response body
				resp_text = http_resp.read()
				if resp_text == "":
					raise GeocoderError("Empty HTTP response body")

				# It worked.
				break

			return resp_text

		except socket.gaierror:		# address-related error
			print "Lookup of %s failed." % self.url_server
			raise NoInet

		except socket.error as e:	# likely errno 104, connection reset by peer
			if e.errno == errno.ECONNRESET:
				raise GeocoderError("ECONNRESET")
			else:
				raise

	def result_truly_matches(self, address, reply_address_components):
		to_find = (
			('house_number', address[self.f_house_number]),
			('street', address[self.f_street]),
			(None, address[self.f_town]),
			('state', address[self.f_state]),
			)
		find_in = list(reply_address_components)[:]
		#self.debug("Find %s in %s" % (str(to_find), str(find_in)))
		for find_name, find_value in to_find:
			#self.debug("Searching for %s %s..." % (find_name, find_value))
			while True:
				if len(find_in) == 0:
					return False
				next_name, next_value = find_in.pop(0)
				#self.debug(" %s %s" % (next_name, next_value))
				if (find_name is None or next_name == find_name) and next_value == find_value:
					break	
		return True		

	def result_town_matches(self, town, reply_address_components):
		for name, value in reply_address_components:
			if value == town:
				return True
		return False

	#--------------------------------------------------------------
	# Override these in derived classes
	#--------------------------------------------------------------

	def FindAddr(self, address, countrycode=None):
		raise GeocoderUnimplemented

	def FindStreet(self, street, town, state, countrycode=None):
		raise GeocoderUnimplemented

	def FindTown(self, town, state, countrycode=None):
		raise GeocoderUnimplemented

	def Reverse(self, lat, lon, countrycode=None):
		raise GeocoderUnimplemented

	def should_cache(self):
		return True

# What a geocoder returns
class GeocoderResult(object):
	def __init__(self, query_address, source):
		self.query_address = query_address
		self.postal_code = None
		self.coordinates = None
		self.precision = None
		self.source = source
		self.alternative_addresses = []
	def __str__(self):
		return ",".join(map(lambda i: "%s:%s" % (i, str(getattr(self,i))), vars(self)))
	def add_alternative_address(self, address_dict):
		alt_addr = []
		for i in ("house_number", "street", "sublocality", "locality", "town", "city", "state", "postal_code"):
			if i in address_dict:
				alt_addr.append(address_dict[i])
		self.alternative_addresses.append(", ".join(alt_addr))

# Geocoders throw this for most errors.
class GeocoderError(Exception):
	def __init__(self, message, retryable=True):
		self.message = message
		self.retryable = retryable
	def __str__(self):
		return self.message

# For methods which a particular geocoder does not implement.
class GeocoderUnimplemented(GeocoderError):
	pass

