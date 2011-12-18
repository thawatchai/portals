from django.conf import settings
from django.contrib.auth.models import User

import httplib, base64

class Backend:
    def authenticate(self, username=None, password=None, **kwargs):
        username = username.lower()

        conn = httplib.HTTPConnection(settings.HTTP_BASIC_AUTH_SERVER)
        conn.request('POST', settings.HTTP_BASIC_AUTH_URL, '1', {
            'Authorization': 'Basic %s' % base64.b64encode('%s:%s' % (username, password)),
            'Content-Length': 1,
            })
        res = conn.getresponse()
        if res.status == 200:
            body = res.read()
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User.objects.create_user(username, '', password)
            self.__update_user_info(user, password, body)
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def __update_user_info(self, user, password, s):
        l = s.split('\n') if s else []
        if len(l) == 3:
            email, first_name, last_name = l
            modified = False
            if user.email != email:
                user.email = email
                modified = True
            if repr(user.first_name) != repr(first_name):
                user.first_name = first_name
                modified = True
            if repr(user.last_name) != repr(last_name):
                user.last_name = last_name
                modified = True

        user.password = password
        user.save()

