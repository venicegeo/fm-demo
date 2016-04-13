# Copyright 2016, RadiantBlue Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import unicode_literals

from django.db import models
from django.core.files.storage import FileSystemStorage
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import os
import json
from datetime import datetime, timedelta

if getattr(settings, 'SITENAME', '').lower() == 'geoshape':
    fulcrum_media_dir = getattr(settings, 'FILESERVICE_CONFIG', {}).get('store_dir')
else:
    fulcrum_media_dir = getattr(settings, 'MEDIA_ROOT', None)
if not fulcrum_media_dir:
    if not os.path.exists(os.path.join(os.getcwd(), 'media')):
        os.mkdir(os.path.join(os.getcwd(), 'media'))
    fulcrum_media_dir = os.path.join(os.getcwd(), 'media')

fulcrum_data_dir = getattr(settings, 'FULCRUM_UPLOAD', None)
if not fulcrum_data_dir:
    fulcrum_data_dir = getattr(settings, 'MEDIA_ROOT', None)
if not fulcrum_data_dir:
    if not os.path.exists(os.path.join(os.getcwd(), 'data')):
        os.mkdir(os.path.join(os.getcwd(), 'data'))
    fulcrum_data_dir = os.path.join(os.getcwd(), 'data')


def get_media_dir():
    return fulcrum_media_dir


def get_data_dir():
    return fulcrum_data_dir


def default_datetime():
    return datetime(1, 1, 1, 0, 0, 0)


def get_asset_name(instance, *args):
    """

    Args:
        instance: The model instance.

    Returns:
        a string representing the file with an extension.

    """
    return './{}.{}'.format(instance.asset_uid, get_type_extension(instance.asset_type))


def get_type_extension(file_type):
    """

    Args:
        file_type: A generic for the file (e.g. photos, videos, audio).

    Returns:
        The mapped extension (e.g. jpg, mp4, m4a).
    """
    asset_types = {'photos': 'jpg', 'videos': 'mp4', 'audio': 'm4a'}
    if asset_types.get(file_type):
        return asset_types.get(file_type)
    else:
        return None


def get_all_features(after_time_added=None):
    """

    Args:
        after_time_added: get all features that were added to the db after this date.

    Returns:

    """
    features = []
    if after_time_added:
        for feature in Feature.objects.exclude(feature_added_time__lt=after_time_added):
            features += [json.loads(feature.feature_data)]
    else:
        for feature in Feature.objects.all():
            features += [json.loads(feature.feature_data)]
    return {"features": features}


class Asset(models.Model):
    """Structure to hold file locations."""
    asset_uid = models.CharField(max_length=100, primary_key=True)
    asset_type = models.CharField(max_length=100)
    asset_data = models.FileField(storage=FileSystemStorage(location=get_media_dir()), upload_to=get_asset_name)


class Layer(models.Model):
    """Structure to hold information about layers."""
    layer_name = models.CharField(max_length=100, primary_key=True)
    layer_uid = models.CharField(max_length=100)
    layer_date = models.IntegerField(default=0)
    layer_media_keys = models.CharField(max_length=2000, default="{}")

    class Meta:
        unique_together = (("layer_name", "layer_uid"),)


class Feature(models.Model):
    """Structure to hold information about and actual feature data."""
    feature_uid = models.CharField(max_length=100)
    feature_version = models.IntegerField(default=0)
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE, default="")
    feature_data = models.CharField(max_length=10000)
    feature_added_time = models.DateTimeField(default=datetime.now())

    class Meta:
        unique_together = (("feature_uid", "feature_version"),)


class S3Sync(models.Model):
    """Structure to persist knowledge of a file download."""
    s3_filename = models.CharField(max_length=500, primary_key=True)


class S3Credential(models.Model):
    s3_name = models.CharField(max_length=100)
    s3_key = models.CharField(max_length=100)
    s3_secret = models.CharField(max_length=255)
    s3_gpg = models.CharField(max_length=255)

    class Meta:
        unique_together = (("s3_key", "s3_secret"),)

    def __unicode__(self):
        return "{}({})".format(self.s3_name, self.s3_key)


class S3Bucket(models.Model):
    s3_bucket = models.CharField(max_length=511)
    s3_credential = models.ForeignKey(S3Credential, on_delete=models.CASCADE, default="")

    def __unicode__(self):
        return self.s3_bucket


class FulcrumApiKey(models.Model):
    fulcrum_api_description = models.CharField(max_length=100)
    fulcrum_api_key = models.CharField(max_length=255, default="", primary_key=True)

    def __unicode__(self):
        return self.fulcrum_api_description


class Filter(models.Model):
    """Structure to hold knowledge of filters in the filter package."""

    filter_name = models.TextField(primary_key=True)
    filter_active = models.BooleanField(default=False)
    filter_previous = models.BooleanField(default=False)
    filter_previous_status = models.TextField(default="")
    filter_previous_time = models.DateTimeField(default=timezone.now() - timedelta(minutes=5))

    def get_lock_id(self):
        """

        Returns: A name to use to store the lock.

        """
        name = "djfulcrum.tasks.task_update_layers"
        return '{0}-lock-{1}'.format(name, self.filter_name)

    def save(self, *args, **kwargs):
        super(Filter, self).save(*args, **kwargs)
        if self.filter_previous and not self.is_filter_running():
            run_time = timezone.now().isoformat()
            from .tasks import task_filter_features
            if getattr(settings, 'DJANGO_FULCRUM_USE_CELERY', True):
                task_filter_features.apply_async(kwargs={'filter_name': self.filter_name,
                                                         'features': get_all_features(
                                                                 after_time_added=self.filter_previous_time),
                                                         'run_once': True,
                                                         'run_time': run_time})
            else:
                task_filter_features(filter_name=self.filter_name,
                                     features=self.filter_previous_time,
                                     run_once=True,
                                     run_time=run_time)
            self.filter_previous = False
        if self.is_filter_running():
            self.filter_previous_status = "Filtering is in progress..."
        else:
            self.filter_previous_status = "Filtering is current as of {}.".format(self.filter_previous_time)
        super(Filter, self).save(*args, **kwargs)

    def is_filter_running(self):
        """

        Returns: True if a lock exists for the current filter.

        """

        if cache.get(self.get_lock_id()):
            return True
        return False

    def __unicode__(self):
        if self.filter_active:
            status = "  (Active)"
        else:
            status = "  (Inactive)"
        if self.is_filter_running():
            status = "{} - Filtering old features...)".format(status[:-1])
        return self.filter_name + status


# def get_defaults(Model):
#     from django.db.models.fields import NOT_PROVIDED
#     defaults = {}
#     for field in get_all_field_names(Model):
#         default_value = Model._meta.get_field(field).default
#         if default_value != NOT_PROVIDED:
#             defaults[field] = Model._meta.get_field(field).default
#     return defaults
#
#
# def get_all_field_names(Model):
#     # https://docs.djangoproject.com/en/1.9/ref/models/meta/
#     try:
#         from itertools import chain
#         return list(set(chain.from_iterable(
#                 (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
#                 for field in Model._meta.get_fields()
#                 # For complete backwards compatibility, you may want to exclude
#                 # GenericForeignKey from the results.
#                 if not (field.many_to_one and field.related_model is None)
#         )))
#     except AttributeError:
#         return Model._meta.get_all_field_names()
