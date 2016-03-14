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

# Note to download data from S3 a lock must exist on that process downloading the file or multiple process may destroy
# the workflow. This can be done using just one process of course, or a process safe cache such as memcached.
# Note that django locmem (the default), is NOT multiprocess safe.
from __future__ import absolute_import

from .models import S3Sync
import os
from django.conf import settings
from django.core.cache import cache
from S3.Exceptions import *
from S3.S3 import S3
from S3.Config import Config
from S3.S3Uri import S3Uri
from .fulcrum_importer import process_fulcrum_data
from hashlib import md5


def list_bucket_files(s3, bucket):
    response = s3.bucket_list(bucket)
    for key in response["list"]:
        yield key["Key"], key["Size"]


def is_loaded(file_name):
    s3_file = S3Sync.objects.filter(s3_filename=file_name)
    if s3_file:
        return True
    return False


def s3_download(s3, uri, file_name, file_size):
    start_pos = 0
    print "File Size Reported: {}".format(int(file_size))
    if os.path.exists(os.path.join(settings.FULCRUM_UPLOAD, file_name)):
        start_pos = int(os.path.getsize(os.path.join(settings.FULCRUM_UPLOAD, file_name)))
        print("Starting Position Reported for {}: {}".format(os.path.join(settings.FULCRUM_UPLOAD, file_name), start_pos))
        if start_pos == int(file_size):
            return True
    print("Downloading from S3: {}".format(file_name))
    with open(os.path.join(settings.FULCRUM_UPLOAD, file_name), 'wb') as download:
        response = s3.object_get(uri, download, file_name, start_position=start_pos-8)
    return response


def pull_all_s3_data():
    #http://docs.celeryproject.org/en/latest/tutorials/task-cookbook.html#ensuring-a-task-is-only-executed-one-at-a-time
    #https://www.mail-archive.com/s3tools-general@lists.sourceforge.net/msg00174.html

    LOCK_EXPIRE = 60 * 2160 # LOCK_EXPIRE IS IN SECONDS (i.e. 60*2160 is 1.5 days)

    name = "fulcrum_importer.tasks.pull_s3_data"
    try:
        S3_KEY = settings.S3_KEY
        S3_SECRET = settings.S3_SECRET
    except AttributeError:
        S3_KEY = None
        S3_SECRET = None

    try:
        S3_GPG = settings.S3_GPG
    except AttributeError:
        S3_GPG = None

    cfg = Config(configfile=settings.S3_CFG, access_key=S3_KEY, secret_key=S3_SECRET)
    if S3_GPG:
        cfg.gpg_passphrase = S3_GPG
    s3 = S3(cfg)

    function_name_hexdigest = md5(name).hexdigest()
    lock_id = '{0}-lock-{1}'.format(name, function_name_hexdigest)
    acquire_lock = lambda: cache.add(lock_id, "true", LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    if acquire_lock():
        try:
            for file_name, file_size in list_bucket_files(s3, settings.S3_BUCKET):
                handle_file(s3, file_name, file_size)
        finally:
            release_lock()


def handle_file(s3, file_name, file_size):
    if is_loaded(file_name):
        return
    if s3_download(s3, S3Uri("s3://{}/{}".format(settings.S3_BUCKET,file_name)), file_name, file_size):
        print("Processing: {}".format(file_name))
        process_fulcrum_data(file_name)
        S3Sync.objects.create(s3_filename=file_name)