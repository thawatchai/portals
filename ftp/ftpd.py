#! /usr/bin/env python

'''
This script borrows a few lines from GooglePagesFTPd.
'''

from django.core.management import setup_environ 
import settings 
setup_environ(settings)

from django.contrib.auth import authenticate

import os, time
from os import path
from pyftpdlib import ftpserver

from backend.lib import get_user

class PortalAuthorizer(ftpserver.DummyAuthorizer):

    def validate_authentication(self, username, password):
        valid = False
        if authenticate(username=username, password=password):
            if settings.ALWAYS_ALLOW_UPLOAD:
                valid = True
            else:
                u = get_user(username)
                try:
                    profile = u.get_profile()
                except:
                    profile = None
                if profile and profile.allow_ftp:
                    valid = True
        return valid

    def has_user(self, username):
        return username != 'anonymous'

    def has_perm(self, username, perm, path=None):
        # TODO: ?
        return True

    def get_perms(self, username):
        # TODO: Are these enough and secured?
        return 'lrdw'

    def get_home_dir(self, username):
        home = '%s%s' % (settings.FTP_ROOT, username)
        if not path.isdir(home):
            os.mkdir(home)
        return home

    def get_msg_login(self, username):
        return 'Welcome %s' % username

    def get_msg_quit(self, username):
        return 'Goodbye %s' % username

# Start FTP server

now = lambda: time.strftime("[%Y-%b-%d %H:%M:%S]")

f1, f2 = None, None
   
def standard_logger(msg):
    f1.write("%s %s\n" %(now(), msg))
   
def line_logger(msg):
    f2.write("%s %s\n" %(now(), msg))

def main():
    global f1, f2
    f1 = open('%sftpd.log' % settings.FTP_LOG_DIR, 'a')
    f2 = open('%sftpd.lines.log' % settings.FTP_LOG_DIR, 'a')
    ftpserver.log = standard_logger
    ftpserver.logline = line_logger
    
    ftp_handler = ftpserver.FTPHandler
    ftp_handler.authorizer = PortalAuthorizer()
    ftp_handler.banner = "UsablePortal FTP Service ready."

    ftpd = ftpserver.FTPServer((settings.FTP_IP, settings.FTP_PORT), ftp_handler)
    ftpd.max_cons = 256
    ftpd.max_cons_per_ip = 5

    ftpd.serve_forever()

if __name__ == '__main__':
    main()

