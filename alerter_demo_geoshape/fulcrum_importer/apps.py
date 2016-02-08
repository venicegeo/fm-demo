from __future__ import unicode_literals

from django.apps import AppConfig


class FulcrumImporterConfig(AppConfig):
    name = 'fulcrum_importer'

    def ready(self):
        from django.db.utils import OperationalError
        try:
            from .models import Layer
            from geoshape_fulcrum import Fulcrum_Importer
            print("Server loaded.")
            fulcrum = Fulcrum_Importer()
            # fulcrum.start()
        except OperationalError:
            print("Data has not yet been migrated.")

