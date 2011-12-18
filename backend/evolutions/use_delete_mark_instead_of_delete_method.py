from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
        AddField('Hit', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('Keyword', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('EditLock', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('Portal', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('PortalRevision', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('Page', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('PageRevision', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('NewsCategory', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('News', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('NewsRevision', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('EventCategory', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('Event', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('EventRevision', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('MediaFile', 'deleted', models.BooleanField, initial=False, db_index=True),
        AddField('MediaFileRevision', 'deleted', models.BooleanField, initial=False, db_index=True),
        ]

