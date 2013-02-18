from django.db import models

# Create your models here.

class RecordHistory(models.Model):
	task_id = models.IntegerField()
	path = models.CharField(max_length=384, unique=True, blank=True)
	digest = models.CharField(max_length=384, unique=True, blank=True)
	uptime = models.DateTimeField(null=True, blank=True)
	class Meta:
		db_table = u'record_history'

class ProtoTest(models.Model):
	task_id = models.IntegerField()
	path = models.CharField(max_length=384, unique=True, blank=True)
	func = models.CharField(max_length=384, unique=True, blank=True)
	main_proto = models.IntegerField()
	sub_proto = models.IntegerField()
	result = models.CharField(max_length=512, unique=True, blank=True)
	class Meta:
		db_table = u'proto_test'
