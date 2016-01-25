from __future__ import unicode_literals

from django.apps import AppConfig
from django.core.cache import cache

class AlertsConfig(AppConfig):
    name = 'alerts'

    def ready(self):
        from django.db.utils import OperationalError
        try:
            from alerts.consumer import create_consumer
            create_consumer("consumer")
        except OperationalError:
            print "DB hasn't yet been initialized."
            print "Try makemigrations; migrate."
            print "If you are doing that right now then ignore."

