from kafka import KeyedProducer, KafkaClient
import base64
import json
import time

file_path = './image.jpg'
with open(file_path, 'rb') as data_file:
    encoded_string = base64.b64encode(data_file.read())

json_data = json.dumps({'uid': 'duck', 'type': 'jpg', 'data': encoded_string})

# # To send messages asynchronously
client = KafkaClient('kafka.dev:9092')
producer = KeyedProducer(client, async=True)
topic = 'starbucks'
client.ensure_topic_exists(topic)
feature_count = 1
interval = 1 #in seconds

index = 0
while index < feature_count:
    time.sleep(interval)
    producer.send_messages(topic, 'asset', json_data)
    print "Sent image to topic: {}.".format(topic)
    index += 1