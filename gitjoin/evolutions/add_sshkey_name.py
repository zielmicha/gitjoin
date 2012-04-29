from django_evolution.mutations import AddField
from django.db import models

MUTATIONS = [
    AddField('SSHKey', 'name', models.CharField, initial="", max_length=50)
]
