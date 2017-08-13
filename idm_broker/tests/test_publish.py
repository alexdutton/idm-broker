import json

import kombu
from django.apps import apps
from django.db import transaction
from django.test import TransactionTestCase

from idm_broker.tests.test_app.models import Person, Robot


class NotificationTestCase(TransactionTestCase):

    def setUp(self):
        self.broker = apps.get_app_config('idm_broker').broker

    def testPersonCreate(self):
        with self.broker.acquire(block=True) as conn:
            queue = kombu.Queue(exclusive=True).bind(conn)
            queue.declare()
            queue.bind_to(exchange=kombu.Exchange('idm_broker.test.person'), routing_key='#')
            with transaction.atomic():
                person = Person(name='Alice')
                person.save()
            message = queue.get()
            self.assertIsInstance(message, kombu.Message)
            self.assertEqual(message.delivery_info['routing_key'],
                             'Person.created.{}'.format(str(person.id)))
            self.assertEqual(message.content_type, 'application/json')
            self.assertEqual(json.loads(message.body.decode())['name'], 'Alice')

    def testPersonCreateDelete(self):
        with self.broker.acquire(block=True) as conn:
            queue = kombu.Queue(exclusive=True).bind(conn)
            queue.declare()
            queue.bind_to(exchange=kombu.Exchange('idm_broker.test.person'), routing_key='#')
            with transaction.atomic():
                person = Person()
                person.save()
                person.delete()
            message = queue.get()
            self.assertIsNone(message)

    def testPersonDelete(self):
        with self.broker.acquire(block=True) as conn:
            queue = kombu.Queue(exclusive=True).bind(conn)
            queue.declare()
            queue.bind_to(exchange=kombu.Exchange('idm_broker.test.person'), routing_key='#')
            with transaction.atomic():
                person = Person()
                person.save()
            message = queue.get()
            with transaction.atomic():
                person.delete()
            message = queue.get()
            self.assertIsInstance(message, kombu.Message)
            self.assertEqual(message.delivery_info['routing_key'],
                             'Person.deleted.{}'.format(str(person.id)))
            self.assertEqual(message.content_type, 'application/json')


    def testNoNotifcationWhenNotChanged(self):
        with self.broker.acquire(block=True) as conn:
            with transaction.atomic():
                person = Person()
                person.save()
            queue = kombu.Queue(exclusive=True).bind(conn)
            queue.declare()
            queue.bind_to(exchange=kombu.Exchange('idm_broker.test.person'), routing_key='#')
            with transaction.atomic():
                person.save()
            message = queue.get()
            self.assertIsNone(message)

    def testNoNotifcationWhenOnlyModifiedChanged(self):
        # Robot has an auto_now field
        with self.broker.acquire(block=True) as conn:
            with transaction.atomic():
                robot = Robot()
                robot.save()
            queue = kombu.Queue(exclusive=True).bind(conn)
            queue.declare()
            queue.bind_to(exchange=kombu.Exchange('idm_broker.test.person'), routing_key='#')
            with transaction.atomic():
                robot.save()
            message = queue.get()
            self.assertIsNone(message)

    def testNotifcationWhenChanged(self):
        with self.broker.acquire(block=True) as conn:
            with transaction.atomic():
                person = Person()
                person.save()
            queue = kombu.Queue(exclusive=True).bind(conn)
            queue.declare()
            queue.bind_to(exchange=kombu.Exchange('idm_broker.test.person'), routing_key='#')
            with transaction.atomic():
                person.name = 'Bob'
                person.save()
            message = queue.get()
            self.assertIsInstance(message, kombu.Message)
            self.assertEqual(message.delivery_info['routing_key'],
                             'Person.changed.{}'.format(str(person.id)))
            self.assertEqual(message.content_type, 'application/json')
            self.assertEqual(json.loads(message.body.decode())['name'], 'Bob')
