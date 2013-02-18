from django.db import models

class Record(models.Model):
    task_id = models.IntegerField(unique=True, null=True, blank=True)
    path = models.CharField(max_length=254, blank=True)
    confirm = models.SmallIntegerField(null=True, blank=True)
    class Meta:
        db_table = u'record'
