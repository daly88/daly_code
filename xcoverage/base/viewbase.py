import os,sys
from django.http import HttpResponse


class ViewBase(object):
	def __init__(self):
		self.action_seq = []
		self.action_seq.append("check_auth")
		self.action_seq.append("init_request")
		self.action_seq.append("output_page")

	def process(self, req):
		self.req = req
		for procname in self.action_seq:
			proc = getattr(self, procname)
			resp = proc()
			if resp != True:
				return resp

		return HttpResponse('hello')

	def output_page(self):
		return True

	#override by subclass
	def init_request(self):
		return True
	
	def output_page(self):
		return True
