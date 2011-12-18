from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to

urlpatterns = patterns('portals.backend.views',

        # login/logout
        (r'^login/$', 'user_login'),
        (r'^logout/$', 'user_logout'),

        # etc.
        (r'^i18n/', include('django.conf.urls.i18n')),
        (r'^support/$', 'contact_support'),

        # users
        (r'^users/([^/]+)/$', 'user_portal_list'),

        # contributors 
        (r'^([^/]+)/contributors/$', 'contributor_list'),
        (r'^([^/]+)/contributors/create/$', 'contributor_create'),
        (r'^([^/]+)/contributors/create/confirm/$', 'contributor_create_confirm'),
        (r'^(?P<portal>[^/]+)/contributors/(?P<username>[^/]+)/$', redirect_to, {'url': '/portals/%(portal)s/contributors/',}),
        (r'^([^/]+)/contributors/([^/]+)/delete/$', 'contributor_delete'),

        # newscategories
        (r'^([^/]+)/news/categories/$', 'newscategory_list'),
        (r'^([^/]+)/news/categories/create/$', 'newscategory_create'),
        (r'^(?P<portal>[^/]+)/news/categories/(?P<nc>[^/]+)/$', redirect_to, {'url': '/portals/%(portal)s/news/categories/%(nc)s/edit/',}),
        (r'^([^/]+)/news/categories/([^/]+)/edit/$', 'newscategory_edit'),
        #(r'^([^/]+)/news/categories/([^/]+)/delete/$', 'newscategory_delete'),

        # news
        (r'^([^/]+)/news/$', 'news_list'),
        (r'^([^/]+)/news/data/$', 'news_list_data'),
        (r'^([^/]+)/news/create/$', 'news_create'),
        (r'^(?P<portal>[^/]+)/news/(?P<id>\d+)/$', redirect_to, {'url': '/portals/%(portal)s/news/%(id)s/edit/',}),
        (r'^([^/]+)/news/(\d+)/edit/$', 'news_edit'),
        (r'^([^/]+)/news/(\d+)/delete/$', 'news_delete'),

        # eventcategories
        (r'^([^/]+)/events/categories/$', 'eventcategory_list'),
        (r'^([^/]+)/events/categories/create/$', 'eventcategory_create'),
        (r'^(?P<portal>[^/]+)/events/categories/(?P<ec>[^/]+)/$', redirect_to, {'url': '/portals/%(portal)s/events/categories/%(ec)s/edit/',}),
        (r'^([^/]+)/events/categories/([^/]+)/edit/$', 'eventcategory_edit'),
        #(r'^([^/]+)/events/categories/([^/]+)/delete/$', 'eventcategory_delete'),

        # events
        (r'^([^/]+)/events/$', 'event_list'),
        (r'^([^/]+)/events/data/$', 'event_list_data'),
        (r'^([^/]+)/events/create/$', 'event_create'),
        (r'^(?P<portal>[^/]+)/events/(?P<id>\d+)/$', redirect_to, {'url': '/portals/%(portal)s/events/%(id)s/edit/',}),
        (r'^([^/]+)/events/(\d+)/edit/$', 'event_edit'),
        (r'^([^/]+)/events/(\d+)/delete/$', 'event_delete'),

        # pages
        (r'^([^/]+)/pages/$', 'page_list'),
        (r'^([^/]+)/pages/data/$', 'page_list_data'),
        (r'^([^/]+)/pages/create/$', 'page_create'),
        (r'^(?P<portal>[^/]+)/pages/(?P<id>\d+)/$', redirect_to, {'url': '/portals/%(portal)s/pages/%(id)s/edit/',}),
        (r'^([^/]+)/pages/(\d+)/edit/$', 'page_edit'),
        (r'^([^/]+)/pages/(\d+)/delete/$', 'page_delete'),

        # files
        (r'^([^/]+)/files/ftp-access/$', 'ftp_access'),
        (r'^([^/]+)/files/$', 'file_list'),
        (r'^([^/]+)/files/data/$', 'file_list_data'),
        (r'^([^/]+)/files/upload/$', 'file_create'),
        (r'^(?P<portal>[^/]+)/files/(?P<id>\d+)/$', redirect_to, {'url': '/portals/%(portal)s/files/%(id)s/edit/',}),
        (r'^([^/]+)/files/(\d+)/edit/$', 'file_edit'),
        (r'^([^/]+)/files/(\d+)/delete/$', 'file_delete'),

        # podcastcategories
        (r'^([^/]+)/podcasts/categories/$', 'podcastcategory_list'),
        (r'^([^/]+)/podcasts/categories/create/$', 'podcastcategory_create'),
        (r'^(?P<portal>[^/]+)/podcasts/categories/(?P<nc>[^/]+)/$', redirect_to, {'url': '/portals/%(portal)s/podcasts/categories/%(nc)s/edit/',}),
        (r'^([^/]+)/podcasts/categories/([^/]+)/edit/$', 'podcastcategory_edit'),
        #(r'^([^/]+)/podcasts/categories/([^/]+)/delete/$', 'podcastcategory_delete'),

        # podcast
        (r'^([^/]+)/podcasts/$', 'podcast_list'),
        (r'^([^/]+)/podcasts/data/$', 'podcast_list_data'),
        (r'^([^/]+)/podcasts/create/$', 'podcast_create'),
        (r'^(?P<portal>[^/]+)/podcasts/(?P<id>\d+)/$', redirect_to, {'url': '/portals/%(portal)s/podcasts/%(id)s/edit/',}),
        (r'^([^/]+)/podcasts/(\d+)/edit/$', 'podcast_edit'),
        (r'^([^/]+)/podcasts/(\d+)/delete/$', 'podcast_delete'),

        # keywords
        (r'^([^/]+)/keywords/$', 'keyword_list'),
        (r'^([^/]+)/keywords/create/$', 'keyword_create'),
        (r'^(?P<portal>[^/]+)/keywords/(?P<kw>[^/]+)/$', redirect_to, {'url': '/portals/%(portal)s/keywords/%(kw)s/edit/',}),
        (r'^([^/]+)/keywords/([^/]+)/edit/$', 'keyword_edit'),
        #(r'^([^/]+)/keywords/([^/]+)/delete/$', 'keyword_delete'),

        # portals
        (r'^$', 'portal_list'),
        (r'^create/$', 'portal_create'),
        (r'^([^/]+)/$', 'portal_main'),
        (r'^([^/]+)/edit/$', 'portal_edit'),
        (r'^([^/]+)/delete/$', 'portal_delete'),
        (r'^([^/]+)/under-development/$', 'under_development'),
        (r'^(?P<portal>[^/]+)/homepage/$', redirect_to, {'url': '/portals/%(portal)s/homepage/page',}),
        (r'^([^/]+)/homepage/page/$', 'portal_homepage_page'),
        (r'^([^/]+)/homepage/news/$', 'portal_homepage_news'),
        (r'^([^/]+)/homepage/event/$', 'portal_homepage_event'),
        (r'^([^/]+)/theme/$', 'portal_theme'),

        )

