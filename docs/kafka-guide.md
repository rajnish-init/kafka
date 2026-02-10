# Kafka Python Demo - Complete Guide

A hands-on guide to test Kafka with Python Producer and Consumer running on Kubernetes.

---

## Prerequisites

- Kubernetes cluster with Kafka deployed in `kafka` namespace
- `kubectl` configured to access the cluster
- Python 3.12+ (local, for development)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                              │
│                                                                     │
│  ┌─────────────────┐         ┌─────────────────────────────────┐   │
│  │  test namespace │         │       kafka namespace           │   │
│  │                 │         │                                 │   │
│  │  ┌───────────┐  │         │  ┌─────────┐ ┌─────────┐       │   │
│  │  │ Python    │  │  ───▶   │  │ broker-0│ │ broker-1│ ...   │   │
│  │  │ Producer  │  │         │  └─────────┘ └─────────┘       │   │
│  │  │ Consumer  │  │         │       │ Topic: orders │         │   │
│  │  └───────────┘  │         │       └───────────────┘         │   │
│  └─────────────────┘         └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Create a Python Pod

Create a temporary pod to run Python scripts inside the cluster.

```bash
# Create pod in your namespace (e.g., 'test')
kubectl run kafka-producer --image=python:3.12-slim -n test --restart=Never --command -- sleep 3600
```

**Wait for pod to be ready:**
```bash
kubectl get pods -n test -w
```

---

## Step 2: Create the Producer Script

Create `producer.py` locally with the following content:

```python
from confluent_kafka import Producer
import json
import time
import random

conf = {
    'bootstrap.servers': 'kafka.kafka.svc.cluster.local:9092',
    'client.id': 'stock-producer'
}

producer = Producer(conf)

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

topic = 'orders'

while True:
    order = {
        'order_id': random.randint(1000, 9999),
        'user': random.choice(['Alice', 'Bob', 'Charlie', 'David']),
        'product': random.choice(['Laptop', 'Phone', 'Tablet', 'Watch']),
        'price': round(random.uniform(100, 500), 2),
        'timestamp': time.time(),
    }

    # Key determines which partition (same product -> same partition -> ordered)
    producer.produce(topic, key=order['product'], value=json.dumps(order), callback=delivery_report)
    producer.poll(0)  # Triggers delivery callbacks
    time.sleep(5)     # Send every 5 seconds
```

---

## Step 3: Create the Consumer Script

Create `consumer.py` locally with the following content:

```python
from confluent_kafka import Consumer
import json

conf = {
    'bootstrap.servers': 'kafka.kafka.svc.cluster.local:9092',
    'group.id': 'order-service-v1',    # Change this for fresh start
    'auto.offset.reset': 'latest'      # 'earliest' = all messages, 'latest' = new only
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
    
    no_message_count = 0  # Reset counter when we get a message
    
    data = json.loads(msg.value().decode('utf-8'))
    print(f"Received: {data['product']} @ ${data['price']}")
```

---

## Step 4: Copy Scripts to the Pod

```bash
# Copy producer
kubectl cp producer.py test/kafka-producer:/producer.py

# Copy consumer
kubectl cp consumer.py test/kafka-producer:/consumer.py
```

---

## Step 5: Install Dependencies

```bash
kubectl exec -n test kafka-producer -- pip install confluent-kafka
```

---

## Step 6: Run the Producer

In **Terminal 1**:
```bash
kubectl exec -n test kafka-producer -- python -u /producer.py
```

**Expected output:**
```
Message delivered to orders [0]
Message delivered to orders [2]
Message delivered to orders [1]
```

---

## Step 7: Run the Consumer

In **Terminal 2**:
```bash
kubectl exec -n test kafka-producer -- python -u /consumer.py
```

**Expected output:**
```
Consumer started. Waiting for messages...
Received: Laptop @ $330.97
Received: Phone @ $284.46
Received: Watch @ $201.97
```

---

## Key Concepts Explained

### Message Key
```python
key=order['product']  # Same product -> Same partition -> Ordered
```
- Kafka uses `hash(key) % partitions` to route messages
- Same key = Same partition = Guaranteed order

### Consumer Group
```python
'group.id': 'order-service-v1'
```
- Consumers with SAME `group.id` share work (each message to one consumer)
- Consumers with DIFFERENT `group.id` each get all messages

### auto.offset.reset
- `'earliest'`: Read from beginning (all historical messages)
- `'latest'`: Read only new messages

### Bootstrap Servers
- Same namespace: `kafka:9092`
- Different namespace: `kafka.kafka.svc.cluster.local:9092`

---

## Experiments to Try

### 1. Test Fault Tolerance

Kill a broker and watch the system recover:
```bash
kubectl delete pod kafka-broker-0 -n kafka
```

### 2. Test Consumer Scaling

Run multiple consumers with same `group.id`:
```bash
# Terminal 2
kubectl exec -n test kafka-producer -- python -u /consumer.py

# Terminal 3 (same command)
kubectl exec -n test kafka-producer -- python -u /consumer.py
```
Messages will be split between consumers.

### 3. Check Partitions

```bash
kubectl exec -n kafka kafka-broker-0 -- kafka-topics.sh --describe --topic orders --bootstrap-server localhost:9092
```

### 4. Add More Partitions

```bash
kubectl exec -n kafka kafka-broker-0 -- kafka-topics.sh --alter --topic orders --partitions 3 --bootstrap-server localhost:9092
```

---

## Cleanup

```bash
# Delete the test pod
kubectl delete pod kafka-producer -n test
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `No module 'confluent_kafka'` | Run `pip install confluent-kafka` in the pod |
| Connection refused | Check if Kafka brokers are running: `kubectl get pods -n kafka` |
| Consumer exits immediately | Increase timeout or use a new `group.id` |
| No messages received | Start producer BEFORE consumer, use `'auto.offset.reset': 'latest'` |
| KeyError in consumer | Old messages have different schema; use a new topic or new `group.id` |

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `kubectl run kafka-producer --image=python:3.12-slim -n test --restart=Never --command -- sleep 3600` | Create Python pod |
| `kubectl cp producer.py test/kafka-producer:/producer.py` | Copy file to pod |
| `kubectl exec -n test kafka-producer -- python -u /producer.py` | Run script (-u = unbuffered) |
| `kubectl get pods -n kafka` | Check Kafka broker status |
| `kubectl delete pod kafka-producer -n test` | Cleanup |
