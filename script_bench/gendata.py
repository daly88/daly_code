import random


def gen_array():
	arr = {}
	for i in xrange(0, 300):
		v = random.randint(1, 100000)
		if len(arr) > 200: break
		if v not in arr:
			arr[v] = 1

	msg = ''
	for v in arr:
		msg += str(v) + ','

	print msg

gen_array()
