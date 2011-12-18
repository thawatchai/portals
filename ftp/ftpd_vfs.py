#! /usr/bin/env python

from django.core.management import setup_environ 
import settings 
setup_environ(settings)

from django.contrib.auth import authenticate

import os
from pyftpdlib import ftpserver

class PortalAuthorizer(ftpserver.DummyAuthorizer):

    def validate_authentication(self, username, password):
        return authenticate(username=username, password=password)
    
    def has_user(self, username):
        return username != 'anonymous'

    def has_perm(self, username, perm, path=None):
        return True

    def get_perms(self, username):
        # TODO: Do these cover all options?
        return 'lrdw'

    def get_home_dir(self, username):
        return os.sep + username

    def get_msg_login(self, username):
        return 'Welcome %s' % username

    def get_msg_quit(self, username):
        return 'Goodbye %s' % username

class PortalFS(ftpserver.AbstractedFS):

    def listdir(self, path):
        pass

# Start FTP server

def main():
    ftp_handler = ftpserver.FTPHandler
    ftp_handler.authorizer = PortalAuthorizer()
    ftpd = ftpserver.FTPServer((settings.FTP_IP, settings.FTP_PORT), ftp_handler)
    ftpd.serve_forever()

if __name__ == '__main__':
    main()

