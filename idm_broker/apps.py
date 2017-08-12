import json
from urllib.parse import urljoin

import collections
import kombu
from dirtyfields import DirtyFieldsMixin
from django.apps import AppConfig
from django.conf import settings
from django.db import connection
from django.db.models.signals import pre_delete, post_save
from rest_framework.renderers import JSONRenderer, BaseRenderer
from rest_framework.serializers import BaseSerializer

from kombu import Connection
from kombu.pools import connections


class _FakeRequest(object):
    def build_absolute_uri(self, url):
        return urljoin(settings.API_BASE, url)

    GET = {}


class IDMBrokerConfig(AppConfig):
    name = 'idm_broker'

    _notification_registry = collections.defaultdict(list)
    _related_notification_registry = collections.defaultdict(list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.broker = connections[Connection(hostname=settings.BROKER_HOSTNAME,
                                            ssl=settings.BROKER_SSL,
                                            virtual_host=settings.BROKER_VHOST,
                                            userid=settings.BROKER_USERNAME,
                                            password=settings.BROKER_PASSWORD,
                                            transport=settings.BROKER_TRANSPORT)]
        self.broker_prefix = settings.BROKER_PREFIX

    def ready(self):
        post_save.connect(self._instance_changed)
        pre_delete.connect(self._instance_deleted)

    def register_notification(self, *, serializer, exchange, model=None, renderer=JSONRenderer):
        if model is None:
            model = serializer.Meta.model
        if not isinstance(exchange, kombu.Exchange):
            exchange = kombu.Exchange(settings.BROKER_PREFIX + exchange, 'topic', durable=True)
        with self.broker.acquire(block=True) as conn:
            exchange(conn).declare()
        assert issubclass(serializer, BaseSerializer)
        assert issubclass(renderer, BaseRenderer)
        self._notification_registry[model].append((serializer, renderer, exchange))

    def register_notifications(self, registrations):
        for registration in registrations:
            self.register_notification(**registration)

    def register_related_notification(self, model, accessor):
        self._related_notification_registry[model].append(accessor)

    def _publish_change(self, sender, instance, **kwargs):
        needs_publish = instance._needs_publish
        instance._needs_publish = set()

        for serializer, renderer, exchange in self._notification_registry[sender]:
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
            renderer = renderer()
            assert isinstance(renderer, BaseRenderer)

            with self.broker.acquire(block=True) as conn:
                exchange = exchange(conn)
                representation = serializer.to_representation(instance)
                exchange.publish(exchange.Message(renderer.render(representation),
                                                  content_type=renderer.media_type),
                                 routing_key='{}.{}.{}'.format(representation.get('@type') or type(instance).__name__,
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

    def _instance_changed(self, sender, instance, created, force=False, **kwargs):
        if sender in self._notification_registry:
            publish_type = 'created' if created else 'changed'
            if not force and not created and isinstance(instance, DirtyFieldsMixin) and not instance.is_dirty():
                return
            # If we can see which fields have changed, then if all of those have auto_now=True, then we don't need to
            # publish anything
            if isinstance(instance, DirtyFieldsMixin):
                for field in instance.get_dirty_fields():
                    if not getattr(instance._meta.get_field(field), 'auto_now', False):
                        break
                else:
                    return
            self._needs_publish(instance, publish_type)
        if sender in self._related_notification_registry:
            for accessor in self._related_notification_registry[sender]:
                related = accessor(instance)
                if related:
                    self._instance_changed(sender=type(related), instance=related, created=False, force=True)

    def _instance_deleted(self, sender, instance, **kwargs):
        if sender in self._notification_registry:
            self._needs_publish(instance, 'deleted')
        if sender in self._related_notification_registry:
            for accessor in self._related_notification_registry[sender]:
                related = accessor(instance)
                if related:
                    self._instance_changed(sender=type(related), instance=related, created=False, force=True)
