import http.client
from unittest import mock

import kombu
from django.apps import apps
from rest_framework.test import APITestCase

from idm_broker.tests.test_app.celery import app as celery_app


class ConsumeViewTestCase(APITestCase):
    data = b'<some-xml xmlns="http://example.org/"><child attr="one"/><child attr="two"/></some-xml>'

    def setUp(self):
        self.broker = apps.get_app_config('idm_broker').broker

    @mock.patch.object(celery_app, 'send_task')
    def test_task_queued(self, send_task):
        response = self.client.post('/api/xml-consume-to-task/',
                                    data=self.data,
                                    content_type='application/xml')
        self.assertEqual(response.status_code, http.client.ACCEPTED)

        self.assertEqual(1, send_task.call_count)
        self.assertEqual(self.data.decode(), send_task.call_args[1]['kwargs']['body'])
        self.assertEqual('application/xml', send_task.call_args[1]['kwargs']['content_type'])

    @mock.patch.object(celery_app, 'send_task')
    def test_tasks_queued_xpath(self, send_task):
        response = self.client.post('/api/xml-consume-to-task-xpath/',
                                    data=self.data,
                                    content_type='application/xml')
        self.assertEqual(response.status_code, http.client.ACCEPTED)

        self.assertEqual(2, send_task.call_count)
        self.assertEqual('<child xmlns="http://example.org/" attr="one"/>',
                         send_task.call_args_list[0][1]['kwargs']['body'])
        self.assertEqual('<child xmlns="http://example.org/" attr="two"/>',
                         send_task.call_args_list[1][1]['kwargs']['body'])
        self.assertEqual('application/xml', send_task.call_args_list[0][1]['kwargs']['content_type'])
        self.assertEqual('application/xml', send_task.call_args_list[1][1]['kwargs']['content_type'])

    @mock.patch.object(celery_app, 'send_task')
    def test_not_acceptable(self, send_task):
        response = self.client.post('/api/xml-consume-to-task/',
                                    data=self.data,
                                    content_type='text/plain')
        self.assertEqual(response.status_code, http.client.NOT_ACCEPTABLE)
        self.assertFalse(send_task.called)

    @mock.patch.object(celery_app, 'send_task')
    def test_invalid_xml(self, send_task):
        response = self.client.post('/api/xml-consume-to-task/',
                                    data=b'<test><bar></test>',
                                    content_type='application/xml')
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)
        self.assertFalse(send_task.called)

    def test_published(self):
        with self.broker.acquire(block=True) as conn:
            queue = kombu.Queue(exclusive=True).bind(conn)
            queue.declare()
            queue.bind_to(exchange=kombu.Exchange('idm_broker.test.xml'), routing_key='#')

            response = self.client.post('/api/xml-consume-to-exchange/',
                                        data=self.data,
                                        content_type='application/xml')
            self.assertEqual(response.status_code, http.client.ACCEPTED)

            message = queue.get()
            self.assertIsInstance(message, kombu.Message)
            self.assertEqual(message.delivery_info['routing_key'], 'xml-routing-key')
            self.assertEqual(message.content_type, 'application/xml')

