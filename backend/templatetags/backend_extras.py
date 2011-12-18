from django import template
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import stringfilter

from backend.lib import strip_script as lib_strip_script

import re

register = template.Library()

@register.filter
def user_display_name(user):
    full_name = user.get_full_name()
    return mark_safe('%s (%s)' % (full_name, user.username) if full_name else '%s' % user.username)

@register.simple_tag
def breadcrumbs_tag(req_path, portal=None, obj=None):
    if req_path == '/':
        return ''
    else:
        paths = req_path.strip('/').split('/')
        a_paths = []
        if portal and portal.domain_address:
            del paths[0]
            a_paths.append('<a class="breadcrumb" href="/">home</a>')
        for i in range(len(paths)):
            a_paths.append('<a class="breadcrumb" href="/%s">%s</a>' % ('/'.join(paths[:i+1]), obj.title if obj and i == len(paths)-1 else paths[i]))
        return mark_safe('%s%s' % ('&rsaquo;&nbsp;', '&nbsp;&rsaquo;&nbsp;'.join(a_paths)))

@register.filter
@stringfilter
def breadcrumbs(req_path, portal=None):
    if req_path == '/':
        return ''
    else:
        paths = req_path.strip('/').split('/')
        a_paths = []
        if portal and portal.domain_address:
            del paths[0]
            a_paths.append('<a class="breadcrumb" href="/">home</a>')
        for i in range(len(paths)):
            a_paths.append('<a class="breadcrumb" href="/%s">%s</a>' % ('/'.join(paths[:i+1]), paths[i]))
        return mark_safe('%s%s' % ('&rsaquo;&nbsp;', '&nbsp;&rsaquo;&nbsp;'.join(a_paths)))

@register.filter
@stringfilter
def cancel_url(req_path):
    paths = req_path.split('/')
    if paths[-1] == '':
        del paths[-1]
    if paths[-1] == 'edit':
        del paths[-1]
    del paths[-1]
    return mark_safe('/'.join(paths))

re_script = re.compile('<script.+script>', re.IGNORECASE)

@register.filter
@stringfilter
def escape_script(s):
    m = re_script.match(s)
    if m:
        v = s[m.start():m.end()] if m.end() > 0 else s
        return v.sub('<', '&lt;').sub('>', '&gt;')
    else:
        return s

@register.filter
@stringfilter
def strip_script(s):
    return lib_strip_script(s)

@register.filter
def contributor_list(contributors):
    l = []
    for c in contributors.all():
        l.append('<a href="%s">%s</a>' % (reverse('portals.backend.views.user_portal_list', args=[c.username]), user_display_name(c)))
    return mark_safe(', '.join(l)) if l else _("This portal does not have a contributor. Click 'Add' to add a contributor.")

@register.filter
def print_button_label(l):
    return l if l else _('Save')

@register.filter
def dash(v):
    return v if v else '-'

@register.filter
def boolean_text(b):
    return _('True') if b else _('False')

@register.filter
def yesno_text(b):
    return _('Yes') if b else _('No')

@register.simple_tag
def in_list(list, item):
    return True if item in list else False

@register.simple_tag
def view_url(portal):
    if portal.domain_address:
        return 'http://%s/' % portal.address
    else:
        return reverse('portals.frontend.views.portal_home', args=[portal.address])

@register.tag
def url_format(parser, token):
    return FormatUrl(token.split_contents())

class FormatUrl(template.Node):
    def __init__(self, args):
        self.url_prefix = args[1]
        self.action = args[2]
        self.args = args[3:]

    def render(self, context):
        return reverse('%s%s' % (template.Variable(self.url_prefix).resolve(context), self.action),
                args=[template.Variable(v).resolve(context) for v in self.args])

