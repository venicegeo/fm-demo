from __future__ import unicode_literals

from django.db import models


def get_asset_name(instance, filename):
    return './{}.{}'.format(instance.asset_uid, get_type_extension(instance.asset_type))


def get_type_extension(type):
    asset_types = {'photos': 'jpg', 'videos': 'mp4', 'audio': 'm4a'}
    return asset_types.get(type)


class Asset(models.Model):
    asset_uid = models.CharField(max_length=100, primary_key=True)
    asset_type = models.CharField(max_length=100)
    asset_data = models.FileField(upload_to=get_asset_name)


class Layer(models.Model):
    layer_name = models.CharField(max_length=100)
    layer_uid = models.CharField(max_length=100)
    layer_date = models.IntegerField(default=0)

    class Meta:
        unique_together = (("layer_name", "layer_uid"),)


class Feature(models.Model):
    feature_uid = models.CharField(max_length=100, primary_key=True)
    layer = models.ForeignKey(Layer,on_delete=models.CASCADE,default="")
    feature_data = models.CharField(max_length=10000)


class Links(models.Model):
    asset = models.ForeignKey(Asset,on_delete=models.CASCADE,default="")
    feature = models.ForeignKey(Feature,on_delete=models.CASCADE,default="")


