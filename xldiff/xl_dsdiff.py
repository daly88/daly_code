#!/usr/local/bin/python
#
#
# Excel diff for specific game data config datasheet 
# the format of datasheet:
#     column 0: the unique id to identify unique row config
#               suppose there's no conflict id in column 0
#     row 0: the column title
#
# two sheet must have the same amount of sheet with the same sheet name
# Author: Daly 2013-5

import sys
import xlrd
import hashlib

INPUT_CHARSET = 'gbk'
MAX_SHOWFIELD = 6
MAX_FIELD_LEN = 8

class DsDiffTool(object):
	def __init__(self, sh_old, sh_new):
		self.sh_old = sh_old
		self.sh_new = sh_new
		self.pure_del = []
		self.pure_add = []
		self.modify = []
	
	def compute_diff(self):
		old_row = None
		for id, row in self.sh_old.unique_id_row.items():
			if id not in self.sh_new.unique_id_row:
				self.pure_del.append(row)

		for id, row in self.sh_new.unique_id_row.items():
			if id not in self.sh_old.unique_id_row:
				self.pure_add.append(row)
			else:
				old_row = self.sh_old.unique_id_row[id]
				ret = self.compare_row(old_row, row)
				if ret != -1:
					self.modify.append((old_row, row))
	
	def compare_row(self, r1, r2):
		for col in xrange(self.sh_new.ncols_):
			v1 = self.sh_old.sheet_.cell(r1, col).value
			v2 = self.sh_new.sheet_.cell(r2, col).value
			if v1 != v2: return col
		return -1


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

class DataSheet(object):
	def __init__(self, workbook, index):
		self.unique_id_row = {}
		self.title_ = []
		self.wb_ = workbook

		self.sheet_ = self.wb_.sheet_by_index(index)
		self.ncols_ = self.sheet_.ncols
		self.nrows_ = self.sheet_.nrows
		for j in xrange(self.ncols_):
			self.title_.append(self.sheet_.cell(0, j).value)

		pid = 0
		for i in xrange(self.nrows_):
			pid = self.str_value(i, 0)
			self.unique_id_row[pid] = i

	
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
		

def output_diff(sh_old, sh_new):
	df = DsDiffTool(sh_old, sh_new)
	df.compute_diff()
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
				v1 = sh_old.str_value(i[0], f)
				v2 = sh_new.str_value(i[1], f)
				if v1 != v2:
					if len(v1) > MAX_FIELD_LEN: v1 = v1[:MAX_FIELD_LEN] + u'....'
					if len(v2) > MAX_FIELD_LEN: v2 = v2[:MAX_FIELD_LEN] + u'....' 
					msg1 = msg1 + u'%s: %s   ' % (sh_old.title_[f], v1)
					msg2 = msg2 + u'%s: %s   ' % (sh_new.title_[f], v2)

			print u'- %d ' % i[0] + sh_old.str_value(i[0]-1, 0) + u' ' + msg1
			print u'+ %d ' % i[1] + sh_new.str_value(i[1]-1, 0) + u' ' + msg2


def do_diff(book_old, book_new):	
	wb_new = Workbook(book_new)
	wb_old = Workbook(book_old)
	if wb_old.nsheets() != wb_new.nsheets():
		print 'diffrent sheet count'
		return 
	scount = wb_old.nsheets()
	for i in xrange(scount):
		sa = DataSheet(wb_old, i)
		sb = DataSheet(wb_new, i)
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

