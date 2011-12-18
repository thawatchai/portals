from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to

urlpatterns = patterns('portals.frontend.views',

        (r'^page-not-found/$', 'page_not_found'),

        # home
        (r'^([^/]+)/$', 'portal_home'),

        # pages
        (r'^([^/]+)/pages/$', 'page_list'),
        (r'^([^/]+)/pages/([^/]+)/$', 'page_item'),
        (r'^([^/]+)/pages/keyword/([^/]+)/$', 'page_keyword'),

        # news
        (r'^([^/]+)/news/$', 'news_category_list'),
        (r'^([^/]+)/news/(\d+)/$', 'news_item'),
        (r'^([^/]+)/news/category/([^/]+)/$', 'news_list_by_category'),
        (r'^([^/]+)/news/keyword/([^/]+)/$', 'news_keyword'),

        # events
        (r'^([^/]+)/events/$', 'event_category_list'),
        (r'^([^/]+)/events/(\d+)/$', 'event_item'),
        (r'^([^/]+)/events/category/([^/]+)/$', 'event_list_by_category'),
        (r'^([^/]+)/events/keyword/([^/]+)/$', 'event_keyword'),

        # podcasts
        (r'^([^/]+)/podcasts/$', 'podcast_category_list'),
        (r'^([^/]+)/podcasts/(\d+)/$', 'podcast_item'),
        (r'^([^/]+)/podcasts/category/([^/]+)/$', 'podcast_list_by_category'),
        (r'^([^/]+)/podcasts/keyword/([^/]+)/$', 'podcast_keyword'),

        # feeds
        (r'^([^/]+)/feeds/$', 'feed_list'),
        (r'^([^/]+)/feeds/latest/$', 'feed_latest'),
        (r'^([^/]+)/feeds/news/$', 'feed_news'),
        (r'^([^/]+)/feeds/podcast/$', 'feed_podcast'),

        # misc
        (r'^([^/]+)/next-portal/$', 'next_portal'),

        # system
        (r'^(?P<portal>[^/]+)/system/$', redirect_to, {'url': '/%(portal)s/'}),
        (r'^([^/]+)/system/stat/$', 'system_stat'),
        (r'^([^/]+)/system/portals/$', 'system_portal_list'),

        (r'^$', 'portal_main'),
        )

