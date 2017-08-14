import logging
import threading

import celery.app
from django.apps import apps
from django.conf import settings
from django.db import connection
from kombu.mixins import ConsumerMixin
from kombu import Message


logger = logging.getLogger(__name__)


class BrokerTaskConsumer(ConsumerMixin):
    """
    A kombu :py:class:`kombu.mixins.ConsumerMixin` that consumes from queues declared in
    ``settings.IDM_BROKER['CONSUMERS']``, and dispatches each message received to one or more configured celery tasks.
    """
    ready = None  # type: threading.Event

    def __init__(self):
        super().__init__()
        self.ready = threading.Event()

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
            callbacks = [self.get_callback(name) for name in c['tasks']]
            consumers.append(Consumer(queues=c['queues'],
                                      accept=c.get('accept'),
                                      callbacks=callbacks,
                                      auto_declare=True))
        return consumers

    def on_consume_ready(self, connection, channel, consumers, **kwargs):
        super().on_consume_ready(connection, channel, consumers, **kwargs)
        self.ready.set()

    @classmethod
    def get_callback(cls, task_name):
        def f(body, message: Message):
            celery_app = celery.app.default_app  # type: celery.app.base.App
            try:
                celery_app.send_task(task_name, kwargs={
                    'body': body,
                    'delivery_info': message.delivery_info,
                    'content_type': message.content_type,
                    'properties': message.properties,
                    'headers': message.headers,
                })
            except Exception:  # pragma: nocover
                message.reject()
                logger.exception("Couldn't send task for '%s' (%s, %s)",
                                 task_name, message.delivery_tag, message.delivery_info['routing_key'], extra={
                        'body': body,
                        'delivery_info': message.delivery_info,
                    })
            else:
                message.ack()
                logger.debug("Sent task for '%s' (%s, %s)",
                             task_name, message.delivery_tag, message.delivery_info['routing_key'], extra={
                        'body': body,
                        'delivery_info': message.delivery_info,
                    })
        return f
