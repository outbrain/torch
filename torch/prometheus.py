import math
import datetime
from collections import OrderedDict

_INF = float('inf')
_MINUS_INF = float('-inf')
_DEFAULT_BUCKETS = (.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, _INF)

# TODO: Validate label names are not using illegal characters or reserved words

class Metric(object):
	def __init__(self, name, labels):
		self.name = name
		self.labels = self.normalize_labels(labels)

	@staticmethod
	def normalize_labels(labels):
		if isinstance(labels, frozenset):
			return labels
		elif labels is None:
			return frozenset()
		elif isinstance(labels, dict):
			return frozenset(labels.items())
		elif isinstance(labels, (list, tuple, set)):
			return frozenset(labels)
		else:
			raise TypeError('could not normalize labels')

	@staticmethod
	def format_labels(label_pairs):
		label_pairs = ','.join(["{}=\"{}\"".format(key, value) for key, value in sorted(label_pairs)])
		if label_pairs:
			label_pairs = '{{{}}}'.format(label_pairs)
		return label_pairs

	@staticmethod
	def format_value(value):
		if value == _INF:
			return '+Inf'
		elif value == _MINUS_INF:
			return '-Inf'
		elif math.isnan(value):
			return 'NaN'
		else:
			return repr(float(value))

	def render_part(self, name, labels, value):
		labels = self.format_labels(labels)
		value = self.format_value(value)
		return '{name}{labels} {value}'.format(name=name, labels=labels, value=value)

	def render(self): # pragma: nocover
		raise NotImplementedError('render')

class Counter(Metric):
	type_ = 'counter'
	def __init__(self, name, labels):
		super(Counter, self).__init__(name, labels)
		self.value = 0

	def inc(self, amount=1):
		if amount < 0:
			raise ValueError('counter cannot increment by a negative number')
		self.value += amount

	def render(self):
		return self.render_part(self.name, self.labels, self.value)

class Gauge(Metric):
	type_ = 'gauge'
	def __init__(self, name, labels):
		super(Gauge, self).__init__(name, labels)
		self.value = 0

	def inc(self, amount=1):
		self.value += amount

	def dec(self, amount=1):
		self.value -= amount

	def set(self, amount):
		self.value = amount

	def render(self):
		return self.render_part(self.name, self.labels, self.value)

class Histogram(Metric):
	type_ = 'histogram'
	def __init__(self, name, labels, buckets=_DEFAULT_BUCKETS):
		super(Histogram, self).__init__(name, labels)
		try:
			assert len(buckets) > 0
			assert buckets[0] != _INF
		except AssertionError:
			raise ValueError('bad bucket values')

		buckets = sorted(buckets)
		if buckets[-1] != _INF:
			buckets = list(buckets)+[_INF]
		self.buckets = OrderedDict.fromkeys(buckets, 0)
		self.count = 0
		self.sum = 0

	def observe(self, amount):
		self.count += 1
		self.sum += amount
		for bucket in reversed(self.buckets.keys()):
			if amount <= bucket:
				self.buckets[bucket] += 1
			else:
				break

	def render(self):
		metrics = [
			self.render_part(self.name+'_count', self.labels, self.count),
			self.render_part(self.name+'_sum', self.labels, self.sum)
		]
		bucket_labels = set(self.labels)
		bucket_name = self.name+'_bucket'
		for bucket, value in self.buckets.iteritems():
			metrics.append(self.render_part(bucket_name, bucket_labels.union([('le', bucket)]), value))
		return '\n'.join(metrics)

class Summary(Metric):
	type_ = 'summary'
	def __init__(self, name, labels):
		super(Summary, self).__init__(name, labels)
		self.count = 0
		self.sum = 0

	def observe(self, amount):
		self.count += 1
		self.sum += amount

	def render(self):
		metrics = [
			self.render_part(self.name+'_count', self.labels, self.count),
			self.render_part(self.name+'_sum', self.labels, self.sum)
		]
		return '\n'.join(metrics)

class MetricFamily(object):
	def __init__(self, klass, name, description, **kwargs):
		self.klass = klass
		self.kwargs = kwargs
		self.name = name
		self.description = description
		self.metrics = {}
		self.metric_seen = {}

	def labels(self, key):
		labels = Metric.normalize_labels(key)
		try:
			metric = self.metrics[labels]
		except KeyError:
			metric = self.metrics[labels] = self.klass(self.name, labels, **self.kwargs)
		self.metric_seen[labels] = datetime.datetime.utcnow()
		return metric

	def cleanup(self, ttl):
		if ttl:
			now = datetime.datetime.utcnow()
			for label in self.metric_seen.keys():
				if now - self.metric_seen[label] > ttl:
					del self.metric_seen[label]
					del self.metrics[label]

	def render(self):
		results = [
			'# HELP {} {}'.format(self.name, self.description),
			'# TYPE {} {}'.format(self.name, self.klass.type_)
		]

		for metric in self.metrics.itervalues():
			metric_txt = metric.render()
			results.append(metric_txt)

		return '\n'.join(results)

class Registry(dict):
	def __init__(self, ttl=None):
		super(Registry, self).__init__()
		if ttl is not None and not isinstance(ttl, datetime.timedelta):
			raise ValueError('invalid ttl value: {!r}'.format(ttl))
		self.ttl = ttl

	def __setitem__(self, key, value):
		if key in self and self[key].klass != value.klass:
			raise ValueError('metric type conflict')
		super(Registry, self).__setitem__(key, value)

	def render(self):
		results = '{}\n'.format('\n'.join(metric.render() for metric in self.itervalues()))
		for metric in self.itervalues():
			metric.cleanup(self.ttl)
		return results

	def add_metric(self, klass, name, description, **kwargs):
		return self.setdefault((klass, name), MetricFamily(klass, name, description, **kwargs))
