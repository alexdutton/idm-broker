import http.client
import logging

import celery.app
import defusedxml.lxml
from django.apps import apps
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
import lxml.etree

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class XMLConsumeView(View):
    """A view to which one POSTs XML documents, which are then queued for processing"""

    xpath = None
    namespaces = {}
    content_type = 'application/xml'

    def post(self, request, **kwargs):
        if request.META.get('CONTENT_TYPE') != self.content_type:
            return HttpResponse(status=http.client.NOT_ACCEPTABLE)

        try:
            data = defusedxml.lxml.parse(request)
        except lxml.etree.XMLSyntaxError as e:
            return HttpResponseBadRequest("XML syntax error: {}\n".format(e))
        if self.xpath:
            items = data.xpath(self.xpath, namespaces=self.namespaces)
            print(items)
        else:
            items = [data]

        for item in items:
            self.process_item(request, item)

        return HttpResponse(status=http.client.ACCEPTED)

    def process_item(self, request, item):
        pass


class XMLConsumeToExchangeView(XMLConsumeView):
    exchange = None
    _bound_exchange = None

    def post(self, request, **kwargs):
        broker = apps.get_app_config('idm_broker').broker
        with broker.acquire(block=True) as conn:
            self._bound_exchange = self.exchange(conn)
            super().post(request, **kwargs)

    def process_item(self, request, item):
        exchange = self._bound_exchange
        exchange.publish(exchange.Message(defusedxml.lxml.tostring(item),
                                          content_type='application/xml'))
        super().process_item(request, item)


class XMLConsumeToTaskView(XMLConsumeView):
    task_name = None

    def process_item(self, request, item):
        celery_app = celery.app.default_app  # type: celery.app.base.App
        body = defusedxml.lxml.tostring(item, encoding='utf-8').decode('utf-8')
        try:
            celery_app.send_task(self.task_name, kwargs={
                'body': body,
                'content_type': 'application/xml'
            })
        except:  # pragma: nocover
            logger.exception("Couldn't send task for '%s'", self.task_name,
                             extra={'body': body})
            raise
        super().process_item(request, item)
