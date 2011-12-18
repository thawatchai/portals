from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
        AddField('SystemInfo', 'ftp_access_message', models.TextField, initial='')
        ]
