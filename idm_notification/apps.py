import json
from urllib.parse import urljoin

import kombu
from dirtyfields import DirtyFieldsMixin
from django.apps import AppConfig
from django.conf import settings
from django.db import connection
from django.db.models.signals import pre_delete, post_save

from . import broker


class _FakeRequest(object):
    def build_absolute_uri(self, url):
        return urljoin(settings.API_BASE, url)

    GET = {}


class NotificationConfig(AppConfig):
    name = 'idm_notification'

    _notification_registry = {}

    def ready(self):
        post_save.connect(self._instance_changed)
        pre_delete.connect(self._instance_deleted)

    def register(self, model, serializer, exchange):
        if not isinstance(exchange, kombu.Exchange):
            exchange = kombu.Exchange(settings.BROKER_PREFIX + exchange, 'topic', durable=True)
        with broker.connection.acquire(block=True) as conn:
            exchange(conn).declare()
        self._notification_registry[model] = (serializer, exchange)

    def register_many(self, registrations):
        for registration in registrations:
            self.register(*registration)

    def _publish_change(self, sender, instance, **kwargs):
        serializer, exchange = self._notification_registry[sender]

        needs_publish = instance._needs_publish
        instance._needs_publish = set()

        if 'created' in needs_publish and 'deleted' in needs_publish:
            return
        elif not needs_publish:
            return
        elif 'deleted' in needs_publish:
            publish_type = 'deleted'
        elif 'created' in needs_publish:
            publish_type = 'created'
        else:
            publish_type = 'changed'

        serializer = serializer(context={'request': _FakeRequest()})

        with broker.connection.acquire(block=True) as conn:
            exchange = exchange(conn)
            exchange.publish(exchange.Message(json.dumps(serializer.to_representation(instance)),
                                              content_type='application/json'),
                             routing_key='{}.{}.{}'.format(type(instance).__name__,
                                                           publish_type,
                                                           instance.pk))

    def _needs_publish(self, instance, publish_type):
        sender = type(instance)
        assert sender in self._notification_registry
        try:
            instance._needs_publish.add(publish_type)
        except AttributeError:
            instance._needs_publish = {publish_type}
        connection.on_commit(lambda: self._publish_change(sender, instance))

    def _instance_changed(self, sender, instance, created, **kwargs):
        if sender in self._notification_registry:
            publish_type = 'created' if created else 'changed'
            if not created and isinstance(instance, DirtyFieldsMixin) and not instance.is_dirty():
                return
            self._needs_publish(instance, publish_type)

    def _instance_deleted(self, sender, instance, **kwargs):
        if sender in self._notification_registry:
            self._needs_publish(instance, 'deleted')
