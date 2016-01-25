from django.conf import settings
from django.apps import apps
from django.core.cache import cache
from kafka import KafkaConsumer
from alerts.models import Listener, Alert, Key
from threading import Thread
import dill
import time


class Consumer:

    def __init__(self, name='consumer', listener_topics=None):
        print "Creating consumer " + name+ "(" + str(id(self))+")"

        self.name = name
        cache.set(consumer_cache_name(self.name),{"running": False, "alive": False})
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
                if not is_running(self.name):
                    break
                try:
                    print "Recieved Message: " + message.value
                    print message.topic
                    print message.key
                    try:
                        key = Key.objects.get(listener=Listener.objects.get(listener_topic=message.topic),
                                              listener_key=message.key)
                        write_alerts(key, message.value)
                    except Exception as e:
                        if 'DoesNotExist' in e:
                            return
                        else:
                            print e
                except KeyboardInterrupt:
                    break
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


def write_alerts(key, message):
    print "Writing alert for : (" + str(key.listener_key) + ") " + message
    return Alert.objects.get_or_create(key=key, alert_msg=message)


def consumer_cache_name(consumer_name):
    return consumer_name + '_consumer'


def get_listener_topics():
    listeners = Listener.objects.all()
    listener_topics = []
    for listener in listeners:
        listener_topics += [listener.listener_topic]
    return listener_topics


def main():
    pass

if __name__ == "__main__":
    pass
