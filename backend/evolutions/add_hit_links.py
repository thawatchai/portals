from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('News', 'hit', models.OneToOneField, unique=True, null=True, related_model='backend.Hit'),
    AddField('NewsRevision', 'hit', models.OneToOneField, unique=True, null=True, related_model='backend.Hit'),
    AddField('Event', 'hit', models.OneToOneField, unique=True, null=True, related_model='backend.Hit'),
    AddField('EventRevision', 'hit', models.OneToOneField, unique=True, null=True, related_model='backend.Hit'),
    AddField('Page', 'hit', models.OneToOneField, unique=True, null=True, related_model='backend.Hit'),
    AddField('PageRevision', 'hit', models.OneToOneField, unique=True, null=True, related_model='backend.Hit'),
]

