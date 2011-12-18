from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.utils.safestring import mark_safe
from django.utils import simplejson as json
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.http import HttpResponse
from django.http import HttpResponseRedirect as redirect
from django.core.mail import send_mail

from backend.models import *
from backend.lib import *

from os import path
import socket

# General

@login_required
@get_portal
def under_development(request, portal):
    return render_to_response('b/msg_box.html', {
        'title': _('Under Development'),
        'message': _('This feature is currently under development. Please wait for the next release.'),
        'return_url': reverse('portals.backend.views.portal_main', args=[portal.address]),
        }, portal_request_context(request, portal))

@login_required
def contact_support(request):
    if request.method == 'POST':
        form = SupportForm(request.POST)
        if form.is_valid():
            sys_info = get_sys_info()
            try:
                send_mail('[%s] %s' % (sys_info.site_title,
                    form.cleaned_data['subject']), form.cleaned_data['message'],
                    request.user.email, [sys_info.support_email], fail_silently=False)
                sent = True
            except:
                sent = False
            if sent:
                request.user.message_set.create(message=ugettext('The email has been sent.'))
                return redirect(reverse('portals.backend.views.portal_list'))
            else:
                request.user.message_set.create(message=ugettext('Cannot send the email. Please check the form balow.'))
    else:
        form = SupportForm()
    return render_to_response('b/common_form.html', {
        'title': _('Contact Support Team'),
        'form': form,
        'disable_tiny_mce': True,
        'button_label': _('Send'),
        }, system_request_context(request))

@login_required
def mailing_list(request):
    if request.method == 'POST':
        pass
    else:
        pass

# User

@login_required
def user_portal_list(request, username):
    user = get_user(username)
    if user:
        return get_user_portal_list(request, user)
    else:
        return access_denied_response(request)

def user_login(request):
    if request.user.is_authenticated():
        return redirect(reverse('portals.backend.views.portal_list'))

    form = LoginForm(request.POST) if request.method == 'POST' else LoginForm()
    error = None
    if request.method == 'POST' and form.is_valid():
        user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
        if user and user.is_active:
            login(request, user)
            return redirect(reverse('portals.backend.views.portal_list'))
        else:
            error = ugettext('The username and password did not match. Please try again.')
    return render_to_response('b/login.html', {
        'form': form,
        'error': error,
        }, system_request_context(request))

def user_logout(request):
    if request.user.is_authenticated():
        logout(request)
    return redirect(reverse('portals.backend.views.user_login'))

# Portal

@login_required
def portal_list(request):
    return get_user_portal_list(request, request.user)

@login_required
@get_portal
def portal_main(request, portal):
    x = 5
    return render_to_response('b/portal_main.html', {
        'recently_modified_pages': portal.page_set.filter(deleted=False).order_by('-modified_at')[:x],
        'recent_news': portal.news_set.filter(deleted=False).order_by('-created_at')[:x],
        'recent_events': portal.event_set.filter(deleted=False).order_by('-created_at')[:x],
        'recent_podcasts': portal.podcast_set.filter(deleted=False).order_by('-created_at')[:x],
        }, portal_request_context(request, portal))

@login_required
def portal_create(request):
    return portal_create_or_edit(request)

@login_required
@get_portal
def portal_edit(request, portal):
    x = EditLock.get(portal.id, 'PORTAL')
    if x and x.valid_lock(request.user):
        return locked_error(request, portal, x, reverse('portals.backend.views.portal_main', args=[portal.address]))
    else:
        return portal_create_or_edit(request, portal)

@login_required
@get_portal
def portal_delete(request, portal):
    children_count = portal.children_count()
    if children_count > 0:
        return render_to_response('b/msg_box.html', {
            'title': _('Unable to Delete'),
            'message': _('This portal (%(title)s) cannot be deleted. It contains %(count)s items of pages, news, events, and files. You may delete them first.') % {
                'title': portal.title,
                'count': children_count
                },
            'return_url': reverse('portals.backend.views.portal_main', args=[portal.address]),
            }, portal_request_context(request, portal))
    else:
        if request.method == 'POST':
            if request.POST.has_key('yes'):
                portal.mark_deleted()
            return redirect(reverse('portals.backend.views.portal_list'))
        return render_to_response('b/confirm_form.html', {
            'title': _('Are you sure you want to delete this portal?'),
            'message': portal.title,
            }, portal_request_context(request, portal))

@login_required
@get_portal
def portal_homepage_page(request, portal):
    return set_portal_homepage(request, portal,
            [(item.id, item.title) for item in portal.page_set.filter(deleted=False).filter(hidden=False).order_by('title')],
            portal.homepage_page, 'page', _('Book Page'),
            _('Select a book page to be the first page of this portal, or select none to reset it.'))

@login_required
@get_portal
def portal_homepage_news(request, portal):
    return set_portal_homepage(request, portal,
            [(item.id, item.title) for item in portal.news_set.filter(deleted=False).filter(hidden=False).order_by('created_at')],
            portal.homepage_news, 'news', _('News'),
            _('Select a news item to be the first page of this portal, or select none to reset it.'))

@login_required
@get_portal
def portal_homepage_event(request, portal):
    return set_portal_homepage(request, portal,
            [(item.id, item.title) for item in portal.event_set.filter(deleted=False).filter(hidden=False).order_by('created_at')],
            portal.homepage_event, 'event', _('Event'),
            _('Select an event to be the first page of this portal, or select none to reset it.'))

@login_required
@get_portal
def portal_theme(request, portal):
    if request.method == 'POST':
        form = CssForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['css']:
                portal.custom_css = form.cleaned_data['css']
                portal.hide_header_title = form.cleaned_data['hide_header_title']
                portal.left_sidebar = form.cleaned_data['left_sidebar']
                portal.save()
                save_success_message(request)
                if request.POST.has_key('save-continue'):
                    return redirect(reverse('portals.backend.views.portal_theme', args=[portal.address]))
                else:
                    return redirect(reverse('portals.backend.views.portal_main', args=[portal.address]))
    else:
        form = CssForm({
            'css': portal.custom_css,
            'left_sidebar': portal.left_sidebar,
            'hide_header_title': portal.hide_header_title,
            }) if portal.custom_css else CssForm()
    return render_to_response('b/common_form.html', {
        'title': _('Set Custom CSS'),
        'form': form,
        'disable_tiny_mce': True,
        'enable_code_mirror': True,
        }, portal_request_context(request, portal))

# Contributor

@login_required
@get_portal
def contributor_list(request, portal):
    return render_to_response('b/contributor_list.html', {
        'contributors': portal.contributors.all(),
        }, portal_request_context(request, portal))

@login_required
@get_own_portal
def contributor_create(request, portal):
    form = ContributorForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        user = get_user(form.cleaned_data['username'])
        if portal.valid_contributor(user, request.user):
            confirm = ContributorConfirmationForm({'username': user.username})
            return render_to_response('b/common_form.html', {
                'title': user_display_name(user),
                'message': _('Do you want to add this person as a contributor of this portal?'),
                'form': confirm,
                'button_label': _('Add'),
                'action': reverse('portals.backend.views.contributor_create_confirm', args=[portal.address]),
                }, portal_request_context(request, portal))
        elif user == request.user:
            form.errors['username'] = [_('The user is the owner of this portal.')]
        elif user in portal.contributors.all():
            form.errors['username'] = [_('The user has already been a contributor of this portal.')]
        else:
            form.errors['username'] = [_('Cannot find a person with the username.')]
    return render_to_response('b/common_form.html', {
        'title': _('Add Contributor'),
        'form': form,
        'button_label': _('Next') + ' &rsaquo;',
        'help_text': _('A contributor is a person that can do anything the owner of a portal can. This suits a site with a small editorial team.'),
        }, portal_request_context(request, portal))

@login_required
@get_own_portal
def contributor_create_confirm(request, portal):
    if request.method == 'POST':
        form = ContributorConfirmationForm(request.POST)
        if form.is_valid():
            user = get_user(form.cleaned_data['username'])
            if portal.valid_contributor(user, request.user):
                portal.contributors.add(user)
                portal.save()
                save_success_message(request)
            return redirect(reverse('portals.backend.views.contributor_list', args=[portal.address]))
    else:
        return redirect(reverse('portals.backend.views.contributor_create', args=[portal.address]))

@login_required
@get_own_portal
def contributor_delete(request, portal, username):
    return_url = reverse('portals.backend.views.contributor_list', args=[portal.address])
    user = get_user(username)
    if user and user in portal.contributors.all():
        if request.method == 'POST':
            if request.POST.has_key('yes'):
                portal.contributors.remove(user)
                portal.save()
                save_success_message(request)
            return redirect(return_url)
        else:
            return render_to_response('b/confirm_form.html', {
                'title': user_display_name(user),
                'message': _('Do you want to add this person as a contributor of this portal?'),
                'message': _('Are you sure you want to remove this person from the contributor list?'),
                'return_url': return_url,
                }, portal_request_context(request, portal))
    else:
        return render_to_response('b/msg_box.html', {
            'title': _('Unknown User or User Not Contributor'),
            'message': _('Either cannot find a user by the username, or the user is not a contributor of this portal.'),
            'return_url': return_url,
            }, portal_request_context(request, portal))

# Keyword

@login_required
@get_portal
def keyword_list(request, portal):
    return category_list(request, portal, _('Keywords'),
            portal.keyword_set.all().order_by('title'),
            'portals.backend.views.keyword_',
            _("This portal does not have a keyword. Click 'Create' to define a new keyword."))

@login_required
@get_portal
def keyword_create(request, portal):
    cinfo = keyword_form_info(portal)
    return category_create(request, portal, _('Create New Keyword'), KeywordForm, cinfo[0], cinfo[1], help_text=cinfo[2])

@login_required
@get_portal
@get_keyword
def keyword_edit(request, portal, keyword):
    x = EditLock.get(keyword.id, 'KEYWORD')
    if x and x.valid_lock(request.user):
        return locked_error(request, portal, x, reverse('portals.backend.views.keyword_list', args=[portal.address]))
    else:
        cinfo = keyword_form_info(portal)
        return category_edit(request, portal, keyword, _('Edit This Keyword'), KeywordForm, cinfo[0], cinfo[1], 'KEYWORD')

#@login_required
#@get_portal
#@get_keyword
#def keyword_delete(request, portal, keyword):
#    return category_delete(request, portal, keyword,
#            keyword.page_set.count() + keyword.news_set.count() + keyword.event_set.count() + keyword.mediafile_set.count(),
#            reverse('portals.backend.views.keyword_list', args=[portal.address]))

# NewsCategory

@login_required
@get_portal
def newscategory_list(request, portal):
    return category_list(request, portal, _('News Categories'),
            portal.newscategory_set.order_by('title'),
            'portals.backend.views.newscategory_',
            _("This portal does not have a news category. Click 'Create' to define a news category."),
            {
                'label': _('Create News'),
                'url': reverse('portals.backend.views.news_create', args=[portal.address]),
                })

@login_required
@get_portal
def newscategory_create(request, portal):
    cinfo = newscategory_form_info(portal)
    return category_create(request, portal, _('Create a News Category'), NewsCategoryForm, cinfo[0], cinfo[1])

@login_required
@get_portal
@get_newscategory
def newscategory_edit(request, portal, newscategory):
    x = EditLock.get(newscategory.id, 'NEWSCATEGORY')
    if x and x.valid_lock(request.user):
        return locked_error(request, portal, x, reverse('portals.backend.views.newscategory_list', args=[portal.address]))
    else:
        cinfo = newscategory_form_info(portal)
        return category_edit(request, portal, newscategory, _('Edit This News Category'), NewsCategoryForm, cinfo[0], cinfo[1], 'NEWSCATEGORY')

#@login_required
#@get_portal
#@get_newscategory
#def newscategory_delete(request, portal, newscategory):
#    return category_delete(request, portal, newscategory, newscategory.news_set.count(), 
#            reverse('portals.backend.views.newscategory_list', args=[portal.address]))

# News

@login_required
@get_portal
def news_list(request, portal):
    return render_to_response('b/news_list.html', {
        'total': portal.news_set.filter(deleted=False).count(),
        }, portal_request_context(request, portal))

@never_cache
@login_required
@get_portal
def news_list_data(request, portal):
    return HttpResponse(
            json.dumps({
                'results': [{
                    'id': n.id,
                    'title': n.title,
                    'category': n.category.title,
                    'created': n.created_at.ctime(),
                    'hidden': ugettext('Yes') if n.hidden else ugettext('No'),
                    'sticky': ugettext('Yes') if n.sticky else ugettext('No'),
                    'edit_url': reverse('portals.backend.views.news_edit', args=[portal.address, n.id]),
                    'view_url': reverse('portals.frontend.views.news_item', args=[portal.address, n.id]),
                    } for n in get_page_obj(request, portal.news_set.filter(deleted=False).order_by('-created_at')).object_list]
                }),
            mimetype='application/json')

@login_required
@get_portal
@keyword_required
@newscategory_required
def news_create(request, portal):
    return news_create_or_edit(request, portal)

@login_required
@get_portal
@keyword_required
@newscategory_required
@get_news
def news_edit(request, portal, news):
    x = EditLock.get(news.id, 'NEWS')
    if x and x.valid_lock(request.user):
        return locked_error(request, portal, x, reverse('portals.backend.views.news_list', args=[portal.address]))
    else:
        return news_create_or_edit(request, portal, news)

@login_required
@get_portal
@get_news
def news_delete(request, portal, news):
    return node_delete(request, portal, news,
            news.title,
            _('Are you sure you want to delete this news?'),
            reverse('portals.backend.views.news_list', args=[portal.address]))

# EventCategory

@login_required
@get_portal
def eventcategory_list(request, portal):
    return category_list(request, portal, _('Event Categories'),
            portal.eventcategory_set.all().order_by('title'),
            'portals.backend.views.eventcategory_',
            _("This portal does not have an event category. Click 'Create' to define an event category."),
            {
                'label': _('Create Event'),
                'url': reverse('portals.backend.views.event_create', args=[portal.address]),
                })

@login_required
@get_portal
def eventcategory_create(request, portal):
    cinfo = eventcategory_form_info(portal)
    return category_create(request, portal, _('Create an Event Category'), EventCategoryForm, cinfo[0], cinfo[1])

@login_required
@get_portal
@get_eventcategory
def eventcategory_edit(request, portal, eventcategory):
    x = EditLock.get(eventcategory.id, 'EVENTCATEGORY')
    if x and x.valid_lock(request.user):
        return locked_error(request, portal, x, reverse('portals.backend.views.eventcategory_list', args=[portal.address]))
    else:
        cinfo = eventcategory_form_info(portal)
        return category_edit(request, portal, eventcategory, _('Edit This Event Category'), EventCategoryForm, cinfo[0], cinfo[1], 'EVENTCATEGORY')

#@login_required
#@get_portal
#@get_eventcategory
#def eventcategory_delete(request, portal, eventcategory):
#    return category_delete(request, portal, eventcategory, eventcategory.event_set.count(),
#            reverse('portals.backend.views.eventcategory_list', args=[portal.address]))

# Event

@login_required
@get_portal
def event_list(request, portal):
    return render_to_response('b/event_list.html', {
        'total': portal.event_set.filter(deleted=False).count(),
        }, portal_request_context(request, portal))

@never_cache
@login_required
@get_portal
def event_list_data(request, portal):
    return HttpResponse(
            json.dumps({
                'results': [{
                    'id': n.id,
                    'title': n.title,
                    'category': n.category.title,
                    'begin': n.begin.ctime(),
                    'end': n.end.ctime(),
                    'hidden': ugettext('Yes') if n.hidden else ugettext('No'),
                    'sticky': ugettext('Yes') if n.sticky else ugettext('No'),
                    'edit_url': reverse('portals.backend.views.event_edit', args=[portal.address, n.id]),
                    'view_url': reverse('portals.frontend.views.event_item', args=[portal.address, n.id]),
                    } for n in get_page_obj(request, portal.event_set.filter(deleted=False).order_by('-created_at')).object_list]
                }),
            mimetype='application/json')

@login_required
@get_portal
@keyword_required
@eventcategory_required
def event_create(request, portal):
    return event_create_or_edit(request, portal)

@login_required
@get_portal
@keyword_required
@eventcategory_required
@get_event
def event_edit(request, portal, event):
    x = EditLock.get(event.id, 'EVENT')
    if x and x.valid_lock(request.user):
        return locked_error(request, portal, x, reverse('portals.backend.views.event_list', args=[portal.address]))
    else:
        return event_create_or_edit(request, portal, event)

@login_required
@get_portal
@get_event
def event_delete(request, portal, event):
    return node_delete(request, portal, event,
            event.title,
            _('Are you sure you want to delete this event?'),
            reverse('portals.backend.views.event_list', args=[portal.address]))

# Page

@login_required
@get_portal
def page_list(request, portal):
    try:
        pi = int(request.GET.get('p', 0))
    except:
        pi = 0
    return render_to_response('b/page_list.html', {
        'root': get_page_info(portal, root=True),
        'pi': get_page_info(portal, pi),
        }, portal_request_context(request, portal))

@never_cache
@login_required
@get_portal
def page_list_data(request, portal):
    return HttpResponse(
            json.dumps(get_page_info(portal, request.GET.get('node', None)), sort_keys=True),
            mimetype='application/json')

@login_required
@get_portal
@keyword_required
def page_create(request, portal):
    return page_create_or_edit(request, portal)

@login_required
@get_portal
@keyword_required
@get_page
def page_edit(request, portal, page):
    x = EditLock.get(page.id, 'PAGE')
    if x and x.valid_lock(request.user):
        return locked_error(request, portal, x, reverse('portals.backend.views.page_list', args=[portal.address]))
    else:
        return page_create_or_edit(request, portal, page)

@login_required
@get_portal
@get_page
def page_delete(request, portal, page):
    children_count = page.page_set.filter(deleted=False).count()
    if children_count > 0:
        return render_to_response('b/msg_box.html', {
            'title': _('Unable to Delete'),
            'message': _('This book page (%(title)s) cannot be deleted. It has %(count)s children. You may delete them first.') % {
                'title': page.title,
                'count': children_count
                },
            'return_url': '%s?p=%s' % (reverse('portals.backend.views.page_list', args=[portal.address]), page.id),
            }, portal_request_context(request, portal))
    else:
        if request.method == 'POST':
            if request.POST.has_key('yes'):
                page.mark_deleted()
            return redirect(reverse('portals.backend.views.page_list', args=[portal.address]))
        return render_to_response('b/confirm_form.html', {
            'title': _('Are you sure you want to delete this book page?'),
            'message_title': page.title,
            'message': mark_safe(page.content),
            }, portal_request_context(request, portal))

# File

@login_required
@get_portal
def ftp_access(request, portal):
    sys_info = get_sys_info()
    return render_to_response('b/msg_box.html', {
        'title': _('FTP Access'),
        'message': sys_info.ftp_access_message if sys_info.ftp_access_message else _('This system does not provide FTP access, or the administrator does not give an instruction how to access the system.'),
        'return_url': request.META['HTTP_REFERER'] if request.META['HTTP_REFERER'] else reverse('portals.backend.views.portal_main', args=[portal.address]),
        }, portal_request_context(request, portal))

@login_required
@get_portal
@allow_upload
def file_list(request, portal):
    fi = request.GET.get('f', None)
    return render_to_response('b/file_list.html', {
        'file_count': portal.mediafile_set.count(),
        'years': get_file_info(portal),
        'fi': get_file_info(portal, fi) if fi else None,
        }, portal_request_context(request, portal))

@never_cache
@login_required
@get_portal
def file_list_data(request, portal):
    return HttpResponse(
            json.dumps(get_file_info(portal, request.GET.get('node', None)), sort_keys=True),
            mimetype='application/json')

@login_required
@get_portal
@allow_upload
@keyword_required
def file_create(request, portal):
    f = MediaFile(portal=portal)
    if request.method == 'POST':
        form = FileForm(portal, request.POST, request.FILES, instance=f)
        if form.is_valid():
            file_name_err = validate_file_name(request.FILES['file'].name)
            if file_name_err:
                form.errors['file'] = [file_name_err]
            else:
                # check if the file exists on the database
                try:
                    exf = portal.mediafile_set.get(name=request.FILES['file'].name)
                except:
                    exf = None
                # check if the file exists in the destination directory
                existed = True if path.exists(file_location(portal.id, date.today(), request.FILES['file'])) else False
                if not exf and not existed:
                    f = form.save(commit=False)
                    f.name = request.FILES['file'].name
                    f.content_type = request.FILES['file'].content_type
                    f.save()
                    form.save_m2m()
                    f.save_writer(request.user)
                    save_success_message(request)
                    return redirect('%s?f=%s' % (reverse('portals.backend.views.file_list', args=[portal.address]), f.name))
                elif exf:
                    form.errors['file'] = [
                            _('You have uploaded a file with this name.'),
                            _('You may rename this new file or edit the old file.'),
                            mark_safe(_('Click this link to edit the old file') + ': <a href="%s">%s</a>' % (
                                reverse('portals.backend.views.file_edit', args=[portal.address, exf.id]),
                                exf.name,))]
                else:
                    form.errors['file'] = [_('A file with this name already exists in the destination directory. It was uploaded directly.')]
    else:
        form = FileForm(portal, instance=f)

    return render_to_response('b/common_form.html', {
        'title': _('Upload File'),
        'form': form,
        'button_label': _('Upload'),
        }, portal_request_context(request, portal))

@login_required
@get_portal
@allow_upload
@keyword_required
@get_file
def file_edit(request, portal, f):
    x = EditLock.get(f.id, 'MEDIAFILE')
    if x and x.valid_lock(request.user):
        return locked_error(request, portal, x, reverse('portals.backend.views.file_list', args=[portal.address]))
    else:
        if request.method == 'POST':
            form = FileForm(portal, request.POST, request.FILES, instance=f)
            if form.is_valid():
                file_name = request.FILES['file'].name if 'file' in request.FILES else f.name
                file_name_err = validate_file_name(file_name)
                if file_name_err:
                    form.errors['file'] = [file_name_err]
                else:
                    if f.name == file_name:
                        if 'file' in request.FILES:
                            f.remove_file()
                        f = form.save()
                        f.save_writer(request.user)
                        save_success_message(request)
                        EditLock.unset(request.user, f.id, 'MEDIAFILE')
                        return redirect('%s?f=%s' % (reverse('portals.backend.views.file_list', args=[portal.address]), f.name))
                    else:
                        form.errors['file'] = [
                                _('The uploaded file does not have the same name as the original file.'),
                                _('Please rename it to the following name') + ': %s' % f.name,]
        else:
            form = FileForm(portal, instance=f)
            EditLock.set(request.user, f.id, 'MEDIAFILE')
        return render_to_response('b/common_form.html', {
            'title': _('Update File') + ': %s' % f.name,
            'form': form,
            'button_label': _('Update'),
            'delete_url': reverse('portals.backend.views.file_delete', args=[portal.address, f.id]),
            }, portal_request_context(request, portal))

@login_required
@get_portal
@allow_upload
@get_file
def file_delete(request, portal, f):
    if request.method == 'POST':
        if request.POST.has_key('yes'):
            f.mark_deleted()
        return redirect(reverse('portals.backend.views.file_list', args=[portal.address]))
    return render_to_response('b/confirm_form.html', {
        'title': f.name,
        'message': _('Are you sure you want to delete this file?'),
        }, portal_request_context(request, portal))

# PodcastCategory

@login_required
@get_portal
def podcastcategory_list(request, portal):
    return category_list(request, portal, _('Podcast Categories'),
            portal.podcastcategory_set.order_by('title'),
            'portals.backend.views.podcastcategory_',
            _("This portal does not have a podcast category. Click 'Create' to define a podcast category."),
            {
                'label': _('Create Podcast'),
                'url': reverse('portals.backend.views.podcast_create', args=[portal.address]),
                })

@login_required
@get_portal
def podcastcategory_create(request, portal):
    cinfo = podcastcategory_form_info(portal)
    return category_create(request, portal, _('Create a Podcast Category'), PodcastCategoryForm, cinfo[0], cinfo[1])

@login_required
@get_portal
@get_podcastcategory
def podcastcategory_edit(request, portal, podcastcategory):
    x = EditLock.get(podcastcategory.id, 'PODCASTCATEGORY')
    if x and x.valid_lock(request.user):
        return locked_error(request, portal, x, reverse('portals.backend.views.podcastcategory_list', args=[portal.address]))
    else:
        cinfo = podcastcategory_form_info(portal)
        return category_edit(request, portal, podcastcategory, _('Edit This Podcast Category'), PodcastCategoryForm, cinfo[0], cinfo[1], 'PODCASTCATEGORY')

# Podcast

@login_required
@get_portal
def podcast_list(request, portal):
    return render_to_response('b/podcast_list.html', {
        'total': portal.podcast_set.filter(deleted=False).count(),
        }, portal_request_context(request, portal))

@never_cache
@login_required
@get_portal
def podcast_list_data(request, portal):
    return HttpResponse(
            json.dumps({
                'results': [{
                    'id': n.id,
                    'title': n.title,
                    'file': '<a href="%s">%s</a>' % (n.enclosure_url, n.enclosure_url.split('/')[-1]),
                    'length': n.enclosure_length,
                    'media_type': n.media_type(),
                    'category': n.category.title,
                    'created': n.created_at.ctime(),
                    'hidden': ugettext('Yes') if n.hidden else ugettext('No'),
                    'sticky': ugettext('Yes') if n.sticky else ugettext('No'),
                    'edit_url': reverse('portals.backend.views.podcast_edit', args=[portal.address, n.id]),
                    'view_url': reverse('portals.frontend.views.podcast_item', args=[portal.address, n.id]),
                    } for n in get_page_obj(request, portal.podcast_set.filter(deleted=False).order_by('-created_at')).object_list]
                }),
            mimetype='application/json')

@login_required
@get_portal
@keyword_required
@podcastcategory_required
def podcast_create(request, portal):
    return podcast_create_or_edit(request, portal)

@login_required
@get_portal
@keyword_required
@podcastcategory_required
@get_podcast
def podcast_edit(request, portal, podcast):
    x = EditLock.get(podcast.id, 'PODCAST')
    if x and x.valid_lock(request.user):
        return locked_error(request, portal, x, reverse('portals.backend.views.podcast_list', args=[portal.address]))
    else:
        return podcast_create_or_edit(request, portal, podcast)

@login_required
@get_portal
@get_podcast
def podcast_delete(request, portal, podcast):
    return node_delete(request, portal, podcast,
            podcast.title,
            _('Are you sure you want to delete this podcast episode?'),
            reverse('portals.backend.views.podcast_list', args=[portal.address]))

