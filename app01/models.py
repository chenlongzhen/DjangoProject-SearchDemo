from django.db import models

# Create your models here.
class Publisher(models.Model):
    name = models.TextField(max_length=1024)
    key = models.TextField(max_length=1024, default='None')


