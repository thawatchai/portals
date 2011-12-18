from django.conf import settings
from django.contrib.auth.models import User

import imaplib

class Backend:
    def authenticate(self, username=None, password=None, **kwargs):
        username = username.lower()

        try:
            imap_port = settings.IMAP_AUTH_PORT
        except:
            imap_port = 143

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
                try:
                     org = kwargs['organization']
                except KeyError:
                     org = ''
                if (hasattr(settings, 'IMAP_ACCEPTED_DOMAINS') and
                    org in settings.IMAP_ACCEPTED_DOMAINS):
                    username = str(username) + '.' + kwargs['organization']
                    try:
                        user = User.objects.get(username=username)
                    except User.DoesNotExist:
                        user = User.objects.create_user(username, '', password)
                    return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

