from django import template
from django.template import TemplateSyntaxError
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __
from django.template.defaultfilters import stringfilter, force_escape
from django.conf import settings

from frontend.lib import domain_reverse

register = template.Library()

@register.tag
def domain_url(parser, token):
    bits = token.split_contents()
    if len(bits) < 3:
        raise TemplateSyntaxError("'%s' takes at least one argument (path to a view)." % bits[0])

    portal = parser.compile_filter(bits[1])
    view_name = bits[2]
    args = []
    if len(bits) > 3:
        bits = iter(bits[3:])
        for bit in bits:
            for arg in bit.split(','):
                if arg:
                    args.append(parser.compile_filter(arg))
    return DomainUrlNode(portal, view_name, args)

class DomainUrlNode(template.Node):
    def __init__(self, portal, view_name, args):
        self.portal = portal
        self.view_name = view_name
        self.args = args 

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        return domain_reverse(self.portal.resolve(context), self.view_name, args=args)

## BEGIN TOC ##

def append_page(portal, l, page, req_page, ul=''):
    l.append('<li page_id="%s" %s><a href="%s"><span %s>%s</span></a>%s</li>' % (
        page.id,
        'class="expanded"' if ul or page == req_page else '',
        domain_reverse(portal, 'portals.frontend.views.page_item', args=[portal.address, page.slug if page.slug else page.id]),
        'class="selected"' if page == req_page else '',
        force_escape(page.title),
        ul))

def make_page_ul(portal, page, req_page=None, selected_child=None, ul=''):
    if not req_page:
        req_page = page 
    l = []
    for child in portal.page_set.filter(deleted=False).filter(hidden=False).filter(parent=page).order_by('weight'):
        if child == selected_child:
            append_page(portal, l, child, req_page, ul)
        else:
            append_page(portal, l, child, req_page)
    ul = '<ul>%s</ul>' % ''.join(l) if l else ''
    return make_page_ul(portal, page.parent, req_page, page, ul) if page else ul

@register.filter
def page_toc(portal, page):
    return mark_safe(make_page_ul(portal, page))

@register.filter
def root_toc(portal):
    return page_toc(portal, None)

## END TOC ##

@register.filter
def keyword_list_old(keywords, portal):
    l = []
    for k in keywords.all():
        l.append('<a href="%s">%s</a>' % (domain_reverse(portal, 'portals.frontend.views.page_keyword', args=[portal.address, k.slug]), k.title))
    return mark_safe(', '.join([a for a in l]))

@register.simple_tag
def keyword_list(keywords, portal, url_part):
    l = []
    for k in keywords.all():
        l.append('<a href="%s">%s</a>' % (domain_reverse(portal, 'portals.frontend.views.%s_keyword' % url_part, args=[portal.address, k.slug]), k.title))
    return mark_safe(', '.join([a for a in l]))

@register.filter
@stringfilter
def js_escape_single_quote(s):
    return s.replace("'", "\\'")

@register.filter
@stringfilter
def license_statement(license):
    if license == 'ALL':
        return _('All Rights Reserved')
    elif license == 'PD':
        return _('Public Domain')
    elif license == 'CC BY-NC-SA':
        return _('Creative Commons Attribution Non-Commercial Share Alike License')
    elif license == 'CC BY-NC-ND':
        return _('Creative Commons Attribution Non-Commercial No Derivatives License')
    elif license == 'CC BY-ND':
        return _('Creative Commons Attribution No Derivatives License')
    elif license == 'CC BY-NC':
        return _('Creative Commons Attribution Non-Commercial License')
    elif license == 'CC BY-SA':
        return _('Creative Commons Attribution Share Alike License')
    elif license == 'CC BY':
        return _('Creative Commons Attribution License')

@register.filter
@stringfilter
def truncatechars(s, count):
    return '%s ...' % s.replace('&nbsp;', ' ')[:count]

@register.filter
@stringfilter
def split_filename(path):
    return path.split('/')[-1]

@register.simple_tag
def default_theme():
    return settings.DEFAULT_THEME if hasattr(settings, 'DEFAULT_THEME') else 'optimist'

