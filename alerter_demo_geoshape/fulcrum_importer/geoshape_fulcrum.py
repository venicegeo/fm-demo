from fulcrum import Fulcrum
from django.conf import settings
from django.core.cache import cache
import requests
from .models import Layer
from dateutil import parser


class Fulcrum_Importer():
    def __init__(self):
        self.conn = Fulcrum(key=settings.FULCRUM_API_KEY)

    def start(self, interval=5):
        from threading import Thread
        if cache.get(settings.FULCRUM_API_KEY):
            return
        else:
            cache.set(settings.FULCRUM_API_KEY, True)
            thread = Thread(target=self.run, args=[interval])
            thread.daemon = True
            thread.start()

    def run(self, interval):
        import time

        while cache.get(settings.FULCRUM_API_KEY):
            self.update_all_layers()
            time.sleep(interval)

    def stop(self):
        cache.set(settings.FULCRUM_API_KEY, False)

    def get_forms(self):
        return self.conn.forms.find('').get('forms')

    def ensure_layer(self, layer_name=None, layer_id=None):
        layer, created = Layer.objects.get_or_create(layer_name=layer_name, layer_uid=layer_id)
        return layer, created

    def update_records(self, form):
        import json
        import time

        filtered_feature_count = 0

        layer = Layer.objects.get(layer_uid=form.get('id'))
        if not layer:
            print("Layer {} doesn't exist.".format(form.get('id')))

        temp_features = []
        if layer.layer_date:
            url_params={'form_id': layer.layer_uid,'updated_since': layer.layer_date+1}
        else:
            url_params={'form_id': layer.layer_uid}
        imported_features = self.conn.records.search(url_params=url_params)
        temp_features += imported_features.get('records')
        while imported_features.get('current_page') < imported_features.get('total_pages'):
            url_params['page'] = imported_features.get('current_page') + 1
            imported_features = self.conn.records.search(url_params=url_params)

        imported_geojson = self.convert_to_geojson(temp_features, form)

        pulled_record_count = len(imported_geojson.get('features'))

        # A place holder for filtering to follow.
        filtered_features = imported_geojson
        latest_time = self.get_latest_time(imported_geojson, layer.layer_date)

        if filtered_features.get('features'):
            for filter in settings.DATA_FILTERS:
                filtered_results = requests.post(filter, data=json.dumps(filtered_features)).json()

                if filtered_results.get('failed'):
                    print("Some features failed the {} filter.".format(filter))
                if filtered_results.get('passed'):
                    filtered_features = filtered_results.get('passed')
                    filtered_feature_count = len(filtered_results.get('passed').get('features'))
                else:
                    filtered_features = None
        else:
            filtered_features = None

        uploads = []

        if filtered_features:
            for feature in filtered_features.get('features'):
                for asset_type in {'photos', 'videos', 'audio'}:
                    if feature.get('properties').get(asset_type):
                        for id in feature.get('properties').get(asset_type):
                            print("Getting asset :{}".format(id))
                            feature['properties']['{}_url'.format(asset_type)] += [self.get_asset(id, asset_type)]
                write_feature(feature.get('properties').get('id'), layer, feature)
                uploads += [feature]
            if settings.DATABASE_NAME:
                upload_to_postgis(uploads, settings.DATABASE_USER, settings.DATABASE_NAME, layer.layer_name)
            layer.layer_date = latest_time
            layer.save()
        print("RESULTS\n---------------")
        print("Total Records Pulled: {}".format(pulled_record_count))
        print("Total Records Passed Filter: {}".format(filtered_feature_count))
        return

    def get_latest_time(self, new_features, old_layer_time):
        import time

        layer_time = old_layer_time
        for new_feature in new_features.get('features'):
            feature_date = time.mktime(parser.parse(new_feature.get('properties').get('updated_at')).timetuple())
            if feature_date > layer_time:
                layer_time = feature_date
        return layer_time

    def update_all_layers(self):
        for form in self.get_forms():
            layer, created = self.ensure_layer(layer_name=form.get('name'), layer_id=form.get('id'))
            if layer.layer_name == "Test":
                if created:
                    print("The layer {}({}) was created.".format(layer.layer_name, layer.layer_uid))
                print("Getting records for {}".format(form.get('name')))
                self.update_records(form)

    def convert_to_geojson(self, results, form):
        map = self.get_element_map(form)
        features = []
        for result in results:
            feature = {"type": "Feature",
                       "geometry": {"type": "Point",
                                    "coordinates": [result.get('longitude'),
                                                    result.get('latitude')]
                                    }}
            properties = {}
            assets = {'videos': [], 'videos_cap': [], 'videos_url': [],
                      'photos': [], 'photos_cap': [], 'photos_url': [],
                      'audio': [], 'audio_cap': [], 'audio_url': []}
            for asset, val in assets.iteritems():
                properties[asset] = val
            for key in result:
                if key == 'form_values':
                    for fv_key, fv_val in result['form_values'].iteritems():
                        if map.get(fv_key) in assets:
                            for asset_prop in fv_val:
                                for asset_prop_key, asset_prop_val in asset_prop.iteritems():
                                    if 'id' in asset_prop_key:
                                        if asset_prop_val:
                                            properties[map.get(fv_key)] += [asset_prop_val]
                                            ## This needs to be tested to ensure captions match assets.
                                            if asset_prop.get('caption'):
                                                properties['{}_cap'.format(map.get(fv_key))] += [asset_prop_val]
                        else:
                            properties[map.get(fv_key)] = fv_val
                else:
                    if result[key]:
                        properties[key] = result[key]
            feature['properties'] = properties
            features += [feature]
        geojson = {"type": "FeatureCollection", "features": features}
        return geojson

    def get_element_map(self, form):
        elements = form.get('elements')
        map = {}
        for element in elements:
            map[element.get('key')] = element.get('data_name')
        return map

    def get_asset(self, asset_id, asset_type):
        if asset_id:
            return write_asset_from_url(asset_id, asset_type)
        else:
            print "An asset_id must be provided."
            return None

    def __del__(self):
        cache.set(settings.FULCRUM_API_KEY, False)


def process_fulcrum_data(f):
    from django.conf import settings
    import os

    layers = []
    file_path = os.path.join(settings.FULCRUM_UPLOAD, f.name)
    if save_file(f, file_path):
        unzip_file(file_path)
        for folder, subs, files in os.walk(os.path.join(settings.FULCRUM_UPLOAD, os.path.splitext(file_path)[0])):
            for filename in files:
                if '.geojson' in filename:
                    upload_geojson(file_path=os.path.abspath(os.path.join(folder, filename)))
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


def upload_geojson(file_path=None, features=None):
    import json
    from django.conf import settings
    from .models import get_type_extension
    import os

    from_file = False
    if file_path and features:
        raise "upload_geojson() must take file_path OR features"
        return False
    elif features:
        features = features.get('features')
    elif file_path:
        with open(file_path) as data_file:
            features = json.load(data_file).get('features')
            from_file = True
    else:
        raise "upload_geojson() must take file_path OR features"

    uploads = []
    print "\n\n FEATURES {} \n\n".format(features)
    for feature in features:
        for asset_type in ['photos', 'videos', 'audio']:
            if(from_file and feature.get('properties').get(asset_type)):
                urls = []
                if type(feature.get('properties').get(asset_type)) == list:
                    asset_uids = feature.get('properties').get(asset_type)
                else:
                    asset_uids = feature.get('properties').get(asset_type).split(',')
                for asset_uid in asset_uids:
                    asset, created = write_asset_from_file(asset_uid,
                                                           asset_type,
                                                           os.path.dirname(file_path))
                    if asset:
                        if asset.asset_data:
                            urls += [asset.asset_data.url]
                    else:
                        urls += ['Import Needed.']
                feature['properties']['{}_url'.format(asset_type)] = urls
            elif(from_file and not feature.get('properties').get(asset_type)):
                feature['properties'][asset_type] = None
                feature['properties']['{}_url'.format(asset_type)] = None
        layer = write_layer(os.path.basename(os.path.dirname(file_path)))
        write_feature(feature.get('properties').get('fulcrum_id'),
                      layer,
                      feature)
        uploads += [feature]
    upload_to_postgis(uploads, settings.DATABASE_USER, settings.DATABASE_NAME, os.path.splitext(os.path.basename(file_path))[0])


def write_layer(name, date=None):
    from .models import Layer
    from datetime import datetime
    import time

    if not date:
        date = time.mktime(datetime.now().timetuple())
    layer, layer_created = Layer.objects.get_or_create(layer_name=name, defaults={'layer_date': date})
    return layer


def write_feature(key, app, feature_data):
    from .models import Feature
    import json
    feature, feature_created = Feature.objects.get_or_create(feature_uid=key,
                                                             defaults={'layer': app,
                                                                       'feature_data': json.dumps(feature_data)})
    return feature


def write_asset_from_url(asset_uid, asset_type, url=None):
    from django.core.files import File
    from django.core.files.temp import NamedTemporaryFile
    import requests
    import os
    from .models import Asset, get_asset_name, get_type_extension
    from django.conf import settings

    asset, created = Asset.objects.get_or_create(asset_uid=asset_uid, asset_type=asset_type)
    if created:
        if not os.path.exists(settings.MEDIA_ROOT):
            os.mkdir(settings.MEDIA_ROOT)
        with NamedTemporaryFile() as temp:
            if not url:
                url = 'https://api.fulcrumapp.com/api/v2/{}/{}.{}'.format(asset.asset_type, asset.asset_uid,
                                                                          get_type_extension(asset_type))
            response = requests.get(url, headers={'X-ApiToken': settings.FULCRUM_API_KEY})
            print "{}:{}".format(response.status_code, response.headers.get('Content-Type').split(';')[0].split('/')[1])
            # response.headers.get('Content-Type').split(';')[0].split('/')[1]
            for content in response.iter_content(chunk_size=1028):
                temp.write(content)
            temp.flush()
            asset.asset_data.save(asset.asset_uid, File(temp))
    else:
        print "Asset already created."
        asset = Asset.objects.get(asset_uid=asset_uid)
    return asset.asset_data.url


def write_asset_from_file(asset_uid, asset_type, file_dir):
    from django.core.files import File
    import os
    from .models import Asset, get_type_extension
    from django.conf import settings

    file_path = os.path.join(file_dir, '{}.{}'.format(asset_uid, get_type_extension(asset_type)))
    asset, created = Asset.objects.get_or_create(asset_uid=asset_uid, asset_type=asset_type)
    if created:
        if not os.path.exists(settings.MEDIA_ROOT):
            os.mkdir(settings.MEDIA_ROOT)
        if os.path.exists(file_path):
            with open(file_path) as open_file:
                asset.asset_data.save(os.path.splitext(os.path.basename(file_path))[0],
                                      File(open_file))
        else:
            print("The file {}.{} was not included in the archive.".format(asset_uid, get_type_extension(asset_type)))
            return None, False
    return asset, created


def upload_to_postgis(feature_data, user, database, table):
    import json
    import subprocess
    import os

    for feature in feature_data:
        for property in feature.get('properties'):
            if not feature.get('properties').get(property):
                continue
            if type(feature.get('properties').get(property)) == list:
                print("feature.get('properties').get({}): {}".format(property, feature.get('properties').get(property)))
                feature['properties'][property] = ','.join(feature['properties'][property])

    # for asset_type in ['photos']:
    #     for feature in feature_data:
    #         if feature.get('properties').get(asset_type):
    #             for asset in feature.get('properties').get(asset_type).split(','):
    #                 feature['properties'][
    #                     asset_type] = "http://geoshape.dev:8004/fulcrum_importer/assets/{}.jpg".format(asset)
    #                 feature['properties'][
    #                     asset_type + '_url'] = "http://geoshape.dev:8004/fulcrum_importer/assets/{}.jpg".format(asset)

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
