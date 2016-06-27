from setuptools import setup, find_packages

setup(name='torch',
      version='0.0',
      description="Prometheus aggregator",
      long_description="""A Prometheus aggregator which registers with Consul for discovery purposes""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      author='Joshua Forman',
      author_email='jforman@outbrain.com',
      url='http://www.outbrain.com',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=False,
      zip_safe=True,
      install_requires=[
          'WebOb',
          'python-consul',
          'gevent',
          'prometheus_client',
      ],
      entry_points="""
      [console_scripts]
      torch = torch.__main__:main
      """
      )
