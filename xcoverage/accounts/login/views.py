# -*- coding: gbk -*-
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib import auth
from django.contrib.auth import logout
import datetime
import time

def get_page(req):
	iscb = req.POST.get('cb_tag', '')
	if len(iscb) < 1: 
		resp = render_to_response('login.html')
		return resp

	username = req.POST.get('username', '')
	passwd = req.POST.get('passwd', '')
	user = auth.authenticate(username=username, password=passwd)
	if user is not None and user.is_active:
		auth.login(req, user)
		return HttpResponseRedirect('/xyq_cover')
	else:
		return render_to_response('login.html', {'error':'密码或用户名错误'.decode('gbk')})
	

def do_logout(req):
	logout(req)
	return HttpResponseRedirect('/login')
