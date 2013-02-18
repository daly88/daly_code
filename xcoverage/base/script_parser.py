#! /usr/local/bin/python
# -*- coding: gbk -*-

#A script source parser for coverage tools
# Author: Daly 2012-8-23
# Notes:
#     a simple script parser to create code block info for branch coverage test tool 
#     That means no strict syntax analysis, just code block construction
#     a code block is 
#		1. a function
#		2. codes block after branching keyword such as if,while,for,break,return...


import os,sys

#token type
T_EOF = 0
T_IDENT = 1
T_BRANCH_WORD = 2
T_VARTYPE = 3     #variable define keyword
T_LBRACE= 4
T_RBRACE= 5
T_LPAREN = 6
T_RPAREN = 7
T_STRING = 8
T_POINTER = 9    # if have pointer type (* & ...)
T_NUMBER = 10
T_COMMA = 11
T_SEMICOLON = 12
T_SPECIAL = 13
T_OPER  = 14      #operator
T_LINEEND = 15
T_IGNORE = 99

#source block
class SrcBlock(object):
	def __init__(self):
		self.lbrace = 0  #block大括号处
		self.rbrace = 0
		self.begin = 0    #声明开始处
		self.child = []
		self.parent = None
		self.procname = ''
		self.depth = 0
		self.run = 0        #use for test coverage
		self.modified = 0   #use for diff
		self.isfunc = 0     #is it a function block

	def in_block(self, line):
		return line >= begin and line <= rbrace

class SrcParser(object):
	def __init__(self, path, codefile):
		self.path = path
		self.file = codefile
		self.lines = {}
		self.root = SrcBlock()
		self.linecnt = 0
		self.done = 0      #is parsed done
		#parser var
		self.cur_lno = 1
		self.cur_pos = 0
		self.next_lno = 0
		self.next_pos = 1
		self.token = (T_IGNORE, '')
		#define in subclass for specific script language
		self.vartype = {}
		self.branch_word = {}
		self.space = ' \t '	
		self.line_comment = '//'
		self.line_ignore_head = ['#']
		self.special_head = {}
		self.bcomment_s = '/*'   #block comment start and end
		self.bcomment_e = '*/'
		self.spliter = '\r\n{}(),*;: '
		self.oper = '+-*/'

	def print_cur(self):
		stk = str(self.token[1])
		if self.token[0] == T_LINEEND:
			stk = '\\n'
		arr = (self.cur_lno, self.cur_pos, self.token[0], stk, self.next_lno, self.next_pos)
		print 'cur %d:%d, token:%d %s; next %d:%d' % arr

	def next(self):
		self.move()
		r = self.peek()
		return r

	def set_token_and_next(self, lno, pos, tk):
		self.next_lno = lno
		self.next_pos = pos
		self.token = tk
		return tk

	#move to next token
	def move(self):
		self.cur_lno = self.next_lno
		self.cur_pos = self.next_pos
		return self.token

	def which_spliter(self, c):
		return (T_IGNORE, '')

	#move forward until reach token in stop_tks
	def seek(self, stop_tks):
		tk = self.peek()
		while tk[0] != T_EOF:
			if tk[0] in stop_tks:
				return tk
			tk = self.next()

		return (T_EOF, '')

	#scan legal identity
	def scan_id(self, lno, pos):
		begin = pos
		val = ''
		s = self.lines[lno]
		#id must in the same line
		while pos + 1 <= len(s):
			c = s[pos]
			if c in self.spliter or c == '"':
				val = s[begin:pos]
				val = val.strip()
				if val in self.vartype:
					t = (T_VARTYPE, val)
				elif val in self.branch_word:
					t = (T_BRANCH_WORD, val)
				elif val in self.special_head:
					t = (T_SPECIAL, val)
				else:
					t = (T_IDENT, val)

				return (lno, pos, t)
			else:
				pos = pos + 1
				continue

		return (lno, pos, (T_IGNORE, val))

	def scan_number(self, lno, pos):
		begin = pos
		s = self.lines[lno]
		if s[pos] == '-': 
			pos = pos + 1
		while pos + 1 < len(s):
			c = s[pos]
			if not c.isdigit() and c != '.':
				return (lno, pos, (T_NUMBER, s[begin:pos]))
			else:
				pos = pos + 1
		
		return (lno, pos, (T_NUMBER, s[begin:]))

	def scan_string(self, lno, pos):
		begin = (lno, pos)
		val = ''
		while lno <= self.linecnt:
			s = self.lines[lno]
			if pos >= len(s): 
				lno = lno + 1
				pos = 0
				continue
			#skip trans
			if s[pos] == '\\':
				pos = pos + 2
				continue
			elif s[pos] == '\"':
				if begin[0] == lno: 
					val = s[begin[1]:pos-1]
					pos = pos + 1
					break
				else:
					val = self.lines[begin[0]][pos:]
					for l in xrange(begin[0]+1, lno):
						val = val + self.lines[l]
					val = val + s[:pos-1]
					pos = pos + 1
					break;
			else:
				pos = pos + 1
			
		return (lno, pos, val)

	#skip block comment
	def scan_comment(self, lno, pos):
		while lno <= self.linecnt:
			s = self.lines[lno]
			if pos >= len(s): 
				lno = lno + 1
				pos = 0
				continue
			if s[pos] != self.bcomment_e[0]:
				pos = pos + 1
				continue

			len_c = len(self.bcomment_e)
			if s[pos:pos+len_c] == self.bcomment_e:
				pos = pos + len_c
				break
			else:
				pos = pos + 1
		return (lno, pos)

	#see next token but don't move
	def peek(self):
		lno = self.cur_lno
		pos = self.cur_pos
		begin = (0,0)
		while lno <= self.linecnt:
			s = self.lines[lno]
			if pos >= len(s):
				lno = lno + 1
				pos = 0
				continue

			#ignore some line leading by line_ignore_head
			if pos == 0:
				found = 0
				for e in self.line_ignore_head:
					if s.find(e) == 0:
						found = 1
						break
				if found == 1:
					lno = lno + 1
					pos = 0
					continue

			c = s[pos]			
			if c in self.space:
				pos = pos + 1
				continue
			elif c == '\n':
				return self.set_token_and_next(lno+1, 0, (T_LINEEND, '\n'))

			#skip line comment
			if c == self.line_comment[0]:
				len_c = len(self.line_comment)
				if s[pos:pos+len_c] == self.line_comment:
					return self.set_token_and_next(lno+1, 0, (T_LINEEND, '\n'))

			#skip block comment
			if c == self.bcomment_s[0]:
				len_c = len(self.bcomment_s)
				if s[pos:pos+len_c] == self.bcomment_s:
					lno, pos = self.scan_comment(lno, pos+1)	
					continue
			elif c.isalpha() or c == '_':
				(lno, pos, val) = self.scan_id(lno, pos)
				return self.set_token_and_next(lno, pos, val)
			#string
			elif c == '\"':
				(lno, pos, val) = self.scan_string(lno, pos+1)
				return self.set_token_and_next(lno, pos, (T_STRING, val))
			elif c in self.spliter:
				return self.set_token_and_next(lno, pos+1, self.which_spliter(c))
			elif c == '-':
				if pos + 1 < len(s) and s[pos+1].isdigit():
					(lno, pos, val) = self.scan_number(lno, pos)
					return self.set_token_and_next(lno, pos, val)
				else:
					return self.set_token_and_next(lno, pos+1, (T_IGNORE, c))
			elif c.isdigit():
				(lno, pos, val) = self.scan_number(lno, pos)
				return self.set_token_and_next(lno, pos, val)
			else:
				#ignore normal statement, add parsing when needed
				(lno, pos, val) = self.scan_id(lno, pos)
				return self.set_token_and_next(lno, pos, (T_IGNORE, val[1]))

			pos = pos + 1	

		return self.set_token_and_next(lno, pos, (T_EOF, ''))



#LPC script source parser
class LpcParser(SrcParser):
	def __init__(self, path, codefile, encode):
		super(LpcParser, self).__init__(path, codefile)
		self.encode = encode
		self.vartype = {'void':1, 'int':1, 'string':1, 'object':1, 'mixed':1}
		self.branch_word = {'if':1, 'else':1, 'for':1, 'foreach':1, 'while':1, 'do':1}
		self.line_comment = '//'
		self.bcomment_s = '/*'
		self.bcomment_e = '*/'
		self.spliter = '\r\n\t{}(),*;#=!: '
		self.special_head = {'create':1 }
		self.line_ignore_head = ['#include', 'DECLARE_', '#define', '//']

	def which_spliter(self, c):
		if c == '{':
			return (T_LBRACE, '{')
		elif c == '}':
			return (T_RBRACE, '}')
		elif c == '(':
			return (T_LPAREN, '(')
		elif c == ')':
			return (T_RPAREN, ')')
		elif c == '*':
			return (T_POINTER, '*')
		elif c == ',':
			return (T_COMMA, ',')
		elif c == ';':
			return (T_SEMICOLON, ';')

		return (T_IGNORE, c)

	#parse jump branch
	def parse_branch(self, block):
		procname = self.token[1]

		self.next()
		#must followed by branch_word (...)
		if self.token[0] == T_BRANCH_WORD and self.token[1] == 'if' and procname == 'else':
			procname = 'elseif'
			self.next()

		if procname != 'else':
			if self.token[0] == T_LPAREN: self.next()
			else:
				return 0

		lno_declare = self.cur_lno
		#parenthese (())
		if procname == 'else':
			pass
			#self.next()
		else:
			p = 1
			while p > 0 and self.token[0] != T_EOF:
				tk = self.seek([T_LPAREN, T_RPAREN])
				if tk[0] == T_LPAREN: p = p + 1
				elif tk[0] == T_RPAREN: p = p - 1
				self.next()

		while self.token[0] == T_LINEEND: self.next()

		me = SrcBlock()
		me.procname = procname
		me.depth = block.depth + 1
		me.begin = lno_declare
		block.child.append(me)

		if self.token[0] == T_LBRACE: 
			me.lbrace = self.cur_lno
			self.next()
		else:
			me.lbrace = lno_declare
			lno = self.cur_lno
			me.rbrace = self.cur_lno
			while self.token[0] != T_EOF and self.next_lno == lno:
				if self.token[0] == T_BRANCH_WORD:
					self.parse_branch(me)
					me.rbrace = self.cur_lno

				if self.token[0] == T_LINEEND: break
				self.next()
			#no brace {}, one line branch
			return 1	

		dp = 1
		while dp > 0 and self.token[0] != T_EOF:
			tk = self.seek([T_BRANCH_WORD, T_LBRACE, T_RBRACE,])
			if tk[0] == T_EOF:  return 0
			elif tk[0] == T_LBRACE: dp = dp + 1
			elif tk[0] == T_RBRACE: dp = dp - 1
			else: self.parse_branch(me)
			if dp == 0: me.rbrace = self.next_lno

			if self.token[0] == T_BRANCH_WORD: continue
			elif dp == 0: break
			self.next()	
		
		return 1

	# vattype idenf ( param ... ) 
	# { ... }
	def parse_func(self, block):
		procname = ''
		if self.token[0] == T_VARTYPE:
			self.next()
			if self.token[0] == T_POINTER: self.next()
			if self.token[0] == T_IDENT or self.token[0] == T_SPECIAL: 
				procname = self.token[1]
				self.next()
			else: return 0
		elif self.token[0] == T_SPECIAL and self.token[1] == 'create':
			procname = 'create'
			self.next()
		else: 
			return 0

		if self.token[0] == T_LPAREN: self.next()
		else: return 0
	
		lno_declare = self.cur_lno
		#skip param list
		tk = self.seek([T_RPAREN])

		if tk[0] == T_EOF: return 0
		self.next()
		if self.token[0] == T_IGNORE and self.token[1] == '\r': self.next()
		while self.token[0] == T_LINEEND: self.next()
		if tk[0] == T_EOF: return 0
		
		#line number of declaration
		if self.token[0] == T_LBRACE: 
			self.next()
			#function block begin
			me = SrcBlock()
			me.procname = procname
			me.depth = block.depth + 1
			me.lbrace = self.cur_lno
			me.begin = lno_declare
			me.parent = block
			me.isfunc = 1
			block.child.append(me)

			d_brace = 1
			while d_brace > 0 and self.token[0] != T_EOF:
				tk = self.seek([T_BRANCH_WORD, T_LBRACE, T_RBRACE,])
				if tk[0] == T_EOF: 
					me.rbrace = self.next_lno
					return 0
				if tk[0] == T_LBRACE: d_brace = d_brace + 1
				elif tk[0] == T_RBRACE: d_brace = d_brace - 1
				else: self.parse_branch(me)

				if d_brace == 0: me.rbrace = self.next_lno
				self.next()	
		else:
			#just declaration not implementation
			return 0

		return 1

	#root block
	def parse_block(self, block):
		done = 0
		#find function declare
		while self.token[0] != T_EOF:
			tk = self.seek([T_VARTYPE, T_SPECIAL])
			self.parse_func(block)
			self.next()

	def parse_source(self):
		if self.file == '' or self.path == '': return -1
		file = os.path.join(self.path, self.file)
		try:
			f = open(file, 'r')
		except:
			return -1

		lno = 0
		for line in f:
			lno = lno + 1
			s = line.lstrip()
			self.lines[lno] = unicode(s, self.encode)

		self.linecnt = lno
		self.parse_block(self.root)
		self.done = 1
		f.close()
	
	#output the code structure as plain text
	def print_tree(self, block):
		dp = block.depth
		tab = ''
		for i in xrange(1,dp):
			tab = tab + '\t'
		if dp > 0:
			print tab, block.procname, block.lbrace, block.rbrace
		for child in block.child:
			self.print_tree(child)



if __name__ == '__main__':
	args = sys.argv
	if len(args) < 1 :
		print 'script_parser <codefile name>'
		exit(0)

	r = LpcParser('.', args[1], 'gbk')
	r.parse_source()
	r.print_tree(r.root)


