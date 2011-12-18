from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.shortcuts import render_to_response
from django.template import RequestContext
from django import forms
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect as redirect
from django.db import IntegrityError
from django.conf import settings

from captcha.fields import CaptchaField
from backend.models import *

import re
import os
from os import path
import socket

ITEMS_PER_PAGE = 20

# General

class ForceDefaultLanguageMiddleware(object):
    def process_request(self, request):
        if request.META.has_key('HTTP_ACCEPT_LANGUAGE'):
            del request.META['HTTP_ACCEPT_LANGUAGE']

def set_message(request, msg):
    request.user.message_set.create(message=msg)

def slug_field(required=True, optional=True):
    return forms.RegexField(
            label=_('Slug'),
            regex=r'^[\-a-z0-9]+$',
            help_text=_('A slug is a string representing a title in a web address (URL). Valid characters are a-z, 0-9, and dashes (-). Space is not allowed, and it cannot begin or end with a dash. (optional)') if optional else _('A slug is a string representing a title in a web address (URL). Valid characters are a-z, 0-9, and dashes (-). Space is not allowed, and it cannot begin or end with a dash.'),
            required=required)

def date_field():
    pass

def time_choices():
    l = []
    for h in range(24):
        for m in ('00', '30',):
            t = '%s:%s' % (h, m)
            l.append((t, t))
    return l

def time_choice_field(label):
    return forms.TimeField(
            label=label,
            input_formats=['%H:%M'],
            widget=forms.Select(choices=time_choices()))

def textarea_attrs():
    return {'id': 'form-content', 'rows': 20,}

def get_user(username):
    try:
        user = User.objects.get(username=username)
    except:
        user = None
    return user

def user_display_name(user):
    full_name = user.get_full_name()
    return full_name if full_name else user.username

def get_sys_info():
    sys_info = cache.get('sys_info')
    if not sys_info:
        try:
            sys_info = SystemInfo.objects.all()[0]
        except:
            sys_info = None
        cache.set('sys_info', sys_info, 86400)
    return sys_info

def get_item_object(otype, portal, id):
    if otype == 'page':
        try:
            item = portal.page_set.get(id=id)
        except:
            item = None
    elif otype == 'news':
        try:
            item = portal.news_set.get(id=id)
        except:
            item = None
    elif otype == 'event':
        try:
            item = portal.event_set.get(id=id)
        except:
            item = None
    return item

def is_allowed_upload(u):
    try:
        profile = u.get_profile()
    except:
        profile = None
    return True if profile and profile.allow_upload else False

def system_request_context(request, c={}):
    c['sys_info'] = get_sys_info()
    c['form_base'] = 'b/base2r.html'
    return RequestContext(request, c)

def portal_request_context(request, portal):
    return RequestContext(request, {
        'portal': portal,
        'sys_info': get_sys_info(),
        'ITEMS_PER_PAGE': ITEMS_PER_PAGE,
        'form_base': 'b/base2b.html',
        'allow_upload': is_allowed_upload(request.user),
        })

def get_req_page(request):
    try:
        return int(request.GET.get('page', '1'))
    except ValueError:
        return 1

def get_page_obj(request, qset):
    paginator = Paginator(qset, ITEMS_PER_PAGE)
    try:
        return paginator.page(get_req_page(request))
    except (EmptyPage, InvalidPage):
        return paginator.page(paginator.num_pages)

def node_delete(request, portal, node, title, message, return_url):
    if request.method == 'POST':
        if request.POST.has_key('yes'):
            node.mark_deleted()
        return redirect(return_url)
    return render_to_response('b/confirm_form.html', {
        'title': title,
        'message': message,
        }, portal_request_context(request, portal))

class FormWithKeywords(forms.ModelForm):
    def __init__(self, portal, *args, **kwargs):
        super(FormWithKeywords, self).__init__(*args, **kwargs)
        self.fields['keywords'].queryset = portal.keyword_set.order_by('title')

def access_denied_response(request, return_url=None):
    if not return_url:
        return_url = request.META['HTTP_REFERER'] if request.META.has_key('HTTP_REFERER') else reverse('portals.backend.views.portal_list')
    return render_to_response('b/msg_box.html', {
        'title': _('Access Denied'),
        'message': _('You attempt to access an unauthorized feature.'),
        'return_url': return_url,
        }, system_request_context(request))

def save_success_message(request):
    request.user.message_set.create(message=ugettext('The action was completed successfully.'))

class SupportForm(forms.Form):
    subject = forms.CharField(label=_('Email Subject'))
    message = forms.CharField(label=_('Email Message'), widget=forms.Textarea)

def locked_error(request, portal, x, return_url):
    return render_to_response('b/msg_box.html', {
        'title': _('Being Edited Now'),
        'message': x.error_message(request.user),
        'return_url': return_url,
        }, portal_request_context(request, portal))

re_script = re.compile(r'<script.+script>')

def strip_script(s):
    return re_script.sub('<span class="js-mark">JavaScript</span>', s)

# User

class LoginForm(forms.Form):
    username = forms.CharField(label=_('Username'))
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput)
    captcha = CaptchaField()

# Portal

class PortalForm(forms.ModelForm):
    address = forms.RegexField(label=_('Address'), regex=r'^[a-z][\-\.a-z0-9]+[a-z0-9]$', required=True, min_length=3, max_length=50)

    def __init__(self, sys_info, *args, **kwargs):
        super(PortalForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['address', 'domain_address', 'title', 'subtitle', 'copyright_holder', 'license', 'description', 'contact_information', 'language', 'other_information', 'footer', 'announcement', 'gmap_api_key']
        if sys_info:
            self.fields['address'].help_text = _('A portal address must start with an a-z character following by a-z, 0-9, - (dash), or . (dot) characters. It must be less than 100 characters. For example "mgt-psu", in which it will be accessible from "%s"') % 'http://%s/mgt-psu' % sys_info.site_address
            self.fields['domain_address'].help_text = _('This is a valid domain and its DNS server maps it to %s. (You may need to contact your network administrator to use this feature.)') % settings.FRONTEND_IP

    class Meta:
        model = Portal

def get_own_portal(f):
    def d(request, address, *args):
        try:
            portal = request.user.portal_set.get(address__exact=address)
        except ObjectDoesNotExist:
            return access_denied_response(request)
        return f(request, portal, *args)
    return d

def get_portal(f):
    def d(request, address, *args):
        if address in ('users',):
            return redirect(reverse('portals.backend.views.portal_list'))
        try:
            portal = Portal.objects.get(address__exact=address)
        except:
            portal = None
        if portal and request.user != portal.owner and request.user not in portal.contributors.all():
            portal = None
        if portal and portal.deleted:
            portal = None
        if not portal:
            return access_denied_response(request)
        return f(request, portal, *args)
    return d

def portal_create_or_edit(request, portal=None):
    edit = True if portal else False
    if request.method == 'POST':
        form = PortalForm(get_sys_info(), request.POST, instance=portal) if edit else PortalForm(get_sys_info(), request.POST)
        if form.is_valid():
            portal = form.save(commit=False)

            valid_address = True
            if portal.domain_address:
                try:
                    ip = socket.gethostbyname(portal.address)
                except:
                    ip = None
                if not ip or ip != settings.FRONTEND_IP:
                    valid_address = False
                    form.errors['address'] = [_('This domain must set to the following IP address: %s') % settings.FRONTEND_IP]
                    form.errors['domain_address'] = [_('You cannot use this feature because the domain name has not been properly set.')]

            #if valid_address:
            if True:
                if not edit:
                    portal.owner = request.user
                portal.save()
                save_success_message(request)
                if request.POST.has_key('save-continue'):
                    return redirect(reverse('portals.backend.views.portal_edit', args=[portal.address]))
                else:
                    if edit:
                        EditLock.unset(request.user, portal.id, 'PORTAL')
                    return redirect(reverse('portals.backend.views.portal_main', args=[portal.address]))
    else:
        form = PortalForm(get_sys_info(), instance=portal)
        if edit:
            EditLock.set(request.user, portal.id, 'PORTAL')
    return render_to_response('b/common_form.html', {
        'title': _('Edit This Portal') if edit else _('Create New Portal'),
        'form': form,
        'disable_tiny_mce': True,
        #'delete_url': reverse('portals.backend.views.portal_delete', args=[portal.address]) if edit else None,
        }, portal_request_context(request, portal))

class HomePageForm(forms.Form):
    item = forms.TypedChoiceField(coerce=int, required=False,
            help_text=_('Select a page to be the first page of this portal, or select none to reset it.'))

    def __init__(self, label, help_text, *args, **kwargs):
        super(HomePageForm, self).__init__(*args, **kwargs)
        self.fields['item'].label = label
        self.fields['item'].help_text = help_text

def set_portal_homepage(request, portal, choices, current_item, otype, type_label, help_text):
    if choices:
        d = request.POST if request.method == 'POST' else None
        form = HomePageForm(type_label, help_text, d)
        form.fields['item'].choices = [(0, '---------'),] + choices
        if current_item:
            form.fields['item'].initial = current_item.id

        if request.method == 'POST' and form.is_valid():
            portal.set_homepage(otype, get_item_object(otype, portal, form.cleaned_data['item']) if form.cleaned_data['item'] > 0 else None)
            save_success_message(request)
            return redirect(reverse('portals.backend.views.portal_main', args=[portal.address]))
        return render_to_response('b/common_form.html', {
            'title': _('Set Home Page'),
            'form': form,
            'button_label': _('Set'),
            'help_text': _('''You can set three items as the home page of a portal: an event, a news, and a page. However, all items will not be the home page in the same time. If set, the event will be chosen as the home page following by the news and the page. For example, if you want to set a news as the home page, you must not set a page.'''),
            }, portal_request_context(request, portal))
    else:
        return render_to_response('b/msg_box.html', {
            'title': _('No %s') % type_label,
            'message': _('This portal does not have an item in the type you want to set as its homepage. Please create a item first.'),
            'return_url': reverse('portals.backend.views.portal_main', args=[portal.address]),
            }, portal_request_context(request, portal))

class CssForm(forms.Form):
    css = forms.CharField(label=_('CSS'), widget=forms.Textarea(attrs=textarea_attrs()))
    left_sidebar = forms.BooleanField(label=_('Left Sidebar'), required=False,
            help_text=_('Check to display a sidebar on the left side. Uncheck to display it on the right side.'))
    hide_header_title = forms.BooleanField(label=_('Hide Header Title'), required=False,
            help_text=_('Check above to hide the header title.'))

def get_user_portal_list(request, user):
    return render_to_response('b/portal_list.html', {
        'my_portals': user.portal_set.filter(deleted=False),
        'contributed_portals': Portal.objects.filter(deleted=False).filter(contributors__exact=user),
        'portal_user': user,
        }, system_request_context(request))

# Contributor

class ContributorForm(forms.Form):
    username = forms.CharField(label=_('Username'),
            help_text=_('Enter the username of the person to add as a contributor of this portal. The user must have logged in to this system before.'))

class ContributorConfirmationForm(forms.Form):
    username = forms.CharField(widget=forms.HiddenInput)

# Category

class CategoryForm(forms.ModelForm):
    slug = slug_field(optional=False)

    class Meta:
        model = Category

def category_list(request, portal, title, categories, url_prefix, no_item_msg, create_item_info=None):
    return render_to_response('b/category_list.html', {
        'title': title,
        'categories': categories,
        'url_prefix': url_prefix,
        'no_item_msg': no_item_msg,
        'create_item_info': create_item_info,
        }, portal_request_context(request, portal))

def category_create(request, portal, form_title, FormClass, success_url, err_msg, help_text=None):
    return category_create_or_edit(request, portal, form_title, FormClass, success_url, err_msg, help_text=help_text)

def category_edit(request, portal, category, form_title, FormClass, success_url, err_msg, lock_otype, help_text=None):
    return category_create_or_edit(request, portal, form_title, FormClass, success_url, err_msg, category, lock_otype, help_text)

def category_create_or_edit(request, portal, form_title, FormClass, success_url, err_msg, category=None, lock_otype=None, help_text=None):
    edit = True if category else False
    if request.method == 'POST':
        form = FormClass(request.POST, instance=category) if edit else FormClass(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.portal = portal
            success = False
            try:
                category.save()
                success = True
            except IntegrityError:
                pass
            if success:
                save_success_message(request)
                if edit:
                    EditLock.unset(request.user, category.id, lock_otype)
                return redirect(success_url)
            else:
                form.errors['title'] = [err_msg]
    else:
        form = FormClass(instance=category) if edit else FormClass()
        if edit:
            EditLock.set(request.user, category.id, lock_otype)
    return render_to_response('b/common_form.html', {
        'title': form_title,
        'form': form,
        'button_label': _('Save'),
        'help_text': help_text,
        'form_base': 'b/base2r.html',
        }, portal_request_context(request, portal))

#def category_delete(request, portal, category, count, return_url):
#    if count > 0:
#        return render_to_response('b/msg_box.html', {
#            'title': _('Unable to Delete'),
#            'message': _('%d items depend on this category or keyword. It cannot be deleted.') % count,
#            'return_url': return_url,
#            }, portal_request_context(request, portal))
#    else:
#        if request.method == 'POST':
#            if request.POST.has_key('yes'):
#                category.delete()
#            return redirect(return_url)
#        else:
#            print 'abc'
#        return render_to_response('b/confirm_form.html', {
#            'title': _('Are you sure you want to delete this?'),
#            'message': '%s (%s)' % (category.title, category.slug),
#            }, portal_request_context(request, portal))

# Keyword

class KeywordForm(CategoryForm):
    class Meta(CategoryForm.Meta):
        model = Keyword

def get_keyword(f):
    def d(request, portal, slug):
        try:
            keyword = portal.keyword_set.get(slug__exact=slug)
        except ObjectDoesNotExist:
            return redirect(reverse('portals.backend.views.keyword_list', args=[portal.address]))
        return f(request, portal, keyword)
    return d

def keyword_required(f):
    def d(request, portal, item=None):
        if portal.keyword_set.count() == 0:
            return render_to_response('b/msg_box.html', {
                'title': _('No Keyword'),
                'message': _('This portal does not have keywords to tag contents of this portal. Please create some keywords first.'),
                }, portal_request_context(request, portal))
        else:
            return f(request, portal, item) if item else f(request, portal)
    return d

def keyword_form_info(portal):
    return [reverse('portals.backend.views.keyword_list', args=[portal.address]),
            _('A keyword with the title or the slug is already defined for this portal.'),
            _('''A keyword is a word that represent a concept. Keywords are used to identify the key ideas of pages, news, events, and files. For example, a school portal may have the following keywords: Teaching, Extra Curriculum Activity, Parent, etc.

Keywords can also be used to distinguish relavance of information to groups of users. As an example, the following keywords may be defined for a university portal: Prospective Students, Current Students, Researchers, Staff, Visitors.'''),]

# NewsCategory

class NewsCategoryForm(CategoryForm):
    class Meta(CategoryForm.Meta):
        model = NewsCategory

def get_newscategory(f):
    def d(request, portal, slug):
        try:
            newscategory = portal.newscategory_set.get(slug__exact=slug)
        except ObjectDoesNotExist:
            return redirect(reverse('portals.backend.views.newscategory_list', args=[portal.address]))
        return f(request, portal, newscategory)
    return d

def newscategory_required(f):
    def d(request, portal, news=None):
        if portal.newscategory_set.count() == 0:
            return render_to_response('b/msg_box.html', {
                'title': _('No News Category'),
                'message': _('No news category has been defined for this portal. To post a news, you need a news category. Please create a news category first.'),
                }, portal_request_context(request, portal))
        else:
            return f(request, portal, news) if news else f(request, portal)
    return d

def newscategory_form_info(portal):
    return [reverse('portals.backend.views.newscategory_list', args=[portal.address]),
            _('A news category with the title or the slug is already defined for this portal.')]

# News

class NewsForm(FormWithKeywords):
    content = forms.CharField(label=_('Content'), widget=forms.Textarea(attrs=textarea_attrs()))

    def __init__(self, portal, *args, **kwargs):
        super(NewsForm, self).__init__(portal, *args, **kwargs)
        self.fields.keyOrder = ['title', 'content', 'hidden', 'sticky', 'category', 'latitude', 'longitude', 'keywords']
        self.fields['category'].queryset = portal.newscategory_set.order_by('title')

    class Meta:
        model = News

def get_news(f):
    def d(request, portal, news_id):
        try:
            news = portal.news_set.get(id__exact=news_id)
        except:
            return redirect(reverse('portals.backend.views.news_list', args=[portal.address]))
        return f(request, portal, news)
    return d

def news_create_or_edit(request, portal, news=None):
    edit = True if news else False
    if request.method == 'POST':
        form = NewsForm(portal, request.POST, instance=news) if news else NewsForm(portal, request.POST)
        if form.is_valid():
            news = form.save(commit=False)
            news.portal = portal
            news.save()
            form.save_m2m()
            news.save_writer(request.user)
            save_success_message(request)
            if request.POST.has_key('save-continue'):
                return redirect(reverse('portals.backend.views.news_edit', args=[portal.address, news.id]))
            else:
                if edit:
                    EditLock.unset(request.user, news.id, 'NEWS')
                return redirect(reverse('portals.backend.views.news_list', args=[portal.address]))
    else:
        form = NewsForm(portal, instance=news) if news else NewsForm(portal)
        if edit:
            EditLock.set(request.user, news.id, 'NEWS')
    return render_to_response('b/common_form.html', {
        'title': _('Edit News') if edit else _('Create News'),
        'form': form,
        'edit': edit,
        'delete_url': reverse('portals.backend.views.news_delete', args=[portal.address, news.id]) if edit else None,
        'view_url': reverse('portals.frontend.views.news_item', args=[portal.address, news.id]) if edit else None,
        }, portal_request_context(request, portal))

# EventCategory

class EventCategoryForm(CategoryForm):
    class Meta(CategoryForm.Meta):
        model = EventCategory

def get_eventcategory(f):
    def d(request, portal, slug):
        try:
            eventcategory = portal.eventcategory_set.get(slug__exact=slug)
        except ObjectDoesNotExist:
            return redirect(reverse('portals.backend.views.eventcategory_list', args=[portal.address]))
        return f(request, portal, eventcategory)
    return d

def eventcategory_required(f):
    def d(request, portal, event=None):
        if portal.eventcategory_set.count() == 0:
            return render_to_response('b/msg_box.html', {
                'title': _('No Event Category'),
                'message': _('No event category has been defined for this portal. To post an event, you need an event category. Please create an event category first.'),
                }, portal_request_context(request, portal))
        else:
            return f(request, portal, event) if event else f(request, portal)
    return d

def eventcategory_form_info(portal):
    return [reverse('portals.backend.views.eventcategory_list', args=[portal.address]),
            _('An event category with the title or the slug is already defined for this portal.')]

# Event

class EventForm(FormWithKeywords):
    content = forms.CharField(label=_('Content'), widget=forms.Textarea(attrs=textarea_attrs()))
#    begin_time = time_field(_('Begin Time'))
#    end_time = time_field(_('End Time'))

    def __init__(self, portal, *args, **kwargs):
        super(EventForm, self).__init__(portal, *args, **kwargs)
        self.fields.keyOrder = ['title', 'content', 'hidden', 'sticky', 'category', 'location', 'begin', 'end', 'latitude', 'longitude', 'keywords']
        self.fields['category'].queryset = portal.eventcategory_set.order_by('title')

    class Meta:
        model = Event

def get_event(f):
    def d(request, portal, event_id):
        try:
            event = portal.event_set.get(id__exact=event_id)
        except:
            return redirect(reverse('portals.backend.views.event_list', args=[portal.address]))
        return f(request, portal, event)
    return d

def event_create_or_edit(request, portal, event=None):
    edit = True if event else False
    if request.method == 'POST':
        form = EventForm(portal, request.POST, instance=event) if event else EventForm(portal, request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.portal = portal
            if event.begin < event.end:
                event.save()
                form.save_m2m()
                event.save_writer(request.user)
                save_success_message(request)
                if request.POST.has_key('save-continue'):
                    return redirect(reverse('portals.backend.views.event_edit', args=[portal.address, event.id]))
                else:
                    if edit:
                        EditLock.unset(request.user, event.id, 'EVENT')
                    return redirect(reverse('portals.backend.views.event_list', args=[portal.address]))
            else:
                form.errors['begin'] = [_('The beginning time must preceed the ending time.')]
    else:
        form = EventForm(portal, instance=event) if event else EventForm(portal)
        if edit:
            EditLock.set(request.user, event.id, 'EVENT')
    return render_to_response('b/common_form.html', {
        'title': _('Edit Event') if edit else _('Create Event'),
        'form': form,
        'edit': edit,
        'delete_url': reverse('portals.backend.views.event_delete', args=[portal.address, event.id]) if edit and event.id else None,
        'view_url': reverse('portals.frontend.views.event_item', args=[portal.address, event.id]) if edit and event.id else None,
        }, portal_request_context(request, portal))

# Page

class PageForm(FormWithKeywords):
    content = forms.CharField(label=_('Content'), widget=forms.Textarea(attrs=textarea_attrs()))
    slug = slug_field(required=False)

    def __init__(self, portal, *args, **kwargs):
        super(PageForm, self).__init__(portal, *args, **kwargs)
        self.fields.keyOrder = ['title', 'content', 'hidden', 'sticky', 'parent', 'slug', 'weight', 'show_children', 'latitude', 'longitude', 'keywords']
        self.fields['parent'].queryset = portal.page_set.filter(deleted=False).order_by('title')

    class Meta:
        model = Page

def get_page(f):
    def d(request, portal, page_id):
        page = cache.get('page_id_%s' % page_id)
        if not page:
            try:
                page = portal.page_set.get(id__exact=page_id)
            except:
                return redirect(reverse('portals.backend.views.page_list', args=[portal.address]))
            cache.set('page_id_%s' % page.id, page, 86400)
        return f(request, portal, page)
    return d

def valid_slug(portal, page):
    if page.slug:
        exist_pages = portal.page_set.filter(slug=page.slug)
        if exist_pages:
            return True if exist_pages[0].id == page.id else False
    return True

def valid_title(portal, page):
    exist_pages = portal.page_set.filter(title=page.title)
    if exist_pages:
        return True if exist_pages[0].id == page.id else False
    return True

def page_create_or_edit(request, portal, page=None):
    edit = True if page else False
    if not page:
        page = Page(portal=portal)
        source_id = request.GET.get('source')
        if source_id:
            try:
                source = portal.page_set.get(id=source_id)
            except:
                source = None
            if source:
                page.title = '%s (%s)' % (source.title, _('copy'))
                page.content = source.content
    if request.method == 'POST':
        form = PageForm(portal, request.POST, instance=page)
        if form.is_valid():
            page = form.save(commit=False)
            if not edit or page.parent == None or page.id not in page.parent.ancestor_id_list():
                if valid_slug(portal, page):
                    if valid_title(portal, page):
                        page.save()
                        form.save_m2m()
                        page.save_writer(request.user)
                        save_success_message(request)
                        if request.POST.has_key('save-continue'):
                            return redirect(reverse('portals.backend.views.page_edit', args=[portal.address, page.id]))
                        else:
                            if edit:
                                EditLock.unset(request.user, page.id, 'PAGE')
                            return redirect('%s?p=%s' % (reverse('portals.backend.views.page_list', args=[portal.address]), page.id))
                    else:
                        form.errors['title'] = [_('A book page with this title already exists. Please choose another one.')]
                else:
                    form.errors['slug'] = [_('This slug is already used. Please choose another one.')]
            else:
                form.errors['parent'] = [_('Invalid value. The new parent is a child of this page.')]
    else:
        form = PageForm(portal, instance=page)
        if edit:
            EditLock.set(request.user, page.id, 'PAGE')
    return render_to_response('b/common_form.html', {
        'title': _('Edit Book Page') if edit else _('Create Book Page'),
        'form': form,
        'delete_url': reverse('portals.backend.views.page_delete', args=[portal.address, page.id]) if edit else None,
        'view_url': reverse('portals.frontend.views.page_item', args=[portal.address, page.slug if page.slug else page.id]) if edit else None,
        'help_text': _('A portal website is an online book that contains information of an organization, a group, or an individual. Book pages are arranged in hierarchical fashion.'),
        }, portal_request_context(request, portal))

def get_page_info(portal, pi=None, root=False):
    page = get_item_object('page', portal, pi) if pi else None
    if page or root:
        return {
                'ancestor_id_list': page.ancestor_id_list() if page else [],
                'children': [{
                    'id': p.id,
                    'title': p.title,
                    'content': strip_script(p.content),
                    'slug': p.slug,
                    'created': str(p.created_at),
                    'modified': str(p.modified_at),
                    'weight': p.weight,
                    'keywords': ', '.join([k.title for k in p.keywords.all()]),
                    'latitude': p.latitude,
                    'longitude': p.longitude,
                    } for p in portal.page_set.filter(deleted=False).filter(parent=page).order_by('weight')],
                }
    return None

# File

class FileForm(FormWithKeywords):
    class Meta:
        model = MediaFile
        exclude = ('latitude', 'longitude',)

def get_file(f):
    def d(request, portal, file_id):
        try:
            m = portal.mediafile_set.get(id__exact=file_id)
        except:
            return redirect(reverse('portals.backend.views.file_list', args=[portal.address]))
        return f(request, portal, m)
    return d

re_file_name = re.compile('^[a-zA-Z0-9][a-zA-Z0-9_\-\.]+[a-zA-Z0-9]$')

def validate_file_name(name):
    return _('This file name contains disallowed character(s). Please rename it.') if not re_file_name.match(name) else None

def get_uploaded_file_info(portal, fn):
    try:
        qf = portal.mediafile_set.get(name=fn.split('/')[-1])
    except:
        qf = None
    try:
        qf_stat = os.stat(qf.file.path)
    except:
        qf_stat = None
    return {
            'name': qf.name,
            'type': 1,
            'url': qf.file.url,
            'id': qf.id,
            'year': qf.created_at.year,
            'month': digit_string_prefix(qf.created_at.month),
            'day': digit_string_prefix(qf.created_at.day),
            'keywords': [kw.title for kw in qf.keywords.all()],
            'size': qf_stat.st_size,
            } if qf and qf_stat else None

def get_file_info(portal, fparam=None):
    root_dir = '%s%s' % (settings.MEDIA_ROOT, '/'.join(list(str(portal.id))))
    f = root_dir if not fparam else '%s/%s' % (root_dir, fparam.replace('..', ''))

    if path.isdir(f):
        dlist = os.listdir(f)
        dlist.sort()
        r = []
        for t in dlist:
            if not fparam and len(t) < 4:
                continue
            fn = '%s/%s' % (f, t)
            if path.isdir(fn):
                r.append({'name': t, 'type': 0})
            else:
                finfo = get_uploaded_file_info(portal, fn)
                if finfo:
                    r.append(finfo)
                else:
                    r.append({
                        'name': t,
                        'type': 2,
                        'url': fn.partition('public')[-1],
                        })
        return r
    else:
        return get_uploaded_file_info(portal, fparam)

def allow_upload(f):
    def d(request, portal, file_id=None):
        if settings.ALWAYS_ALLOW_UPLOAD:
            return f(request, portal, file_id) if file_id else f(request, portal)
        else:
            try:
                profile = request.user.get_profile()
            except:
                profile = None
            if profile and profile.allow_upload:
                return f(request, portal, file_id) if file_id else f(request, portal)
            else:
                sys_info = get_sys_info()
                return render_to_response('b/msg_box.html', {
                    'title': _('Not Allowed'),
                    'message': _('You are not allowed to upload or update a file.') if not sys_info or not sys_info.upload_permission_message else sys_info.upload_permission_message,
                    'return_url': reverse('portals.backend.views.file_list', args=[portal.address]),
                    }, portal_request_context(request, portal))
    return d

# PodcastCategory

class PodcastCategoryForm(CategoryForm):
    class Meta(CategoryForm.Meta):
        model = PodcastCategory

def get_podcastcategory(f):
    def d(request, portal, slug):
        try:
            podcastcategory = portal.podcastcategory_set.get(slug__exact=slug)
        except ObjectDoesNotExist:
            return redirect(reverse('portals.backend.views.podcastcategory_list', args=[portal.address]))
        return f(request, portal, podcastcategory)
    return d

def podcastcategory_required(f):
    def d(request, portal, podcast=None):
        if portal.podcastcategory_set.count() == 0:
            return render_to_response('b/msg_box.html', {
                'title': _('No Podcast Category'),
                'message': _('No podcast category has been defined for this portal. To post a podcast, you need a podcast category. Please create a podcast category first.'),
                }, portal_request_context(request, portal))
        else:
            return f(request, portal, podcast) if podcast else f(request, portal)
    return d

def podcastcategory_form_info(portal):
    return [reverse('portals.backend.views.podcastcategory_list', args=[portal.address]),
            _('A podcast category with the title or the slug is already defined for this portal.')]

# Podcast

class PodcastForm(FormWithKeywords):
#    content = forms.CharField(label=_('Content'), widget=forms.Textarea(attrs=textarea_attrs()))

    def __init__(self, portal, *args, **kwargs):
        super(PodcastForm, self).__init__(portal, *args, **kwargs)
        self.fields.keyOrder = ['title', 'enclosure_url', 'enclosure_length', 'enclosure_type', 'content', 'hidden', 'sticky', 'category', 'latitude', 'longitude', 'keywords']
        self.fields['category'].queryset = portal.podcastcategory_set.order_by('title')

    class Meta:
        model = Podcast

def get_podcast(f):
    def d(request, portal, podcast_id):
        try:
            podcast = portal.podcast_set.get(id__exact=podcast_id)
        except:
            return redirect(reverse('portals.backend.views.podcast_list', args=[portal.address]))
        return f(request, portal, podcast)
    return d

def podcast_create_or_edit(request, portal, podcast=None):
    edit = True if podcast else False
    if request.method == 'POST':
        form = PodcastForm(portal, request.POST, instance=podcast) if podcast else PodcastForm(portal, request.POST)
        if form.is_valid():
            podcast = form.save(commit=False)
            podcast.portal = portal
            podcast.save()
            form.save_m2m()
            podcast.save_writer(request.user)
            save_success_message(request)
            if request.POST.has_key('save-continue'):
                return redirect(reverse('portals.backend.views.podcast_edit', args=[portal.address, podcast.id]))
            else:
                if edit:
                    EditLock.unset(request.user, podcast.id, 'PODCAST')
                return redirect(reverse('portals.backend.views.podcast_list', args=[portal.address]))
    else:
        form = PodcastForm(portal, instance=podcast) if podcast else PodcastForm(portal)
        if edit:
            EditLock.set(request.user, podcast.id, 'PODCAST')
    return render_to_response('b/common_form.html', {
        'title': _('Edit Podcast') if edit else _('Create Podcast'),
        'form': form,
        'disable_tiny_mce': True,
        'edit': edit,
        'delete_url': reverse('portals.backend.views.podcast_delete', args=[portal.address, podcast.id]) if edit else None,
        'view_url': reverse('portals.frontend.views.podcast_item', args=[portal.address, podcast.id]) if edit else None,
        }, portal_request_context(request, portal))

