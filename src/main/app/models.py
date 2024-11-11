""" Models for database interaction."""

from django.db import models


class BaseKPI(models.Model):
    """Represents a base KPI (that has to be taken from the database)."""

    name = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)
    value = models.FloatField()
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.name} - {self.machine} - {self.value} - {self.timestamp}"
