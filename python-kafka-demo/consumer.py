from confluent_kafka import Consumer
import json

conf = {
    'bootstrap.servers': 'kafka.kafka.svc.cluster.local:9092',
    'group.id': 'order-service-2',
    'auto.offset.reset': 'latest'
}

consumer = Consumer(conf)
consumer.subscribe(['orders'])

print("Consumer started. Waiting for messages...")

no_message_count = 0
while True:
    msg = consumer.poll(1.0)
    
    if msg is None:
        no_message_count += 1
        if no_message_count > 30:  # Exit after 30 seconds of no messages
            print("No more messages. Exiting.")
            break
        continue
    
    if msg.error():
        print(f"Error: {msg.error()}")
        continue
    
    no_message_count = 0  # Reset counter when we get a message!
    
    data = json.loads(msg.value().decode('utf-8'))
    print(f"Received: {data['product']} @ ${data['price']}")