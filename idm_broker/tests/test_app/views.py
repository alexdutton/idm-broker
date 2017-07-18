from rest_framework.viewsets import ModelViewSet

from . import models, serializers


class PersonViewSet(ModelViewSet):
    serializer_class = serializers.PersonSerializer
    queryset = models.Person.objects.all()
