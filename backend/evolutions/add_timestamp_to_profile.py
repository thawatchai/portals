from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
        AddField('Profile', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('Profile', 'created_at', models.DateTimeField, initial=datetime.datetime(2009, 1, 1, 1, 1, 1), db_index=True),
        AddField('Profile', 'modified_at', models.DateTimeField, initial=datetime.datetime(2009, 1, 1, 1, 1, 1), db_index=True),
        ]
