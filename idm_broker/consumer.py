import logging

import celery.app
from celery.app.base import App
from django.apps import apps
from django.conf import settings
from django.db import connection
from kombu.mixins import ConsumerMixin
from kombu import Message


logger = logging.getLogger(__name__)


class BrokerTaskConsumer(ConsumerMixin):
    def __call__(self):
        idm_broker_config = apps.get_app_config('idm_broker')
        with idm_broker_config.broker.acquire(block=True) as conn:
            self.connection = conn
            self.run()

    def run(self, _tokens=1, **kwargs):
        try:
            super().run(_tokens=_tokens, **kwargs)
        finally:
            connection.close()

    def get_consumers(self, Consumer, channel):
        consumers = []
        for c in settings.IDM_BROKER['CONSUMERS']:
            callbacks = [self.get_send_task(name) for name in c['tasks']]
            consumers.append(Consumer(queues=c['queues'],
                                      accept=c.get('accept'),
                                      callbacks=callbacks,
                                      auto_declare=True))
        return consumers

    def get_send_task(self, name):
        def f(body, message):
            celery_app = celery.app.default_app
            print(type(celery_app))
            assert isinstance(celery_app, App)
            assert isinstance(message, Message)
            try:
                celery_app.send_task(name, kwargs={
                    'body': body,
                    'delivery_info': message.delivery_info,
                    'content_type': message.content_type,
                    'properties': message.properties,
                    'headers': message.headers,
                })
            except Exception:
                message.reject()
                logger.exception("Couldn't send task for '%s' (%s, %s)",
                                 name, message.delivery_tag, message.delivery_info['routing_key'], extra={
                        'body': body,
                        'delivery_info': message.delivery_info,
                    })
            else:
                message.ack()
                logger.debug("Sent task for '%s' (%s, %s)",
                             name, message.delivery_tag, message.delivery_info['routing_key'], extra={
                        'body': body,
                        'delivery_info': message.delivery_info,
                    })
        return f
