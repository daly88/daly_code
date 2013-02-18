from django.conf.urls import patterns, include, url
import settings

urlpatterns = patterns('',
   	url(r'^xyq_cover$', 'app.qcover.views.get_page'),
	url(r'^upload/$', 'app.upload.views.get_result'),
	url(r'^result$', 'app.result.views.get_result'),
	url(r'^result_new$', 'app.result.view_new.get_result'),
	url(r'^confirm$', 'app.result.views.do_confirm'),
	

	url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root':settings.STATIC_ROOT,}),
	url(r'^task$', 'app.taskview.views.get_page'),
	url(r'^task_action$', 'app.taskview.views.do_task_action'),

	url(r'^login$', 'accounts.login.views.get_page'),
	url(r'^logout$', 'accounts.login.views.do_logout'),
	url(r'^regist$', 'accounts.useradmin.views.do_regist'),
	url(r'^profile$', 'accounts.useradmin.views.do_modify'),
	url(r'^help$', 'app.help.views.get_result'),	
)
