from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    DeleteField('EventRevision', 'last_ip'),
    DeleteField('EventRevision', 'counter'),
    DeleteField('PageRevision', 'last_ip'),
    DeleteField('PageRevision', 'counter'),
    DeleteField('MediaFile', 'counter'),
    DeleteField('MediaFile', 'last_ip'),
    DeleteField('Portal', 'last_ip'),
    DeleteField('Portal', 'counter'),
    DeleteField('MediaFileRevision', 'counter'),
    DeleteField('MediaFileRevision', 'last_ip'),
    DeleteField('News', 'last_ip'),
    DeleteField('News', 'counter'),
    DeleteField('PortalRevision', 'last_ip'),
    DeleteField('PortalRevision', 'counter'),
    DeleteField('Page', 'last_ip'),
    DeleteField('Page', 'counter'),
    DeleteField('NewsRevision', 'last_ip'),
    DeleteField('NewsRevision', 'counter'),
    DeleteField('Event', 'last_ip'),
    DeleteField('Event', 'counter')
]

