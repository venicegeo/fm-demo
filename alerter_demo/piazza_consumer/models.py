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


class Message(models.Model):
    key = models.ForeignKey(Key,on_delete=models.CASCADE,default="")
    message_body = models.CharField(max_length=10000)
    message_date = models.DateTimeField(default=now)

    def __str__(self):
        return ' '.join([
            self.listener.listener_topic,
            self.listener_key,
            self.message_body,
            self.message_date,
        ])

    # def save(self, *args, **kwargs):
    #     super(Message, self).save(*args, **kwargs)


class Asset(models.Model):
    asset_uid = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=100)
    asset_data = models.FileField(upload_to='assets/')


class Links(models.Model):
    message = models.ForeignKey(Message,on_delete=models.CASCADE,default="")
    asset = models.ForeignKey(Asset,on_delete=models.CASCADE,default="")