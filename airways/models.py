from django.db import models


class Resource(models.Model):
    name = models.CharField(max_length=100)


class Event(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
