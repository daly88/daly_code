# Create your views here.
import os,sys
from django.template import RequestContext
from django.http import HttpResponse
from django.db import connection

REPO_PATH = 'repository/'

def get_result(req):
	if req.method == 'POST':
		dat = req.FILES['file'].read()
		name = req.POST.get('filename', '')
		path = req.POST.get('path', '')
		taskid = int(req.POST.get('taskid', '0'))
		is_xml = 0
		#check filename
		if name.find('..') != -1:
			return HttpResponse('-2 filename invalid')

		if name[-2:] != '.c' and name[-4:] != '.xml':
			return HttpResponse('-2 filetype invalid %s' % name)
		seg = name.split('.')
		if len(seg) < 2 or len(seg) > 5:
			return HttpResponse('-2 filename invalid')
		
		repo_path = REPO_PATH + 'src/'
		if name.find('.xml') != -1:
			repo_path = REPO_PATH + 'result/'
			is_xml = 1

		if name[-2:] == '.c':
			name = name[:-2] + '.%d.c' % taskid

		if not os.path.isdir(repo_path + path):
			try:
				os.makedirs(repo_path + path, 0755)
			except:
				return HttpResponse('-100 repository error')

		try:
			whole_filename = path + name
			real_path = repo_path + path + name
			max_id = 0
			#found max_id of history submit
			sql = "select max(id) from submit_record where taskid=%d and file='%s'" % (taskid, whole_filename)
			cur = connection.cursor()
			try:
				cur.execute(sql)
				rows = cur.fetchall()
				if rows: max_id = rows[0][0]
			except:
				return HttpResponse('-2 DB failed')

			if os.path.isfile(real_path):
				#file exist
				try:
					os.system('mv %s %s.%d' % (real_path, real_path, max_id))
				except:
					pass

			f = open(real_path, 'w')
			f.write(dat)
			f.close()
			#add to submit_record
			if is_xml == 1:
				cur = connection.cursor()
				sql = "insert into submit_record values(NULL,%d,'%s',1,0,0,NULL)" % (taskid, whole_filename)
				try:
					cur.execute(sql)
				except:
					return HttpResponse('-2 DB failed')

			return HttpResponse('200 OK')
		except:
			return HttpResponse('-1 failed')

	elif req.method == 'GET':
		return HttpResponse('-100 failed')
