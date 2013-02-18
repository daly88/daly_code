from django.db import models

# Create your models here.

class Task(models.Model):
    task_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=192, blank=True)
    host = models.IntegerField(null=True, blank=True)
    path_root = models.CharField(max_length=384, blank=True)
    qc = models.CharField(max_length=192, blank=True)
    coder = models.CharField(max_length=192, blank=True)
    svn_base = models.IntegerField(null=True, blank=True)
    svn_branch = models.CharField(max_length=384, blank=True)
    svn_finish = models.IntegerField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    last_update = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = u'task'
