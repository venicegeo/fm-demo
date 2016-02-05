from __future__ import unicode_literals

from django.db import models


class Asset(models.Model):
    asset_uid = models.CharField(max_length=100, primary_key=True)
    asset_type = models.CharField(max_length=100)
    asset_data = models.FileField(upload_to='assets/')


class Layer(models.Model):
    layer_name = models.CharField(max_length=100, primary_key=True)


class Feature(models.Model):
    feature_uid = models.CharField(max_length=100, primary_key=True)
    layer = models.ForeignKey(Layer,on_delete=models.CASCADE,default="")
    feature_data = models.CharField(max_length=10000)


class Links(models.Model):
    asset = models.ForeignKey(Asset,on_delete=models.CASCADE,default="")
    feature = models.ForeignKey(Feature,on_delete=models.CASCADE,default="")


