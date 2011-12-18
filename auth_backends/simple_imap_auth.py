#
# This works for most IMAP servers
#

from django.conf import settings
from django.contrib.auth.models import User

import imaplib

class Backend:
    def authenticate(self, username=None, password=None):
        username = username.lower()
        imap_port = settings.IMAP_AUTH_PORT if hasattr(settings, 'IMAP_AUTH_PORT') else 143

        try:
            m = imaplib.IMAP4(settings.IMAP_AUTH_SERVER, imap_port)
        except:
            m = None

        if m:
            try:
                r = m.login(username, password)
            except:
                r = None

            if r and r[0] == 'OK':
                domain = settings.IMAP_MAIL_DOMAIN if hasattr(settings, 'IMAP_MAIL_DOMAIN') else ''
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    user = User.objects.create_user(username, '%s@%s' % (username, domain), password)
                return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

