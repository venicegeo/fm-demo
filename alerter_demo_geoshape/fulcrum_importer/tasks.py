from __future__ import absolute_import

from celery import shared_task
from S3.Exceptions import *
from S3.S3 import S3
from S3.Config import Config
from S3.S3Uri import S3Uri
import os
from .models import S3Sync
from .fulcrum_importer import FulcrumImporter, process_fulcrum_data
from .mapping import get_geojson
from django.conf import settings
import json


@shared_task(name="fulcrum_importer.tasks.print_test")
def print_test(data):
    print("Test success: {}.".format(data))


@shared_task(name="fulcrum_importer.tasks.task_update_layers")
def task_update_layers():
    fulcrum_importer = FulcrumImporter()
    fulcrum_importer.update_all_layers()


@shared_task(name="fulcrum_importer.tasks.pull_S3_data")
def pull_S3_data():
    #https://www.mail-archive.com/s3tools-general@lists.sourceforge.net/msg00174.html

    try:
        S3_KEY = settings.S3_KEY
        S3_SECRET = settings.S3_SECRET
    except AttributeError:
        S3_KEY = None
        S3_SECRET = None
        pass

    try:
        S3_GPG = settings.S3_GPG
    except AttributeError:
        S3_GPG = None
        pass

    cfg = Config(configfile=settings.S3_CFG, access_key=S3_KEY, secret_key=S3_SECRET)
    if S3_GPG:
        cfg.gpg_passphrase = S3_GPG
    s3 = S3(cfg)
    for file_name, file_size in list_bucket_files(s3, settings.S3_BUCKET):
        if is_loaded(file_name):
            continue
        s3_download(s3, get_uri("s3://{}/{}".format(settings.S3_BUCKET,file_name)), file_name, file_size)
        print("Processing: {}".format(file_name))
        process_fulcrum_data(file_name)
        S3Sync.objects.create(s3_filename=file_name)


def get_uri(string):
    return S3Uri(string)


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
    if os.path.exists(os.path.join(settings.FULCRUM_UPLOAD, file_name)):
        start_pos = os.path.getsize(os.path.join(settings.FULCRUM_UPLOAD, file_name))
        if start_pos==file_size:
            return
    print("Downloading from S3: {}".format(file_name))
    with open(os.path.join(settings.FULCRUM_UPLOAD, file_name), 'wb') as download:
        s3.object_get(uri, download, file_name, start_position = start_pos)
    return
