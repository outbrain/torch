import json
import urllib2

class UndefinedMetric(Exception):
	pass

class MetricsClient(object):
	def __init__(self, torch_url):
		self.torch_url = torch_url
		self.metrics = {}
		self.buckets = {}

	def add_metric(self, name, description, buckets=None):
		self.metrics[name] = description
		if buckets:
			self.buckets[name] = buckets

	def _get_metric(self, name):
		try:
			return {
				'name': name,
				'description': self.metrics[name]
			}
		except KeyError:
			raise UndefinedMetric(name)

	def _make_request(self, path, metric):
		data = json.dumps(metric)
		req = urllib2.Request(self.torch_url+path, data, {'Content-Type': 'application/json', 'Content-Length': len(data)})
		f = urllib2.urlopen(req)
		f.read()
		f.close()

	def inc_counter(self, name, labels, amount=1):
		metric = self._get_metric(name)
		metric['labels'] = labels
		metric['value'] = amount
		self._make_request('/metrics/counter', metric)

	def inc_gauge(self, name, labels, amount):
		metric = self._get_metric(name)
		metric['labels'] = labels
		metric['value'] = amount
		self._make_request('/metrics/gauge/inc', metric)

	def dec_gauge(self, name, labels, amount):
		metric = self._get_metric(name)
		metric['labels'] = labels
		metric['value'] = amount
		self._make_request('/metrics/gauge/dec', metric)

	def set_gauge(self, name, labels, amount):
		metric = self._get_metric(name)
		metric['labels'] = labels
		metric['value'] = amount
		self._make_request('/metrics/gauge/set', metric)

	def summary(self, name, labels, amount):
		metric = self._get_metric(name)
		metric['labels'] = labels
		metric['value'] = amount
		self._make_request('/metrics/summary', metric)

	def histogram(self, name, labels, amount):
		metric = self._get_metric(name)
		metric['labels'] = labels
		metric['value'] = amount
		buckets = self.buckets.get(name)
		if buckets:
			metric['buckets'] = buckets
		self._make_request('/metrics/histogram', metric)

