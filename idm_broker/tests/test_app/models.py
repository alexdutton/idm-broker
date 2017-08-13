from dirtyfields import DirtyFieldsMixin
from django.db import models


class Person(DirtyFieldsMixin, models.Model):
    name = models.CharField(max_length=20)

class Robot(DirtyFieldsMixin, models.Model):
    name = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
