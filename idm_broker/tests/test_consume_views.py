import http.client
from unittest import mock

from rest_framework.test import APITestCase

from idm_broker.tests.test_app.celery import app as celery_app


class ConsumeViewTestCase(APITestCase):
    @mock.patch.object(celery_app, 'send_task')
    def test_task_queued(self, send_task):
        data = b'<some-xml><child attr="one"/><child attr="two"/></some-xml>'

        response = self.client.post('/api/xml-consume-to-task/',
                                    data=data,
                                    content_type='application/xml')
        self.assertEqual(response.status_code, http.client.ACCEPTED)

        self.assertEqual(1, send_task.call_count)
        self.assertEqual(data.decode(), send_task.call_args[1]['kwargs']['body'])
        self.assertEqual('application/xml', send_task.call_args[1]['kwargs']['content_type'])
