from fulcrum import Fulcrum
from django.conf import settings
from django.core.cache import cache
import requests
from .models import Layer
from dateutil import parser
from celery.execute import send_task


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
        from .tasks import update_tiles
        layer = Layer.objects.get(layer_uid=form.get('id'))
        if not layer:
            print("Layer {} doesn't exist.".format(form.get('id')))

        temp_features = []
        if layer.layer_date:
            url_params={'form_id': layer.layer_uid,'updated_since': layer.layer_date+1}
        else:
            url_params={'form_id': layer.layer_uid}
        imported_features = self.conn.records.search(url_params=url_params)
        if imported_features.get('current_page') > imported_features.get('total_pages'):
            print("Received {} page 0 of 0".format(layer.layer_name))
        else:
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
            for feature in filtered_features.get('features'):
                for asset_type in {'photos', 'videos', 'audio'}:
                    if feature.get('properties').get(asset_type):
                        for id in feature.get('properties').get(asset_type):
                            print("Getting asset :{}".format(id))
                            feature['properties']['{}_url'.format(asset_type)] += [self.get_asset(id, asset_type)]
                write_feature(feature.get('properties').get('id'), layer, feature)
                uploads += [feature]
            print "FULCRUM_DATABASE_NAME: {}".format(settings.FULCRUM_DATABASE_NAME)
            if settings.FULCRUM_DATABASE_NAME:
                upload_to_postgis(uploads, settings.DATABASE_USER, settings.FULCRUM_DATABASE_NAME, layer.layer_name)
                publish_layer(layer.layer_name)
                update_geoshape_layers()
                send_task('fulcrum_importer.tasks.task_update_tiles',(filtered_features, layer.layer_name))
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
                    print("Uploading the geojson file: {}".format(os.path.abspath(os.path.join(folder, filename))))
                    upload_geojson(file_path=os.path.abspath(os.path.join(folder, filename)))
                    layers += [os.path.splitext(filename)[0]]
        delete_folder(os.path.splitext(file_path)[0])
    return layers


def filter_features(features):
    import json

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
            if filtered_results.get('failed'):
                print("Some features failed the {} filter.".format(filter))
                # with open('./failed_features.geojson', 'a') as failed_features:
                #     failed_features.write(json.dumps(filtered_results.get('failed')))
            if filtered_results.get('passed'):
                filtered_features = filtered_results.get('passed')
                filtered_feature_count = len(filtered_results.get('passed').get('features'))
            else:
                filtered_features = None
    else:
        filtered_features = None
        filtered_feature_count = 0

    return filtered_features, filtered_feature_count


def save_file(f, file_path):
    from django.conf import settings
    import os
    if os.path.splitext(file_path)[1] != '.zip':
        return False
    if os.path.exists(file_path):
        return True
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

    print("Unzipping the file: {}".format(file_path))
    with zipfile.ZipFile(file_path) as zf:
        zf.extractall(os.path.join(settings.FULCRUM_UPLOAD, os.path.splitext(file_path)[0]))

def delete_folder(file_path):
    import shutil
    shutil.rmtree(file_path)


def delete_file(file_path):
    import os
    os.remove(file_path)


def upload_geojson(file_path=None, geojson=None):
    import json
    from django.conf import settings
    from.models import get_type_extension
    import os

    from_file = False
    if file_path and geojson:
        raise "upload_geojson() must take file_path OR features"
        return False
    elif geojson:
        geojson = geojson
    elif file_path:
        with open(file_path) as data_file:
            geojson = json.load(data_file)
            from_file = True
    else:
        raise "upload_geojson() must take file_path OR features"

    print geojson
    geojson, filtered_count = filter_features(geojson)
    if not geojson:
        return
    if geojson.get('features'):
        features = geojson.get('features')
    else:
        return

    uploads = []
    count = 0
    for feature in features:
        for asset_type in ['photos', 'videos', 'audio']:
            if from_file and feature.get('properties').get(asset_type):
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
                            if settings.FILESERVICE_CONFIG.get('url_template'):
                                print asset.asset_data.path
                                urls += ['{}{}.{}'.format(settings.FILESERVICE_CONFIG.get('url_template').rstrip("{}"),
                                                          asset_uid,
                                                          get_type_extension(asset_type))]
                            else:
                                urls += [asset.asset_data.url]
                    else:
                        urls += ['Import Needed.']
                feature['properties']['{}_url'.format(asset_type)] = urls
            elif from_file and not feature.get('properties').get(asset_type):
                feature['properties'][asset_type] = None
                feature['properties']['{}_url'.format(asset_type)] = None
        layer = write_layer(os.path.basename(os.path.dirname(file_path)))
        if feature.get('properties').get('fulcrum_id'):
            key_name = 'fulcrum_id'
        else:
            key_name = 'id'
        write_feature(feature.get('properties').get(key_name),
                      layer,
                      feature)
        uploads += [feature]
        count += 1
    upload_to_postgis(uploads, settings.DATABASE_USER, settings.FULCRUM_DATABASE_NAME, os.path.splitext(os.path.basename(file_path))[0])
    publish_layer(layer.layer_name)
    update_geoshape_layers()


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
    from .models import Asset, get_type_extension
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
            for content in response.iter_content(chunk_size=1028):
                temp.write(content)
            temp.flush()
            if is_valid_photo(File(temp)):
                asset.asset_data.save(asset.asset_uid, File(temp))
            else:
                asset.delete()
                return None
    else:
        print "Asset already created."
        asset = Asset.objects.get(asset_uid=asset_uid)
    if asset.asset_data:
        if settings.FILESERVICE_CONFIG.get('url_template').rstrip("{}"):
            return'{}{}.{}'.format(settings.FILESERVICE_CONFIG.get('url_template').rstrip("{}"),asset_uid,get_type_extension(asset_type))
        else:
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
            decoded = TAGS.get(tag,tag)
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
    import subprocess
    import os

    try:
        GEOSHAPE_SERVER = settings.GEOSHAPE_SERVER
        GEOSHAPE_USER = settings.GEOSHAPE_USER
        GEOSHAPE_PASSWORD = settings.GEOSHAPE_PASSWORD
    except AttributeError:
        GEOSHAPE_SERVER = None
        pass
    if GEOSHAPE_SERVER:
        #http://stackoverflow.com/questions/13567507/passing-csrftoken-with-python-requests
        client = requests.session()
        URL = 'https://{}/account/login'.format(GEOSHAPE_SERVER)
        client.get(URL, verify=False)
        csrftoken = client.cookies['csrftoken']
        login_data = dict(username=GEOSHAPE_USER, password=GEOSHAPE_PASSWORD, csrfmiddlewaretoken=csrftoken, next='/gs/updatelayers/')
        client.post(URL, data=login_data, headers=dict(Referer=URL), verify=False)
    else:
        python_bin =  '/var/lib/geonode/bin/python'
        manage_script = '/var/lib/geonode/rogue_geonode/manage.py'
        env = {}
        execute = [python_bin,
                   manage_script,
                   'updatelayers',
                   '--ignore-errors',
                   '--remove-deleted',
                   '--skip-unadvertised']
        DEVNULL = open(os.devnull, 'wb')
        subprocess.Popen(execute, env=env,stdout=DEVNULL, stderr=DEVNULL)


def upload_to_postgis(feature_data, user, database, table):
    import json
    import subprocess
    import os
    from .models import get_type_extension
    remove_urls = []
    if not feature_data:
        return
    for feature in feature_data:
        for property in feature.get('properties'):
            if not feature.get('properties').get(property):
                continue
            if type(feature.get('properties').get(property)) == list:
                type_ext = get_type_extension(property)
                if type_ext:
                    props = []
                    for prop in feature.get('properties').get(property):
                        props += ['{}.{}'.format(prop, type_ext)]
                    feature['properties'][property] = props
                try:
                    feature['properties'][property] = json.dumps(feature['properties'][property])
                except TypeError:
                    #Null arrays are fine.
                    continue
            if 'url' in str(property):
                remove_urls += [property]
        for prop in remove_urls:
            try:
                del feature['properties'][prop]
            except KeyError:
                pass
        if not feature.get('id'):
            if feature.get('properties').get('name'):
                feature['id'] = feature.get('properties').get('name')
            elif feature.get('properties').get('title'):
                feature['id'] = feature.get('properties').get('title')

    temp_file = os.path.join(settings.FULCRUM_UPLOAD, 'temp.json')
    temp_file = '/'.join(temp_file.split('\\'))

    feature_collection = {"type": "FeatureCollection", "features": feature_data}

    with open(temp_file, 'w') as open_file:
        open_file.write(json.dumps(feature_collection))
    conn_string = "dbname={} user={}".format(database, user)
    execute_append = ['ogr2ogr',
                      '-f', 'PostgreSQL',
                      '-append',
                      '-skipfailures',
                      'PG:"{}"'.format(conn_string),
                      temp_file,
                      '-nln', table]

    if feature_data[0].get('properties').get('fulcrum_id'):
        key_name = 'fulcrum_id'
    else:
        key_name = 'id'
    execute_alter = ['/usr/bin/psql', '-d', 'fulcrum', '-c', "ALTER TABLE {} ADD UNIQUE({});".format(table, key_name)]
    try:
        DEVNULL = open(os.devnull, 'wb')
        out = subprocess.Popen(' '.join(execute_append), shell=True, stdout=DEVNULL, stderr=DEVNULL)
        out = subprocess.Popen(execute_alter, stdout=DEVNULL, stderr=DEVNULL)

    except subprocess.CalledProcessError:
        pass


def publish_layer(layer_name):
    from geoserver.catalog import Catalog

    url = "http://localhost:8080/geoserver/rest"
    workspace_name = "geonode"
    workspace_uri = "http://www.geonode.org/"
    datastore_name = "{}".format(settings.FULCRUM_DATABASE_NAME)
    host = "localhost"
    port = "5432"
    database = settings.FULCRUM_DATABASE_NAME
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
        # from multiprocessing import Process
        # p = Process(target=update_geoshape_layers())
        # p.start()
