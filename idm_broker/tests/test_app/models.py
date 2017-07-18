from dirtyfields import DirtyFieldsMixin
from django.db import models


class Person(DirtyFieldsMixin, models.Model):
    name = models.CharField(max_length=20)
