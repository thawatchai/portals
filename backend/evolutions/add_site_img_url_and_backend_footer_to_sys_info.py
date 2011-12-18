from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
        AddField('SystemInfo', 'site_img_url', models.CharField, initial='', max_length=255),
        AddField('SystemInfo', 'backend_footer', models.TextField, initial='')
        ]
