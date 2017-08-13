from django.conf.urls import include, url
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register('person', views.PersonViewSet, base_name='person')
router.register('robot', views.RobotViewSet, base_name='robot')


urlpatterns = [
    url(r'^api/', include(router.urls)),
]