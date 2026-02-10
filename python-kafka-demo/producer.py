from confluent_kafka import Producer
import json
import time
import random

conf = {
    'bootstrap.servers': 'kafka.kafka.svc.cluster.local:9092',
    'client.id': 'stock-producer'
}

producer = Producer(conf)

def delivery_report(err,msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

topic = 'orders'

while True:
    stock = {
        'order_id': random.randint(1000, 9999),
        'user': random.choice(['Alice', 'Bob', 'Charlie', 'David']),
        'product': random.choice(['Laptop', 'Phone', 'Tablet', 'Watch']),
        'price': round(random.uniform(100, 500), 2),
        'timestamp': time.time(),
    }


#The key has two purposes:
#It determines which partition the message goes to (for ordering/routing)
#It's also sent along with the message (the consumer can read it)
    producer.produce(topic, key=stock['product'], value=json.dumps(stock), callback=delivery_report)
    producer.poll(0)
    time.sleep(5)