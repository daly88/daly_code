#!/usr/local/bin/python
#coding=utf-8
import sys
import xlrd
import hashlib

INPUT_CHARSET = 'gbk'
OUTPUT_CHARSET = 'utf-8'
MAX_SHOWFIELD = 6
MAX_FIELD_LEN = 8

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


class Workbook(object):
	def __init__(self, bookname):
		self.wb_name = bookname
		try:
			self.wb_ = xlrd.open_workbook(bookname)
		except:
			print 'unable to open workbook %s' % bookname
			sys.exit(-1)

	def sheet_by_index(self, index):
		return self.wb_.sheet_by_index(index)

	def nsheets(self):
		return self.wb_.nsheets
	
	def find_index(name):
		names = self.wb_.sheet_names()
		i = 1
		for s in names:
			if name == s: return i
			i = i + 1
		return -1

class SingleSheet(object):
	def __init__(self, workbook, index):
		self.row_digest = []
		self.title_ = []
		self.wb_ = workbook

		self.sheet_ = self.wb_.sheet_by_index(index)
		self.ncols_ = self.sheet_.ncols
		self.nrows_ = self.sheet_.nrows
		for j in xrange(self.ncols_):
			self.title_.append(self.sheet_.cell(0, j).value)

	
	def serialize_row(self, row):
		field = []
		for col in xrange(self.ncols_):	
			field.append(self.str_value(row-1, col))

		msg = u''
		i = 0
		for f in field:
			if i > MAX_SHOWFIELD: 
				msg = msg + u'......' 
				break
			if len(f) > MAX_FIELD_LEN: f = f[:MAX_FIELD_LEN] + u'....'
			try:
				msg = msg + u' ' + f
				i = i + 1
			except:
				msg = msg + u'????'

		return msg

	def str_value(self, i, j):
		node = self.sheet_.cell(i, j)
		if node.ctype == xlrd.XL_CELL_NUMBER: 
			return unicode(int(node.value))
		elif node.ctype == xlrd.XL_CELL_TEXT: 
			return node.value
		else:
			return u''
		

	def read_row_digest(self):
		for i in xrange(0, self.nrows_):
			msg = u''
			for j in xrange(self.ncols_):
				msg = msg + self.str_value(i, j)
				
			m = hashlib.md5(msg.encode(INPUT_CHARSET))
			self.row_digest.append(m.hexdigest())

	def dump_digest(self):
		for v in self.row_digest: print v

def output_diff(sh_old, sh_new):
	sh_old.read_row_digest()
	sh_new.read_row_digest()
	df = DiffMatrix(sh_old.row_digest, sh_new.row_digest)
	df.fill_lcs_matrix()
	df.traceback_matrix()
	print u'@@ %s @@' % sh_new.sheet_.name
	if len(df.pure_del) > 0:
		print '===DEL==='
		for i in df.pure_del: print u'- %d ' % i + sh_old.serialize_row(i)
	if len(df.pure_add) > 0:
		print '===ADD==='
		for i in df.pure_add: print u'+ %d ' % i + sh_new.serialize_row(i)
	if len(df.modify) > 0:
		print '===MOD==='
		for i in df.modify: 
			msg1 = u''
			msg2 = u''
			for f in xrange(sh_old.ncols_):
				v1 = sh_old.str_value(i[0]-1, f)
				v2 = sh_new.str_value(i[1]-1, f)
				if len(v1) > MAX_FIELD_LEN: v1 = v1[:MAX_FIELD_LEN] + u'....'
				if len(v2) > MAX_FIELD_LEN: v2 = v2[:MAX_FIELD_LEN] + u'....' 
				if v1 != v2:
					msg1 = msg1 + u'%s: %s   ' % (sh_old.title_[f], v1)
					msg2 = msg2 + u'%s: %s   ' % (sh_new.title_[f], v2)

			print u'- %d ' % i[0] + sh_old.str_value(i[0]-1, 0) + u' ' + msg1
			print u'+ %d ' % i[1] + sh_new.str_value(i[1]-1, 0) + u' ' + msg2


def do_diff(book_old, book_new):
	wb_old = Workbook(book_old)
	wb_new = Workbook(book_new)
	#print 'Index: %s' % book_new
	#print '======================================'
	if wb_old.nsheets() != wb_new.nsheets():
		print 'diffrent sheet count'
		return 
	scount = wb_old.nsheets()
	for i in xrange(scount):
		sa = SingleSheet(wb_old, i)
		sb = SingleSheet(wb_new, i)
		if sa.sheet_.name != sb.sheet_.name: continue
		output_diff(sa, sb)
	
if __name__ == '__main__':
	args = sys.argv
	if len(args) < 2:
		print 'xldiff book_old book_new' 
		sys.exit(0)
	if len(args) == 8 and args[1] == '-u':
		print '--- %s' % args[3]
		print '+++ %s' % args[5]

		#pass from svn parameter
		do_diff(args[6], args[7])
	else:
		#not from svn diff, just diff with two excel files
		print 'Index: %s' % args[2] 
		print '======================================'

		do_diff(args[1], args[2])

