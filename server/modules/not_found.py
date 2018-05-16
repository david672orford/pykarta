def application(environ, start_response):
	start_response("404 Not Found", [])
	return ["Not found"]
