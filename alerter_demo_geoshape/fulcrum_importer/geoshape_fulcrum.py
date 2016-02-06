from fulcrum import Fulcrum
from django.conf import settings


class Fulcrum(Fulcrum):
    def __init__(self):
        key = settings.FULCRUM_API_KEY
        super(Fulcrum, self).__init__()


def process_fulcrum_data(f):
    from django.conf import settings
    import os
    import shutil

    layers = []
    file_path = os.path.join(settings.FULCRUM_UPLOAD, f.name)
    if save_file(f, file_path):
        unzip_file(file_path)
        for folder, subs, files in os.walk(os.path.join(settings.FULCRUM_UPLOAD, os.path.splitext(file_path)[0])):
            for filename in files:
                if '.geojson' in filename:
                    upload_geojson(os.path.abspath(os.path.join(folder, filename)))
                    layers += [os.path.splitext(filename)[0]]
        delete_folder(os.path.splitext(file_path)[0])
    return layers


def save_file(f, file_path):
    from django.conf import settings
    import os
    if os.path.splitext(file_path)[1] != '.zip':
        return False
    try:
        if not os.path.exists(settings.FULCRUM_UPLOAD):
            os.mkdir(settings.FULCRUM_UPLOAD)
        with open(file_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
    except:
        print "Failed to save the file: {}".format(f.name)
        return False
    print "Saved the file: {}".format(f.name)
    return True


def unzip_file(file_path):
    from django.conf import settings
    import os
    import zipfile
    # http://stackoverflow.com/questions/12886768/how-to-unzip-file-in-python-on-all-oses

    with zipfile.ZipFile(file_path) as zf:
        for member in zf.infolist():
            # Path traversal defense copied from
            # http://hg.python.org/cpython/file/tip/Lib/http/server.py#l789
            words = member.filename.split('/')
            path = os.path.join(settings.FULCRUM_UPLOAD, os.path.splitext(file_path)[0])
            for word in words[:-1]:
                drive, word = os.path.splitdrive(word)
                head, word = os.path.split(word)
                if word in (os.curdir, os.pardir, ''): continue
                path = os.path.join(path, word)
            zf.extract(member, path)


def delete_folder(file_path):
    import shutil
    shutil.rmtree(file_path)


def delete_file(file_path):
    import os
    os.remove(file_path)


def upload_geojson(file_path):
    import json
    from django.conf import settings
    from .models import Asset
    import os
    with open(file_path) as data_file:
        features = json.load(data_file).get('features')
    print("DEBUG: File path is {}".format(file_path))
    uploads = []
    for feature in features:
        for asset_type in ['photos']:
            if feature.get('properties').get(asset_type):
                urls = []
                if type(feature.get('properties').get(asset_type)) == list:
                    for asset_uid in feature.get('properties').get(asset_type):
                        asset, created = write_asset_from_file(asset_uid,
                                                               asset_type,
                                                               os.path.dirname(file_path))
                        if asset:
                            if asset.asset_data:
                                urls += [asset.asset_data.url]
                        else:
                            urls += ['Import Needed.']
                else:
                    for asset_uid in feature.get('properties').get(asset_type).split(','):
                        asset, created = write_asset_from_file(asset_uid,
                                                               asset_type,
                                                               os.path.dirname(file_path))
                        if asset:
                            if asset.asset_data:
                                urls += [asset.asset_data.url]
                        else:
                            urls += ['Import Needed.']
                feature['properties']['{}_url'.format(asset_type)] = urls
            else:
                feature['properties'][asset_type] = None
                feature['properties']['{}_url'.format(asset_type)] = None
        layer = write_layer(os.path.basename(os.path.dirname(file_path)))
        write_feature(feature.get('properties').get('fulcrum_id'),
                      layer,
                      json.dumps(feature))
        uploads += [feature]
    upload_to_postgis(uploads, settings.DB_USER, settings.DB_NAME, os.path.splitext(os.path.basename(file_path))[0])


def write_layer(name, date=None):
    from .models import Layer
    from datetime import datetime

    if not date:
        date = datetime.now()

    layer, layer_created = Layer.objects.get_or_create(layer_name=name, defaults={'layer_date':date})
    return layer


def write_feature(key, app, data):
    from .models import Feature
    feature, feature_created = Feature.objects.get_or_create(feature_uid=key,
                                                             defaults={'layer': app, 'feature_data': data})
    return feature


def write_asset_from_url(asset_uid, asset_type, url):
    from django.core.files import File
    from django.core.files.temp import NamedTemporaryFile
    import urllib2
    import os
    from .models import Asset
    from django.conf import settings

    asset, created = Asset.objects.get_or_create(asset_uid=asset_uid, asset_type=asset_type)
    if created:
        if not os.path.exists(settings.MEDIA_ROOT):
            os.mkdir(settings.MEDIA_ROOT)
        with NamedTemporaryFile() as temp:
            file_ext = {'image': 'jpg'}
            response = urllib2.urlopen(url)
            temp.write(response.read())
            file_type = response.info().maintype
            temp.flush()
            asset.asset_data.save('{}.{}'.format(asset_uid, file_ext.get(file_type)), File(temp))
    return asset, created


def write_asset_from_file(asset_uid, asset_type, file_dir):
    from django.core.files import File
    import os
    from .models import Asset
    from django.conf import settings

    asset_types = {'photos': 'jpg', 'videos': 'mp4', 'audio': 'm4a'}
    file_path = os.path.join(file_dir, '{}.{}'.format(asset_uid, asset_types.get(asset_type)))
    asset, created = Asset.objects.get_or_create(asset_uid=asset_uid, asset_type=asset_type)
    if created:
        if not os.path.exists(settings.MEDIA_ROOT):
            os.mkdir(settings.MEDIA_ROOT)
        if os.path.exists(file_path):
            with open(file_path) as open_file:
                asset.asset_data.save(os.path.splitext(os.path.basename(file_path))[0],
                                      File(open_file))
        else:
            print("The file {}.{} was not included in the archive.".format(asset_uid, asset_types.get(asset_type)))
            return None, False
    return asset, created


def upload_to_postgis(feature_data, user, database, table):
    import json
    import subprocess
    import os

    for feature in feature_data:
        for property in feature.get('properties'):
            if type(feature.get('properties').get(property)) == list:
                feature['properties'][property] = ','.join(feature['properties'][property])

    for asset_type in ['photos']:
        for feature in feature_data:
            if feature.get('properties').get(asset_type):
                for asset in feature.get('properties').get(asset_type).split(','):
                    feature['properties'][
                        asset_type] = "http://geoshape.dev:8004/fulcrum_importer/assets/{}.jpg".format(asset)
                    feature['properties'][
                        asset_type + '_url'] = "http://geoshape.dev:8004/fulcrum_importer/assets/{}.jpg".format(asset)

    temp_file = os.path.abspath('./temp.json')
    temp_file = '/'.join(temp_file.split('\\'))

    feature_collection = {"type": "FeatureCollection", "features": feature_data}

    with open(temp_file, 'w') as open_file:
        open_file.write(json.dumps(feature_collection))
    out = ""
    conn_string = "dbname={} user={}".format(database, user)
    execute_append = ['ogr2ogr',
                      '-f', 'PostgreSQL',
                      '-append',
                      '-skipfailures',
                      'PG:"{}"'.format(conn_string),
                      temp_file,
                      '-nln', table]

    execute_alter = ['/usr/bin/psql', '-d', 'fulcrum', '-c', "ALTER TABLE {} ADD UNIQUE(fulcrum_id);".format(table)]
    try:
        DEVNULL = open(os.devnull, 'wb')
        out = subprocess.Popen(' '.join(execute_append), shell=True, stdout=DEVNULL, stderr=DEVNULL)
        out = subprocess.Popen(execute_alter, stdout=DEVNULL, stderr=DEVNULL)
    except subprocess.CalledProcessError:
        print "Failed to call:\n" + ' '.join(execute_append)
        print out
