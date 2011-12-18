from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
        AddField('Portal', 'gmap_api_key', models.CharField, initial='', max_length=255),
        AddField('PortalRevision', 'gmap_api_key', models.CharField, initial='', max_length=255),
        ]
