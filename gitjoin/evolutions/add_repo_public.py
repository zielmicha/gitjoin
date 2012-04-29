from django_evolution.mutations import AddField
from django.db import models


MUTATIONS = [
    AddField('Repo', 'public', models.BooleanField, initial=True)
]
