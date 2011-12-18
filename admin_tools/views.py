from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect as redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail, send_mass_mail

from django.conf import settings
from portals.backend.models import *
from portals.backend.views import set_message, get_sys_info, SupportForm

# Private Functions --------------------------------------------------

# Public Views -------------------------------------------------------

@staff_member_required
def tool_list(request):
    return render_to_response('at_tool_list.html', {
        'app_label': _('Tools'),
        'cl': {'opts': {'verbose_name_plural': _('List')}},
        }, RequestContext(request))

# NOTE: may not practical for a really large group of users
@staff_member_required
def email_all(request):
    if request.method == 'POST':
        form = SupportForm(request.POST)
        if form.is_valid():
            sys_info = get_sys_info()
            dt = []
            for user in User.objects.all():
                dt.append((
                    form.cleaned_data['subject'],
                    form.cleaned_data['message'],
                    sys_info.support_email,
                    [user.email],
                    ))
            try:
                send_mass_mail(dt)
                set_message(request, ugettext('The email has been sent.'))
            except:
                set_message(request, ugettext('ERROR!! The email could not be sent.'))
            return redirect('/admin/tools/')
    else:
        form = SupportForm()
    return render_to_response('at_email_all.html', {
        'form': form,
        'app_label': _('Tools'),
        'opts': {'verbose_name_plural': _('Email')},
        'original': _('All'),
        }, RequestContext(request, {}))

