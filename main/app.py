import time
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable
import threading
 
# Configuration
BOOTSTRAP_SERVER = '52.224.142.72:9092'
TOPIC = 'test-pipeline'

def run_producer():
    print("Initializing Producer...")
    producer = None
    # Retry logic until Kafka is reachable
    while not producer:
        try:
            producer = KafkaProducer(bootstrap_servers=[BOOTSTRAP_SERVER])    
        except NoBrokersAvailable:
            print("Waiting for Kafka brokers...")
            time.sleep(5)
            
    print("Producer started. Sending messages...")
    while True:
        msg = f"Data packet sent at {time.ctime()}".encode('utf-8')
        producer.send(TOPIC, msg)
        producer.flush()
        print(f" [PRODUCER] -> Sent to Kafka: {msg.decode()}")
        time.sleep(5)

def run_consumer():
    print("Initializing Consumer...")
    consumer = None
    while not consumer:
        try:
            consumer = KafkaConsumer(
                TOPIC, 
                bootstrap_servers=[BOOTSTRAP_SERVER], 
                auto_offset_reset='earliest',
                group_id='test-group'
            )
        except NoBrokersAvailable:
            time.sleep(5)

    print("Consumer started. Reading from Kafka...")
    for msg in consumer:
        print(f" [CONSUMER] <- Received from Kafka: {msg.value.decode()}")

if __name__ == "__main__":
    # Run producer in background, consumer in foreground
    threading.Thread(target=run_producer, daemon=True).start()
    run_consumer()