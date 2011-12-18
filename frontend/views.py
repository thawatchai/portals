from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
from django.http import HttpResponse, Http404, HttpResponseNotFound
from django.http import HttpResponseRedirect as redirect
from django.utils import feedgenerator

from backend.models import *
from backend.lib import get_page_obj, get_sys_info, system_request_context

from frontend.lib import *

# Portal

def page_not_found(request):
    return HttpResponseNotFound(loader.get_template('f/msg_box.html').render(system_request_context(request, {
        'msg': _('The requested page is not found. Please check the address.'),
        })))

def internal_server_error(request):
    return HttpResponseNotFound(loader.get_template('f/msg_box.html').render(system_request_context(request, {
        'msg': _('The system runs into a problem. It will be fixed as soon as possible.'),
        })))

def portal_main(request):
    sys_info = get_sys_info()
    if sys_info:
        return redirect(reverse('portals.frontend.views.portal_home', args=[sys_info.main_portal_address]))
    else:
        return HttpResponseNotFound(loader.get_template('f/msg_box.html').render(RequestContext(request, {
            'msg': _('Please set a main portal site address in "System information" using the admin interface.'),
            })))

@get_portal
def portal_home(request, portal):
    if portal.homepage_event:
        return redirect(domain_reverse(portal, 'portals.frontend.views.event_item', args=[portal.address, portal.homepage_event.id]))
    elif portal.homepage_news:
        return redirect(domain_reverse(portal, 'portals.frontend.views.news_item', args=[portal.address, portal.homepage_news.id]))
    elif portal.homepage_page:
        return redirect(domain_reverse(portal, 'portals.frontend.views.page_item', args=[portal.address, page_sid(portal.homepage_page)]))
    else:
        return render_to_response('f/base2.html', {
            }, portal_request_context(request, portal))

# Page

@get_portal
def page_list(request, portal):
    return domain_redirect_to(request, portal, '/')

@get_portal
def page_item(request, portal, s):
    page_item = get_page(portal, s)
    return render_to_response('f/page_item.html', {
        'page_obj': True,
        'map_info': make_map_info(portal, page_item),
        }, portal_request_context(request, portal, obj=page_item))

@get_portal
@get_keyword
def page_keyword(request, portal, k):
    page = get_page_obj(request, k.page_set.all().filter(deleted=False).filter(hidden=False).order_by('-modified_at'))
    return render_to_response('f/page_list.html', {
        'title': '%s: %s' % (__('Keyword'), k.title),
        'page': page,
        'total': page.paginator.count,
        }, portal_request_context(request, portal))

# News

@get_portal
def news_category_list(request, portal):
    page = get_page_obj(request, portal.news_set.all().filter(deleted=False).filter(hidden=False).filter(sticky=False).order_by('-created_at'))
    categories = get_page_obj(request, portal.newscategory_set.all().filter(deleted=False).order_by('title'))
    return render_to_response('f/news_category_list.html', {
        'page': page,
        'total': page.paginator.count,
        'categories': categories,
        }, portal_request_context(request, portal))

@get_portal
def news_list_by_category(request, portal, s):
    try:
        category = portal.newscategory_set.get(slug__exact=s)
    except ObjectDoesNotExist:
        return redirect(reverse('portals.frontend.views.news_category_list', args=[portal.address]))
    page = get_page_obj(request, portal.news_set.all().filter(deleted=False).filter(hidden=False).filter(sticky=False).filter(category=category).order_by('-created_at'))
    return render_to_response('f/news_list.html', {
        'title': '%s: %s' % (__('Category'), category.title),
        'page': page,
        'total': page.paginator.count,
        }, portal_request_context(request, portal))

@get_portal
def news_item(request, portal, news_id):
    news_item = cache.get('news_id_%s' % news_id)
    if not news_item:
        try:
            news_item = portal.news_set.filter(deleted=False).filter(hidden=False).get(id=news_id)
        except:
            raise Http404
        cache.set('news_id_%s' % news_item.id, news_item, 86400)
    return render_to_response('f/news_item.html', {
        'map_info': make_map_info(portal, news_item),
        }, portal_request_context(request, portal, obj=news_item))

@get_portal
@get_keyword
def news_keyword(request, portal, k):
    page = get_page_obj(request, k.news_set.all().filter(deleted=False).filter(hidden=False).order_by('-created_at'))
    return render_to_response('f/news_list.html', {
        'title': '%s: %s' % (__('Keyword'), k.title),
        'page': page,
        'total': page.paginator.count,
        }, portal_request_context(request, portal))

# Event

@get_portal
def event_category_list(request, portal):
    page = get_page_obj(request, portal.event_set.filter(deleted=False).filter(hidden=False).filter(sticky=False).order_by('-begin'))
    categories = get_page_obj(request, portal.eventcategory_set.all().filter(deleted=False).order_by('title'))
    return render_to_response('f/event_category_list.html', {
        'page': page,
        'total': page.paginator.count,
        'categories': categories,
        'sticky_event_list': portal.event_set.filter(deleted=False).filter(hidden=False).filter(sticky=True).order_by('-begin'),
        }, portal_request_context(request, portal))

@get_portal
def event_list_by_category(request, portal, s):
    try:
        category = portal.eventcategory_set.get(slug__exact=s)
    except ObjectDoesNotExist:
        return redirect(reverse('portals.frontend.views.event_category_list', args=[portal.address]))
    page = get_page_obj(request, portal.event_set.all().filter(deleted=False).filter(hidden=False).filter(sticky=False).filter(category=category).order_by('-begin'))
    return render_to_response('f/event_list.html', {
        'title': '%s: %s' % (__('Category'), category.title),
        'page': page,
        'total': page.paginator.count,
        }, portal_request_context(request, portal))

@get_portal
def event_item(request, portal, event_id):
    event_item = cache.get('event_id_%s' % event_id)
    if not event_item:
        try:
            event_item = portal.event_set.filter(deleted=False).filter(hidden=False).get(id=event_id)
        except:
            raise Http404
        cache.set('event_id_%s' % event_item.id, event_item, 86400)
    return render_to_response('f/event_item.html', {
        'map_info': make_map_info(portal, event_item),
        }, portal_request_context(request, portal, obj=event_item))

@get_portal
@get_keyword
def event_keyword(request, portal, k):
    page = get_page_obj(request, k.event_set.all().filter(deleted=False).filter(hidden=False).order_by('-begin'))
    return render_to_response('f/event_list.html', {
        'title': '%s: %s' % (__('Keyword'), k.title),
        'page': page,
        'total': page.paginator.count,
        }, portal_request_context(request, portal))

# Podcast

@get_portal
def podcast_category_list(request, portal):
    page = get_page_obj(request, portal.podcast_set.all().filter(deleted=False).filter(hidden=False).filter(sticky=False).order_by('-created_at'))
    categories = get_page_obj(request, portal.podcastcategory_set.all().filter(deleted=False).order_by('title'))
    return render_to_response('f/podcast_category_list.html', {
        'page': page,
        'total': page.paginator.count,
        'categories': categories,
        }, portal_request_context(request, portal))

@get_portal
def podcast_list_by_category(request, portal, s):
    try:
        category = portal.podcastcategory_set.get(slug__exact=s)
    except ObjectDoesNotExist:
        return redirect(reverse('portals.frontend.views.podcast_category_list', args=[portal.address]))
    page = get_page_obj(request, portal.podcast_set.all().filter(deleted=False).filter(hidden=False).filter(sticky=False).filter(category=category).order_by('-created_at'))
    return render_to_response('f/podcast_list.html', {
        'title': '%s: %s' % (__('Category'), category.title),
        'page': page,
        'total': page.paginator.count,
        }, portal_request_context(request, portal))

@get_portal
def podcast_item(request, portal, podcast_id):
    podcast_item = cache.get('podcast_id_%s' % podcast_id)
    if not podcast_item:
        try:
            podcast_item = portal.podcast_set.filter(deleted=False).filter(hidden=False).get(id=podcast_id)
        except:
            raise Http404
        cache.set('podcast_id_%s' % podcast_item.id, podcast_item, 86400)
    return render_to_response('f/podcast_item.html', {
        'map_info': make_map_info(portal, podcast_item),
        'enable_flowplayer': True,
        }, portal_request_context(request, portal, obj=podcast_item))

@get_portal
@get_keyword
def podcast_keyword(request, portal, k):
    page = get_page_obj(request, k.podcast_set.all().filter(deleted=False).filter(hidden=False).order_by('-created_at'))
    return render_to_response('f/podcast_list.html', {
        'title': '%s: %s' % (__('Keyword'), k.title),
        'page': page,
        'total': page.paginator.count,
        }, portal_request_context(request, portal))

# Feed

@get_portal
def feed_list(request, portal):
    return domain_redirect_to(request, portal, '/feeds/news/')

@get_portal
def feed_latest(request, portal):
    return domain_redirect_to(request, portal, '/feeds/news/')

@get_portal
def feed_news(request, portal):
    f = create_portal_feed(request, portal)

    for n in portal.news_set.filter(deleted=False).filter(hidden=False).order_by('-created_at')[:15]:
        uri = request.build_absolute_uri(domain_reverse(portal, 'portals.frontend.views.news_item', args=[portal.address, n.id]))
        f.add_item(
                title=n.title,
                description=n.content,
                link=uri,
                pubdate=n.created_at,
                unique_id=uri,
                )

    for evt in portal.upcoming_events():
        uri = request.build_absolute_uri(domain_reverse(portal, 'portals.frontend.views.event_item', args=[portal.address, evt.id]))
        f.add_item(
                title=evt.title,
                description=evt.content,
                link=uri,
                pubdate=evt.created_at,
                unique_id=uri,
                )

    return HttpResponse(f.writeString('UTF-8'), mimetype='application/rss+xml')

@get_portal
def feed_podcast(request, portal):
    f = create_portal_feed(request, portal)

    for n in portal.podcast_set.filter(deleted=False).filter(hidden=False).order_by('-created_at')[:15]:
        uri = request.build_absolute_uri(domain_reverse(portal, 'portals.frontend.views.podcast_item', args=[portal.address, n.id]))
        f.add_item(
                title=n.title,
                description=n.content,
                link=uri,
                pubdate=n.created_at,
                unique_id=uri,
                enclosure=feedgenerator.Enclosure(
                    url=request.build_absolute_uri(n.enclosure_url),
                    length=str(n.enclosure_length),
                    mime_type=n.enclosure_type,
                    ),
                )

    return HttpResponse(f.writeString('UTF-8'), mimetype='application/rss+xml')

# Misc

@get_portal
def next_portal(request, portal):
    return redirect(reverse('portals.frontend.views.portal_home', args=[get_random_portal(portal).address]))

# System

@check_main_portal
@get_portal
def system_stat(request, portal):
    return render_to_response('f/system_stat.html', {
        'users': User.objects.count(),
        'portals': Portal.objects.filter(deleted=False).count(),
        'pages': Page.objects.filter(deleted=False).count(),
        'news': News.objects.filter(deleted=False).count(),
        'events': Event.objects.filter(deleted=False).count(),
        'mediafiles': MediaFile.objects.filter(deleted=False).count(),
        }, portal_request_context(request, portal))

@check_main_portal
@get_portal
def system_portal_list(request, portal):
    page = get_page_obj(request, Portal.objects.filter(deleted=False).filter(suspended=False).order_by('-created_at'))
    return render_to_response('f/system_portal_list.html', {
        'page': page,
        'total': page.paginator.count,
        }, portal_request_context(request, portal))

