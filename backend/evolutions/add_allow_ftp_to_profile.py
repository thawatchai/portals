from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
        AddField('Profile', 'allow_ftp', models.BooleanField, initial=False)
        ]
