from webob import exc
from webob.dec import wsgify

class MultiApp(object):
	def __init__(self):
		self.routes = {}
		self.root = self.default_root

	@staticmethod
	def default_root(request):
		raise exc.HTTPNotFound()

	@wsgify
	def __call__(self, request):
		if request.path_info == '/':
			return self.root(request)
		for prefix, route in self.routes.iteritems():
			if request.path_info.startswith(prefix):
				return route(request)
		raise exc.HTTPNotFound()

	def add_application(self, prefix, app):
		if not prefix.startswith('/'):
			raise ValueError('Route prefix must start with /')
		for existing_route in self.routes:
			if prefix.startswith(existing_route) or existing_route.startswith(prefix):
				raise ValueError('Overlapping route prefix found')
		self.routes[prefix] = app
