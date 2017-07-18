from django.conf.urls import include, url
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register('oidc/client',views.PersonViewSet, base_name='person')


urlpatterns = [
    url(r'^api/', include(router.urls)),
]