from webob import exc
from webob.dec import wsgify
from .prometheus import Registry, Counter, Gauge, Summary, Histogram

class PrometheusMetricCollector(object):
	def __init__(self, prefix='', ttl=None):
		self.routes = {
			prefix: self.report,
			prefix+'/': self.report,
			prefix+'/counter': self.counter,
			prefix+'/gauge/inc': self.gauge_inc,
			prefix+'/gauge/dec': self.gauge_dec,
			prefix+'/gauge/set': self.gauge_set,
			prefix+'/summary': self.summary,
			prefix+'/histogram': self.histogram
		}
		self.metric_registry = Registry(ttl=ttl)

	@wsgify
	def __call__(self, request):
		try:
			route = self.routes[request.path_info]
		except KeyError:
			raise exc.HTTPNotFound()
		else:
			return route(request)

	def metric_from_request(self, klass, body):
		if klass is Histogram and 'buckets' in body:
			metric_family = self.metric_registry.add_metric(klass, body['name'], body['description'], buckets=body['buckets'])
		else:
			metric_family = self.metric_registry.add_metric(klass, body['name'], body['description'])
		try:
			metric = metric_family.labels(body['labels'])
		except TypeError as ex:
			raise ValueError(ex)
		else:
			return metric

	def counter(self, request):
		body = request.json_body
		try:
			metric = self.metric_from_request(Counter, body)
			metric.inc(body['value'])
		except ValueError as ex:
			raise exc.HTTPBadRequest(body=str(ex))
		return exc.HTTPOk()

	def gauge_inc(self, request):
		body = request.json_body
		try:
			metric = self.metric_from_request(Gauge, body)
			metric.inc(body['value'])
		except ValueError as ex:
			raise exc.HTTPBadRequest(body=str(ex))
		return exc.HTTPOk()

	def gauge_dec(self, request):
		body = request.json_body
		try:
			metric = self.metric_from_request(Gauge, body)
			metric.dec(body['value'])
		except ValueError as ex:
			raise exc.HTTPBadRequest(body=str(ex))
		return exc.HTTPOk()

	def gauge_set(self, request):
		body = request.json_body
		try:
			metric = self.metric_from_request(Gauge, body)
			metric.set(body['value'])
		except ValueError as ex:
			raise exc.HTTPBadRequest(body=str(ex))
		return exc.HTTPOk()

	def summary(self, request):
		body = request.json_body
		try:
			metric = self.metric_from_request(Summary, body)
			metric.observe(body['value'])
		except ValueError as ex:
			raise exc.HTTPBadRequest(body=str(ex))
		return exc.HTTPOk()

	def histogram(self, request):
		body = request.json_body
		try:
			metric = self.metric_from_request(Histogram, body)
			metric.observe(body['value'])
		except ValueError as ex:
			raise exc.HTTPBadRequest(body=str(ex))
		return exc.HTTPOk()

	def report(self, request):
		headers = [('Content-type', 'text/plain; version=0.0.4; charset=utf-8')]
		response = exc.HTTPOk(headers=headers, body=self.metric_registry.render())
		return response

