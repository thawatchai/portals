from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
        ChangeField('Page', 'weight', initial=None, db_index=True),
        ChangeField('PageRevision', 'weight', initial=None, db_index=True),
        ]

