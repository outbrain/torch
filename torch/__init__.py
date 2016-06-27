def main():
	from gevent.monkey import patch_all
	patch_all()
	import os
	from gevent import wsgi
	from .multi_app import MultiApp
	from .collector import PrometheusMetricCollector
	from .discovery import ConsulHandler, Service
	class QuietWSGIHandler(wsgi.WSGIHandler):
		"""WSGIHandler subclass that will not create an access log"""
		def log_request(self, *args):
			pass

	port = int(os.environ['SERVICE_PORT'])
	owner = os.environ['SERVICE_OWNER']
	service_type = os.environ['SERVICE_TYPE']

	application = MultiApp()

	metrics_prefix = '/metrics'
	metric_app = PrometheusMetricCollector(metrics_prefix)

	consul_prefix = '/health_check'
	consul_service = Service(port, consul_prefix, owner, service_type)
	consul_app = ConsulHandler(consul_prefix, consul_service)

	application.root = metric_app.report
	application.add_application(metrics_prefix, metric_app)
	application.add_application(consul_prefix, consul_app)

	httpd = wsgi.WSGIServer(('', port), application, handler_class=QuietWSGIHandler)
	try:
		httpd.serve_forever()
	except:
		httpd.stop()
