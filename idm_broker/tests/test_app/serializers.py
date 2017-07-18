from rest_framework import serializers

from . import models


class PersonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Person
        fields = ('url', 'name')
