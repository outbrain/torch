import unittest
import datetime
import mock

from torch.prometheus import (
	Metric,
	Counter,
	Gauge,
	Histogram,
	Summary,
	Registry,
	MetricFamily
	)

class TestMetric(unittest.TestCase):
	def test_normalize_labels(self):
		self.assertEquals(frozenset([('foo', 'bar')]), Metric.normalize_labels(frozenset([('foo', 'bar')])))
		self.assertEquals(frozenset(), Metric.normalize_labels(None))
		self.assertEquals(frozenset([('foo', 'bar')]), Metric.normalize_labels({'foo': 'bar'}))
		self.assertEquals(frozenset([('foo', 'bar')]), Metric.normalize_labels([('foo', 'bar')]))
		self.assertRaises(TypeError, Metric.normalize_labels, 'foobar')

	def test_format_value(self):
		self.assertEquals('+Inf', Metric.format_value(float('inf')))
		self.assertEquals('-Inf', Metric.format_value(float('-inf')))
		self.assertEquals('NaN', Metric.format_value(float('nan')))
		self.assertEquals('1.0', Metric.format_value(1))

	def test_render_part(self):
		metric_no_labels = Metric('foo', None)
		self.assertEquals(
			"foo 5.0",
			metric_no_labels.render_part(metric_no_labels.name, metric_no_labels.labels, 5.0)
		)

		metric = Metric('foo1', {'bar':'baz'})
		self.assertEquals(
			'foo1{bar="baz"} 5.0',
			metric.render_part(metric.name, metric.labels, 5.0)
		)

class TestCounter(unittest.TestCase):
	def setUp(self):
		self.counter = Counter('c', {'foo': 'bar'})

	def test_increment(self):
		self.assertEqual(0, self.counter.value)
		self.counter.inc()
		self.assertEqual(1, self.counter.value)
		self.counter.inc(7)
		self.assertEqual(8, self.counter.value)

	def test_negative_increment_raises(self):
		self.assertRaises(ValueError, self.counter.inc, -1)

	def test_render(self):
		self.counter.inc()
		self.assertEquals(
			'c{foo="bar"} 1.0',
			self.counter.render()
		)

class TestGauge(unittest.TestCase):
	def setUp(self):
		self.gauge = Gauge('g', {'foo': 'bar'})

	def test_gauge(self):
		self.assertEqual(0, self.gauge.value)
		self.gauge.inc()
		self.assertEqual(1, self.gauge.value)
		self.gauge.dec(3)
		self.assertEqual(-2, self.gauge.value)
		self.gauge.set(9)
		self.assertEqual(9, self.gauge.value)

	def test_render(self):
		self.gauge.inc()
		self.assertEquals(
			'g{foo="bar"} 1.0',
			self.gauge.render()
		)


class TestSummary(unittest.TestCase):
	def setUp(self):
		self.summary = Summary('s', {'foo': 'bar'})

	def test_summary(self):
		self.assertEqual(0, self.summary.count)
		self.assertEqual(0, self.summary.sum)
		self.summary.observe(10)
		self.assertEqual(1, self.summary.count)
		self.assertEqual(10, self.summary.sum)

	def test_render(self):
		self.summary.observe(1)
		self.assertEquals(
			's_count{foo="bar"} 1.0\n'
			's_sum{foo="bar"} 1.0',
			self.summary.render()
		)

class TestHistogram(unittest.TestCase):
	def setUp(self):
		self.histogram = Histogram('h', {'foo': 'bar'})

	def test_histogram(self):
		self.assertEqual(0, self.histogram.buckets[1.0])
		self.assertEqual(0, self.histogram.buckets[2.5])
		self.assertEqual(0, self.histogram.buckets[5.0])
		self.assertEqual(0, self.histogram.buckets[float('inf')])
		self.assertEqual(0, self.histogram.count)
		self.assertEqual(0, self.histogram.sum)

		self.histogram.observe(2)
		self.assertEqual(0, self.histogram.buckets[1.0])
		self.assertEqual(1, self.histogram.buckets[2.5])
		self.assertEqual(1, self.histogram.buckets[5.0])
		self.assertEqual(1, self.histogram.buckets[float('inf')])
		self.assertEqual(1, self.histogram.count)
		self.assertEqual(2, self.histogram.sum)

		self.histogram.observe(2.5)
		self.assertEqual(0, self.histogram.buckets[1.0])
		self.assertEqual(2, self.histogram.buckets[2.5])
		self.assertEqual(2, self.histogram.buckets[5.0])
		self.assertEqual(2, self.histogram.buckets[float('inf')])
		self.assertEqual(2, self.histogram.count)
		self.assertEqual(4.5, self.histogram.sum)

		self.histogram.observe(float("inf"))
		self.assertEqual(0, self.histogram.buckets[1.0])
		self.assertEqual(2, self.histogram.buckets[2.5])
		self.assertEqual(2, self.histogram.buckets[5.0])
		self.assertEqual(3, self.histogram.buckets[float('inf')])
		self.assertEqual(3, self.histogram.count)
		self.assertEqual(float("inf"), self.histogram.sum)

	def test_setting_buckets(self):
		h = Histogram('h', {'foo': 'bar'}, buckets=[0, 1, 2])
		self.assertEqual([0.0, 1.0, 2.0, float("inf")], h.buckets.keys())

		h = Histogram('h', {'foo': 'bar'}, buckets=[0, 1, 2, float("inf")])
		self.assertEqual([0.0, 1.0, 2.0, float("inf")], h.buckets.keys())

		self.assertRaises(ValueError, Histogram, 'h', {'foo': 'bar'}, buckets=[])
		self.assertRaises(ValueError, Histogram, 'h', {'foo': 'bar'}, buckets=[float("inf")])

	def test_render(self):
		h = Histogram('h', {'foo': 'bar'}, buckets=[0, 1, 2])
		h.observe(1)
		self.assertEquals(
			'h_count{foo="bar"} 1.0\n'
			'h_sum{foo="bar"} 1.0\n'
			'h_bucket{foo="bar",le="0"} 0.0\n'
			'h_bucket{foo="bar",le="1"} 1.0\n'
			'h_bucket{foo="bar",le="2"} 1.0\n'
			'h_bucket{foo="bar",le="inf"} 1.0',
			h.render()
		)


class TestMetricFamily(unittest.TestCase):
	def setUp(self):
		self.family = MetricFamily(Counter, 'foo', 'test counter')

	def test_labels(self):
		metric = self.family.labels({'foo': 'bar'})
		self.assertEquals(metric.name, self.family.name)
		self.assertEquals(metric.labels, frozenset([('foo', 'bar')]))

		metric2 = self.family.labels({'foo': 'bar'})
		self.assertIs(metric, metric2)

	def test_histogram_buckets(self):
		buckets = [1.0, 2.0, float('inf')]

		family = MetricFamily(Histogram, 'foo', 'test counter', buckets=buckets)
		metric = family.labels({'foo': 'bar'})

		self.assertEquals(metric.buckets.keys(), buckets)

	def test_render(self):
		self.family.labels({}).inc(1)
		self.family.labels({'foo': 'bar'}).inc(2)

		render_lines = self.family.render().splitlines()

		self.assertEquals(render_lines[0], '# HELP foo test counter')
		self.assertEquals(render_lines[1], '# TYPE foo counter')

	def test_metric_seen(self):
		label = Metric.normalize_labels({'foo': 'bar'})
		self.assert_(label not in self.family.metric_seen)

		# metric_seen is updated when Metric retrieved from MetricFamily.labels
		self.family.labels(label).inc(2)
		self.assert_(label in self.family.metric_seen)

		# metric not removed if ttl not exceeded
		self.family.cleanup(datetime.timedelta(days=1))
		self.assert_(label in self.family.metric_seen)

		now = datetime.datetime.utcnow()
		with mock.patch('datetime.datetime') as mock_datetime:
			mock_datetime.utcnow.return_value = now + datetime.timedelta(hours=1)
			self.family.cleanup(datetime.timedelta(seconds=30))

		self.assert_(label not in self.family.metric_seen)
		self.assert_(label not in self.family.metrics)


class TestRegistry(unittest.TestCase):
	def setUp(self):
		self.registry = Registry()

	def test_add_metric(self):
		self.assertEquals(0, len(self.registry))
		family = self.registry.add_metric(Counter, 'foo', 'test counter')
		self.assertEquals(1, len(self.registry))
		family2 = self.registry.add_metric(Counter, 'foo', 'test counter')
		self.assertEquals(1, len(self.registry))
		self.assertIs(family, family2)

	def test_invalid_ttl(self):
		self.assertRaises(ValueError, Registry, ('foo',))

	def test_metric_conflict(self):
		self.registry[(Counter, 'foo')] = MetricFamily(Counter, 'foo', '')

		try:
			self.registry[(Counter, 'foo')] = MetricFamily(Gauge, 'foo', '')
		except ValueError:
			pass
		else:
			assert False, 'did not throw ValueError'

	def test_render(self):
		counter = self.registry.add_metric(Counter, 'foo', 'test counter')
		counter.labels({}).inc(1)
		gauge = self.registry.add_metric(Gauge, 'bar', 'test gauge')
		gauge.labels({}).inc(1)
		self.assertEquals(
			'# HELP bar test gauge\n'
			'# TYPE bar gauge\n'
			'bar 1.0\n'
			'# HELP foo test counter\n'
			'# TYPE foo counter\n'
			'foo 1.0\n',
			self.registry.render()
		)

if __name__ == '__main__':
	unittest.main()
