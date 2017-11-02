import kombu
from django.conf.urls import include, url
from rest_framework import routers

from idm_broker.views import XMLConsumeToTaskView, XMLConsumeToExchangeView
from . import views

router = routers.DefaultRouter()
router.register('person', views.PersonViewSet, base_name='person')
router.register('robot', views.RobotViewSet, base_name='robot')


urlpatterns = [
    url(r'^api/xml-consume-to-exchange/$',
        XMLConsumeToExchangeView.as_view(exchange=kombu.Exchange('idm_broker.test.xml', type='topic'),
                                         routing_key='xml-routing-key')),
    url(r'^api/xml-consume-to-task/$',
        XMLConsumeToTaskView.as_view(task_name='idm_broker.tests.tasks.test_task')),
    url(r'^api/xml-consume-to-task-xpath/$',
        XMLConsumeToTaskView.as_view(task_name='idm_broker.tests.tasks.test_task',
                                     xpath='/ex:some-xml/ex:child',
                                     namespaces={'ex': 'http://example.org/'})),
    url(r'^api/', include(router.urls)),
]