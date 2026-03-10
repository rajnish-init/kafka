# Kafka Demo — Complete Command Reference

A hands-on reference for deploying, running, and demoing Kafka on AKS using the files in this repository.

---

## Table of Contents

- [Section 0 — Prerequisites](#section-0--prerequisites)
- [Section 1 — Python File Guide](#section-1--python-file-guide)
- [Section 2 — Environment Setup](#section-2--environment-setup)
- [Section 3 — Deploy Kafka Cluster](#section-3--deploy-kafka-cluster)
- [Section 4 — Verify Cluster Health](#section-4--verify-cluster-health)
- [Section 5 — Topic Management](#section-5--topic-management)
- [Section 6 — Automated In-Cluster Demo](#section-6--automated-in-cluster-demo)
- [Section 7 — Manual Demo (Two Terminals)](#section-7--manual-demo-two-terminals)
- [Section 8 — All-in-One Demo (app.py)](#section-8--all-in-one-demo-apppy)
- [Section 9 — CLI Producer / Consumer](#section-9--cli-producer--consumer)
- [Section 10 — Consumer Group Management](#section-10--consumer-group-management)
- [Section 11 — Fault-Tolerance Demo](#section-11--fault-tolerance-demo)
- [Section 12 — Consumer Scaling Demo](#section-12--consumer-scaling-demo)
- [Section 13 — External Access (Local Machine)](#section-13--external-access-local-machine)
- [Section 14 — Monitoring & Debug](#section-14--monitoring--debug)
- [Section 15 — Cleanup](#section-15--cleanup)

---

## Section 0 — Prerequisites

```bash
kubectl version --client          # Must be 1.25+
helm version                      # Must be 3.x
kubectl get nodes                 # AKS cluster must be accessible
```

---

## Section 1 — Python File Guide

| File | Purpose | How to Run |
|------|---------|------------|
| `main/config.py` | **Single source of truth** for Kafka connection settings. Edit `BOOTSTRAP_SERVER` and `TOPIC` here before running any script. | _(imported by other scripts)_ |
| `main/config_alternatives.py` | Alternative bootstrap server examples (internal ClusterIP vs external LoadBalancer). Swap values into `config.py` as needed. | _(reference only)_ |
| `main/kafka_client.py` | **Core reusable library.** Exposes `run_producer()` and `run_consumer()` with retry logic, structured logging, and graceful Ctrl+C shutdown. | _(imported, do not run directly)_ |
| `main/producer.py` | Thin entry-point that calls `run_producer()`. Sends a timestamped message every **5 seconds**. | `python producer.py` |
| `main/consumer.py` | Thin entry-point that calls `run_consumer()`. Reads **all messages** from the topic (`earliest`) and prints them. | `python consumer.py` |
| `main/app.py` | Standalone all-in-one script. Runs producer in a background thread and consumer in the foreground. Used by `kafka-test-deploy.yaml` for automated in-cluster validation. | `python app.py` |
| `main/test_connection.py` | **Quick health-check.** Verifies the Kafka broker is reachable. Run this first to diagnose connectivity issues. | `python test_connection.py` |
| `main/kafka-test-deploy.yaml` | Kubernetes manifest. Bundles `app.py` into a ConfigMap and deploys it as a Pod (`kafka-validation-app`) inside the cluster. | `kubectl apply -f` |
| `main/values.yaml` | Helm values for the Bitnami Kafka chart. KRaft mode, 3 brokers, Azure `managed-csi` storage, LoadBalancer external access. | `helm upgrade --install` |

---

## Section 2 — Environment Setup

> Run these once before anything else.

```bash
# Create the kafka namespace
kubectl create namespace kafka

# Add Bitnami Helm repository
helm repo add bitnami https://charts.bitnami.com/bitnami

# Update local Helm chart cache
helm repo update
```

---

## Section 3 — Deploy Kafka Cluster

> Uses `main/values.yaml` — KRaft mode, 3 brokers, 10Gi storage per broker, Azure managed-csi.

```bash
# Run from the root of the kafka/ repo
helm upgrade --install kafka bitnami/kafka \
  --namespace kafka \
  --values main/values.yaml \
  --wait --timeout 10m
```

To upgrade after editing `values.yaml`:
```bash
helm upgrade kafka bitnami/kafka \
  --namespace kafka \
  --values main/values.yaml
```

---

## Section 4 — Verify Cluster Health

```bash
# Watch pods until all brokers show Running (Ctrl+C to stop)
kubectl get pods -n kafka -w

# Expected:
#   kafka-broker-0     1/1     Running
#   kafka-broker-1     1/1     Running
#   kafka-broker-2     1/1     Running

# Check all resources (pods, services, PVCs)
kubectl get all -n kafka

# Check Kafka services and their IPs/ports
kubectl get svc -n kafka

# Check persistent volume claims
kubectl get pvc -n kafka

# View live broker logs
kubectl logs kafka-broker-0 -n kafka --tail=50
```

---

## Section 5 — Topic Management

> All `kafka-topics.sh` commands run inside a Kafka broker or debug pod.

### 5.1 Create a debug client pod

```bash
kubectl run kafka-client \
  --restart='Never' \
  --image docker.io/bitnami/kafka:3.9.0 \
  --namespace kafka \
  --command -- sleep infinity

# Shell into the client pod
kubectl exec -it kafka-client -n kafka -- bash
```

### 5.2 Topic commands (run inside the pod shell)

```bash
# List ALL topics
kafka-topics.sh --list --bootstrap-server kafka:9092

# Create a topic
kafka-topics.sh --create \
  --bootstrap-server kafka:9092 \
  --replication-factor 3 \
  --partitions 3 \
  --topic test-pipeline

# Describe a topic (see partitions, leaders, replicas, ISR)
kafka-topics.sh --describe \
  --bootstrap-server kafka:9092 \
  --topic test-pipeline

# Expected:
#   Topic: test-pipeline  PartitionCount: 3  ReplicationFactor: 3
#   Partition: 0  Leader: 0  Replicas: 0,1,2  Isr: 0,1,2

# Add more partitions to an existing topic
kafka-topics.sh --alter \
  --bootstrap-server kafka:9092 \
  --topic test-pipeline \
  --partitions 6

# Delete a topic
kafka-topics.sh --delete \
  --bootstrap-server kafka:9092 \
  --topic my-test-topic

exit
```

---

## Section 6 — Automated In-Cluster Demo

> Easiest demo: one command deploys a pod that runs producer + consumer together inside the cluster.

```bash
# Deploy the validation app (creates ConfigMap + Pod)
kubectl apply -f main/kafka-test-deploy.yaml

# Wait until pod is Running
kubectl get pods -n kafka -l app=kafka-tester -w

# Follow live logs
kubectl logs kafka-validation-app -n kafka -f
```

**Expected output (every 60 seconds):**
```
Starting Producer logic...
Starting Consumer logic...
[PRODUCER] Sent: Validated message at Tue Mar 10 09:30:00 2026
[CONSUMER] Received: Validated message at Tue Mar 10 09:30:00 2026
```

```bash
# If the pod crashes, check events
kubectl describe pod kafka-validation-app -n kafka

# Restart the validation app
kubectl delete pod kafka-validation-app -n kafka
kubectl apply -f main/kafka-test-deploy.yaml
```

---

## Section 7 — Manual Demo (Two Terminals)

> Runs `producer.py` + `consumer.py` inside a Python pod inside the cluster.

```bash
# Create a Python pod in the 'test' namespace
kubectl create namespace test 2>/dev/null || true
kubectl run kafka-demo-pod \
  --image=python:3.12-slim \
  -n test \
  --restart=Never \
  --command -- sleep 3600

# Wait for pod to be Ready
kubectl get pod kafka-demo-pod -n test -w

# Install kafka-python library inside the pod
kubectl exec -n test kafka-demo-pod -- pip install kafka-python

# Copy all Python files into the pod
kubectl cp main/config.py          test/kafka-demo-pod:/config.py
kubectl cp main/kafka_client.py    test/kafka-demo-pod:/kafka_client.py
kubectl cp main/producer.py        test/kafka-demo-pod:/producer.py
kubectl cp main/consumer.py        test/kafka-demo-pod:/consumer.py
kubectl cp main/test_connection.py test/kafka-demo-pod:/test_connection.py

# (Optional) Verify broker connectivity first
kubectl exec -n test kafka-demo-pod -- python -u /test_connection.py
```

**Terminal 1 — Start the Producer:**
```bash
kubectl exec -n test kafka-demo-pod -- python -u /producer.py
# Sends a timestamped message every 5 seconds. Ctrl+C to stop.
```

**Terminal 2 — Start the Consumer:**
```bash
kubectl exec -n test kafka-demo-pod -- python -u /consumer.py
# Reads ALL messages from the topic and prints them live. Ctrl+C to stop.
```

---

## Section 8 — All-in-One Demo (app.py)

> Runs producer + consumer in a single process. Producer runs as a daemon thread; consumer runs in the foreground.

```bash
kubectl cp main/app.py test/kafka-demo-pod:/app.py
kubectl exec -n test kafka-demo-pod -- python -u /app.py
```

---

## Section 9 — CLI Producer / Consumer

> Built-in Kafka CLI tools — no Python needed. Great for quick sanity checks.

**Terminal 1 — Produce via CLI:**
```bash
kubectl exec -it kafka-client -n kafka -- \
  kafka-console-producer.sh \
    --bootstrap-server kafka:9092 \
    --topic test-pipeline
# Type any message, press Enter. Ctrl+C to stop.
```

**Terminal 2 — Consume via CLI:**
```bash
# Read from beginning
kubectl exec -it kafka-client -n kafka -- \
  kafka-console-consumer.sh \
    --bootstrap-server kafka:9092 \
    --topic test-pipeline \
    --from-beginning

# Read only new messages
kubectl exec -it kafka-client -n kafka -- \
  kafka-console-consumer.sh \
    --bootstrap-server kafka:9092 \
    --topic test-pipeline
```

---

## Section 10 — Consumer Group Management

> Run these inside the `kafka-client` pod shell.

```bash
# List all consumer groups
kafka-consumer-groups.sh \
  --bootstrap-server kafka:9092 \
  --list

# Describe a group (see lag / offsets per partition)
kafka-consumer-groups.sh \
  --bootstrap-server kafka:9092 \
  --describe \
  --group demo-group

# Reset offsets to re-read all messages from the beginning
kafka-consumer-groups.sh \
  --bootstrap-server kafka:9092 \
  --group demo-group \
  --topic test-pipeline \
  --reset-offsets \
  --to-earliest \
  --execute
```

---

## Section 11 — Fault-Tolerance Demo

> Kafka replicates data across 3 brokers. Delete one and watch Kafka self-heal.

```bash
# Delete one broker pod (StatefulSet will restart it automatically)
kubectl delete pod kafka-broker-1 -n kafka

# Watch it restart (~30-60 seconds)
kubectl get pods -n kafka -w

# Confirm the consumer still receives messages during recovery
kubectl logs kafka-validation-app -n kafka -f

# After recovery, verify ISR is full again
kubectl exec -it kafka-client -n kafka -- \
  kafka-topics.sh --describe \
    --bootstrap-server kafka:9092 \
    --topic test-pipeline
```

---

## Section 12 — Consumer Scaling Demo

> When multiple consumers share the same `group.id`, Kafka distributes partitions across them — each message goes to exactly **one** consumer.

**Terminal 1:**
```bash
kubectl exec -n test kafka-demo-pod -- python -u /consumer.py
```

**Terminal 2 (same group, different partition assignment):**
```bash
kubectl exec -n test kafka-demo-pod -- python -u /consumer.py
```

> **Tip:** To have two consumers each receive **all** messages independently, change `group_id` to a different value in `main/config.py` before running the second consumer.

---

## Section 13 — External Access (Local Machine)

External LoadBalancer IPs are configured in `main/values.yaml`:

| Broker | External IP | Port |
|--------|-------------|------|
| 0 | `52.186.140.22` | 9094 |
| 1 | `13.82.136.111` | 9094 |
| 2 | `172.191.54.0` | 9094 |

`main/config.py` currently points to `20.121.149.203:9094`. Update `BOOTSTRAP_SERVER` there if the IP changes.

```bash
# Set up a local virtualenv
cd main
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate
# Activate (Linux/macOS)
# source venv/bin/activate

pip install kafka-python

# Check connectivity from your laptop
python test_connection.py

# Terminal 1 — Run producer locally
python producer.py

# Terminal 2 — Run consumer locally
python consumer.py
```

---

## Section 14 — Monitoring & Debug

```bash
# All resources in kafka namespace
kubectl get all -n kafka

# View Kafka broker configuration
kubectl exec kafka-broker-0 -n kafka -- cat /bitnami/kafka/config/server.properties

# Live broker logs
kubectl logs kafka-broker-0 -n kafka -f

# Describe pod for events (useful when a pod is stuck/crashing)
kubectl describe pod kafka-broker-0 -n kafka
kubectl describe pod kafka-validation-app -n kafka

# Check Helm release status
helm status kafka -n kafka

# View currently deployed Helm values
helm get values kafka -n kafka
```

---

## Section 15 — Cleanup

```bash
# Remove automated validation app only
kubectl delete -f main/kafka-test-deploy.yaml

# Remove manual demo pods
kubectl delete pod kafka-demo-pod -n test
kubectl delete pod kafka-client -n kafka --ignore-not-found

# ⚠ Remove the ENTIRE Kafka cluster (data will be permanently lost!)
helm uninstall kafka -n kafka
kubectl delete pvc --all -n kafka
kubectl delete namespace kafka

# Remove test namespace
kubectl delete namespace test
```

---

> **Full shell script version:** see [`command.sh`](./command.sh)
