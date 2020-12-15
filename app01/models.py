from django.db import models
import django.utils.timezone as timezone

# Create your models here.
class SearchDB(models.Model):
    key = models.TextField(max_length=1024)
    key_pinyin = models.TextField(max_length=1024, default='')
    value = models.TextField(max_length=1024)

class ActivityDB(models.Model):
    key = models.TextField(max_length=1024)
    key_pinyin = models.TextField(max_length=1024, default='')
    value = models.TextField(max_length=1024)
    st_dt = models.DateField(default = timezone.now)
    ed_dt = models.DateField(default = timezone.now)

class BlackBoxDB(models.Model):
    key = models.TextField(max_length=1024)
    key_pinyin = models.TextField(max_length=1024, default='')
    value = models.TextField(max_length=1024)

class Search2SearchDB(models.Model):
    key = models.TextField(max_length=1024)
    key_pinyin = models.TextField(max_length=1024, default='')
    value = models.TextField(max_length=1024)
