from django.db import models

# Create your models here.
class SearchDB(models.Model):
    key = models.TextField(max_length=1024)
    value = models.TextField(max_length=1024)


