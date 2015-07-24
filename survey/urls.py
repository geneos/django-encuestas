from django.conf.urls import patterns, include, url, handler404
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import settings

admin.autodiscover()
media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')

urlpatterns = patterns('',	
	url(r'^$', 'survey.views.Index', name='home'),
	url(r'^survey/(\d+)/(\d+)/(\d+)/(\d)/(\d+)$', 'survey.views.SurveyDetail', name='surveydetail'),	
	url(r'^confirm/(?P<uuid>\w+)/$', 'survey.views.Confirm', name='confirmation'),
	url(r'^login/$', 'survey.views.login_page', name="login"),
    url(r'^logout/', 'django.contrib.auth.views.logout', {'next_page': '/'} , name="logout"),
	url(r'^admin/', include(admin.site.urls)),
)

#handler404 = 'survey.views.error404'

# media url hackery. le sigh. 
urlpatterns += patterns('',
    (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
     { 'document_root': settings.MEDIA_ROOT, 'show_indexes':True }),
)

