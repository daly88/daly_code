#!/usr/bin/python
#coding=utf-8

import xlrd
import hashlib

INPUT_CHARSET = 'gbk'

class DiffMatrix(object):
	OLD_DEL = 1
	NEW_ADD = 2
	def __init__(self, m_tokens, n_tokens):
		mat = []
		m = len(m_tokens)
		n = len(n_tokens)
		self.m_tokens = m_tokens
		self.n_tokens = n_tokens
		for i in xrange(0, m+1):
			mat.append([])
			for j in xrange(0, n+1):
				mat[i].append(0)

		self.mat = mat
		self.m = m
		self.n = n

	def fill_lcs_matrix(self):
		p,q,r = 0,0,0
		for i in xrange(1, self.m+1):
			for j in xrange(1, self.n+1):
				p = self.mat[i-1][j-1]
				if self.m_tokens[i-1] == self.n_tokens[j-1]:  p = p + 1
				q = self.mat[i-1][j]
				r = self.mat[i][j-1]
				self.mat[i][j] = max(p,q,r)

	def traceback_matrix(self):
		p,q,v = 0,0,0
		stack = []
		i = self.m
		j = self.n	
		#trace back LCS matrix
		while i > 0 or j > 0:
			if i == 0:
				stack.append((self.NEW_ADD, j))
				j = j - 1
				continue
			if j == 0:
				stack.append((self.OLD_DEL, i))
				i = i - 1
				continue

			p = self.mat[i-1][j]
			q = self.mat[i][j-1]
			v = self.mat[i][j]
			if p == q:
				if v == p: stack.append((self.OLD_DEL,i))
				else: j = j - 1
				i = i - 1
			elif p > q:
				stack.append((self.OLD_DEL,i))  #go vertical
				i = i - 1
			else:
				stack.append((self.NEW_ADD,j))  #go horizontal
				j = j - 1
		stack.reverse()
		self.result_stack = stack
		#make raw diff(+/-)
		self.old_del = {}
		self.new_add = {}
		for r in stack:
			if r[0] == self.NEW_ADD:  self.new_add[r[1]] = 1
			else:  self.old_del[r[1]] = 1

		#analyze pretty diff info
		#identify modify/pure_add/pure_del
		p_old, p_new = 1, 1
		self.pure_del = []
		self.pure_add = []
		self.modify = []

		while p_old <= self.m or p_new <= self.n:
			if p_old in self.old_del:
				if p_new in self.new_add:
					self.modify.append((p_old, p_new))
					p_new = p_new + 1
				else:
					self.pure_del.append(p_old)
				p_old = p_old + 1
			elif p_new in self.new_add:
				self.pure_add.append(p_new)
				p_new = p_new + 1
			else:
				p_old = p_old + 1
				p_new = p_new + 1



class SheetMgr(object):
	def __init__(self, workbook, name):
		self.row_digest = []
		self.title_ = []
		self.wb_name = workbook
		self.wb_ = xlrd.open_workbook(workbook)
		self.sheet_name = name

		self.sheet_ = self.wb_.sheet_by_name(name)
		self.ncols_ = self.sheet_.ncols
		self.nrows_ = self.sheet_.nrows
		for j in xrange(self.ncols_):
			self.sheet_.cell(0, j).value

	
	def serialize_row(self, row):
		field = []
		for col in xrange(self.ncols_):	
			try:
				node = self.sheet_.cell(row-1, col)
			except:
				return '??error?? %d %d' % (row, col)
			if node.ctype == xlrd.XL_CELL_NUMBER:
				field.append(unicode(str(int(node.value))))
			elif node.ctype == xlrd.XL_CELL_TEXT:
				field.append(node.value)

		msg = ''
		i = 0
		for f in field:
			if len(f) > 20: f = f[:20] + '....'
			try:
				msg = msg + ' ' + f.encode('utf-8')
				i = i + 1
			except:
				msg = msg + '????'
		return msg

	def read_row_digest(self):
		for i in xrange(0, self.nrows_):
			msg = ''
			for j in xrange(self.ncols_):
				node = self.sheet_.cell(i, j)
				if node.ctype == xlrd.XL_CELL_NUMBER:
					msg = msg + str(node.value)
				elif node.ctype == xlrd.XL_CELL_TEXT:
					msg = msg + node.value
			m = hashlib.md5(msg.encode(INPUT_CHARSET))
			self.row_digest.append(m.hexdigest())

	def dump_digest(self):
		for v in self.row_digest: print v


def output_diff(sh_old, sh_new):
	df = DiffMatrix(sh_old.row_digest, sh_new.row_digest)
	#df = DiffMatrix(a,b)
	df.fill_lcs_matrix()
	df.traceback_matrix()
	for i in df.pure_del: 
		print '- ' + sh_old.serialize_row(i)
	for i in df.pure_add: 
		print '+ ' + sh_new.serialize_row(i)
	for i in df.modify: 
		print '!- ' + sh_old.serialize_row(i[0])
		print '!+ ' + sh_new.serialize_row(i[1])


if __name__ == '__main__':
	sh1 = SheetMgr('books.xls', 'legend')
	sh1.read_row_digest()
	#sh1.dump_digest()
	sh2 = SheetMgr('books2.xls', 'legend')
	sh2.read_row_digest()
	#sh2.dump_digest()
	output_diff(sh1, sh2)

