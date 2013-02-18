#!/usr/bin/env python
# -*- coding: gb18030 -*-

import time
import httplib

################################################################################
def strfnow():
    '''��ȡ��ǰʱ��'''
    return time.strftime('%Y-%m-%d(%a) %H:%M:%S')

def strfdate(date):
    '''����������ʾ��ʽ'''
    t = time.strptime(date, '%Y%m%d')
    t = time.strftime('%Y-%m-%d(%a)', t)
    return t

def log(msg):
	f = open('debug.log', 'a')
	f.write(strfnow() + '  ')
	f.write(msg)
	f.write('\n')
	f.close()

if __name__=='__main__':
	log('gsfsdf')
