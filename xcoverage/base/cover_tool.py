#! /usr/local/bin/python
# -*- coding: gbk -*-

#coverage file parser 
#the result can output to xml or load from xml file

import os,sys
import getopt
from xml.dom.minidom import * 
from script_parser import *

COV_SUFFIX = '.cov'
DIFF_SUFFIX = '.diff'
DIFF_UPDATE_SUFFIX = '.difftmp'

#cover file and source code analyzer
class CoverAnalyzer(object):
	def __init__(self, path, codefile, taskid):
		self.path_root = path
		self.xml_path = path
		self.cov_path = path
		self.diff_path = path
		self.codefile = codefile
		self.do_diff = 0   #is diff?
		self.taskid = taskid

		self.diffline = {}  #line modified
		self.linedepth = {}  #the line depth
		self.codetree = LpcParser(self.path_root, self.codefile, 'gbk')
		self.cover = CoverParser(self.cov_path, self.codefile, taskid)
		impl = getDOMImplementation()
		self.doc = impl.createDocument(None, "Node", None)
		self.dom_root = self.doc.documentElement
		self.output_update = ''

		#summer
		self.branch_count = 0
		self.cover_count = 0
		self.diff_branch = 0
		self.diff_cover = 0

	def set_cov_path(self, path):
		self.cov_path = path
		self.cover.path_root = path

	def update_run(self, block):
		for b in block.child:
			self.update_run(b)

		if block.isfunc == 0:
			if block.procname == 'foreach' or block.procname == 'for' or block.procname == 'while':
				for i in xrange(block.lbrace+1, block.rbrace):
					if self.cover.bm.get(i, 0) == 1:
						self.cover_count = self.cover_count + 1
						block.run = 1
						if block.modified > 0: self.diff_cover = self.diff_cover + 1
						break
				return	
			elif block.procname == 'else':
				for i in xrange(block.begin, block.rbrace+1):	
					if self.cover.bm.get(i, 0) == 1:
						self.cover_count = self.cover_count + 1
						block.run = 1
						if block.modified > 0: self.diff_cover = self.diff_cover + 1
						return
			elif self.cover.branch.get(block.begin, 0) == 1:
				self.cover_count = self.cover_count + 1
				block.run = 1
				if block.modified > 0: self.diff_cover = self.diff_cover + 1
				return
			elif block.begin < block.lbrace:
				for i in xrange(block.begin, block.lbrace):
					if self.cover.branch.get(i, 0) == 1:
						self.cover_count = self.cover_count + 1
						block.run = 1
						if block.modified > 0: self.diff_cover = self.diff_cover + 1
						return
			else:
				return

		#if func
		for i in xrange(block.lbrace+1, block.rbrace):
			if self.cover.bm.get(i, 0) == 1:
				self.cover_count = self.cover_count + 1
				block.run = 1
				if block.modified > 0: self.diff_cover = self.diff_cover + 1
				return

	#find in which branch
	def find_modified(self, l, b, depth_count):
		for child in b.child:
			end = child.rbrace
			if child.isfunc == 1: end = end - 1 
			if l >= child.begin and l <= end:
				if child.modified == 0:
					self.diff_branch = self.diff_branch + 1
					self.linedepth[l] = self.linedepth.get(l, 0) + 1
				child.modified = 1
				self.find_modified(l, child, depth_count)
			if l < end and l > child.lbrace: break


	def parse_diff(self, suffix_type):
		diff_file = os.path.join(self.diff_path, self.codefile + '.' + str(self.taskid) + suffix_type)
		try:
			f_diff = open(diff_file, 'r')
		except:
			return -1
	
		start = 0
		p_old = 1
		p_new = 1
		new_bm = {}
		new_branch = {}
		has_diff = 0
		i_new = 0
		i_old = 0
		lno = 0

		for line in f_diff:
			lno = lno + 1
			if line[0:3] in ['---','+++','===', 'Ind']: 
				old = (0,0)
				new = (0,0)
				start = 0
				has_diff = 1
				continue
			
			if line[0:2] == '@@':
				field = line.split()
				old = field[1][1:].split(",")
				new = field[2][1:].split(",")
				i_new = int(new[0])
				i_old = int(old[0])
				last = ''
				while p_old < i_old:
					if self.cover.bm.get(p_old,0) == 1: new_bm[p_new] = 1
					if self.cover.branch.get(p_old,0) == 1: new_branch[p_new] = 1
					p_new = p_new + 1
					p_old = p_old + 1
				continue

			c = line[0]
			
			if c == '+':
				self.diffline[i_new] = 1
				i_new = i_new + 1
			elif c == '-':
				if last == ' ':
					self.diffline[i_new - 1] = 2
				i_old = i_old + 1
			elif c == ' ':
				if last == '-':
					self.diffline[i_new] = 2

				if self.cover.bm.get(i_old,0) == 1: new_bm[i_new] = 1
				if self.cover.branch.get(i_old, 0): new_branch[i_new] = 1

				i_new = i_new + 1	
				i_old = i_old + 1

			p_new = i_new
			p_old = i_old
			last = c

		while p_old < self.cover.total_linecnt:
			if self.cover.bm.get(p_old, 0) == 1: new_bm[p_new] = 1
			if self.cover.branch.get(p_old, 0) == 1: new_branch[p_new] = 1
			p_new = p_new + 1
			p_old = p_old + 1

		#update diff cover
		for l in self.diffline:
			if suffix_type == DIFF_UPDATE_SUFFIX:
				self.find_modified(l, self.codetree.root, 1)			
			else:
				self.find_modified(l, self.codetree.root, 0)

		if has_diff == 1: 
			self.do_diff = 1
			#has diff
			if suffix_type == DIFF_UPDATE_SUFFIX and self.cover.done == 1 and lno >= 3:
				self.cover.bm = new_bm
				self.cover.branch = new_branch

		f_diff.close()
		if suffix_type == DIFF_UPDATE_SUFFIX:
			os.system('rm %s' % diff_file)
		return 1


	def clear_bm_by_diff(self,node):	
		for child in node.child:
			should_clear = 0
			if child.modified == 1:
				for l in xrange(child.begin, child.rbrace+1):
					if self.linedepth.get(l,0) == child.depth:
						should_clear = 1
						break
				if should_clear == 1:
					for l in xrange(child.begin, child.rbrace+1):
						self.cover.bm.pop(l,None)
						self.cover.branch.pop(l, None)
				self.clear_bm_by_diff(child)

	
	#output actual diff when update
	def diff_update(self):
		dfile = self.diff_path + self.codefile
		os.system('diff -u %s %s > %s.%s.difftmp' % (dfile, self.codefile, dfile, self.taskid))

		self.parse_diff(DIFF_UPDATE_SUFFIX)
		#remove diff branch's cover. 
		#QC should retest this branch
		self.clear_bm_by_diff(self.codetree.root)

		return 1

	#output new bitmap as a string for the game engine to remap
	def remap_run(self):
		begin, end = -1,-1
		sorted_bm = self.cover.bm.keys()
		sorted_bm.sort()
		for l in sorted_bm:
			if self.cover.bm.get(l, 0) == 0: continue
			if begin == -1:
				begin = l
			if l - 1 != end and end != -1:
				self.output_update += '%d-%d,' % (begin,end)
				begin = l

			end = l
		
		if begin > 1: self.output_update += '%d-%d' % (begin,end)
		self.output_update += '\n'
		for l in self.cover.branch:
			if self.cover.branch.get(l, 0) == 0: continue
			self.output_update += '%d,' % l
	
		self.output_update += '\n'

	def get_md5(self):
		real_code_file = os.path.join(self.cover.path_root, self.cover.codefile)
		for line in os.popen("md5 %s | cut -d ' ' -f 4" % real_code_file):
			return line.strip()

	def do_parse(self, which):
		if self.codetree.done == 0:
			r = self.codetree.parse_source()

		if which == 'remap':
			self.output_update = ''
			self.cover.load_cover_file()
			if self.get_md5() != self.cover.md5:
				return -2

			r = self.diff_update()
			self.remap_run()

		elif which == 'cover':
			r = self.cover.load_cover_file()
			if r > 0: self.update_run(self.codetree.root)
		elif which == 'diff':
			r = self.parse_diff(DIFF_SUFFIX)
		return r

	def process_xml_node(self, node, parent):
		#process this node's attribute
		b = SrcBlock()
		b.parent = parent
		b.procname = node.getAttribute('procname')
		if not parent: 
			sumnode = node.getElementsByTagName('summarize')
			s = sumnode[0].getAttribute('branch_cnt')
			if len(s) > 0: self.branch_count = int(s)
			s = sumnode[0].getAttribute('branch_cover')
			if len(s) > 0: self.cover_count = int(s)
			s = sumnode[0].getAttribute('diff_cnt')
			if len(s) > 0: self.diff_branch = int(s)
			s = sumnode[0].getAttribute('diff_cover')
			if len(s) > 0: self.diff_cover = int(s)
			s = sumnode[0].getAttribute('isdiff')
			if len(s) > 0: self.do_diff = int(s)
			
			b.depth = 0
		else: 
			b.depth = parent.depth + 1
	
		dom_attr = node.getElementsByTagName('attribution')
		s = dom_attr[0].getAttribute('modified')
		if len(s) > 0: b.modified = int(s)

		s = dom_attr[0].getAttribute('run') 
		if len(s) > 0: b.run = int(s)

		s = dom_attr[0].getAttribute('begin')
		if len(s) > 0: b.begin = int(s)
		b.lbrace = int(dom_attr[0].getAttribute('lbrace'))
		b.rbrace = int(dom_attr[0].getAttribute('rbrace'))
	
		s = dom_attr[0].getAttribute('isfunc')
		if len(s) > 0: b.isfunc = int(s)

		dom_cover = node.getElementsByTagName('coverlines')
		s = dom_cover[0].getAttribute('lines')	
		if len(s) > 0:
			self.cover_line_decode(s, self.cover.bm, b.begin)

		#load diff line info
		dom_diffline = node.getElementsByTagName('diffline')
		if dom_diffline and len(dom_diffline) > 0:
			s = dom_diffline[0].getAttribute('lines')
			if len(s) > 0: self.cover_line_decode(s, self.diffline, b.begin)

		
		if parent: parent.child.append(b)
		#recursive process the child nodes
		for child in node.childNodes:
			if child.nodeType == child.ELEMENT_NODE and child.nodeName == 'Node':
				b_child = self.process_xml_node(child, b)
		return b

	#load from xml to construct codetree
	def load_from_xml(self):
		file = os.path.join(self.xml_path, self.codefile + '.' + str(self.taskid) + '.xml')
		try:
			dom_root = parse(file)
		except:
			return 0

		self.dom_root = dom_root
		dom_nodes = dom_root.getElementsByTagName('Node')	
		if (len(dom_nodes) < 1): return 0
		self.codetree.root = self.process_xml_node(dom_nodes[0], None)
		return 1

	#output as xml file from codetree and cover result
	def output_xml(self):
		self.add_code_block_node(self.dom_root, self.codetree.root)
		sumnode = self.doc.createElement('summarize')
		sumnode.setAttribute('branch_cnt', str(self.branch_count))
		sumnode.setAttribute('branch_cover', str(self.cover_count))
		sumnode.setAttribute('diff_cnt', str(self.diff_branch))
		sumnode.setAttribute('diff_cover', str(self.diff_cover))
		sumnode.setAttribute('isdiff', str(self.do_diff))
		self.dom_root.appendChild(sumnode)

		real_file = os.path.join(self.xml_path, self.codefile + '.' + str(self.taskid) + '.xml')
		try:
			f = open(real_file, 'w')
		except:
			return -1
		f.write(self.doc.toprettyxml(indent='\t', encoding='utf-8'))
		f.close()
		return 1

	#line coverage encode to '1,3,5-7, 8-11'
	def cover_line_encode(self, covers, start, end):
		msg = []
		begin = -1
		last = 0
		if end < start: return ''
		i = 0
		span = end-start+1
		for i in xrange(0, span):
			if covers.get(i + start, 0) == 1:
				if begin == -1: begin = i
				last = i
			elif begin >= 0:
				if last - begin > 0: msg.append( '%d-%d' %(begin, last) )	
				else: msg.append( str(last) )
				begin = -1
		
		if begin >= 0:
			if last -  begin > 0: msg.append( '%d-%d' %(begin, last) )
			else: msg.append(str(last))
		
		return ','.join(msg)

	def cover_line_decode(self, s, covers, start):
		lines = s.split(',')
		for seg in lines:
			bs = seg.split('-')
			if len(bs) == 1 and len(bs[0]) > 0: covers[int(bs[0]) + start] = 1
			elif len(bs) == 2 and int(bs[1]) >= int(bs[0]):
				for i in xrange(int(bs[0]), int(bs[1])+1):
					real_lno = i + start
					covers[real_lno] = 1

	def add_code_block_node(self, pnode, src_block):
		pnode.setAttribute('procname', src_block.procname)
		self.branch_count = self.branch_count + 1	
				
		#cover and diff info
		covernode = self.doc.createElement('coverlines')
		offset = src_block.begin
		cover_msg = self.cover_line_encode(self.cover.bm, offset, src_block.rbrace)
		covernode.setAttribute('lines', cover_msg)
	
		diffnode = self.doc.createElement('diffline')
		offset = src_block.begin
		diff_msg = self.cover_line_encode(self.diffline, offset, src_block.rbrace)
		diffnode.setAttribute('lines', diff_msg)

		attrnode = self.doc.createElement('attribution')
		if src_block.isfunc == 1: attrnode.setAttribute('isfunc', str(src_block.isfunc))
		attrnode.setAttribute('lbrace', str(src_block.lbrace))
		attrnode.setAttribute('rbrace', str(src_block.rbrace))
		attrnode.setAttribute('begin', str(src_block.begin))
		attrnode.setAttribute('modified', str(src_block.modified))
		attrnode.setAttribute('run', str(src_block.run))

		pnode.appendChild(covernode)
		pnode.appendChild(diffnode)
		pnode.appendChild(attrnode)
		for child in src_block.child:
			#ignore qc test function
			if len(child.procname) > 4 :
				if child.procname[0:3] == '_X_' or child.procname[0:5] == 'PROT_': continue
				if child.procname[0:3] == '_T_': continue
			cnode = self.doc.createElement('Node')
			self.add_code_block_node(cnode, child)
			pnode.appendChild(cnode)


#cover file parser
class CoverParser(object):
	def __init__(self, path, codefile, taskid):
		self.path_root = path
		self.codefile = codefile
		self.done = 0
		self.cov_ver = 0
		self.svn_ver = 0
		self.md5 = ''
		self.taskid = taskid

		self.total_linecnt = 0
		self.bm = {}   #touch bitmap
		self.branch = {}   #touch branch

	#parse the cover file
	#cover file format:
	#     ##Desc
	#     ... description info
	#     ##Bitmap
	#     coverlines bitmap (a hex character represent 4 lines, start from line 0)
	#     ##Branch
	#     branch cover bitmap (whether jump into block after if,while,for...)
	def load_cover_file(self):
		if self.codefile == '' or self.path_root == '': return -1
		cov_file = os.path.join(self.path_root , self.codefile + '.' + str(self.taskid) + COV_SUFFIX)

		try:
			f = open(cov_file, 'r')
		except:
			return -1

		lcnt = 0
		seg = ''
		bline = 0
		for line in f:
			lcnt = lcnt + 1		
			if seg != 'Bitmap' and seg != 'Branch' and len(line) < 3: continue
			line = line.rstrip('\n')
			if line[0:2] == '##':
				if line[2:] == 'Desc':
					seg = 'Desc'
				elif line[2:] == 'Bitmap':
					seg = 'Bitmap'
					bline = 0
				elif line[2:] == 'Branch':
					seg = 'Branch'
					bline = 0	
				continue

			if seg == 'Desc':
				field = line.split(' ')
				if len(field) < 2: return -2
				if field[0] == 'svn_ver':
					self.svn_ver = int(field[1])
				elif field[0] == 'cover_ver':
					self.cov_ver = int(field[1])
				elif field[0] == 'md5':
					self.md5 = field[1].strip()
				elif field[0] == 'total_linecnt':
					self.total_linecnt = int(field[1])

			elif seg == 'Bitmap':
				line = line.strip()
				for i in range(len(line)):
					c = 0
					if line[i] >= 'A':
						c = ord(line[i]) - ord('A') + 10
					elif line[i] >= '0' and line[i] <= '9':
						c = ord(line[i]) - ord('0')
					else:
						return -2
					
					self.bm[bline] = c & 0x01
					self.bm[bline+1] = (c >> 1) & 0x01
					self.bm[bline+2] = (c >> 2) & 0x01
					self.bm[bline+3] = (c >> 3) & 0x01
					bline = bline + 4
			elif seg == 'Branch':
				line = line.strip()
				for i in range(len(line)):
					c = 0
					if line[i] >= 'A':
						c = ord(line[i]) - ord('A') + 10
					elif line[i] >= '0' and line[i] <= '9':
						c = ord(line[i]) - ord('0')
					else:
						return -2
					
					self.branch[bline] = c & 0x01
					self.branch[bline+1] = (c >> 1) & 0x01
					self.branch[bline+2] = (c >> 2) & 0x01
					self.branch[bline+3] = (c >> 3) & 0x01
					bline = bline + 4

		self.done = 1
		f.close()
		return 1

	#output a diff style plain text file 
	#just for debug and verification
	def plain_output(self, output_path):
		if not self.done:
			return -2

		codefile = os.path.join(output_path, self.codefile)
		try:
			codefp = open(codefile, 'r')
		except:
			return -3

		outfile = os.path.join(self.path_root, self.codefile + '.out')
		try:
			outfp = open(outfile, 'w')
		except:
			return -3
	
		outfp.write('Index: %s\n' % self.codefile)
		lno = 0
		for line in codefp:
			lno = lno + 1
			if lno >= self.total_linecnt: break
			if self.bm[lno] == 1:
				line = '+ ' + line
			else:
				line = '- ' + line
			outfp.write(line)

		outfp.close()
		#output branch	
		outfile = os.path.join(self.path_root, self.codefile + '.outbranch')
		try:
			outfp = open(outfile, 'w')
		except:
			return -3
	
		outfp.write('Index: %s\n' % self.codefile)
		lno = 0
		codefp.seek(0)
		for line in codefp:
			lno = lno + 1
			if lno >= self.total_linecnt: break
			if self.branch[lno] == 1:
				line = '+ ' + line
			else:
				line = '- ' + line
			outfp.write(line)

		outfp.close()
		codefp.close()
		return 0


if __name__ == '__main__':
	
	args = sys.argv
	if len(args) < 1 :
		print 'cover_tool -r<path_root> -f<codefile> -d<diff_path>'
	
	codefile = ''
	path_root = './'
	cover_path = ''
	diff_path = ''
	xml_path = ''
	taskid = 0
	optlist, args = getopt.getopt(args[1:], 'mr:f:c:d:x:v:')	
	re_mapping = 0
	for opt, v in optlist:
		if opt == '-f':
			codefile = v
		elif opt == '-r':
			path_root = v
		elif opt == '-c':
			cover_path = v 
		elif opt == '-d':
			diff_path = v 
		elif opt == '-x':
			xml_path = v 
		elif opt == '-v':
			taskid = int(v)
		elif opt == '-m':
			#remap cover on file update
			re_mapping = 1

	p = CoverAnalyzer(path_root, codefile, taskid)	
	if len(xml_path) > 0: p.xml_path = xml_path
	if len(diff_path) > 0: p.diff_path = diff_path
	if re_mapping == 1:
		if len(cover_path) > 0: p.set_cov_path(cover_path)
		r = p.do_parse('remap')
		#output to shell (receive by game engine)
		print p.output_update
	else:
		if len(diff_path) > 0: 
			r = p.do_parse('diff')
		if len(cover_path) > 0: 
			p.set_cov_path(cover_path)
			r = p.do_parse('cover')

		p.cover.plain_output(xml_path)
		print p.output_xml()
