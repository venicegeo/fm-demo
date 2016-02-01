from django.conf import settings
from django.core.cache import cache
from kafka import KafkaConsumer
from piazza_consumer.models import Listener, Message, Key, Asset
from threading import Thread
import time
import json

class Consumer:
    def __init__(self, name='consumer', listener_topics=None):
        print "Creating consumer " + name + "(" + str(id(self)) + ")"

        self.name = name
        cache.set(consumer_cache_name(self.name), {"running": False, "alive": False})
        if listener_topics:
            self.listener_topics = listener_topics
        else:
            self.listener_topics = get_listener_topics()
        self.connection_string = settings.KAFKA_HOST + " : " + settings.KAFKA_PORT
        self.thread = None
        if self.listener_topics:
            self.thread = Thread(target=self.consume)
            self.thread.name = name
            self.thread.daemon = True
            start(name)
            self.thread.start()

        print "Consumer initialized."

    def __str__(self):
        return "Consumer object containing the following listeners:\n" + str(self.listener_topics)

    def consume(self):
        consumer = None
        try:
            print "\nCONSUMER TOPICS = " + str(self.listener_topics)
            consumer = KafkaConsumer(*self.listener_topics,
                                     client_id=self.name,
                                     group_id='kafka',
                                     bootstrap_servers=self.connection_string,
                                     auto_offset_reset='smallest')
            self._set_alive(True)
        except Exception as e:
            print "A consumer couldn't be created."
            print e
        while is_running(self.name):
            for message in consumer.fetch_messages():
                asset_success = True
                message_success = True
                if not is_running(self.name):
                    break
                try:
                    try:
                        key = Key.objects.get(listener=Listener.objects.get(listener_topic=message.topic),
                                              listener_key=message.key)
                        feature_data = json.loads(message.value)
                        for asset_type in ['photos', 'videos', 'sounds']:
                            if feature_data.get('properties').get(asset_type):
                                import urllib2
                                urls = []
                                for index, value in enumerate(feature_data.get('properties').get(asset_type)):
                                    asset, created = write_asset(key, value, asset_type, feature_data.get('properties').get('{}_url'.format(asset_type))[index-1])
                                    if not asset:
                                        asset_success = False
                                    else:
                                        print "Asset {} was written.".format(value)
                                    urls += [asset.asset_data.url]
                                feature_data['properties']['{}_url'.format(asset_type)] = urls
                                print "URLS:" + str(urls)
                            else:
                                feature_data['properties'][asset_type] = None
                                feature_data['properties']['{}_url'.format(asset_type)] = None
                        if not write_message(key, json.dumps(feature_data)):
                            message_success = False
                        else:
                            print "Message {} was written.".format(feature_data.get('properties').get('city'))
                            upload(feature_data, 'geoshape', 'gE8rCp5cSmUKM8kX', 'fulcrum', 'starbucks')
                    except Exception as e:
                        if 'DoesNotExist' in e:
                            continue
                        else:
                            print e
                            message_success = False

                except KeyboardInterrupt:
                    break
                if message_success and asset_success:
                    consumer.task_done(message)
                    consumer.commit()
        consumer.close()
        self._set_alive(False)

    def ensure_topic(self, topic):
        from kafka import KafkaClient
        client = KafkaClient(bootstrap_servers=self.connection_string)
        client.ensure_topic_exists(topic)

    def _set_alive(self, bool):
        consumer = cache.get(consumer_cache_name(self.name))
        if consumer:
            consumer['alive'] = bool
            cache.set(consumer_cache_name(self.name), consumer)


def is_alive(consumer_name):
    consumer = cache.get(consumer_cache_name(consumer_name))
    return consumer.get("alive")


def start(consumer_name):
    consumer = cache.get(consumer_cache_name(consumer_name))
    consumer["running"] = True
    cache.set(consumer_cache_name(consumer_name), consumer)


def stop(consumer_name):
    consumer = cache.get(consumer_cache_name(consumer_name))
    consumer["running"] = False
    cache.set(consumer_cache_name(consumer_name), consumer)


def is_running(consumer_name):
    consumer = cache.get(consumer_cache_name(consumer_name))
    if consumer:
        if consumer.get("running"):
            return True
    return False


def create_consumer(consumer_name, listener_topics=None):
    consumer = Consumer(name=consumer_name, listener_topics=listener_topics)
    return consumer


def update_consumer(consumer_name):
    """
    This currently just notifies the old consumer to close, and/or creates a new one.
    Args:
        consumer_name:

    Returns: nothing

    """
    print "Updating: " + str(consumer_name)
    if cache.get(consumer_cache_name(consumer_name)):
        if is_alive(consumer_name):
            stop(consumer_name)
            while is_alive(consumer_name):
                time.sleep(.01)
    create_consumer(consumer_name)


def write_listener(consumer_name, topic, key):
    listener, listener_created = Listener.objects.get_or_create(listener_topic=topic)
    if listener_created:
        update_consumer(consumer_name)
    return Key.objects.get_or_create(listener=listener, listener_key=key)


def write_message(key, message):
    print "Writing message for : (" + str(key.listener_key) + ") " + message
    return Message.objects.get_or_create(key=key, message_body=message)


def write_asset(key, asset_uid, asset_type, asset_data_url):
    from django.core.files import File
    from django.core.files.temp import NamedTemporaryFile
    import urllib2
    from mimetypes import guess_extension

    img_temp = NamedTemporaryFile()
    response = urllib2.urlopen(asset_data_url)
    img_temp.write(response.read())
    file_type = response.info().maintype
    img_temp.flush()
    file_ext = {'image': 'jpg'}

    print "Writing asset for : (" + str(key.listener_key) + ")"
    asset, created = Asset.objects.get_or_create(asset_uid=asset_uid, asset_type=asset_type)

    asset.asset_data.save('{}.{}'.format(asset_uid, file_ext.get(file_type)), File(img_temp))
    return asset, created


def consumer_cache_name(consumer_name):
    return consumer_name + '_consumer'


def get_listener_topics():
    listeners = Listener.objects.all()
    listener_topics = []
    for listener in listeners:
        listener_topics += [listener.listener_topic]
    return listener_topics


def upload(feature_data, user, password, database, table):
    import json
    import subprocess
    import os.path

    for property in feature_data.get('properties'):
        if type(feature_data.get('properties').get(property)) == list:
            feature_data['properties'][property] = ','.join(feature_data['properties'][property])

    temp_file = os.path.abspath('./temp.json')
    temp_file = '/'.join(temp_file.split('\\'))
    with open(temp_file, 'w') as open_file:
        open_file.write(json.dumps(feature_data))
    out = ""
    conn_string = "host=localhost dbname={} user={} password={}".format(database, user, password)
    execute = ['ogr2ogr',
               '-f', 'PostgreSQL',
               '-append',
               'PG:"{}"'.format(conn_string),
               temp_file,
               '-nln', table
               ]
    try:
        out = subprocess.call(' '.join(execute), shell=True)
        print "Uploaded the feature {} to postgis.".format(feature_data.get('properties').get('city'))
    except subprocess.CalledProcessError:
        print "Failed to call:\n" + ' '.join(execute)
        print out


def main():
    pass


if __name__ == "__main__":
    pass
