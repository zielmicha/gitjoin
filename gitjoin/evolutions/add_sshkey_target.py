from django_evolution.mutations import AddField
from django.db import models


MUTATIONS = [
    AddField('SSHKey', 'target', models.ForeignKey, initial=None, related_model='gitjoin.Repo')
]
