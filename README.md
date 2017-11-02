# idm-broker

[![Build Status](https://travis-ci.org/alexsdutton/idm-broker.svg?branch=master)](https://travis-ci.org/alexsdutton/idm-broker) [![codecov](https://codecov.io/gh/alexsdutton/idm-brokerbranch/master/graph/badge.svg)](https://codecov.io/gh/alexsdutton/idm-broker)

A common-use module to support:

* consuming messages from a kombu queue and passing them to celery tasks
* publishing `django-rest-framework`-serialized representations to kombu exchanges when model instances change and the
  transaction has been successfully committed
* receiving XML POSTed to an API, optionally chopping it up, and piping it to a kombu exchange or celery task

Together, these provide inbound and outbound messaging for including Django applications in an event-driven
architecture.

This package supports a prototypical [idm implementation](https://github.com/alexsdutton/idm), and no guarantees are
made about its wider applicability or stability.

## Usage

To consume messages into tasks, add a section like this to your Django settings:

    import kombu

    IDM_BROKER = {
        'CONSUMERS': [{
            'queues': [kombu.Queue('queue-name',
                                   exchange=kombu.Exchange('exchange-name', type='topic'),
                                   routing_key='#')],
            'tasks': ['your_app.tasks.do_something'],
        }],
    }

To publish model changes to a kombu exchange, add this to your Django `AppConfig`'s `ready()` method:

    def ready(self):
        from . import models, serializers

        apps.get_app_config('idm_broker').register_notifications([
            {'serializer': serializers.UserSerializer, 'exchange': 'user'},
        ])

