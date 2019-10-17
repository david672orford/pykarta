def app(environ, start_response):
	start_response("404 Not Found", [])
	return [b"Not found"]
