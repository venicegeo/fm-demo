from fulcrum import Fulcrum
from django.core.cache import cache
from dateutil import parser
from celery.execute import send_task
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import requests
from .models import Asset, get_type_extension
import json
from django.conf import settings
import os
from .models import Layer
from datetime import datetime
import time
from geoserver.catalog import Catalog
import subprocess
from django.db import connection, connections, ProgrammingError, OperationalError, transaction
from django.db.utils import ConnectionDoesNotExist
import re
import ogr2ogr


class FulcrumImporter:
    def __init__(self):
        self.conn = Fulcrum(key=settings.FULCRUM_API_KEY)

    def start(self, interval=30):
        from threading import Thread
        if cache.get(settings.FULCRUM_API_KEY):
            return
        else:
            cache.set(settings.FULCRUM_API_KEY, True)
            thread = Thread(target=self.run, args=[interval])
            thread.daemon = True
            thread.start()

    def run(self, interval):

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
        layer = Layer.objects.get(layer_uid=form.get('id'))
        if not layer:
            print("Layer {} doesn't exist.".format(form.get('id')))

        temp_features = []
        if layer.layer_date:
            url_params = {'form_id': layer.layer_uid, 'updated_since': layer.layer_date + 1}
        else:
            url_params = {'form_id': layer.layer_uid}
        imported_features = self.conn.records.search(url_params=url_params)
        if imported_features.get('current_page') <= imported_features.get('total_pages'):
            print("Received {} page {} of {}".format(layer.layer_name,
                                                     imported_features.get('current_page'),
                                                     imported_features.get('total_pages')))
        temp_features += imported_features.get('records')
        while imported_features.get('current_page') < imported_features.get('total_pages'):
            url_params['page'] = imported_features.get('current_page') + 1
            imported_features = self.conn.records.search(url_params=url_params)
            print("Received {} page {} of {}".format(layer.layer_name,
                                                     imported_features.get('current_page'),
                                                     imported_features.get('total_pages')))
            temp_features += imported_features.get('records')

        imported_geojson = self.convert_to_geojson(temp_features, form)

        pulled_record_count = len(imported_geojson.get('features'))

        latest_time = self.get_latest_time(imported_geojson, layer.layer_date)

        filtered_features, filtered_feature_count = filter_features(imported_geojson)

        uploads = []

        if filtered_features:
            media_keys = find_media_keys(filtered_features.get('features'))
            for feature in filtered_features.get('features'):
                for asset_type in {'photos', 'videos', 'audio'}:
                    if feature.get('properties').get(asset_type):
                        for id in feature.get('properties').get(asset_type):
                            print("Getting asset :{}".format(id))
                            feature['properties']['{}_url'.format(asset_type)] += [self.get_asset(id, asset_type)]
                write_feature(feature.get('properties').get('id'), layer, feature)
                uploads += [feature]
            try:
                database_alias = 'fulcrum'
                connections[database_alias]
            except ConnectionDoesNotExist:
                database_alias = None
            upload_to_db(uploads, layer.layer_name, media_keys, database_alias=database_alias)
            publish_layer(layer.layer_name, database_alias=database_alias)
            update_geoshape_layers()
            send_task('fulcrum_importer.tasks.task_update_tiles', (filtered_features, layer.layer_name))
            layer.layer_date = latest_time
            layer.save()
        if pulled_record_count > 0:
            print("RESULTS\n---------------")
            print("Total Records Pulled: {}".format(pulled_record_count))
            print("Total Records Passed Filter: {}".format(filtered_feature_count))
        return

    def get_latest_time(self, new_features, old_layer_time):
        layer_time = old_layer_time
        for new_feature in new_features.get('features'):
            feature_date = time.mktime(parser.parse(new_feature.get('properties').get('updated_at')).timetuple())
            if feature_date > layer_time:
                layer_time = feature_date
        return layer_time

    def update_all_layers(self):
        for form in self.get_forms():
            layer, created = self.ensure_layer(layer_name=form.get('name'), layer_id=form.get('id'))
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
    layers = []
    try:
        archive_name = f.name
    except AttributeError:
        archive_name = f
    file_path = os.path.join(settings.FULCRUM_UPLOAD, archive_name)
    if save_file(f, file_path):
        unzip_file(file_path)
        for folder, subs, files in os.walk(os.path.join(settings.FULCRUM_UPLOAD, os.path.splitext(file_path)[0])):
            for filename in files:
                if '.geojson' in filename:
                    if 'changesets' in filename:
                        # Changesets aren't implemented here, they need to be either handled with this file, and/or
                        # handled implicitly with geogig.
                        continue
                    print("Uploading the geojson file: {}".format(os.path.abspath(os.path.join(folder, filename))))
                    upload_geojson(file_path=os.path.abspath(os.path.join(folder, filename)))
                    layers += [os.path.splitext(filename)[0]]
        delete_folder(os.path.splitext(file_path)[0])
    return layers


def filter_features(features):
    try:
        DATA_FILTERS = settings.DATA_FILTERS
    except AttributeError:
        DATA_FILTERS = []
        pass

    filtered_features = features

    if not DATA_FILTERS:
        return filtered_features, 0
    if filtered_features.get('features'):
        for filter in DATA_FILTERS:
            try:
                filtered_results = requests.post(filter, data=json.dumps(filtered_features)).json()
            except ValueError:
                print("Failed to decode json")
            if filtered_results.get('failed').get('features'):
                print("Some features failed the {} filter.".format(filter))
                # with open('./failed_features.geojson', 'a') as failed_features:
                #     failed_features.write(json.dumps(filtered_results.get('failed')))
            if filtered_results.get('passed').get('features'):
                filtered_features = filtered_results.get('passed')
                filtered_feature_count = len(filtered_results.get('passed').get('features'))
            else:
                filtered_features = None
    else:
        filtered_features = None
        filtered_feature_count = 0

    return filtered_features, filtered_feature_count


def save_file(f, file_path):
    """

    Args:
        f: A url file object.
        file_path:

    Returns:

    """

    if os.path.splitext(file_path)[1] != '.zip':
        return False
    if os.path.exists(file_path):
        return True
    # try:
    if not os.path.exists(settings.FULCRUM_UPLOAD):
        os.mkdir(settings.FULCRUM_UPLOAD)
        # with open(file_path, 'wb+') as destination:
        #     for chunk in f.chunks():
        #         destination.write(chunk)
    # except:
    #     print "Failed to save the file: {}".format(f.name)
    #     return False
    # print "Saved the file: {}".format(f.name)
    return True


def unzip_file(file_path):
    import zipfile

    print("Unzipping the file: {}".format(file_path))
    with zipfile.ZipFile(file_path) as zf:
        zf.extractall(os.path.join(settings.FULCRUM_UPLOAD, os.path.splitext(file_path)[0]))


def delete_folder(file_path):
    import shutil
    shutil.rmtree(file_path)


def delete_file(file_path):
    os.remove(file_path)


def upload_geojson(file_path=None, geojson=None):
    from_file = False
    if file_path and geojson:
        print("upload_geojson() must take file_path OR features")
        return False
    elif geojson:
        geojson = geojson
    elif file_path:
        with open(file_path) as data_file:
            geojson = json.load(data_file)
            from_file = True
    else:
        print("upload_geojson() must take file_path OR features")

    geojson, filtered_count = filter_features(geojson)
    if not geojson:
        return

    if geojson.get('features'):
        features = geojson.get('features')
    else:
        return

    if type(features) != list:
        features = [features]

    uploads = []
    count = 0
    file_basename = os.path.splitext(os.path.basename(file_path))[0]
    layer = write_layer(file_basename)
    media_keys = find_media_keys(features, layer)
    for feature in features:
        for media_key in media_keys:
            if from_file and feature.get('properties').get(media_key):
                urls = []
                if type(feature.get('properties').get(media_key)) == list:
                    asset_uids = feature.get('properties').get(media_key)
                else:
                    asset_uids = feature.get('properties').get(media_key).split(',')
                for asset_uid in asset_uids:
                    asset, created = write_asset_from_file(asset_uid,
                                                           media_keys[media_key],
                                                           os.path.dirname(file_path))
                    if asset:
                        if asset.asset_data:
                            if settings.FILESERVICE_CONFIG.get('url_template'):
                                urls += ['{}{}.{}'.format(settings.FILESERVICE_CONFIG.get('url_template').rstrip("{}"),
                                                          asset_uid,
                                                          get_type_extension(media_keys[media_key]))]
                            else:
                                urls += [asset.asset_data.url]
                    else:
                        urls += [None]
                feature['properties']['{}_url'.format(media_key)] = urls
            elif from_file and not feature.get('properties').get(media_key):
                feature['properties'][media_key] = None
                feature['properties']['{}_url'.format(media_key)] = None
        if not feature.get('properties').get('fulcrum_id'):
            feature['properties']['fulcrum_id'] = feature.get('properties').get('id')

        key_name = 'fulcrum_id'

        write_feature(feature.get('properties').get(key_name),
                      feature.get('properties').get('version'),
                      layer,
                      feature)
        uploads += [feature]
        count += 1

    try:
        database_alias = 'fulcrum'
        connections[database_alias]
    except ConnectionDoesNotExist:
        database_alias = None

    table_name = "fulcrum_{}".format(layer.layer_name)
    if upload_to_db(uploads, table_name, media_keys, database_alias=database_alias):
        publish_layer(table_name, database_alias=database_alias)
        update_geoshape_layers()


def find_media_keys(features, layer=None):
    """
    Args:
        features: An array of features as a dict object.
        layer: The model to update
    Returns:
        A value of keys and types for media fields.
    """
    key_map = {}
    asset_types = {'photos': 'jpg', 'videos': 'mp4', 'audio': 'm4a'}
    for feature in features:
        for prop_key, prop_val in feature.get('properties').iteritems():
            for asset_key in asset_types:
                if '_url' in prop_key:
                    if asset_key in prop_val:
                        media_key = prop_key.rstrip("_url")
                        if not key_map.get(media_key):
                            key_map[media_key] = asset_key
    return key_map


def update_layer_media_keys(key_map=None, layer=None):
    layer_media_keys = json.loads(layer.layer_media_keys)
    for key_map_key in key_map:
        if not layer_media_keys.get(key_map_key):
            layer_media_keys[key_map_key] = key_map.get("key_map_key")
    layer.layer_media_keys = json.dumps(layer_media_keys)
    layer.save()


def write_layer(name, date=None):
    """
    Args:
        name: An SQL compatible string.
        date: An integer representing the date

    Returns:
        The layer model object.
    """
    if not date:
        date = time.mktime(datetime.now().timetuple())
    layer, layer_created = Layer.objects.get_or_create(layer_name=name, defaults={'layer_date': date})
    return layer


def write_feature(key, version, layer, feature_data):
    """

    Args:
        key: A unique key as a string, presumably the Fulcrum UID.
        version: A version number for the feature as an integer, usually provided by Fulcrum.
        app: The layer model object, which represents the Fulcrum App (AKA the layer).
        feature_data: The actual feature data as a dict, mapped like a geojson.

    Returns:
        The feature model object.
    """
    from .models import Feature
    import json
    feature, feature_created = Feature.objects.get_or_create(feature_uid=key,
                                                             feature_version=version,
                                                             defaults={'layer': layer,
                                                                       'feature_data': json.dumps(feature_data)})
    return feature


def write_asset_from_url(asset_uid, asset_type, url=None):
    """

    Args:
        asset_uid: The assigned ID from Fulcrum.
        asset_type: A string of 'Photos', 'Videos', or 'Audio'.
        url: A Url where the asset can be downloaded, if blank it tries to download
        from the fulcrum site based on the UID and type.

    Returns:
        The new url (provided by the django model FileField) for the asset.
    """

    asset, created = Asset.objects.get_or_create(asset_uid=asset_uid, asset_type=asset_type)
    if created:
        if not os.path.exists(settings.MEDIA_ROOT):
            os.mkdir(settings.MEDIA_ROOT)
        with NamedTemporaryFile() as temp:
            if not url:
                url = 'https://api.fulcrumapp.com/api/v2/{}/{}.{}'.format(asset.asset_type, asset.asset_uid,
                                                                          get_type_extension(asset_type))
            response = requests.get(url, headers={'X-ApiToken': settings.FULCRUM_API_KEY})
            for content in response.iter_content(chunk_size=1028):
                temp.write(content)
            temp.flush()
            print get_type_extension(asset_type)
            if get_type_extension(asset_type) == 'jpg':
                if is_valid_photo(File(temp)):
                    asset.asset_data.save(asset.asset_uid, File(temp))
                else:
                    asset.delete()
                    return None
            else:
                asset.asset_data.save(asset.asset_uid, File(temp))
    else:
        asset = Asset.objects.get(asset_uid=asset_uid)
    if asset.asset_data:
        # if settings.FILESERVICE_CONFIG.get('url_template').rstrip("{}"):
        #     return '{}{}.{}'.format(settings.FILESERVICE_CONFIG.get('url_template').rstrip("{}"), asset_uid,
        #                             get_type_extension(asset_type))
        # else:
        return asset.asset_data.url


def write_asset_from_file(asset_uid, asset_type, file_dir):
    """

    Args:
        asset_uid: The assigned ID from Fulcrum.
        asset_type: A string of 'Photos', 'Videos', or 'Audio'.
        url: A Url where the asset can be downloaded, if blank it tries to download
        from the fulcrum site based on the UID and type.

    Returns:
        A tuple of the asset model object, and a boolean representing 'was created'.
    """
    from django.core.files import File
    import os
    from .models import Asset, get_type_extension
    from django.conf import settings

    file_path = os.path.join(file_dir, '{}.{}'.format(asset_uid, get_type_extension(asset_type)))
    asset, created = Asset.objects.get_or_create(asset_uid=asset_uid, asset_type=asset_type)
    if created:
        if not os.path.exists(settings.MEDIA_ROOT):
            os.mkdir(settings.MEDIA_ROOT)
        if os.path.isfile(file_path):
            with open(file_path) as open_file:
                asset.asset_data.save(os.path.splitext(os.path.basename(file_path))[0],
                                      File(open_file))
        else:
            print("The file {} was not found, and is most likely missing from the archive.".format(file_path))
            return None, False
    return asset, created


def is_valid_photo(photo_file):
    # https://gist.github.com/erans/983821#file-get_lat_lon_exif_pil-py-L40
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    im = Image.open(photo_file)
    info = im._getexif()
    properties = {}
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]

                properties[(decoded)] = gps_data
            elif decoded != "MakerNote":
                properties[(decoded)] = (value)

        if "GPSInfo" in properties:
            gps_info = properties["GPSInfo"]

            try:
                gps_lat = gps_info["GPSLatitude"]
                gps_lat_ref = gps_info["GPSLatitudeRef"]
                gps_long = gps_info["GPSLongitude"]
                gps_long_ref = gps_info["GPSLongitudeRef"]

            except:
                print "Could not get lat/long"
                return False

            lat = convert_to_degrees(gps_lat)
            if gps_lat_ref != "N":
                lat = 0 - lat

            long = convert_to_degrees(gps_long)
            if gps_lat_ref != "E":
                long = 0 - long

            coords = [round(lat, 6), round(long, 6)]

            features = []
            feature = {"type": "Feature",
                       "geometry": {"type": "Point",
                                    "coordinates": [coords[1], coords[0]]
                                    },
                       "properties": properties
                       }
            features += [feature]
            geojson = {"type": "FeatureCollection", "features": features}
            filtered_features, count = filter_features(geojson)
            if filtered_features.get('features'):
                print "Photo passed the filter"
                return True
            else:
                print "Photo did not pass the filter"
                return False
        else:
            print "No GPS info found"
            return True
    else:
        print "No EXIF Info"
        return True


def convert_to_degrees(value):
    d0 = value[0][0]
    d1 = value[0][1]
    d = float(d0) / float(d1)

    m0 = value[1][0]
    m1 = value[1][1]
    m = float(m0) / float(m1)

    s0 = value[2][0]
    s1 = value[2][1]
    s = float(s0) / float(s1)

    return d + (m / 60.0) + (s / 3600.0)


def update_geoshape_layers():
    """
        Makes a subprocess call to tell geoshape to make available any new postgis layers.

    Returns:
        None
    """
    try:
        GEOSHAPE_SERVER = settings.GEOSHAPE_SERVER
        GEOSHAPE_USER = settings.GEOSHAPE_USER
        GEOSHAPE_PASSWORD = settings.GEOSHAPE_PASSWORD
    except AttributeError:
        GEOSHAPE_SERVER = None
        pass
    if GEOSHAPE_SERVER:
        # http://stackoverflow.com/questions/13567507/passing-csrftoken-with-python-requests
        client = requests.session()
        URL = 'https://{}/account/login'.format(GEOSHAPE_SERVER)
        client.get(URL, verify=False)
        csrftoken = client.cookies['csrftoken']
        login_data = dict(username=GEOSHAPE_USER, password=GEOSHAPE_PASSWORD, csrfmiddlewaretoken=csrftoken,
                          next='/gs/updatelayers/')
        client.post(URL, data=login_data, headers=dict(Referer=URL), verify=False)
    else:
        python_bin = '/var/lib/geonode/bin/python'
        manage_script = '/var/lib/geonode/rogue_geonode/manage.py'
        env = {}
        execute = [python_bin,
                   manage_script,
                   'updatelayers',
                   '--ignore-errors',
                   '--remove-deleted',
                   '--skip-unadvertised']
        DEVNULL = open(os.devnull, 'wb')
        subprocess.Popen(execute, env=env, stdout=DEVNULL, stderr=DEVNULL)


def upload_to_db(feature_data, table, media_keys, database_alias=None):
    """

    Args:
        feature_data: A dict mapped as a geojson.
        table: The name of the layer being added. If exists it will data will be appended,
            else a new table will be created.
        media_keys: A dict where the key is the name of a properties field containing
            a media file, and the value is the type (i.e. {'bldg_pic': 'photos'})
        database_alias: Alias of database in the django DATABASES dict.
    Returns:
        True, if no errors occurred.
    """

    remove_urls = []
    if not feature_data:
        return False

    try:
        sitename = settings.SITENAME
    except AttributeError:
        sitename = None

    if sitename == 'GeoSHAPE':
        feature_data = prepare_features_for_geoshape(feature_data, media_keys=media_keys)

    key_name = 'fulcrum_id'

    # Use ogr2ogr to create a table and add an index, before any non unique values are added.
    if not table_exists(table=table, database_alias=database_alias):
        ogr2ogr_geojson_to_db(geojson_file=features_to_file(feature_data[0]),
                              database_alias=database_alias,
                              table=table)
        add_unique_constraint(database_alias=database_alias, table=table, key_name=key_name)
        feature_data = feature_data[1:]

    # Sort the data in memory before making a ton of calls to the server.
    feature_data, non_unique_features = get_duplicate_features(features=feature_data, properties_id='fulcrum_id')

    # Try to upload the presumed unique values in bulk, repeatedly.
    uploaded = False
    while not uploaded:
        if not feature_data:
            break
        feature_data, non_unique_feature_data = check_db_for_features(feature_data,
                                                                      table,
                                                                      database_alias=database_alias)
        if non_unique_feature_data:
            update_db_features(non_unique_feature_data, table, database_alias=database_alias)

        if not ogr2ogr_geojson_to_db(geojson_file=features_to_file(feature_data),
                                     database_alias=database_alias,
                                     table=table):
            continue

        uploaded = True

    # Finally update one by one all of the features we know are in the database
    if non_unique_feature_data:
        update_db_features(non_unique_features, table, database_alias=database_alias)
    return True


def prepare_features_for_geoshape(feature_data, media_keys=None):

    if not feature_data:
        return None

    remove_urls = []
    for feature in feature_data:
        for feat_prop in feature.get('properties'):
            if not feature.get('properties').get(feat_prop):
                continue
            if type(feature.get('properties').get(feat_prop)) == list:
                type_ext = get_type_extension(feat_prop)
                if type_ext:
                    props = []
                    for prop in feature.get('properties').get(feat_prop):
                        props += ['{}.{}'.format(prop, type_ext)]
                    feature['properties'][feat_prop] = props
                try:
                    feature['properties'][feat_prop] = json.dumps(feature['properties'][feat_prop])
                except TypeError:
                    # Null arrays are fine.
                    continue

        for media_key, media_val in media_keys.iteritems():
            try:
                url_prop = "{}_url".format(media_key)
                del feature['properties'][url_prop]
            except KeyError:
                print("ERROR: Could not delete the key {}.".format(url_prop))
                pass
            media_ext = get_type_extension(media_val)
            if media_val == 'audio':
                #Because of maploom
                media_val == 'audios'
            if media_val != media_key:
                new_key = '{}_{}'.format(media_val, media_key)
            else:
                new_key = media_val
                feature['properties']['caption_{}'.format(media_key)] = feature['properties']['{}_caption'.format(media_key)]
                try:
                    del feature['properties']['{}_caption'.format(media_key)]
                except KeyError:
                    print "Could not delete key {}.".format('{}_caption'.format(media_key))

            if feature.get('properties').get(media_key):
                media_assets = ["{}.{}".format(s, media_ext)
                                for s in feature.get('properties').get(media_key).split(',')]
                feature['properties'][new_key] = json.dumps(media_assets)

    return feature_data


def features_to_file(features, file_path=None):
    if not file_path:
        try:
            file_path = os.path.join(settings.FULCRUM_UPLOAD, 'temp.json')
            file_path = '/'.join(file_path.split('\\'))
        except AttributeError:
            print "ERROR: Unable to write features_to_file because " \
                  "file_path AND settings.FULCRUM_UPLOAD are not defined."

    if type(features) == list:
        feature_collection = {"type": "FeatureCollection", "features": features}
    else:
        feature_collection = {"type": "FeatureCollection", "features": [features]}

    with open(file_path, 'w') as open_file:
        open_file.write(json.dumps(feature_collection))

    return file_path


def get_pg_conn_string(database_alias=None):
    if database_alias:
        db_conn = connections[database_alias]
    else:
        db_conn = connection

    return "host={host} " \
           "port={port} " \
           "dbname={database} " \
           "user={user} " \
           "password={password}".format(host=db_conn.settings_dict.get('HOST'),
                                        port=db_conn.settings_dict.get('PORT'),
                                        database=db_conn.settings_dict.get('NAME'),
                                        user=db_conn.settings_dict.get('USER'),
                                        password=db_conn.settings_dict.get('PASSWORD'))


def ogr2ogr_geojson_to_db(geojson_file, database_alias=None, table=None, fid=None):

    if database_alias:
        db_conn = connections[database_alias]
    else:
        db_conn = connection

    if 'postgis' in db_conn.settings_dict.get('ENGINE') or 'postgres' in db_conn.settings_dict.get('ENGINE'):
        db_format = 'PostgreSQL'
        dest = "PG:{}".format(get_pg_conn_string(database_alias))
    else:
        db_format = 'SQLite'
        sqlite_file = connection.settings_dict.get('NAME')
        dest = '{}'.format(sqlite_file)

    execute_append = ['',
                      '-f', db_format,
                      '-update',
                      '-append',
                      '-skipfailures',
                      dest,
                      '{}'.format(geojson_file),
                      '-nln', table]

    with transaction.atomic():
        ogr2ogr.main(execute_append)


def add_unique_constraint(database_alias=None, table=None, key_name=None):
    if not is_alnum(table):
        return None

    if database_alias:
        db_conn = connections[database_alias]
    else:
        db_conn = connection

    cur = db_conn.cursor()

    if 'sqlite' in db_conn.settings_dict.get('NAME'):
        query = "CREATE UNIQUE INDEX unique_{key_name} on {table}({key_name})".format(table=table, key_name=key_name)
    else:
        query = "ALTER TABLE {} ADD UNIQUE({});".format(table, key_name)

    try:
        with transaction.atomic():
            cur.execute(query)
    except ProgrammingError:
        print("Unable to add a key because {} was not created yet.".format(table))
    finally:
        cur.close()


def table_exists(database_alias=None, table=None):
    if not is_alnum(table):
        return None

    if database_alias:
        db_conn = connections[database_alias]
    else:
        db_conn = connection

    cur = db_conn.cursor()

    query = "select * from {};".format(table)

    try:
        with transaction.atomic():
            cur.execute(query)
        does_table_exist = True
    except ProgrammingError:
        does_table_exist = False
    except OperationalError:
        does_table_exist = False
    finally:
        cur.close()
    return does_table_exist


def check_db_for_features(features, table, database_alias=None):
    if not features:
        return None
    db_features = get_all_db_features(table, database_alias=database_alias)
    unique_features = []
    non_unique_features = []
    for feature in features:
        if check_db_for_feature(feature, db_features):
            non_unique_features += [feature]
        else:
            unique_features += [feature]
    return unique_features, non_unique_features


def get_duplicate_features(features, properties_id=None):
    if not features or not properties_id:
        print "get_duplicate_features requires features and a properties_id"
        return None, None
    if len(features) == 1:
        return features, None

    sorted_features = sort_features(sort_features(features, 'version'), properties_id)

    unique_features = [sorted_features[0]]
    non_unique_features = []
    for feature in sorted_features[1:]:
        if feature.get('properties').get(properties_id) == unique_features[-1].get('properties').get(properties_id):
            non_unique_features += [feature]
        else:
            unique_features += [feature]
    return unique_features, non_unique_features


def sort_features(features, properties_key=None):
    return sorted(features, key=lambda (feature): feature['properties'][properties_key])


def check_db_for_feature(feature, db_features=None):
    fulcrum_id = feature.get('properties').get('fulcrum_id')
    if not db_features:
        return None
    if db_features.get(fulcrum_id):
        # While it is unlikely that the database would have a newer version than the one being presented.
        # Older versions should be rejected.  If they fail to be handled at least they won't overwrite a
        # more current value.
        if db_features.get('version') > feature.get('properties').get('version'):
            return "reject"
        feature['ogc_fid'] = db_features.get('ogc_fid')
        return feature
    return None


def get_all_db_features(layer, database_alias=None):
    if not is_alnum(layer):
        return None

    if database_alias:
        cur = connections[database_alias].cursor()
    else:
        cur = connection.cursor()

    query = "SELECT * FROM {};".format(layer)
    try:
        with transaction.atomic():
            cur.execute(query)
            features = {}
            fulcrum_id_index = get_column_index('fulcrum_id', cur)
            version_index = get_column_index('version', cur)
            for feature in cur:
                features[feature[fulcrum_id_index]] = {'fulcrum_id': feature[fulcrum_id_index],
                                                       'version': feature[version_index],
                                                       'feature_data': feature}
    except ProgrammingError:
        return None
    finally:
        cur.close()

    return features


def get_column_index(name, cursor):
    if not cursor.description:
        return
    for ind, val in enumerate([desc[0] for desc in cursor.description]):
        if val == name:
            return ind


def update_db_features(features, layer, database_alias=None, pg_conn_string=None, sqlite_file=None):
    if type(features) != list:
        features = [features]
    for feature in features:
        update_db_feature(feature,
                          layer,
                          database_alias=database_alias,
                          pg_conn_string=pg_conn_string,
                          sqlite_file=None)


def update_db_feature(feature, layer, database_alias=None, pg_conn_string=None, sqlite_file=None):
    if not is_alnum(layer):
        return

    if not feature:
        return

    if not feature.get('ogc_fid'):
        check_feature = check_db_for_feature(feature, get_all_db_features(layer, database_alias=database_alias))
        if not check_feature:
            print("WARNING: An attempted to update a feature that doesn't exist in the database.")
            print(" A new entry will be created for the feature {}.".format(feature))
        elif check_feature == 'reject':
            print("WARNING: An attempt was made to update a feature with an older version. "
                  "The feature {} was rejected.".format(feature))
        else:
            feature = check_feature

    delete_db_feature(feature,
                          layer=layer,
                          database_alias=database_alias)

    ogr2ogr_geojson_to_db(geojson_file=features_to_file(feature),
                          database_alias=database_alias,
                          table=layer)


def delete_db_feature(feature, layer, database_alias=None):
    if not is_alnum(layer):
        return

    if not feature:
        return

    if not feature.get('ogc_fid'):
        check_feature = check_db_for_feature(feature, get_all_db_features(layer, database_alias=database_alias))
        if not check_feature:
            print("WARNING: An attempt was made to delete a feature "
                  "that doesn't exist in the database (or have an OGC_FID.")
        elif check_feature == 'reject':
            print("WARNING: An attempt was made to update a feature with an older version. "
                  "The feature {} was rejected.".format(feature))
    if database_alias:
        cur = connections[database_alias].cursor()
    else:
        cur = connection.cursor()

    query = "DELETE FROM {} WHERE fulcrum_id = '{}';".format(layer, feature.get('properties').get('fulcrum_id'))

    try:
        cur.execute(query)
    except ProgrammingError:
        print("Unable to delete the feature:")
        print(str(feature))
        print("It is most likely not in the database or missing a fulcrum_id.")
    finally:
        cur.close()


def remove_items(iterable, remove=[]):
    if type(iterable) == list:
        items = []
        for item in iterable:
            if item not in remove:
                items += [item]
    else:
        items = {}
        for item in iterable:
            if item not in remove:
                items[item] = iterable[item]
    return items


def is_alnum(data):
    """
    Used to ensure that only 'safe' data can be used to query data.
    This should never be a problem since Fulcrum implements the same restrictions.

    Args:
        data: String of data to be tested.

    Returns:
        True: if data is only alphanumeric or '_' chars.
    """
    if re.match(r'\w+$', data):
        return True


def publish_layer(layer_name, geoserver_base_url=None, database_alias=None):
    """
    Args:
        layer_name: The name of the table that already exists in postgis,
         to be published as a layer in geoserver.

    Returns:
        None
    """

    if not geoserver_base_url:
        geoserver_base_url = settings.GEOSERVER_URL.rstrip('/')
        # geoserver_base_url = "http://localhost:8080/geoserver"

    url = "{}/rest".format(geoserver_base_url)
    workspace_name = "geonode"
    workspace_uri = "http://www.geonode.org/"
    if database_alias:
        datastore_name = connections[database_alias].settings_dict.get('NAME')
        database = connections[database_alias].settings_dict.get('NAME')
    else:
        datastore_name = connection.settings_dict.get('NAME')
        database = connection.settings_dict.get('NAME')
    host = settings.DATABASE_HOST
    port = settings.DATABASE_PORT
    password = settings.DATABASE_PASSWORD
    db_type = "postgis"
    user = settings.DATABASE_USER
    srs = "EPSG:4326"

    if not password:
        print("Geoserver can not be updated without a database password provided in the settings file.")

    cat = Catalog(url)

    # Check if local workspace exists and if not create it
    workspace = cat.get_workspace(workspace_name)

    if workspace is None:
        current_workspace = cat.create_workspace(workspace_name, workspace_uri)
        print "Workspace " + workspace_name + " created."

    # Get list of datastores
    datastores = cat.get_stores()

    datastore = None
    # Check if remote datastore exists on local system
    for ds in datastores:
        if ds.name.lower() == datastore_name.lower():
            datastore = ds

    if not datastore:
        datastore = cat.create_datastore(datastore_name, workspace_name)
        datastore.connection_parameters.update(port=port,
                                               host=host,
                                               database=database,
                                               passwd=password,
                                               user=user,
                                               dbtype=db_type)
        cat.save(datastore)

    # Check if remote layer already exists on local system
    layers = cat.get_layers()

    layer = None
    for lyr in layers:
        if lyr.resource.name.lower() == layer_name.lower():
            layer = lyr

    if not layer:
        # Publish remote layer
        layer = cat.publish_featuretype(layer_name.lower(), datastore, srs, srs=srs)
        return layer, True
    else:
        return layer, False
    return None, False


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]
