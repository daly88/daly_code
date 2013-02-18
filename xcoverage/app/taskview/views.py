# -*- coding: gbk -*-


from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from app.qcover.models import Task
from app.taskview.models import Record
from base.cover_tool import * 

RESULT_PATH = 'repository/result/'

def get_fileinfo(taskid, file):
	cov = CoverAnalyzer(RESULT_PATH, file, taskid)
	r = cov.load_from_xml()
	if r == 0: return {}

	info = {}
	#calculate cover info
	info['diff_cnt'] = cov.diff_branch
	info['diff_cover'] = cov.diff_cover
	info['name'] = file
	if cov.do_diff == 0:
		info['diff_cnt'] = cov.branch_count
		info['diff_cover'] = cov.cover_count

	if info['diff_cnt'] > 0: 
		info['diff_cover_rate'] = info['diff_cover'] * 100 / info['diff_cnt']
	else:
		info['diff_cover_rate'] = 0
	return info

def get_filelist(tid):
	dat = Record.objects.filter(task_id=tid)
	ls = []
	for r in dat:
		ls.append(r.path)

	return ls

def get_taskinfo(tid):
	dat = Task.objects.filter(task_id=tid)
	if len(dat) > 0:
		return dat[0].svn_branch

	return ''

@login_required
def get_page(req):
	tid = int(req.GET.get('taskid', 0))
	ls = get_filelist(tid)
	user = req.user
	mp = {}
	mp['filelist'] = ls
	mp['fileinfo'] = {}
	for f in ls:
		info = get_fileinfo(tid, f)
		mp['fileinfo'][f] = info

	mp['tid'] = tid
	mp['branch'] = get_taskinfo(tid)
	mp['taskid'] = tid
	mp['username'] = user.username

	task = Task.objects.get(task_id=tid)
	taskinfo = {}
	
	if task is not None:
		taskinfo['path_root'] = task.path_root
		taskinfo['name'] = task.name
		taskinfo['svn_branch'] = task.svn_branch
		taskword = {0:'未测试', 1: '测试中', 2:'已关闭'}
		taskinfo['status'] = taskword.get(task.status, '未测试').decode('gbk')
		taskinfo['svnbase'] = task.svn_base
		if task.status != 2 and (user.username == task.coder or user.username == task.qc):
			taskinfo['action'] = ('<a href="/task_action?taskid=%d">关闭任务</a>' % tid).decode('gbk')
	mp['task'] = taskinfo
	return render_to_response('taskview.html', mp)

@login_required
def do_task_action(req):
	tid = int(req.GET.get('taskid', 0))
	user = req.user
	task = None
	try:
		task = Task.objects.get(task_id=tid)
	except:
		return HttpResponseRedirect('/task?taskid=%d' % tid)	

	task.status = 2
	task.save()	
	return HttpResponseRedirect('/task?taskid=%d' % tid)
