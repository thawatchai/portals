from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to
from django.conf import settings

import os

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
        (r'^portals/', include('portals.backend.urls')),
        (r'^captcha/', include('captcha.urls')),
        (r'^admin/tools/', include('portals.admin_tools.urls')),
        (r'^admin/(.*)', admin.site.root),

        (r'^login/$', redirect_to, {'url': '/portals/login'}),
        (r'^logout/$', redirect_to, {'url': '/portals/logout'}),
        )

if settings.DEBUG:
    urlpatterns += patterns('',
            (r'^files/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '%s/public/files' % os.path.dirname(__file__)}),
            (r'^images/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '%s/public/images' % os.path.dirname(__file__)}),
            (r'^stylesheets/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '%s/public/stylesheets' % os.path.dirname(__file__)}),
            (r'^javascripts/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '%s/public/javascripts' % os.path.dirname(__file__)}),
            (r'^yui/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '%s/public/yui' % os.path.dirname(__file__)}),
            (r'^flowplayer/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '%s/public/flowplayer' % os.path.dirname(__file__)}),
            (r'^themes/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '%s/public/themes' % os.path.dirname(__file__)}),
            )

urlpatterns += patterns('',
        (r'', include('portals.frontend.urls')),
        )

handler404 = 'portals.frontend.views.page_not_found'
handler500 = 'portals.frontend.views.internet_server_error'

