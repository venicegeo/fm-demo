from __future__ import unicode_literals

from django.apps import AppConfig

class AlertsConfig(AppConfig):
    name = 'piazza_consumer'

    def ready(self):
        from django.db.utils import OperationalError
        try:
            from piazza_consumer.consumer import create_consumer
            create_consumer("consumer")
        except OperationalError:
            print "DB hasn't yet been initialized."
            print "Try makemigrations; migrate."
            print "If you are doing that right now then ignore."

