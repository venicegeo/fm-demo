from kafka import KeyedProducer, KafkaClient
import json
import time

file_path = './FinalStarbucks.geojson'
features = ""
with open(file_path) as data_file:
    features = json.load(data_file).get('features')

# To send messages asynchronously
client = KafkaClient('kafka.dev:9092')
producer = KeyedProducer(client, async=True)
topic = 'starbucks'
client.ensure_topic_exists(topic)
feature_count = 200
interval = 1 #in seconds

index = 0
while index < feature_count:
    time.sleep(interval)
    producer.send_messages(topic, b'feature', json.dumps(features[index]))
    print "Sent message to topic: {}.".format(topic)
    index += 1