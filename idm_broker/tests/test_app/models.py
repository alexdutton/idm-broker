from dirtyfields import DirtyFieldsMixin
from django.db import models


class Person(DirtyFieldsMixin, models.Model):
    name = models.CharField(max_length=20)


class Robot(DirtyFieldsMixin, models.Model):
    name = models.CharField(max_length=20)
    owner = models.ForeignKey(Person, null=True, blank=True, related_name='robots')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
