from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now


class Listener(models.Model):
    listener_topic = models.CharField(max_length=100, primary_key=True)
    def __str__(self):
        return ' '.join([
            self.listener_topic
        ])


class Key(models.Model):
    listener = models.ForeignKey(Listener,on_delete=models.CASCADE)
    listener_key = models.CharField(max_length=100, default="")

    class Meta:
        unique_together = ("listener", "listener_key")

    def __str__(self):
        return ' '.join([
            self.listener.listener_topic,
            self.listener_key,
        ])


class Alert(models.Model):
    key = models.ForeignKey(Key,on_delete=models.CASCADE,default="")
    alert_msg = models.CharField(max_length=10000)
    alert_date = models.DateTimeField(default=now)

    def __str__(self):
        return ' '.join([
            self.listener.listener_topic,
            self.listener_key,
            self.alert_msg,
            self.alert_date,
        ])

    def save(self, *args, **kwargs):
        super(Alert, self).save(*args, **kwargs)
