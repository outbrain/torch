def main():
	from gevent.monkey import patch_all
	patch_all()
	import os
	from datetime import timedelta
	from gevent import wsgi
	import gevent.socket as socket
	from .collector import PrometheusMetricCollector
	class QuietWSGIHandler(wsgi.WSGIHandler):
		"""WSGIHandler subclass that will not create an access log"""
		def log_request(self, *args):
			pass

	if os.environ.get('LISTEN_FDS') == '1' and \
			os.environ.get('LISTEN_PID') == str(os.getpid()):
		listener = socket.fromfd(3, socket.AF_UNIX, socket.SOCK_STREAM)
	else:
		listener = ('0.0.0.0', int(os.environ['SERVICE_PORT']))

	ttl = timedelta(hours=int(os.environ.get('TORCH_TTL', 24)))
	metrics_prefix = '/metrics'

	application = PrometheusMetricCollector(prefix=metrics_prefix, ttl=ttl)

	httpd = wsgi.WSGIServer(listener, application, handler_class=QuietWSGIHandler)
	try:
		httpd.serve_forever()
	except:
		httpd.stop()
