# Kafka Microservices Learning Plan - Updated for Direct Kafka Integration

## Overview
This plan guides you through integrating Kafka into your microservices architecture. You'll first deploy services to AKS, then integrate Kafka for event-driven communication.

## Prerequisites ✅
You have:
- Order Service (Port 8080) - Receives orders via REST
- Inventory Service (Port 8081) - Manages inventory  
- Notification Service (Port 8082) - Sends notifications
- Services built and ready locally (Docker Compose working)

## What You Need to Do:
- Deploy services to AKS
- Set up Kafka cluster in AKS
- Integrate Kafka into services

---

## 📋 PART 1: PREPARATION & UNDERSTANDING

### Phase 1.1: Deploy Microservices to AKS

**What to Do:**
Deploy your existing microservices to AKS before Kafka integration.

**Detailed Steps:**

1. **Containerize Services** - Build and push Docker images:
   - Build images for all three services
   - Push to Azure Container Registry (ACR) or Docker Hub
   - Document image tags and registry details

2. **Create Kubernetes Manifests** - Create `k8s/` directory:
   - Deployment YAML for each service
   - Service YAML (ClusterIP or LoadBalancer) for each service
   - ConfigMaps for environment variables
   - Add comments explaining each configuration option

3. **Deploy to AKS**:
   ```bash
   # Create namespace
   kubectl create namespace ecommerce
   
   # Apply manifests
   kubectl apply -f k8s/ -n ecommerce
   
   # Verify deployments
   kubectl get pods -n ecommerce
   kubectl get services -n ecommerce
   ```

4. **Test Services in AKS**:
   - Verify all pods are running
   - Test health endpoints
   - Document service endpoints

**Deliverables:**
- Docker images pushed to registry
- k8s/order-service-deployment.yaml
- k8s/inventory-service-deployment.yaml
- k8s/notification-service-deployment.yaml
- k8s/services.yaml
- All services running in AKS

---

### Phase 1.2: Set Up Kafka Cluster in AKS

**What to Do:**
Deploy Kafka cluster to your AKS environment.

**Detailed Steps:**

1. **Choose Kafka Deployment Method**:
   - Option 1: Strimzi Operator (recommended for production)
   - Option 2: Confluent Helm Charts
   - Option 3: Bitnami Kafka Helm Chart (simpler for learning)
   - Document your choice with reasoning

2. **Deploy Kafka using Helm** (Bitnami example):
   ```bash
   # Add Bitnami repo
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm repo update
   
   # Create namespace
   kubectl create namespace kafka
   
   # Install Kafka
   helm install kafka bitnami/kafka \
     --namespace kafka \
     --set replicaCount=3 \
     --set zookeeper.replicaCount=3
   ```

3. **Verify Kafka Installation**:
   ```bash
   kubectl get pods -n kafka
   kubectl get services -n kafka
   ```

4. **Document Kafka Access**:
   - Internal endpoint: kafka.kafka.svc.cluster.local:9092
   - Number of brokers
   - Zookeeper endpoints

**Deliverables:**
- Kafka cluster running in AKS
- Documentation of endpoints and configuration
- Verified broker connectivity

---

### Phase 1.3: Prepare for Kafka Integration

**What to Do:**
Review and document your current setup, plan the event-driven transformation.

**Detailed Steps:**

1. **Document Current State** - Create `docs/current-architecture.md`:
   - List all existing endpoints in each service
   - Document current service communication method
   - Diagram the current flow (REST calls, database, etc.)

2. **Design Event-Driven Flow** - Create `docs/event-driven-design.md`:
   - Define all events: OrderCreated, InventoryReserved, InventoryFailed, NotificationSent, OrderCompleted, OrderCancelled
   - Design event schema with: event_id, event_type, timestamp, correlation_id, payload, metadata
   - Add comments explaining WHY each field exists (correlation_id for tracing, event_id for idempotency, etc.)

3. **Plan Kafka Topics** - Create `docs/kafka-topics-design.md`:
   - Topic naming: orders.created, inventory.reserved, inventory.failed, notifications.sent, orders.completed, orders.cancelled
   - For each topic: 3 partitions, replication factor 2, 7-day retention
   - Partition key strategy: use order_id for ordering guarantee
   - Add comments explaining all design decisions

4. **Add Kafka Dependencies**:
   - Python: `confluent-kafka==2.3.0` in requirements.txt (with comments on why confluent-kafka over kafka-python)
   - Node.js: `kafkajs: ^2.2.4` in package.json (with comments on why kafkajs)
   - Java: spring-kafka dependency in pom.xml (with comments on Spring integration benefits)

5. **Verify Kafka Access from Services**:
   ```bash
   kubectl get pods -n kafka
   kubectl get services -n kafka
   # Document: service name, endpoint, number of brokers
   ```

**Deliverables:**
- docs/current-architecture.md
- docs/event-driven-design.md  
- docs/kafka-topics-design.md
- Updated dependency files
- Kafka cluster details documented

---

### Phase 1.4: Learn Kafka Concepts

**What to Do:**
Create comprehensive understanding document BEFORE coding.

**Create `docs/kafka-concepts-explained.md` covering:**

1. **Architecture**: Brokers, Zookeeper/KRaft, cluster coordination
2. **Topics & Partitions**: Why partition, ordering guarantees, partition key strategy
3. **Producers**: Configurations (acks, retries, compression, batching), workflow, trade-offs
4. **Consumers**: Configurations (group.id, auto.offset.reset, commit strategies), workflow
5. **Consumer Groups**: Load balancing, partition assignment, rebalancing
6. **Offsets**: What they are, commit strategies (auto vs manual), at-least-once vs exactly-once
7. **Replication**: Leader/followers, ISR, fault tolerance
8. **Performance**: Partitions vs throughput, batching vs latency, compression comparison

**For each concept:**
- Explain what it is
- Explain why it matters  
- Show examples from order processing
- Include ASCII diagrams
- Document trade-offs and design decisions

**Deliverables:**
- Comprehensive docs/kafka-concepts-explained.md with diagrams and examples

---

## 📋 PART 2: KAFKA INTEGRATION

### Phase 2.1: Create Kafka Topics

**What to Do:**
Create all topics in your AKS Kafka cluster.

**Steps:**

1. Connect to Kafka pod:
   ```bash
   kubectl exec -it <kafka-broker-pod> -n kafka -- bash
   ```

2. Create each topic with comments:
   ```bash
   kafka-topics.sh --create \
     --topic orders.created \
     --partitions 3 \
     --replication-factor 2 \
     --config retention.ms=604800000 \
     --bootstrap-server localhost:9092
   # Repeat for: inventory.reserved, inventory.failed, notifications.sent, orders.completed, orders.cancelled
   ```

3. Verify topics:
   ```bash
   kafka-topics.sh --list --bootstrap-server localhost:9092
   kafka-topics.sh --describe --topic orders.created --bootstrap-server localhost:9092
   ```

4. Create management script `scripts/kafka-topics-setup.sh` for recreation

5. Test with console producer/consumer

**Deliverables:**
- All 6 topics created
- scripts/kafka-topics-setup.sh
- Console test successful
- Updated docs with actual configuration

---

### Phase 2.2: Order Service as Kafka Producer

**What to Do:**
Transform Order Service to publish events instead of REST calls.

**Implementation:**

1. **Create Kafka Config** (`config/kafka_config.py`):
   - bootstrap.servers, acks='all', retries=3, enable.idempotence=True
   - compression.type='gzip', batch.size=16384, linger.ms=10
   - **Add comments explaining EVERY configuration and trade-off**

2. **Create Producer Wrapper** (`kafka/producer.py`):
   - Wrap confluent_kafka Producer
   - publish_event() method with error handling
   - Delivery callbacks for monitoring
   - Partition key logic (use order_id)
   - **Extensive comments on why wrapper pattern, async callbacks, error handling**

3. **Update Order Endpoint**:
   - Change POST /api/orders to:
     1. Validate input
     2. Generate order_id and correlation_id
     3. Create OrderCreated event
     4. Publish to Kafka
     5. Return 202 Accepted (NOT 200 OK)
   - **Comments explaining 202 vs 200, correlation_id purpose, immediate return**

4. **Add Status Endpoint**:
   - GET /api/orders/{id} for polling status
   - Returns PENDING/CONFIRMED/CANCELLED
   - **Comments on why needed in event-driven**

5. **Add Consumer to Order Service** (`kafka/consumer.py`):
   - Subscribe to inventory.reserved, inventory.failed
   - Update order status based on events
   - Manual offset commit after processing
   - **Comments on at-least-once semantics, idempotency**

6. **Update Deployment**:
   - Two containers: api + consumer
   - Separate env vars, resource limits
   - Health + readiness probes
   - **Comments on multi-container pattern**

**Deliverables:**
- config/kafka_config.py
- kafka/producer.py
- kafka/consumer.py  
- Updated endpoints (202 response)
- Updated k8s deployment
- All code heavily commented
- Tested and verified

---

### Phase 2.3: Inventory Service as Consumer

**What to Do:**
Convert Inventory Service to consume orders.created events.

**Implementation:**

1. **Create Consumer Config**:
   - group.id='inventory-service-group'
   - auto.offset.reset='earliest'
   - enable.auto.commit=False (manual commit)
   - **Comments on consumer group, offset strategy**

2. **Create Consumer** (`kafka/inventory_consumer.py`):
   - Subscribe to orders.created
   - Process each message:
     1. Deserialize event
     2. Check inventory
     3. If available: reserve + publish inventory.reserved
     4. If not: publish inventory.failed
     5. Commit offset
   - **Comments on processing flow, idempotency, error handling**

3. **Create Producer** (for result events):
   - Publish inventory.reserved or inventory.failed
   - Include original correlation_id
   - **Comments on event correlation**

4. **Update Deployment**:
   - Change from REST API to Kafka consumer
   - Or run both (API for manual queries + consumer)
   - **Comments on deployment strategy**

**Deliverables:**
- kafka/inventory_consumer.py
- Event publishing logic
- Updated deployment
- Tested: orders.created → inventory.reserved

---

### Phase 2.4: Notification Service as Consumer

**What to Do:**
Convert Notification Service to multi-topic consumer.

**Implementation:**

1. **Subscribe to Multiple Topics**:
   - orders.created (immediate notification)
   - inventory.reserved (confirmation notification)
   - **Comments on multi-topic subscription**

2. **Event Routing Logic**:
   - Different processing based on event_type
   - Send appropriate notification for each
   - Publish notifications.sent event
   - **Comments on event routing pattern**

3. **Consumer Group Scaling**:
   - Deploy 3 replicas
   - Observe partition distribution
   - **Comments on load balancing**

**Deliverables:**
- Multi-topic consumer
- Event routing logic
- 3 replicas deployed
- End-to-end flow tested

---

### Phase 2.5: Implement Saga Pattern

**What to Do:**
Add compensation logic for failures.

**Saga Flow:**

**Happy Path:**
```
OrderCreated → InventoryReserved → NotificationSent → OrderCompleted
```

**Failure Path:**
```
OrderCreated → InventoryFailed → OrderCancelled → CancellationNotification
```

**Implementation:**

1. **Order Service Compensation**:
   - Consume inventory.failed
   - Publish orders.cancelled
   - Update order status to CANCELLED
   - **Comments on saga choreography vs orchestration**

2. **State Management**:
   - Track order states: PENDING, CONFIRMED, CANCELLED
   - Update based on events
   - **Comments on eventual consistency**

3. **Test Both Paths**:
   - Success: All steps complete
   - Failure: Inventory fails, order cancels
   - **Comments on distributed transaction alternatives**

**Deliverables:**
- Compensation logic implemented
- Both paths tested
- State tracking working
- Saga pattern documented

---

## 📋 PART 3: OPERATIONS & TESTING

### Phase 3.1: Topic Management

**Practice:**
- Create/describe/delete topics
- Modify partitions (can increase, not decrease)
- Change retention policies
- Monitor topic configurations

### Phase 3.2: Consumer Groups

**Practice:**
- List consumer groups
- Describe group (check lag)
- Reset offsets (earliest, latest, specific)
- Monitor rebalancing

### Phase 3.3: Performance Testing

**Test:**
- Producer throughput (kafka-producer-perf-test)
- Consumer throughput (kafka-consumer-perf-test)
- End-to-end latency
- Different configurations (acks, batching, compression)

### Phase 3.4: Failure Scenarios

**Test:**
- Broker failure (delete pod)
- Consumer crash (kill pod)
- Network partition (network policy)
- Poison pill messages
- Message ordering validation

### Phase 3.5: Monitoring

**Setup:**
- Application metrics (messages produced/consumed)
- Distributed tracing (correlation IDs)
- Structured logging (JSON logs)
- Consumer lag monitoring
- Health checks

---

## 📝 SUMMARY

### What You'll Learn:
- Deploying microservices to AKS
- Setting up Kafka cluster in Kubernetes
- Event-driven architecture patterns
- Kafka producer/consumer implementation
- Consumer groups and scaling
- Offset management strategies
- Saga pattern for distributed transactions
- Performance tuning
- Failure handling
- Production operations

### Key Takeaways:
- Loose coupling through events
- Asynchronous processing benefits
- At-least-once delivery semantics
- Idempotency importance
- Replication for fault tolerance
- Partitioning for scalability

---

## 📚 NEXT STEPS

After completing this plan:
1. Add security (SSL/TLS, SASL authentication)
2. Implement schema registry (Avro schemas)
3. Add Kafka Streams for real-time processing
4. Set up monitoring (Prometheus/Grafana)
5. Implement exactly-once semantics
6. Add dead letter queues (DLQ)
7. Performance benchmarking and tuning

---

**Note:** This plan starts with deploying your existing services to AKS, then setting up Kafka, followed by integration. Each phase includes detailed prompts with extensive comments explaining WHY behind every decision. Use the verification guide for step-by-step testing commands.
