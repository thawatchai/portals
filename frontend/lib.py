from django.utils.translation import ugettext_lazy as _
from django.utils import translation
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.http import Http404
from django.http import HttpResponseRedirect as redirect
from django.template import RequestContext
from django.utils import feedgenerator
from django.conf import settings

from backend.models import *
from backend.lib import get_sys_info, ITEMS_PER_PAGE

import random

# Portal

def get_portal(f):
    def d(request, address, *args):
        portal = cache.get('portal_address_%s' % address)
        if not portal:
            try:
                portal = Portal.objects.filter(deleted=False).get(address__exact=address)
            except:
                raise Http404
            cache.set('portal_address_%s' % address, portal, 86400)

        if portal.language:
            translation.activate(portal.language)
            request.LANGUAGE_CODE = portal.language
        else:
            translation.activate(settings.LANGUAGE_CODE)
            request.LANGUAGE_CODE = settings.LANGUAGE_CODE
        if portal.domain_address:
            if request.META['HTTP_HOST'] != portal.address:
                return redirect('http://%s%s' % (
                    portal.address,
                    request.path.replace('/%s' % portal.address, ''),
                    ))
        return f(request, portal, *args)
    return d

def domain_reverse(portal, view_name, urlconf=None, args=None, kwargs=None, prefix=None):
    try:
        uri = reverse(view_name, urlconf=urlconf, args=args, kwargs=kwargs, prefix=prefix)
    except:
        uri = reverse('%s.%s' % (settings.SETTINGS_MODULE.split('.')[0], view_name), urlconf=urlconf, args=args, kwargs=kwargs, prefix=prefix)
    if portal.domain_address:
        return uri.replace('/%s' % portal.address, '')
    else:
        return uri 

def domain_redirect_to(request, portal, url):
    if not portal.domain_address:
        url = '/%s%s' % (portal.address, url)
    return redirect(url)

def check_main_portal(f):
    def d(request, address, *args):
        sys_info = get_sys_info()
        if not sys_info or sys_info.main_portal_address != address:
            return redirect(reverse('portals.frontend.views.portal_home', args=[address]))
        else:
            return f(request, address, *args)
    return d

def portal_request_context(request, portal, obj=None):
    return RequestContext(request, {
        'portal': portal,
        'sys_info': get_sys_info(),
        'ITEMS_PER_PAGE': ITEMS_PER_PAGE,
        'portal_feed_uri': request.build_absolute_uri(domain_reverse(portal, 'portals.frontend.views.feed_news', args=[portal.address])),
        'portal_podcast_feed_uri': request.build_absolute_uri(domain_reverse(portal, 'portals.frontend.views.feed_podcast', args=[portal.address])),
        'obj': obj,
        })

def create_portal_feed(request, portal):
    return feedgenerator.Rss201rev2Feed(
            title=portal.title,
            link=request.build_absolute_uri(domain_reverse(portal, 'portals.frontend.views.portal_home', args=[portal.address])),
            description=portal.subtitle,
            )

def get_random_portal(portal):
    random.seed()
    r = random.randint(1, Portal.objects.filter(deleted=False).count())
    try:
        np = Portal.objects.get(id=r)
    except:
        np = portal
    return np

def get_page(portal, s):
    try:
        return portal.page_set.filter(deleted=False).filter(hidden=False).get(id=s)
    except:
        pass
    try:
        return portal.page_set.filter(deleted=False).filter(hidden=False).get(slug=s)
    except:
        raise Http404

def upcoming_datetime(datetime):
    return True if datetime >= datetime.today() else False

def make_map_info(portal, obj):
    if obj.latitude and obj.longitude:
        key = ''
        if settings.GOOGLE_MAPS_API_KEY:
            key = settings.GOOGLE_MAPS_API_KEY
        if portal.domain_address:
            key = portal.gmap_api_key
        return {
                'key': key,
                'latitude': obj.latitude,
                'longitude': obj.longitude,
                'title': obj.title,
                } if key else {}
    else:
        return {}

def page_sid(page):
    return page.slug if page.slug else page.id

def get_keyword(f):
    def d(request, portal, slug):
        try:
            keyword = portal.keyword_set.get(slug__exact=slug)
        except ObjectDoesNotExist:
            return redirect(reverse('portals.frontend.views.portal_main', args=[portal.address]))
        return f(request, portal, keyword)
    return d
