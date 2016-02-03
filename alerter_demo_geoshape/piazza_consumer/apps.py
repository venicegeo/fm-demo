from __future__ import unicode_literals

from django.apps import AppConfig

class AlertsConfig(AppConfig):
    name = 'piazza_consumer'

    def ready(self):
        pass
