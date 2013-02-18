# -*- coding: gbk -*-
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from app.qcover.models import Task
from django.db.models import Q
import datetime
import time

def get_result(req):
	mp = {}
	return render_to_response('help.html', mp)



