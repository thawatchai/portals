from django.conf.urls.defaults import *

urlpatterns = patterns('portals.admin_tools.views',
        (r'^$', 'tool_list'),
        (r'^email/all/$', 'email_all'),
        )

