def main():
	from gevent.monkey import patch_all
	patch_all()
	import os
	from datetime import timedelta
	from gevent import wsgi
	from .collector import PrometheusMetricCollector
	class QuietWSGIHandler(wsgi.WSGIHandler):
		"""WSGIHandler subclass that will not create an access log"""
		def log_request(self, *args):
			pass

	port = int(os.environ['SERVICE_PORT'])
	ttl = timedelta(hours=int(os.environ.get('TORCH_TTL', 24)))
	metrics_prefix = '/metrics'

	application = PrometheusMetricCollector(prefix=metrics_prefix, ttl=ttl)

	httpd = wsgi.WSGIServer(('0.0.0.0', port), application, handler_class=QuietWSGIHandler)
	try:
		httpd.serve_forever()
	except:
		httpd.stop()
