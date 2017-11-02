from django.conf.urls import include, url
from rest_framework import routers

from idm_broker.views import XMLConsumeToTaskView
from . import views

router = routers.DefaultRouter()
router.register('person', views.PersonViewSet, base_name='person')
router.register('robot', views.RobotViewSet, base_name='robot')


urlpatterns = [
    url(r'^api/xml-consume-to-task/$', XMLConsumeToTaskView.as_view(task_name='idm_broker.tests.tasks.test_task')),
    url(r'^api/', include(router.urls)),
]