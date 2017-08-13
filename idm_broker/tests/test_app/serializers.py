from rest_framework import serializers

from . import models


class RobotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Robot
        fields = ('url', 'name', 'created', 'modified')


class PersonSerializer(serializers.HyperlinkedModelSerializer):
    robots = RobotSerializer(many=True, read_only=True)
    class Meta:
        model = models.Person
        fields = ('url', 'name', 'robots')
