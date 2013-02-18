# -*- coding: gbk -*-
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

class Profile(models.Model):
	user = models.ForeignKey(User, unique=True)
	realname = models.CharField('realname', max_length=64, blank=True, null=True)
	title = models.CharField('title', max_length=64, blank=True, null=True)
	class Meta:
		db_table = u'profile'


def create_user_profile(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
