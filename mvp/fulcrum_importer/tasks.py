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

# ogr2ogr.py is Copyright (c) 2010-2013, Even Rouault <even dot rouault at mines-paris dot org>
# Copyright (c) 1999, Frank Warmerdam


from __future__ import absolute_import

from .fulcrum_importer import FulcrumImporter, truncate_tiles
from django.conf import settings
from django.core.cache import cache
from celery import shared_task
from hashlib import md5
from .s3_downloader import pull_all_s3_data
from .models import FulcrumApi


@shared_task(name="fulcrum_importer.tasks.task_update_layers")
def task_update_layers():

    LOCK_EXPIRE = 60 * 60 # LOCK_EXPIRE IS IN SECONDS

    fulcrum_api_keys = []

    try:
        fulcrum_api_keys = settings.FULCRUM_API_KEYS
    except AttributeError:
        pass

    if type(fulcrum_api_keys) != list:
        fulcrum_api_keys = [fulcrum_api_keys]

    for api_key in FulcrumApi.objects.all():
        fulcrum_api_keys += [api_key.fulcrum_api_key]

    if not fulcrum_api_keys:
        print("Cannot update layers from fulcrum without an API key added to the admin page, "
              "or FULCRUM_API_KEYS = ['some_key'] defined in settings.")

    name = "fulcrum_importer.tasks.task_update_layers"
    #http://docs.celeryproject.org/en/latest/tutorials/task-cookbook.html#ensuring-a-task-is-only-executed-one-at-a-time
    file_name_hexdigest = md5(name).hexdigest()
    lock_id = '{0}-lock-{1}'.format(name, file_name_hexdigest)
    acquire_lock = lambda: cache.add(lock_id, "true", LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)
    if acquire_lock():
        try:
            for fulcrum_api_key in fulcrum_api_keys:
                fulcrum_importer = FulcrumImporter(fulcrum_api_key=fulcrum_api_key)
                fulcrum_importer.update_all_layers()
        except Exception as e:
            print repr(e)
        finally:
            release_lock()


@shared_task(name="fulcrum_importer.tasks.pull_s3_data")
def pull_s3_data():
    pull_all_s3_data()


@shared_task(name="fulcrum_importer.tasks.task_update_tiles")
def update_tiles(filtered_features, layer_name):
    truncate_tiles(layer_name=layer_name.lower(), srs=4326)
    truncate_tiles(layer_name=layer_name.lower(), srs=900913)
