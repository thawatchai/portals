from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from portals.backend.models import *

# Profile ------------------------------------------------------------

class ProfileAdminForm(forms.ModelForm):
    class Meta:
        model = Profile

    def __init__(self, *args, **kwargs):
        super(ProfileAdminForm, self).__init__(*args, **kwargs)
        self.fields['user'].choices = self.make_user_choices()

    def make_user_choices(self):
        user_choices = [('', '----------')]
        for u in User.objects.order_by('username'):
            if u.first_name and u.last_name:
                user_choices.append((u.id, '%s (%s %s)' % (u.username, u.first_name, u.last_name)))
            else:
                user_choices.append((u.id, u.username))
        return user_choices

class ProfileAdmin(admin.ModelAdmin):
    form = ProfileAdminForm

    list_display = ('user', 'user_full_name', 'user_email', 'verified', 'allow_upload', 'allow_ftp',)
    list_filter = ('verified', 'allow_upload', 'allow_ftp',)
    ordering = ('user',)

    def user_full_name(self, obj):
        return obj.user.get_full_name()
    user_full_name.short_description = _('Full Name')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = _('Email')

admin.site.register(Profile, ProfileAdmin)

# Others -------------------------------------------------------------

admin.site.register(SystemInfo)

admin.site.register(Portal)

admin.site.register(Keyword)

admin.site.register(Page)

admin.site.register(NewsCategory)
admin.site.register(News)

admin.site.register(EventCategory)
admin.site.register(Event)

admin.site.register(MediaFile)

