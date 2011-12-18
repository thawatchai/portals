from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

import time
from datetime import date, datetime
import os
from os import path

SHORT_LIST_ITEMS = 3

LICENSES = (
        (_('Creative Commons'), (
            ('CC BY-NC-SA', _('Attribution Non-Commercial Share Alike')),
            ('CC BY-NC-ND', _('Attribution Non-Commercial No Derivatives')),
            ('CC BY-ND', _('Attribution No Derivatives')),
            ('CC BY-NC', _('Attribution Non-Commercial')),
            ('CC BY-SA', _('Attribution Share Alike')),
            ('CC BY', _('Attribution')),
            )),
        (_('Other'), (
            ('ALL', _('All Rights Reserved')),
            ('PD', _('Public Domain')),
            )),
        )

OTYPE = (
        ('KEYWORD', _('Keyword')),
        ('PORTAL', _('Portal')),
        ('PAGE', _('Page')),
        ('NEWS', _('News')),
        ('NEWSCATEGORY', _('News Category')),
        ('EVENT', _('Event')),
        ('EVENTCATEGORY', _('Event Category')),
        ('MEDIAFIIE', _('File')),
        ('PODCAST', _('Podcast')),
        ('PODCASTCATEGORY', _('Podcast Category')),
        )

PODCAST_MEDIA_TYPE = (
        ('audio/mpeg', 'MP3 Audio (mp3)'),
        ('video/mp4', 'MP4 Video (mp4)'),
        ('video/x-flv', 'Flash Video (flv)'),
        )

# Common Functions ---------------------------------------------------

def user_display_name(user):
    full_name = user.get_full_name()
    return full_name if full_name else user.username

def digit_string_prefix(d):
    return '0%s' % d if len(str(d)) == 1 else str(d)

# Common Abstract Classes --------------------------------------------

class StampedModel(models.Model):
    created_at = models.DateTimeField(_('Created'), default=datetime(2009, 1, 1, 1, 1, 1), auto_now_add=True, db_index=True)
    modified_at = models.DateTimeField(_('Modified'), default=datetime(2009, 1, 1, 1, 1, 1), auto_now=True, db_index=True)
    deleted = models.BooleanField(default=False, editable=False, db_index=True)

    class Meta:
        abstract = True

    def save_revision(self, rev):
        for k in self.__dict__:
            if k != 'id':
                rev.__dict__[k] = self.__dict__[k]
        rev.current = self
        rev.save()

    def mark_deleted(self):
        self.deleted = True
        self.save()

class TraceableModel(StampedModel):
    latitude = models.FloatField(_('Latitude'), default=0, null=True, blank=True, db_index=True,
            help_text=_('Enter decimal degree of latitude, e.g., 7.008854. (optional)'))
    longitude = models.FloatField(_('Longitude'), default=0, null=True, blank=True, db_index=True,
            help_text=_('Enter decimal degree of logitude, e.g., 100.5007839. (optional)'))

    class Meta:
        abstract = True

class Category(StampedModel):
    portal = models.ForeignKey('Portal', editable=False)

    title = models.CharField(_('Title'), max_length=255, db_index=True)
    slug = models.SlugField(_('Slug'))

    def __unicode__(self):
        return self.title

    class Meta:
        abstract = True
        unique_together = (('portal', 'title'), ('portal', 'slug'),)
    
    def recent_news(self):
        return self.news_set.filter(deleted=False).filter(hidden=False).filter(sticky=False).order_by('-modified_at')[:5]

    def more_recent_news(self):
        return self.news_set.count() > 5

    def recent_events(self):
        return self.event_set.filter(deleted=False).filter(hidden=False).filter(sticky=False).order_by('-modified_at')[:5]

    def more_recent_event(self):
        return self.event_set.count() > 5 

    def recent_podcasts(self):
        return self.podcast_set.filter(deleted=False).filter(hidden=False).filter(sticky=False).order_by('-modified_at')[:5]

    def more_recent_podcast(self):
        return self.podcast_set.count() > 5  

class ModelWithKeywordsAndWriters(TraceableModel):
    keywords = models.ManyToManyField('Keyword', verbose_name=_('Keywords'))
    writers = models.ManyToManyField(User, editable=False)

    class Meta:
        abstract = True

    def save_writer(self, user):
        if user not in self.writers.all():
            self.writers.add(user)
            self.save()

class Node(ModelWithKeywordsAndWriters):

    portal = models.ForeignKey('Portal', editable=False)

    title = models.CharField(_('Title'), max_length=255, db_index=True)
    content = models.TextField(_('Content'))

    hidden = models.BooleanField(_('Hidden'), default=False, db_index=True,
            help_text=_('Check above to hide this item temporarily.'))
    sticky = models.BooleanField(_('Sticky'), default=False, db_index=True,
            help_text=_('Check this to show this item before others.'))

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title

    def mark_deleted(self):
        self.deleted = True
        self.title = '[DELETED %s] %s' % (int(time.time()), self.title)
        self.save()

# Content Classes ----------------------------------------------------

# EditLock

class EditLock(StampedModel):
    user = models.ForeignKey(User)

    oid = models.IntegerField(default=0, db_index=True)
    otype = models.CharField(max_length=20, choices=OTYPE, db_index=True)

    def lock_elapse(self):
        return (datetime.now() - self.modified_at).seconds / 60

    def valid_lock(self, user):
        return True if settings.EDIT_LOCK_DURATION > self.lock_elapse() and self.user != user else False

    def error_message(self, user):
        if user != self.user:
            return _('This item has been locked for editing by %(name)s. The lock will be expired in %(min)s minutes.') % {
                    'name': user_display_name(self.user),
                    'min': settings.EDIT_LOCK_DURATION - self.lock_elapse(),
                    }

    @staticmethod
    def get(oid, otype):
        try:
            x = EditLock.objects.filter(oid=oid, otype=otype)[0]
        except:
            x = None
        return x

    @staticmethod
    def set(user, oid, otype):
        x = EditLock.get(oid, otype)
        if not x or not x.valid_lock(user):
            if x:
                x.delete()
            v = EditLock(user=user, oid=oid, otype=otype)
            v.save()
            return True
        else:
            return False

    @staticmethod
    def unset(user, oid, otype):
        x = EditLock.get(oid, otype)
        if x and x.user == user:
            x.delete()
            return True
        else:
            return False

# Hit

class Hit(StampedModel):
    counter = models.IntegerField(default=0, db_index=True)
    session_key = models.CharField(max_length=40, blank=True, db_index=True)

# User Profile

class Profile(StampedModel):
    user = models.ForeignKey(User, unique=True)

    verified = models.BooleanField(_('Verified'), default=False)
    allow_upload = models.BooleanField(_('Allow Upload'), default=False)
    allow_ftp = models.BooleanField(_('Allow FTP'), default=False)

    def __unicode__(self):
        return '%s (%s)' % (self.user.get_full_name(), self.user.username)

# System Information

class SystemInfo(models.Model):
    site_title = models.CharField(_('Site Title'), max_length=255,
            help_text=_('Enter a human-readable title of this site.'))
    site_address = models.CharField(_('Site Address'), max_length=50,
            help_text=_('Enter the URL of this site.'))

    main_portal_address = models.CharField(_('Main Portal Address'), max_length=100,
            help_text=_('Enter the address of the main portal site for this system.'))
    support_email = models.EmailField(_('Support Email Address'),
            help_text=_('Enter the email address of the person(s) who takes care this system.'))

    announcement = models.CharField(_('Announcement'), max_length=255, blank=True,
            help_text=_('Enter the announcement for this system. It will display on both frontend and backend pages.'))
    footer = models.TextField(_('Footer'), blank=True,
            help_text=_('Enter the footer of this system. It will display on both frontend and backend pages.'))

    site_img_url = models.CharField(_('Site Image URL'), max_length=255, blank=True,
            help_text=_('Enter the URL for the image for displaying on the top-most headbar of the site.'))
    backend_footer = models.TextField(_('Backend Footer'), blank=True,
            help_text=_('Enter the footer of this system for displaying on the backend pages.'))

    login_form_title = models.CharField(_('Login Form Title'), max_length=150, blank=True,
            help_text=_('Enter the title on the login form.'))
    login_form_message = models.TextField(_('Login Form Message'), blank=True,
            help_text=_('A message to display in the login form.'))

    upload_permission_message = models.TextField(_('Upload Permission Message'), blank=True,
            help_text=_('A message to instruct users how to obtain a permission to upload files.'))

    ftp_access_message = models.TextField(_('FTP Access Message'), blank=True,
            help_text=_('A message to inform users how to upload large files using a FTP client.'))

    class Meta:
        verbose_name_plural = 'system information'

    def __unicode__(self):
        return '%s (%s)' % (self.site_title, self.site_address)

# Portal

class PortalBase(TraceableModel):
    owner = models.ForeignKey(User)

    domain_address = models.BooleanField(_('Domain Address'), default=False)

    title = models.CharField(_('Title'), max_length=255, db_index=True,
            help_text=_('Enter the title of this portal.'))
    subtitle = models.CharField(_('Subtitle'), max_length=255, blank=True,
            help_text=_('Enter the subtitle of this portal. (optional)'))
    description = models.TextField(_('Description'),
            help_text=_('Enter a breif description of this portal.'))
    contact_information = models.TextField(_('Contact Information'),
            help_text=_('Enter the contact information for this portal.'))

    copyright_holder = models.CharField(_('Copyright Holder'), max_length=255,
            help_text=_('Enter name of a person or organization who holds copyright for the contents of this portal.'))
    license = models.CharField(_('License'), max_length=20, choices=LICENSES,
            help_text=_('Choose a license for all contents of this portal.'))

    language = models.CharField(_('Language'), max_length=10, blank=True, choices=settings.LANGUAGES,
            help_text=_('Set the default language for this portal. (optional)'))

    other_information = models.TextField(_('Other Information'), blank=True,
            help_text=_('Enter other information as well as widgets and badges. (optional)'))
    footer = models.TextField(_('Footer'), blank=True,
            help_text=_('Enter footer information of this portal. (optional)'))
    announcement = models.CharField(_('Announcement'), max_length=255, blank=True,
            help_text=_('Enter an announcement to display on the top of every pages. (optional)'))

    gmap_api_key = models.CharField(_('Google Maps API Key'), max_length=255, blank=True,
            help_text=_('If you use your own domain, you need to obtain a Google Maps API Key from http://code.google.com/apis/maps/ (optional)'))

    custom_css = models.TextField(_('Custom CSS'), blank=True)
    hide_header_title = models.BooleanField(default=False)
    left_sidebar = models.BooleanField(default=True)

    suspended = models.BooleanField(default=False, editable=False)

    class Meta:
        abstract = True

    def __unicode__(self):
        return '%s (%s)' % (self.title, self.address)

class Portal(PortalBase):
    contributors = models.ManyToManyField(User, related_name='contributor')
    homepage_page = models.ForeignKey('Page', null=True, related_name='homepage_page')
    homepage_news = models.ForeignKey('News', null=True, related_name='homepage_news')
    homepage_event = models.ForeignKey('Event', null=True, related_name='homepage_event')

    address = models.CharField(_('Address'), max_length=100, db_index=True, unique=True)

    def save(self, force_insert=False, force_update=False):
        super(Portal, self).save(force_insert, force_update)
        self.save_revision(PortalRevision())

    def mark_deleted(self, v=True):
        self.deleted = v
        t = int(time.time())
        self.title = '[DELETED %s] %s' % (t, self.title)
        self.address  = 'deleted-%s-%s' % (t, self.address)
        self.save()

    def valid_contributor(self, user, request_user):
        return True if user and user != request_user and user not in self.contributors.all() else False

    def sticky_pages(self):
        return self.page_set.filter(deleted=False).filter(hidden=False).filter(sticky=True).order_by('-modified_at')[:SHORT_LIST_ITEMS]

    def recent_news(self):
        return self.news_set.filter(deleted=False).filter(hidden=False).filter(sticky=False).order_by('-created_at')[:SHORT_LIST_ITEMS]

    def sticky_news(self):
        return self.news_set.filter(deleted=False).filter(hidden=False).filter(sticky=True).order_by('-created_at')

    def public_news_count(self):
        return self.news_set.filter(deleted=False).filter(hidden=False).count()

    def upcoming_events(self):
        return self.event_set.filter(deleted=False).filter(hidden=False).filter(begin__gte=datetime.today()).order_by('begin')[:SHORT_LIST_ITEMS]

    def sticky_events(self):
        return self.event_set.filter(deleted=False).filter(hidden=False).filter(sticky=True).order_by('begin')[:SHORT_LIST_ITEMS]

    def public_event_count(self):
        return self.event_set.filter(deleted=False).filter(hidden=False).count()

    def recent_podcasts(self):
        return self.podcast_set.filter(deleted=False).filter(hidden=False).filter(sticky=False).order_by('-created_at')[:SHORT_LIST_ITEMS]

    def sticky_podcasts(self):
        return self.podcast_set.filter(deleted=False).filter(hidden=False).filter(sticky=True).order_by('-created_at')

    def public_podcast_count(self):
        return self.podcast_set.filter(deleted=False).filter(hidden=False).count()

    def set_homepage(self, otype, obj):
        if otype == 'page':
            self.homepage_page = obj
        elif otype == 'news':
            self.homepage_news = obj
        elif otype == 'event':
            self.homepage_event = obj
        self.save()

    def children_count(self):
        return self.page_set.filter(deleted=False).count() + self.news_set.filter(deleted=False).count() + self.event_set.filter(deleted=False).count() + self.mediafile_set.filter(deleted=False).count()

class PortalRevision(PortalBase):
    current = models.ForeignKey(Portal, db_index=True, related_name='current')

    contributors = models.ManyToManyField(User, related_name='revision_contributor')
    homepage_page = models.ForeignKey('Page', null=True, related_name='revision_homepage_page')
    homepage_news = models.ForeignKey('News', null=True, related_name='revision_homepage_news')
    homepage_event = models.ForeignKey('Event', null=True, related_name='revision_homepage_event')

    address = models.CharField(_('Address'), max_length=100, db_index=True)

# Keyword

class Keyword(Category):
    pass

# News

class NewsCategory(Category):

    class Meta(Category.Meta):
        verbose_name_plural = 'news categories'

class NewsBase(Node):
    category = models.ForeignKey(NewsCategory, verbose_name=_('Category'))
    hit = models.OneToOneField(Hit, null=True, editable=False)

    class Meta:
        abstract = True

class News(NewsBase):

    class Meta:
        verbose_name_plural = 'news'

    def save(self, force_insert=False, force_update=False):
        super(News, self).save(force_insert, force_update)
        self.save_revision(NewsRevision())

class NewsRevision(NewsBase):
    current = models.ForeignKey(News, db_index=True, related_name='current')

# Event

class EventCategory(Category):

    class Meta(Category.Meta):
        verbose_name_plural = 'event categories'

class EventBase(Node):

    category = models.ForeignKey(EventCategory, verbose_name=_('Category'))
    hit = models.OneToOneField(Hit, null=True, editable=False)

    location = models.CharField(_('Location'), max_length=255,
            help_text=_('Enter the place where this event will take place.'))

    dt_help_text=_('year-month-day hour:minute (such as 2009-01-03 13:21)')
    begin = models.DateTimeField(_('Begin'), db_index=True, help_text=dt_help_text)
    end = models.DateTimeField(_('End'), db_index=True, help_text=dt_help_text)

    class Meta:
        abstract = True

class Event(EventBase):
    def save(self, force_insert=False, force_update=False):
        super(Event, self).save(force_insert, force_update)
        self.save_revision(EventRevision())

    def upcoming(self):
        return True if self.begin >= datetime.today() else False

class EventRevision(EventBase):
    current = models.ForeignKey(Event, db_index=True, related_name='current')

# Page

class PageBase(Node):
    parent = models.ForeignKey('self', null=True, blank=True, verbose_name=_('Parent'),
            help_text=_('Choose a book page that this book page belongs to. Leave it blank for a root book page.'))
    hit = models.OneToOneField(Hit, null=True, editable=False)

    slug = models.SlugField(_('Slug'), blank=True)
    weight = models.IntegerField(_('Weight'), default=0, db_index=True,
            choices=[(x, x) for x in range(-15, 16)],
            help_text=_('Specify weight for sort order. A book page with lesser weight shows above a heavier one.'))
    show_children = models.BooleanField(_('Children List'), default=True,
            help_text=_('Show a list of its children if any in the bottom of its content.'))

    class Meta:
        abstract = True

class Page(PageBase):
    class Meta:
        unique_together = (('portal', 'title'),)

    def __unicode__(self):
        return self.title

    def save(self, force_insert=False, force_update=False):
        super(Page, self).save(force_insert, force_update)
        self.save_revision(PageRevision())

    def ancestor_id_list(self):
        pl = [self.id]
        if self.parent:
            pl.extend(self.parent.ancestor_id_list())
            pl.reverse()
        return pl

    def children(self):
        return self.page_set.filter(deleted=False).filter(hidden=False).order_by('weight')

class PageRevision(PageBase):
    current = models.ForeignKey(Page, db_index=True, related_name='current')

# File (Media)

def chunk_id(id):
    return '/'.join(list(str(id)))

def chunk_date(d):
    return '%s/%s/%s' % (d.year, digit_string_prefix(d.month), digit_string_prefix(d.day))

def file_location(portal_id, d, filename):
    return '%s/%s/%s' % (chunk_id(portal_id), chunk_date(d), filename)

def upload_location(instance, filename):
    d = instance.created_at if instance.id else date.today()
    return file_location(instance.portal.id, d, filename)

class MediaFileBase(ModelWithKeywordsAndWriters):
    portal = models.ForeignKey(Portal, editable=False)

    file = models.FileField(_('File'), upload_to=upload_location,
            help_text=_('Allowed characters for a file name are A-Z, a-z, 0-9, _ (underscore), and - (dash).'))
    name = models.CharField(_('Name'), max_length=255, db_index=True, editable=False)
    content_type = models.CharField(_('Content-Type'), max_length=255, db_index=True, editable=False)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.file.url if not self.deleted else self.name

class MediaFile(MediaFileBase):

    def save(self, force_insert=False, force_update=False):
        super(MediaFile, self).save(force_insert, force_update)
        self.save_revision(MediaFileRevision())
        if path.isfile(self.file.path):
            os.chmod(self.file.path, 0644)

    def mark_deleted(self):
        self.deleted = True
        self.name = '[DELETED %s] %s' % (int(time.time()), self.name)
        self.remove_file()
        self.save()

    def remove_file(self):
        if path.isfile(self.file.path):
            os.remove(self.file.path)

class MediaFileRevision(MediaFileBase):
    current = models.ForeignKey(MediaFile, db_index=True, related_name='current')

# Podcast

class PodcastCategory(Category):

    class Meta(Category.Meta):
        verbose_name_plural = 'podcast categories'

class PodcastBase(Node):
    category = models.ForeignKey(PodcastCategory, verbose_name=_('Category'))
    hit = models.OneToOneField(Hit, null=True, editable=False)

    enclosure_url = models.CharField(_('Media URL'), max_length=255,
            help_text=_('Enter the full URL of the media file.'))
    enclosure_length = models.IntegerField(_('Media Length'), default=0,
            help_text=_('Enter the length (in bytes) of the media file.'))
    enclosure_type = models.CharField(_('Media Type'), max_length=255, choices=PODCAST_MEDIA_TYPE)

    class Meta:
        abstract = True

    def media_type(self):
        for i in range(len(PODCAST_MEDIA_TYPE)):
            if self.enclosure_type == PODCAST_MEDIA_TYPE[i][0]:
                return PODCAST_MEDIA_TYPE[i][1]

    def is_video(self):
        return True if self.enclosure_type in ('video/x-flv', 'video/mp4') else False

    def is_audio(self):
        return True if self.enclosure_type in ('audio/mpeg',) else False

class Podcast(PodcastBase):

    def save(self, force_insert=False, force_update=False):
        super(Podcast, self).save(force_insert, force_update)
        self.save_revision(PodcastRevision())

class PodcastRevision(PodcastBase):
    current = models.ForeignKey(Podcast, db_index=True, related_name='current')


# Invalidate cache fragments
# ---

# http://christiankaula.com/categories/hints/die-cache-die/

from django.core.cache import cache
from django.utils.hashcompat import md5_constructor
from django.utils.http import urlquote

def invalidate_cache_fragment(fragment_name, *args):
    cargs = md5_constructor(u':'.join([urlquote(arg) for arg in args]))
    cache_key = 'template.cache.%s.%s' % (fragment_name, cargs.hexdigest())
    cache.delete(cache_key)

# ---

from django.db.models.signals import post_save


# Page

def invalidate_page_toc_func(page):
    invalidate_cache_fragment('page_toc', page.id)
    if page.parent:
        invalidate_page_toc_func(page.parent)
 
def invalidate_page_toc(sender, **kwargs):
    page = kwargs['instance']
    invalidate_page_toc_func(page)
    for child in page.portal.page_set.filter(deleted=False).filter(parent=page):
        invalidate_cache_fragment('page_toc', child.id)

post_save.connect(invalidate_page_toc, sender=Page)


def invalidate_root_toc(sender, **kwargs):
    if not kwargs['instance'].parent:
        invalidate_cache_fragment('root_toc', kwargs['instance'].portal.address)

post_save.connect(invalidate_root_toc, sender=Page)


def invalidate_page_item(sender, **kwargs):
    invalidate_cache_fragment('page_item', kwargs['instance'].id)

post_save.connect(invalidate_page_item, sender=Page)


# News

def invalidate_sidebar_news(sender, **kwargs):
    invalidate_cache_fragment('sidebar_news', kwargs['instance'].portal.address)

post_save.connect(invalidate_sidebar_news, sender=News)


# Event

def invalidate_sidebar_events(sender, **kwargs):
    invalidate_cache_fragment('sidebar_events', kwargs['instance'].portal.address)

post_save.connect(invalidate_sidebar_events, sender=Event)


# Podcast

def invalidate_sidebar_podcasts(sender, **kwargs):
    invalidate_cache_fragment('sidebar_podcasts', kwargs['instance'].portal.address)

post_save.connect(invalidate_sidebar_podcasts, sender=Podcast)


# Others

def invalidate_sidebar_others(sender, **kwargs):
    invalidate_cache_fragment('sidebar_others', kwargs['instance'].address)

post_save.connect(invalidate_sidebar_others, sender=Portal)

# ---

# Invalidate cache items
# ---

def invalidate_portal_address(sender, **kwargs):
    cache.delete('portal_address_%s' % kwargs['instance'].address)

post_save.connect(invalidate_portal_address, sender=Portal)


def invalidate_sys_info(sender, **kwargs):
    cache.delete('sys_info')

post_save.connect(invalidate_sys_info, sender=SystemInfo)


def invalidate_page_id(sender, **kwargs):
    cache.delete('page_id_%s' % kwargs['instance'].id)

post_save.connect(invalidate_page_id, sender=Page)


def invalidate_news_id(sender, **kwargs):
    cache.delete('news_id_%s' % kwargs['instance'].id)

post_save.connect(invalidate_news_id, sender=News)


def invalidate_event_id(sender, **kwargs):
    cache.delete('event_id_%s' % kwargs['instance'].id)

post_save.connect(invalidate_event_id, sender=Event)


def invalidate_podcast_id(sender, **kwargs):
    cache.delete('podcast_id_%s' % kwargs['instance'].id)

post_save.connect(invalidate_podcast_id, sender=Podcast)

