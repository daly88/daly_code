# -*- coding: gbk -*-

#cover result display

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import Template, Context
from django.template.loader import get_template
from base.lpc_util import *
from base.cover_tool import *
from app.taskview.models import Record
from app.qcover.models import Task
import os,sys
from django.db import connection

SRC_PATH = 'repository/src/'
RESULT_PATH = 'repository/result/'


RUNNED = 1
UNRUNNED = 2
UNRUN_NODIFF = 3

def html_convert(line):
	s = line.replace('\t', '&nbsp&nbsp&nbsp&nbsp')
	s = s.replace('  ', '&nbsp&nbsp')
	s = s.replace('<', '&lt')
	s = s.replace('>', '&gt')
	return s

class HtmlCoverOutput():
	IGNORE = 1
	COVERED_SHOW = 2
	COVERED_HIDE = 4
	UNCOVER_SHOW = 8  #highlight and show the code
	UNCOVER_HIDE = 16   #hide the code segment and show notice
	def __init__(self, src, file, result, taskid):
		self.block = result.codetree.root
		self.diffline = result.diffline
		self.src = src
		self.filename = file
		self.covers = result.cover.bm
		self.codelines = {}
		self.lineflag = {}
		self.show = {}    #shade map
		self.rendered = {}
		self.lno = 0
		self.isdiff = result.do_diff
		self.taskid = taskid
		self.proto_data = {}


	#output the whole line with lineno
	def format_line(self, linetext, style, line_no):
		if self.rendered.get(line_no, 0) != 0:
			return ""

		self.rendered[line_no] = 1
		html_text = html_convert(linetext)
		if style == 'c_unrun':
			line_info = '<span style="color:red;margin-right:8px;">%d</span> ' % line_no
		else:
			line_info = '<span class="lineinfo">%d</span> ' % line_no
		s = '<p class="%s"> ' % style + line_info + html_text + '</p>\n'
		return s

	#shade unrunned function
	def format_unrun_func(self, b, codes):
		ret_msg = ''
		#function not run
		ret_msg = ret_msg + self.format_line(codes[b.begin], 'c_unrun', b.begin)
		if b.lbrace > b.begin:
			ret_msg = ret_msg + self.format_line(codes[b.lbrace], 'c_unrun', b.lbrace)
		ret_msg = ret_msg + '<p class="c_merge_unrun">...本函数未运行...</p>'
		if b.rbrace > b.lbrace:
			ret_msg = ret_msg + self.format_line(codes[b.rbrace], 'c_unrun', b.rbrace) + '<br />'
		return ret_msg

	def shade_seg(self, a, b, flag):
		for l in xrange(a, b+1): self.show[l] = flag


	'''
	calculate line color to block
	suppose no break/return statement in the middle of normal
	consecutive logic. (it must in a condition branch like if, while,for)
	the algorithm like a 2D shader. overlap code block one by one
	'''
	def shade_block(self, block):
		if block.run == 0:
			color = UNRUNNED
			if self.isdiff == 1 and block.modified == 0:
				color = UNRUN_NODIFF 
			if block.rbrace - block.begin < 1:
				self.show[block.begin] = color
				return

			self.shade_seg(block.begin, block.rbrace, color)
			return


		#no child node, shade it directly
		if len(block.child) == 0 or block.rbrace - block.begin < 1:
			self.shade_seg(block.begin, block.rbrace, RUNNED)
			return

		#partly runned
		open_seg = []
		start = block.begin
		end = start
		#split into segment divided by branch
		for b in block.child:
			if start > block.rbrace: break
			if b.begin > start: end = b.begin - 1
			else: end = start
			open_seg.append((start, end))
			start = b.rbrace + 1

		open_seg.append((start, block.rbrace-1))

		for ls, le in open_seg:
			color = UNRUNNED
			has_diff = 0
			for l in xrange(ls, le+1):
				if self.covers.get(l, 0) != 0:
					color = RUNNED
				if self.diffline.get(l, 0) > 0:
					has_diff = 1

			if color == RUNNED:
				self.shade_seg(ls, le, RUNNED)
			elif has_diff == 0:
				self.shade_seg(ls, le, UNRUN_NODIFF)
			else:
				self.shade_seg(ls, le, UNRUNNED)

		#shade child block
		for b in block.child:
			self.shade_block(b)


	#render function line after shading code segment
	def render_function_run(self, func):
		codes = self.codelines
		msg = ""
		render_seg = []
		le = 0  
		begin = func.lbrace + 1
		ls = begin
		color_style = {0: 'c_debug', RUNNED:'c_run', UNRUNNED:'c_unrun', UNRUN_NODIFF:'c_unrun_nodiff'}
		color = 0

		#merge consecutive line with same color
		for l in xrange(begin+1, func.rbrace):
			if self.show.get(l,0) != self.show.get(l-1, 0):
				render_seg.append((ls, l - 1))
				ls = l

		render_seg.append((ls, func.rbrace-1))

		for ls,le in render_seg:
			color = self.show.get(ls, 0)
			if le - ls < 3:
				for l in xrange(ls, le+1):
					msg = msg + self.format_line(codes[l], color_style[color], l)
			else:
				#merge block
				if color == RUNNED:
					msg = msg + '<p class="c_merge_run"> ...已运行%d-%d行...</p>' % (ls, le)
				elif color == UNRUN_NODIFF:
					msg = msg + '<p class="c_merge_unrun_nodiff"> ...未运行%d-%d行...</p>' % (ls, le)
				else:
					#unrun segment display all line
					if le - ls < 10:
						for l in xrange(ls, le+1):
							msg = msg + self.format_line(codes[l], color_style[color], l)
					else:
						msg = msg + self.format_line(codes[ls], color_style[color], ls)
						msg = msg + self.format_line(codes[ls+1], color_style[color], ls+1)
						msg = msg + '<p class="c_merge_unrun_nodiff"> ...分支未运行%d-%d行...</p>' % (ls, le)
						msg = msg + self.format_line(codes[le], color_style[color], le)

		return msg

	def render_diffline(self, func):
		msg = ''
		codes = self.codelines
		msg = msg + self.format_line(codes[func.begin], 'c_run_highlight', func.begin)
		df = {}

		last = 0
		for l in xrange(func.lbrace, func.rbrace):
			if self.diffline.get(l, 0) > 0: 
				if l - last > 3: 
					df[l-2] = self.covers.get(l-2, 0)
					df[l-1] = self.covers.get(l-1, 0)
				df[l] = self.covers.get(l, 0)
				last = l
			elif l - last < 2:
				df[l] = self.covers.get(l, 0)	


		df_line = df.keys()
		df_line.sort()
		last = 0
		for k in df_line:
			if k - last > 3:
				msg = msg + '<p style="margin-left:30px;color:#666666">---------------------------</p>\n'

			if df.get(k,0) != 0:
				msg = msg + self.format_line(codes[ k ], 'c_run', k)
			else:
				msg = msg + self.format_line(codes[ k ], 'c_unrun', k)

			last = k

		return msg

	#shade color to block
	def shade_function_run(self, func):
		self.shade_block(func)
		self.show[func.begin] = RUNNED
		self.show[func.lbrace] = RUNNED
		self.show[func.rbrace] = RUNNED
		
		ret_msg = self.format_line(self.codelines[func.begin], 'c_run_highlight', func.begin)

		if func.lbrace > func.begin:
			ret_msg = ret_msg + self.format_line(self.codelines[func.lbrace], 'c_run_highlight', func.lbrace)
		if func.rbrace - func.lbrace < 4:
			ret_msg = ret_msg + '<p class="c_merge_run">...已运行</p>'
			ret_msg = ret_msg + self.format_line(self.codelines[func.rbrace], 'c_run', func.rbrace)
			return ret_msg


		ret_msg = ret_msg + self.render_function_run(func)
		if self.rendered.get(func.rbrace, 0) == 0:
			ret_msg = ret_msg +  self.format_line(self.codelines[func.rbrace], 'c_run_highlight', func.rbrace)
		return ret_msg

	def output(self, viewpane):
		codefile = SRC_PATH + self.src
		try:
			codefp = open(codefile, 'r')
		except:
			return {'error':1}
		lno = 0
		ret_msg = ''
		b = self.block
		ltype = ''
		#hide info
		hstart = 0
		hend = 0
		lno = 0
		for line in codefp:
			lno = lno + 1
			self.codelines[lno] = line

		codefp.close()

		for func in b.child:
			#skip no diff function
			if self.isdiff == 1 and func.modified == 0: continue
			if viewpane == 'v_branch':
				if func.run == 0:
					ret_msg = ret_msg + self.format_unrun_func(func, self.codelines)
				else:
					ret_msg = ret_msg + self.shade_function_run(func)
			else :
				ret_msg = ret_msg + self.render_diffline(func)
				
			ret_msg = ret_msg + '<p><br /></p>'

		ret = {}
		ret['error'] = 0
		ret['code'] = unicode(ret_msg, 'gbk')
		return ret

	def get_proto_info(self):
		cur = connection.cursor()
		data = {}
		sql = "select func,main_proto, sub_proto, result from proto_test where task_id=%d and path='%s' and tool=1" % (self.taskid, self.filename)
		try:
			cur.execute(sql)
		except:
			return {}
		rows = cur.fetchall()
		res_val = 0
		for row in rows:
			func = row[0]
			if func not in data: 
				data[func] = {}
				data[func]['main'] = row[1]
				data[func]['sub'] = row[2]
				res_val = restore_lpc_var(row[3])
				data[func]['head'] = res_val.keys()
				data[func]['res'] = []
		
			res_val = restore_lpc_var(row[3])
			v = []
			#in order
			for k in data[func]['head']: v.append(res_val[k])
			data[func]['res'].append( v )
			
		self.proto_data = data
		return self.proto_data 

	def nex_proto_result(self):
		data = self.get_proto_info()
		if len(data) == 0: return ""
		tpl = get_template('proto_test_result.html')
		html = tpl.render(Context({'data':data}))
		return html

def do_confirm(req):
	file = req.GET.get('filename', '')
	taskid = int(req.GET.get('taskid', '0'))
	record = Record.objects.get(task_id=taskid, path=file)	
	task = Task.objects.get(task_id=taskid)
	user = req.user
	
	if not user.is_authenticated():
		return HttpResponse('forbid to do this')

	if record is None or task is None:
		return HttpResponseRedirect('/result?filename=%s&taskid=%d' % (file, taskid))

	if user.username == task.coder:
		record.confirm = record.confirm | 0x01
	elif user.username == task.qc:
		record.confirm = record.confirm | 0x02

	record.save()
	return HttpResponseRedirect('/result?filename=%s&taskid=%d' % (file, taskid))

def gen_script_link(file, taskid, viewpane, with_proto):
	url_prefix = "/result?filename=%s&taskid=%d" % (file, taskid)

	s = '$("#v_branch").attr("href", "'+url_prefix+'&view=v_branch");\n\t'
	s = s + '$("#v_line").attr("href", "'+url_prefix+'&view=v_line");\n\t'
	s = s + '$("#v_proto").attr("href", "'+url_prefix+'&view=v_proto");\n\t'
	s = s + '$("#%s").attr("style", "color:#FF2299;border:2px solid #CCCCCC;")' % viewpane

	if with_proto == 1:
		pass
	return s 

def get_result(req):
	file = req.GET.get('filename', '')
	taskid = int(req.GET.get('taskid', '0'))
	viewpane = req.GET.get('view', 'v_branch')
	user = req.user
	vpane_dict = {'v_branch':'分支视图', 'v_line':'line视图', 'v_proto':'NEX协议'}

	if viewpane not in ['v_branch', 'v_line', 'v_proto']: viewpane = 'v_branch'
	if not user.is_authenticated(): return HttpResponse('forbid to review the code!')

	#load info
	task = Task.objects.get(task_id=taskid)
	if task is None: return HttpResponse('Invalid task id')
	if (len(file) < 1): return HttpResponse('Invalid filename')

	#parse coverage info
	cov = CoverAnalyzer(RESULT_PATH, file, taskid)
	r = cov.load_from_xml()
	if r == 0: return HttpResponse('fail to load file %s.%d.xml' % (file, taskid))

	real_file = "%s.%d.c" % (file[:-2], taskid)
	
	covinfo = {}
	#calculate cover info
	covinfo['diff_cnt'] = cov.diff_branch
	covinfo['diff_cover'] = cov.diff_cover
	if cov.do_diff == 0:
		covinfo['diff_cnt'] = cov.branch_count
		covinfo['diff_cover'] = cov.cover_count

	if covinfo['diff_cnt'] > 0: 
		covinfo['diff_cover_rate'] = covinfo['diff_cover'] * 100 / covinfo['diff_cnt']
	else:
		covinfo['diff_cover_rate'] = 0

	resp = HtmlCoverOutput(real_file, file, cov, taskid)
	mp = {}
	mp['filename'] = file
	mp['covinfo'] = covinfo
	if viewpane == 'v_proto': 
		mp['code'] = resp.nex_proto_result()
	else: 
		output_text = resp.output(viewpane)
		if output_text['error'] > 0:
			return HttpResponse('cannot open source file: %s' % file)	

		mp['code'] = output_text['code']
	

	#load cover file status
	record = Record.objects.get(task_id=taskid, path=file)

	if record.confirm & 0x01:
		mp['coder_state'] = '<span style="color:#20CC20">已确认</span>'.decode('gbk')
	else:
		mp['coder_state'] = '<span style="color:#CC2020">未确认</span>'.decode('gbk')
	
	if record.confirm & 0x02:
		mp['qc_state'] = '<span style="color:#20CC20">已确认</span>'.decode('gbk')
	else:
		mp['qc_state'] = '<span style="color:#CC2020">未确认</span>'.decode('gbk')
	
	if task is not None:
		if task.coder == user.username and record.confirm & 0x01 == 0:
			mp['action'] = '<a href="/confirm?filename=%s&taskid=%d">confirm</a>' % (file, taskid)
		elif task.qc == user.username and record.confirm & 0x02 == 0:
			mp['action'] = '<a href="/confirm?filename=%s&taskid=%d">confirm</a>' % (file, taskid)

	with_proto = 0
	if len(resp.proto_data) > 1: with_proto = 1
	mp['js_ctrl'] = gen_script_link(file, taskid, viewpane, with_proto)
	
	rd = render_to_response('cover_view.html', mp)
	return rd
