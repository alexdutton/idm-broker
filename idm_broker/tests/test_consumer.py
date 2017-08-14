import json
import logging
from unittest import mock

import kombu
from django.apps import apps
from django.test import TestCase

from idm_broker.management.commands.broker_task_consumer import Command as BrokerTaskConsumerCommand
from idm_broker.tests.test_app.celery import app as celery_app
from idm_broker.tests.utils import BrokerTaskConsumerTestCaseMixin


class ConsumerTestCase(BrokerTaskConsumerTestCaseMixin, TestCase):
    @mock.patch.object(celery_app, 'send_task')
    def test_task_queued(self, send_task):
        message_body = {'key': 'value'}
        delivery_info = {'routing_key': 'a.b.c',
                         'delivery_tag': 1,
                         'exchange': 'test.exchange',
                         'consumer_tag': 'None1',
                         'redelivered': False}
        headers = {'X-Priority': 'High'}

        idm_broker_config = apps.get_app_config('idm_broker')
        with idm_broker_config.broker.acquire(block=True) as conn:
            exchange = kombu.Exchange('test.exchange', type='topic').bind(conn)
            self.assertIsInstance(exchange, kombu.Exchange)

            message = exchange.Message(
                body=json.dumps(message_body).encode(),
                content_type='application/json',
                headers=headers,
            )

            # Wait for the consumer to be ready, publish, then wait until it's stopped. Otherwise, plenty of races are
            # possible
            self.broker_task_consumer.ready.wait(timeout=5)
            exchange.publish(message, routing_key=delivery_info['routing_key'])
            self.broker_task_consumer.should_stop = True
            self.broker_task_consumer_thread.join()

            self.assertEqual(1, send_task.call_count)
            self.assertEqual(message_body, send_task.call_args[1]['kwargs']['body'])
            self.assertEqual(headers, send_task.call_args[1]['kwargs']['headers'])
            self.assertEqual('application/json', send_task.call_args[1]['kwargs']['content_type'])


@mock.patch('idm_broker.consumer.BrokerTaskConsumer')
class ManagementCommandTestCase(TestCase):
    def testNormalInvocation(self, broker_task_consumer_cls):
        command = BrokerTaskConsumerCommand()
        options = {'verbosity': 0}

        broker_task_consumer = mock.Mock()
        broker_task_consumer_cls.return_value = broker_task_consumer
        command.handle(**options)
        self.assertEqual(1, broker_task_consumer_cls.call_count)
        self.assertEqual(1, broker_task_consumer.call_count)

    def testVerboseInvocation(self, broker_task_consumer_cls):
        command = BrokerTaskConsumerCommand()
        options = {'verbosity': 2}

        broker_task_consumer = mock.Mock()
        broker_task_consumer_cls.return_value = broker_task_consumer
        command.handle(**options)
        self.assertEqual(1, broker_task_consumer_cls.call_count)
        self.assertEqual(1, broker_task_consumer.call_count)
        self.assertEqual(logging.DEBUG, logging.getLogger().level)
