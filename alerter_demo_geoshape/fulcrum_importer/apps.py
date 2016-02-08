from __future__ import unicode_literals

from django.apps import AppConfig

class FulcrumImporterConfig(AppConfig):
    name = 'fulcrum_importer'

    def ready(self):
        from geoshape_fulcrum import Fulcrum_Importer
        print("Loaded server.")
        fulcrum = Fulcrum_Importer()
        # fulcrum.start()
