# Torch: A Prometheus metrics aggregator

Torch is a web application meant to fill in for a use case the the Prometheus Pushgateway explicitly does not support, aggregating metrics.  This is useful for scenarios where standard code instrumentation fails such as a python web application which uses multiple worker processes.  If we use standard instrumentation, we would only get the results from whichever worker serves the page that Prometheus will scrape rather than the combined metrics from all of the worker processes.

## How to use

Install the torch python package. It will create a script named torch. You must set the port for torch to run on by setting the environment variable `SERVICE_PORT`

###Usage

    SERVICE_PORT=9092 torch

## How it works

Torch works via a simple HTTP interface.

Metrics are expected to be sent as JSON blobs with the following format:

    {
    	name: "The name of the metric",
    	description: "The description of the metric",
    	labels: {label1: "value1", label2: "value2"},
    	value: 1.2
    }

If the metric is a histogram you can define the bucket values via an additional "bucket" field to be sent as an array. If the buckets are not defined Torch will use these values by default:

    [.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, +Inf]

If custom bucket values are sent which do not end wit +Inf, torch will automatically add +Inf as the last bucket value.

Example of a histogram metric blob with custom bucket values

    {
    	name: "The name of the metric",
    	description: "The description of the metric",
    	labels: {label1: "value1", label2: "value2"},
    	value: 1.2,
    	buckets: [1, 2, 3, 5, 8, 13, +Inf]
    }


*Note: Torch does not support dynamic quantile calculation for the Summary metric type*

## Clients
A python client is included in the torch package, though implementing a client in other languages should be pretty easy.

## Routes

###	/metrics/
This will generate the scrape page formatted how Prometheus expects

###	/metrics
This will generate the scrape page formatted how Prometheus expects

###	/metrics/counter
Increment Counter

###	/metrics/gauge/inc
Increment Gauge

###	/metrics/gauge/dec
Decrement Gauge

###	/metrics/gauge/set
Set Gauge

###	/metrics/summary
Update Summary

###	/metrics/histogram
Update Histogram

