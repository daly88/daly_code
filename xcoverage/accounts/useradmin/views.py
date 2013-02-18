# -*- coding: gbk -*-
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib import auth
from django.contrib.auth import logout
from django.contrib.auth.models import User 
from accounts.models import Profile
from base.utils import *
import datetime
import time


def get_profile(user):
	profile = None
	try:
		profile = user.get_profile()
	except Profile.DoesNotExist:
		profile = Profile.objects.create(user=user)

	return profile

def do_modify(req):
	user = req.user
	if user is not None and user.is_active:
		username = user.username
	else:
		return HttpResponseRedirect('/login')

	mp = {}
	mp['username'] = username
	pf = get_profile(user)
	if pf.title == 'qc':
		mp['title'] = 'QC'
	else:
		mp['title'] = '����'.decode('gbk')

	if req.method == 'GET':
		return render_to_response("profile.html", mp)	

	
	password = req.POST.get('password', '').replace('"','\\').replace("'",'\\')
	p2 = req.POST.get('password2', '').replace('"','\\').replace("'",'\\')
	
	if password != p2:
		return render_to_response("profile.html", {'error':'�����������벻һ��'.decode('gbk')})

	user.set_password(password)
	user.save()
	return render_to_response("profile.html", {'error':'�޸ĳɹ�'.decode('gbk')})

def do_regist(req):
	if req.method == 'GET':
		return render_to_response("regist.html")	

	username = req.POST.get('username', '').replace('"','\\').replace("'",'\\')
	password = req.POST.get('password', '').replace('"','\\').replace("'",'\\')
	password_confirm = req.POST.get('password2', '')
	if len(username) < 2 or len(password) < 2 or len(username) > 20 or len(password) > 20:
		return render_to_response("regist.html", {'error':'�û�����������Ч'.decode('gbk')})

	if password != password_confirm:
		return render_to_response("regist.html", {'error':'�����������벻һ��'.decode('gbk')})

	try: 
		user = User.objects.get(username=username)
		if user is not None:
			return render_to_response("regist.html", {'error':'���û����Ѵ���'.decode('gbk')})
	except:
		pass
	
	user = User.objects.create_user(username, password)
	if user is not None:
		user.set_password(password)
		user.save()
		log('regist %s' % username)
		profile = get_profile(user)
		profile.title = req.POST.get('title', '')
		profile.save()

		return HttpResponseRedirect('/login')
	else:
		return HttpResponseRedirect('/login')


