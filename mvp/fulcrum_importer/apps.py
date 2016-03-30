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

from __future__ import unicode_literals, absolute_import

from django.apps import AppConfig
from django.core.cache import cache
from hashlib import md5
from sys import exit
from time import sleep

class FulcrumImporterConfig(AppConfig):
    name = 'fulcrum_importer'

    def ready(self):
        test_lock, test_read = test_cache()
        if not test_lock:
            print("Unable to securely write to cache.")
            print("Please ensure you have a process safe cache installed, configured, and running.")
            exit(1)
        if not test_read:
            print("Unable to read/write to cache.")
            print("Please ensure you have a process safe cache installed, configured, and running.")
            exit(1)
        return


def test_cache():
    from multiprocessing import Process
    lock_id = get_lock_id('lock_id')
    cache.delete(lock_id)
    p = Process(target=create_lock, args=(lock_id,))
    p.start()
    p.join()
    if cache.add(lock_id, "true", 1):
        lock_test = False
    else:
        lock_test = True
    if cache.get(lock_id) == 'true':
        cache_test = True
    else:
        cache_test = False
    cache.delete(lock_id)
    return lock_test, cache_test


def create_lock(lock_id):
    cache.add(lock_id, "true", 20)


def get_lock_id(lock_name):
    file_name_hexdigest = md5(lock_name).hexdigest()
    return '{0}-lock-{1}'.format(lock_name, file_name_hexdigest)

