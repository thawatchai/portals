#! /bin/sh

export PYTHONPATH=`pwd`
export DJANGO_SETTINGS_MODULE=portals.settings

./ftp/ftpd.py

