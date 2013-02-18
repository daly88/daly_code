#! /usr/bin/python
# Daly 2012-04-11

import types

#python - LPC serialization tools

BRK_INT = ':]}, '

def serialize_int_or_str(dat):
	res = ''
	if type(dat) is types.StringType:
		res = '\"%s\"' % dat
	elif type(dat) is types.IntType:
		res = '%d' % dat
	return res

#is int or string type
def is_trival_type(dat):
	return type(dat) is types.StringType or type(dat) is types.IntType

#equal to save_variable() in LPC
#serialize python data for LPC deserialize

def serialize_lpc_var(dat):
	res = ''
	if is_trival_type(dat):
		return serialize_int_or_str(dat) 
	elif type(dat) is types.ListType:
		res = '({'
		for v in dat:
			if is_trival_type(v):
				res = res + serialize_int_or_str(v) + ','
				continue
			else:
				res = res + serialize_lpc_var(v) + ','
		res += '})'
		return res
	elif type(dat) is types.DictType:
		res = '(['
		for k,v in dat.items():
			res = res + serialize_int_or_str(k) + ':'		
			if is_trival_type(v):
				res = res + serialize_int_or_str(v) + ','
				continue
			else:
				res = res + serialize_lpc_var(v) + ','

		res += '])'
		return res

#pass remain
def restore_str(s):
	if s[0] != '\"':
		return (0, None)	

	p = s[1:].find('\"')	
	if p == -1:
		return (0,None)
	return (p+2, s[1:p+1])

def restore_int(s):
	for i in xrange(min(11, len(s))):
		if not s[i].isdigit():
			if i==0 and s[0] == '-': continue
			if s[i] in BRK_INT:
				return (i, int(s[:i]))	
			else:	
				return (0, None)
	return (len(s), int(s))

#parse string or int
def restore_trival(s):
	if s[0] == '\"':
		return restore_str(s)
	elif s[0].isdigit() or s[0] == '-':
		return restore_int(s)
	return (0, None)

#restore LPC mapping to python dict	
def restore_map(s):
	res = {}
	tlen = 0
	k = None
	v = None

	while len(s) > 0:
		if s[0] == '\"' or s[0].isdigit() or s[0] == '-':
			offset, m = restore_trival(s)	
			if offset == 0 or m is None: return (0, None)
			if k is None:
				#it's key
				k = m
			else:
				#it's value
				res[k] = m
				k = None

			s = s[offset:]
			tlen = tlen + offset
		elif s[0] == ':':
			#no key
			if k is None: return (0, None) 		
			tlen = tlen + 1
			s = s[1:]
		elif s[0] == ',':
			#the key should be cleared here
			if k is not None: return (0, None)
			tlen = tlen + 1
			s = s[1:]
		elif s[0] == ' ':
			offset = 0
			while s[offset] == ' ' and offset < len(s):			
				offset = offset + 1

			if offset == len(s): return (0, None)
			s = s[offset:]
			tlen =  tlen + offset
		elif s[0] == ']':
			if len(s) < 2:  return (0, None)
			if s[1] == ')':
				return (tlen+2, res)	
			else:
				return (0, None)
		elif s[0] == '(':
			if len(s) < 2 or k is None: return (0, None)

			tlen = tlen + 2
			if s[1] == '[':
				s = s[2:]
				offset, m = restore_map(s)
				if m is None: return (0, None)
				s = s[offset:]
				tlen = tlen + offset
				res[k] = m
				k = None
			elif s[1] == '{':
				s = s[2:]
				offset, m = restore_list(s)

				if m is None: return (0, None)
				s = s[offset:]
				tlen = tlen + offset
				res[k] = m
				k = None
			else: 
				return (0, None)

		else:
			return (0, None)
	
	return (0, None)

#parse the remain part of a list
def restore_list(s):
	res = []
	tlen = 0
	m = None
	while len(s) > 0:
		if s[0] == '\"' or s[0].isdigit() or s[0] == '-': 	
			offset, m = restore_trival(s)
			if offset == 0 or m is None:
				return (0, None)

			res.append(m)
			
			if offset == len(s):
				return (0, None)

			s = s[offset:]
			tlen = tlen + offset

		elif s[0] == '}':
			if len(s) < 2:	return (0, None)
			if s[1] == ')':
				return (tlen+2, res)
			else:
				return (0, None)
		elif s[0] == ',':
			tlen = tlen + 1	
			s = s[1:]
		elif s[0] == ' ':
			offset = 0
			while s[offset] == ' ' and offset < len(s):			
				offset = offset + 1

			if offset == len(s): return (0, None)
			s = s[offset:]
			tlen =  tlen + offset
		elif s[0] == '(':
			if len(s) < 2: return (0, None)

			tlen = tlen + 2
			if s[1] == '[':
				s = s[2:]
				offset, m = restore_map(s)
				if m is None: return (0, None)
				s = s[offset:]
				tlen = tlen + offset
				res.append(m)
			elif s[1] == '{':
				s = s[2:]
				offset, m = restore_list(s)

				if m is None: return (0, None)
				s = s[offset:]
				tlen = tlen + offset
				res.append(m)
			else: 
				return (0, None)
		else:
			return (0, None)

	return (0, None)
		
	
def restore_lpc_var(s):
	offset = 0
	m = None

	if s[0] == '\"' or s[0].isdigit() or s[0] == '-':
		offset, m = restore_trival(s)
		if m is None:
			return None

	if len(s) < 2: 
		return None
	if s[:2] == '([':
		offset, m = restore_map(s[2:])
	elif s[:2] == '({':
		offset, m = restore_list(s[2:])
	
	return m

if __name__ == '__main__':
	a = '({960,961,"on_rep_sync",({11,-2,}), "", ({}),})'
	m = restore_lpc_var(a)
	print str(m)
	'''
	#save_variable
	dat = {"key1":1234, "key2":{1:3,2:"sss", "k3":44}, 123:[1,2,"33", [5,6],{2:3}]}
	print 'save',serialize_lpc_var(dat)

	test_str = []
	test_str.append('\"xxhellog\"')
	test_str.append('12456')
	test_str.append('223FFF') #error
	#map and list
	test_str.append('({1, 3, "hello",  ({1, 2, "gg",}),  ({5,({6, }) }),({}), })')
	test_str.append('([1:3, "xx":44,"yy":"skey", "mm":(["bb":123, "cc":(["ii":567]),]), "dd":([])])')
	test_str.append('({1, "x", (["y":({1, 2, }), "z":32, "qq":(["ii":({5,3})])]), })')

	test_str.append('(["xx":([])])')
	#error map or list
#	test_str.append('([33, 2:3])')
#	test_str.append('({1, 2:"xx"})')
	
	for s in test_str:
		m = restore_lpc_var(s)
		print 'input: ', s
		print 'output: ', str(m)
	'''

