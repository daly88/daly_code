import random
import copy

g_int_array = [1,23,4,5,7,15,6,2]


#shuffle array then find each element in origin position
def shuffle_pick(origin, n):
	l = len(origin)
	pick = []
	for v in origin:
		pick.append(v)

	#shuffle
	i,j,tmp = 0,0,0
	for c in xrange(1, n):
		i = random.randint(0, l-1)
		if i > l/2: 
			j = random.randint(0, i-1)
		else: 
			j = random.randint(i+1, l-1)
		#swap
		tmp = pick[i]
		pick[i] = pick[j]
		pick[j] = tmp
	
	for v in pick:
		for i in xrange(0,l):
			if v == origin[i]:
				#print i
				pass

for i in xrange(0,1000):
	shuffle_pick(g_int_array, 1000)
