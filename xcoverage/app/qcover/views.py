# -*- coding: gbk -*-
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from app.qcover.models import Task
from django.db.models import Q
import datetime
import time

def get_tasklist(username, status, taskname):
	result = []
	task_dat = None
	if len(taskname) > 1:
		task_dat = Task.objects.filter(Q(name=taskname))
	elif len(username) > 1:
		if status == 'open':
			task_dat = Task.objects.filter(Q(coder=username) | Q(qc=username), Q(status=0)|Q(status=1))
		else:
			task_dat = Task.objects.filter(Q(coder=username) | Q(qc=username))
	else:
		if status == 'open':
			task_dat = Task.objects.filter(Q(status=0)|Q(status=1))
		else:
			task_dat = Task.objects.all()

	task_dat = task_dat.order_by('-last_update')
	task_dat = task_dat[:30]

	for task in task_dat:
		date = task.last_update.strftime("%Y-%m-%d %H:%M")
		a = task.path_root.split('/')
		if a[1] == 'home' or a[1] == 'home1': a = a[2:]
		if a[0] == 'home' or a[0] == 'home1': a = a[1:]
		path_root = '/'.join(a[0:2])
		status = '未测试'
		if task.status == 1:
			status = '测试中'
		elif task.status == 2:
			status = '已关闭'
		result.append( {'name':task.name, 'id':task.task_id, 'path_root':path_root, 
				'qc':task.qc, 'programmer':task.coder,
				'date':date, 'status':status.decode('gbk')} )
		
	return result 

@login_required
def get_page(req):
	mp = {}
	user = req.user
	if user is not None and user.is_active:
		mp['username'] = user.username
	else:
		mp['username'] = 'Welcome'

	member = req.GET.get('member', 'me')
	status = req.GET.get('status', 'open')
	taskname = req.GET.get('taskname', '')
	task = None 
	if member == 'me' or member == '':
		task = get_tasklist(user.username, status, taskname)
	elif member == 'all':
		task = get_tasklist('', status, taskname)
	else:
		task = get_tasklist(member, status, taskname)
	mp['tasklist'] = task
	return render_to_response('qcover.html', mp)

