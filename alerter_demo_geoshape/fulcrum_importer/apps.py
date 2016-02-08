from __future__ import unicode_literals

from django.apps import AppConfig
from django.core.cache import cache

class FulcrumImporterConfig(AppConfig):
    name = 'fulcrum_importer'

    def ready(self):
        print("Loaded server.")
        pass
