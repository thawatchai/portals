from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
        ChangeField('Portal', 'latitude', initial=None, null=True),
        ChangeField('Portal', 'longitude', initial=None, null=True),
        ChangeField('PortalRevision', 'latitude', initial=None, null=True),
        ChangeField('PortalRevision', 'longitude', initial=None, null=True),
        ChangeField('Page', 'latitude', initial=None, null=True),
        ChangeField('Page', 'longitude', initial=None, null=True),
        ChangeField('PageRevision', 'latitude', initial=None, null=True),
        ChangeField('PageRevision', 'longitude', initial=None, null=True),
        ChangeField('News', 'latitude', initial=None, null=True),
        ChangeField('News', 'longitude', initial=None, null=True),
        ChangeField('NewsRevision', 'latitude', initial=None, null=True),
        ChangeField('NewsRevision', 'longitude', initial=None, null=True),
        ChangeField('Event', 'latitude', initial=None, null=True),
        ChangeField('Event', 'longitude', initial=None, null=True),
        ChangeField('EventRevision', 'latitude', initial=None, null=True),
        ChangeField('EventRevision', 'longitude', initial=None, null=True),
        ChangeField('MediaFile', 'latitude', initial=None, null=True),
        ChangeField('MediaFile', 'longitude', initial=None, null=True),
        ChangeField('MediaFileRevision', 'latitude', initial=None, null=True),
        ChangeField('MediaFileRevision', 'longitude', initial=None, null=True),
        ]

