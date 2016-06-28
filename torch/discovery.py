import atexit
import sys
from signal import signal, SIGQUIT, SIGTERM
import consul
from webob import exc

class ConsulHandler(object):
	def __init__(self, prefix, service):
		self.service = service

		self.service.setup_deregistration()
		self.service.register()

	def __call__(self, request):
		""" Health check route """
		return exc.HTTPOk()


class Service(object):
	"""Represents a service registered or prepared to register with Consul"""
	def __init__(self, port, health_check, owner, service_type):
		self.name = service_type
		self.owner = owner
		self.health_check = health_check
		self.service_type = service_type
		self.port = int(port)
		self.service_id = '{}_{}'.format(self.name, self.port)

	def register(self):
		tags = {
			'owner': self.owner,
			'servicetype': self.service_type,
			'scrapeport': self.port
		}
		consul.Consul().agent.service.register(
			name=self.name,
			service_id=self.service_id,
			port=self.port,
			tags=['{}-{}'.format(k, v) for k, v in tags.iteritems()],
			check=consul.Check.http(
				url='http://127.0.0.1:{port}{path}'.format(port=self.port, path=self.health_check),
				interval='1s',
				timeout='1s',
			),
		)

	def setup_deregistration(self):
		setup_deregistration(self.service_id)


def deregister(service_id):
	"""Deregister a service from Consul"""
	consul.Consul().agent.service.deregister(service_id)

def setup_deregistration(service_id):
	"""Set up handlers to deregister a service from Consul on exit"""
	# deregister this service from Consul on uncaught exceptions and SIGINT
	atexit.register(deregister, service_id=service_id)

	# define handler to deregister this service on SIGQUIT AND SIGTERM
	def exit_handler(signum, frame):
		deregister(service_id=service_id)
		sys.exit(0)

	# set handler for SIGQUIT and SIGTERM
	for sig in (SIGQUIT, SIGTERM):
		signal(sig, exit_handler)
