from kafka import KeyedProducer, KafkaClient
import json
import time

file_path = '../sample_data/starbucks/starbucks.geojson'
features = ""
with open(file_path) as data_file:
    features = json.load(data_file).get('features')

# To send messages asynchronously
client = KafkaClient('kafka.dev:9092')
producer = KeyedProducer(client, async=True)
topic = 'starbucks2'
client.ensure_topic_exists(topic)
#run all?
feature_count = len(features)
#or run some?
#feature_count = 1
interval = 1 #in seconds

index = 0
while index < feature_count:
    time.sleep(interval)
    photos = []
    photos_url = []
    if features[index].get('properties').get('photos'):
        for photo in features[index].get('properties').get('photos').split(','):
            photos += [photo]
            photos_url += ['http://192.168.99.1:8001/starbucks/{}.jpg'.format(photo)]
    if features[index].get('properties').get('photos'):
        features[index]['properties']['photos'] = photos
    if features[index].get('properties').get('photos_url'):
        features[index]['properties']['photos_url'] = photos_url
    producer.send_messages(topic, b'feature', json.dumps(features[index]))
    print "Sent message to topic: {}.".format(topic)
    print features[index]
    index += 1