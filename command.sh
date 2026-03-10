#!/usr/bin/env bash
# =============================================================================
# Kafka Demo Command Sheet
# Project: completum/kafka
# Generated: 2026-03-10
#
# This file documents all commands needed to demo Kafka end-to-end on AKS.
# It covers setup, deployment, Python script usage, topic management,
# monitoring, fault-tolerance tests, and cleanup.
#
# IMPORTANT: Run commands in the ORDER they appear below.
#            Multi-terminal steps are clearly marked.
# =============================================================================


# =============================================================================
# SECTION 0: PREREQUISITES — CHECK YOUR TOOLS
# =============================================================================

kubectl version --client          # Must be 1.25+
helm version                      # Must be 3.x
kubectl get nodes                 # AKS cluster must be accessible


# =============================================================================
# SECTION 1: UNDERSTANDING THE PYTHON FILES IN main/
# =============================================================================
# Each Python file in main/ has a distinct role in the demo:
#
# ┌─────────────────────┬──────────────────────────────────────────────┐
# │ File                │ Purpose & Usage                              │
# ├─────────────────────┼──────────────────────────────────────────────┤
# │ config.py           │ Single source of truth for Kafka connection  │
# │                     │ settings. Edit BOOTSTRAP_SERVER and TOPIC    │
# │                     │ here before running any Python script.       │
# │                     │                                              │
# │                     │ Key values:                                  │
# │                     │   BOOTSTRAP_SERVER = ["20.121.149.203:9094"] │
# │                     │   TOPIC = "test-pipeline"                    │
# ├─────────────────────┼──────────────────────────────────────────────┤
# │ config_alternatives │ Alternative bootstrap server examples        │
# │ .py                 │ (internal ClusterIP, external LoadBalancer). │
# │                     │ Swap values into config.py as needed.        │
# ├─────────────────────┼──────────────────────────────────────────────┤
# │ kafka_client.py     │ Core reusable library. Contains              │
# │                     │ run_producer() and run_consumer() with       │
# │                     │ retry logic, structured logging, and graceful│
# │                     │ shutdown on Ctrl+C.                          │
# │                     │ Do NOT run this directly.                    │
# ├─────────────────────┼──────────────────────────────────────────────┤
# │ producer.py         │ Thin entry-point that calls run_producer()   │
# │                     │ from kafka_client.py. Sends timestamped      │
# │                     │ messages to TOPIC every 5 seconds.           │
# │                     │                                              │
# │                     │ Run: python producer.py                      │
# ├─────────────────────┼──────────────────────────────────────────────┤
# │ consumer.py         │ Thin entry-point that calls run_consumer()   │
# │                     │ from kafka_client.py. Reads ALL messages      │
# │                     │ from TOPIC (auto_offset_reset=earliest)      │
# │                     │ and prints them.                             │
# │                     │                                              │
# │                     │ Run: python consumer.py                      │
# ├─────────────────────┼──────────────────────────────────────────────┤
# │ app.py              │ Standalone all-in-one script. Runs producer  │
# │                     │ in a background thread and consumer in the   │
# │                     │ foreground. Used by kafka-test-deploy.yaml   │
# │                     │ for automated in-cluster validation.         │
# │                     │                                              │
# │                     │ Run: python app.py                           │
# ├─────────────────────┼──────────────────────────────────────────────┤
# │ test_connection.py  │ Quick health-check script. Verifies that the │
# │                     │ Kafka broker is reachable. Run this first to │
# │                     │ diagnose connection issues before running    │
# │                     │ the producer or consumer.                    │
# │                     │                                              │
# │                     │ Run: python test_connection.py               │
# ├─────────────────────┼──────────────────────────────────────────────┤
# │ kafka-test-         │ Kubernetes manifest that bundles app.py into │
# │ deploy.yaml         │ a ConfigMap and deploys it as a Pod named    │
# │                     │ kafka-validation-app in the kafka namespace. │
# ├─────────────────────┼──────────────────────────────────────────────┤
# │ values.yaml         │ Helm values for Bitnami Kafka chart.         │
# │                     │ Configures KRaft mode (no ZooKeeper),        │
# │                     │ 3 brokers, Azure managed-csi storage, and    │
# │                     │ LoadBalancer external access.                │
# └─────────────────────┴──────────────────────────────────────────────┘


# =============================================================================
# SECTION 2: ENVIRONMENT SETUP (Run Once)
# =============================================================================

# 2.1 — Create the kafka namespace
kubectl create namespace kafka

# 2.2 — Add Bitnami Helm chart repository
helm repo add bitnami https://charts.bitnami.com/bitnami

# 2.3 — Update local Helm chart cache
helm repo update


# =============================================================================
# SECTION 3: DEPLOY KAFKA CLUSTER ON AKS
# =============================================================================
# Uses main/values.yaml which configures:
#   - KRaft mode (modern Kafka, no ZooKeeper)
#   - 3 broker replicas
#   - 10Gi persistent disk per broker (Azure managed-csi)
#   - External LoadBalancer access on port 9094

# Run this from the root of the kafka/ repo:
helm upgrade --install kafka bitnami/kafka \
  --namespace kafka \
  --values main/values.yaml \
  --wait --timeout 10m

# To upgrade an existing installation after editing values.yaml:
helm upgrade kafka bitnami/kafka \
  --namespace kafka \
  --values main/values.yaml


# =============================================================================
# SECTION 4: VERIFY KAFKA CLUSTER IS HEALTHY
# =============================================================================

# 4.1 — Watch pods until all brokers are Running (Ctrl+C to stop watching)
kubectl get pods -n kafka -w

# Expected:
#   NAME               READY   STATUS    RESTARTS   AGE
#   kafka-broker-0     1/1     Running   0          2m
#   kafka-broker-1     1/1     Running   0          2m
#   kafka-broker-2     1/1     Running   0          2m

# 4.2 — Check all resources (pods, services, PVCs)
kubectl get all -n kafka

# 4.3 — Check Kafka services and their IPs/ports
kubectl get svc -n kafka

# 4.4 — Check persistent volumes (storage) are bound
kubectl get pvc -n kafka

# 4.5 — View live broker logs to confirm Kafka started cleanly
kubectl logs kafka-broker-0 -n kafka --tail=50


# =============================================================================
# SECTION 5: TOPIC MANAGEMENT
# =============================================================================
# All kafka-topics.sh commands run inside a Kafka broker or debug pod.
# Use either kafka-broker-0 directly or the kafka-client debug pod (see below).

# 5.1 — Create a debug client pod for topic management
#        (Use Bitnami image — it has Kafka CLI tools pre-installed)
kubectl run kafka-client \
  --restart='Never' \
  --image docker.io/bitnami/kafka:3.9.0 \
  --namespace kafka \
  --command -- sleep infinity

# Wait for client pod to be ready
kubectl get pod kafka-client -n kafka -w

# 5.2 — Open a shell inside the client pod
kubectl exec -it kafka-client -n kafka -- bash

# ---- Inside the pod shell ----

# 5.3 — List ALL existing topics
kafka-topics.sh --list --bootstrap-server kafka:9092

# 5.4 — Create a new topic (manual creation)
kafka-topics.sh --create \
  --bootstrap-server kafka:9092 \
  --replication-factor 3 \
  --partitions 3 \
  --topic orders

# 5.5 — Create the 'test-pipeline' topic used by the Python scripts
kafka-topics.sh --create \
  --bootstrap-server kafka:9092 \
  --replication-factor 3 \
  --partitions 3 \
  --topic test-pipeline

# 5.6 — Describe a topic (see partitions, leaders, replicas, ISR)
kafka-topics.sh --describe \
  --bootstrap-server kafka:9092 \
  --topic test-pipeline

# Expected:
#   Topic: test-pipeline  PartitionCount: 3  ReplicationFactor: 3
#   Partition: 0  Leader: 0  Replicas: 0,1,2  Isr: 0,1,2

# 5.7 — Add more partitions to an existing topic
kafka-topics.sh --alter \
  --bootstrap-server kafka:9092 \
  --topic test-pipeline \
  --partitions 6

# 5.8 — Delete a topic (only works if delete.topic.enable=true)
kafka-topics.sh --delete \
  --bootstrap-server kafka:9092 \
  --topic my-test-topic

# ---- Exit pod shell ----
exit


# =============================================================================
# SECTION 6: RUN AUTOMATED IN-CLUSTER DEMO (kafka-validation-app)
# =============================================================================
# This is the easiest way to demo: deploy a pod that runs producer + consumer
# together inside the cluster. Defined in main/kafka-test-deploy.yaml.

# 6.1 — Deploy the validation app (creates ConfigMap + Pod)
kubectl apply -f main/kafka-test-deploy.yaml

# 6.2 — Wait until pod is Running
kubectl get pods -n kafka -l app=kafka-tester -w

# 6.3 — Follow live logs to see producer/consumer in action
kubectl logs kafka-validation-app -n kafka -f

# Expected output every 60 seconds:
#   Starting Producer logic...
#   Starting Consumer logic...
#   [PRODUCER] Sent: Validated message at Tue Mar 10 09:30:00 2026
#   [CONSUMER] Received: Validated message at Tue Mar 10 09:30:00 2026

# 6.4 — If pod crashes, check events for debug info
kubectl describe pod kafka-validation-app -n kafka

# 6.5 — Restart the validation app (if needed)
kubectl delete pod kafka-validation-app -n kafka
kubectl apply -f main/kafka-test-deploy.yaml


# =============================================================================
# SECTION 7: RUN MANUAL DEMO WITH PYTHON SCRIPTS (Two-Terminal Demo)
# =============================================================================
# This demo runs the modular Python scripts (producer.py / consumer.py)
# inside a Python pod inside the cluster, using Kubernetes internal DNS.
# NOTE: main/config.py points to the external IP (20.121.149.203:9094).
# For internal cluster use, create a pod, copy scripts, and run there.

# 7.1 — Create a Python pod in 'test' namespace
kubectl create namespace test 2>/dev/null || true
kubectl run kafka-demo-pod \
  --image=python:3.12-slim \
  -n test \
  --restart=Never \
  --command -- sleep 3600

# Wait for pod to be Ready
kubectl get pod kafka-demo-pod -n test -w

# 7.2 — Install kafka-python library inside the pod
kubectl exec -n test kafka-demo-pod -- pip install kafka-python

# 7.3 — Copy all required Python files to the pod
kubectl cp main/config.py       test/kafka-demo-pod:/config.py
kubectl cp main/kafka_client.py test/kafka-demo-pod:/kafka_client.py
kubectl cp main/producer.py     test/kafka-demo-pod:/producer.py
kubectl cp main/consumer.py     test/kafka-demo-pod:/consumer.py
kubectl cp main/test_connection.py test/kafka-demo-pod:/test_connection.py

# 7.4 — (Optional) First verify broker connectivity
kubectl exec -n test kafka-demo-pod -- python -u /test_connection.py

# ─── TERMINAL 1: Start the Producer ─────────────────────────────────────────
kubectl exec -n test kafka-demo-pod -- python -u /producer.py
# Sends a "Data packet sent by rajnish at <timestamp>" every 5 seconds.
# Press Ctrl+C to stop.

# ─── TERMINAL 2: Start the Consumer ─────────────────────────────────────────
kubectl exec -n test kafka-demo-pod -- python -u /consumer.py
# Reads ALL messages from the topic (earliest) and prints them live.
# Press Ctrl+C to stop.


# =============================================================================
# SECTION 8: RUN ALL-IN-ONE DEMO (app.py)
# =============================================================================
# app.py runs producer + consumer together in a single process.
# Producer runs as a daemon thread; consumer runs in the foreground.

# Inside the pod:
kubectl exec -n test kafka-demo-pod -- python -u /app.py
# (Copy app.py to the pod first using kubectl cp if needed)
kubectl cp main/app.py test/kafka-demo-pod:/app.py


# =============================================================================
# SECTION 9: CLI PRODUCER / CONSUMER (Built-in Kafka Tools)
# =============================================================================
# Use Kafka's built-in CLI tools for quick sanity checks without Python.

# ─── TERMINAL 1: Produce messages via CLI ────────────────────────────────────
kubectl exec -it kafka-client -n kafka -- \
  kafka-console-producer.sh \
    --bootstrap-server kafka:9092 \
    --topic test-pipeline
# Type any message then press Enter.  Ctrl+C to stop.

# ─── TERMINAL 2: Consume messages via CLI ────────────────────────────────────
kubectl exec -it kafka-client -n kafka -- \
  kafka-console-consumer.sh \
    --bootstrap-server kafka:9092 \
    --topic test-pipeline \
    --from-beginning

# Consume only new messages (skip history):
kubectl exec -it kafka-client -n kafka -- \
  kafka-console-consumer.sh \
    --bootstrap-server kafka:9092 \
    --topic test-pipeline


# =============================================================================
# SECTION 10: CONSUMER GROUP MANAGEMENT
# =============================================================================

# Inside kafka-client pod:

# 10.1 — List all consumer groups
kafka-consumer-groups.sh \
  --bootstrap-server kafka:9092 \
  --list

# 10.2 — Describe a consumer group (see lag / offsets per partition)
kafka-consumer-groups.sh \
  --bootstrap-server kafka:9092 \
  --describe \
  --group demo-group

# 10.3 — Reset offsets (re-read all messages from beginning)
kafka-consumer-groups.sh \
  --bootstrap-server kafka:9092 \
  --group demo-group \
  --topic test-pipeline \
  --reset-offsets \
  --to-earliest \
  --execute


# =============================================================================
# SECTION 11: FAULT-TOLERANCE DEMO (Broker Failure Simulation)
# =============================================================================
# Kafka replicates data across brokers. Delete a broker and watch Kafka recover.

# 11.1 — Delete one broker pod (it will restart automatically via StatefulSet)
kubectl delete pod kafka-broker-1 -n kafka

# 11.2 — Watch the broker restart (should come back in ~30-60 seconds)
kubectl get pods -n kafka -w

# 11.3 — While broker is restarting, verify consumer still receives messages
kubectl logs kafka-validation-app -n kafka -f

# 11.4 — After recovery, verify leader election happened (ISR should be full)
kubectl exec -it kafka-client -n kafka -- \
  kafka-topics.sh --describe \
    --bootstrap-server kafka:9092 \
    --topic test-pipeline


# =============================================================================
# SECTION 12: CONSUMER SCALING DEMO (Multiple Consumers, Same Group)
# =============================================================================
# When multiple consumers share the same group.id, Kafka distributes partitions
# across them — each message goes to exactly ONE consumer.

# ─── TERMINAL 1 ──────────────────────────────────────────────────────────────
kubectl exec -n test kafka-demo-pod -- python -u /consumer.py

# ─── TERMINAL 2 (same group, different messages) ─────────────────────────────
kubectl exec -n test kafka-demo-pod -- python -u /consumer.py

# To have TWO consumers each receive ALL messages, change group_id in config.py:
#   group_id="demo-group-2"   ← different group = independent offset tracking


# =============================================================================
# SECTION 13: EXTERNAL ACCESS (Connect from Local Machine)
# =============================================================================
# External LoadBalancer IPs are configured in main/values.yaml:
#   Broker 0: 52.186.140.22:9094
#   Broker 1: 13.82.136.111:9094
#   Broker 2: 172.191.54.0:9094
#
# main/config.py already points to: 20.121.149.203:9094
# If that changes, update BOOTSTRAP_SERVER in main/config.py.

# Install dependencies locally (in a virtualenv):
cd main
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate
pip install kafka-python

# Check connectivity from your laptop:
python test_connection.py

# Run producer locally (Terminal 1):
python producer.py

# Run consumer locally (Terminal 2):
python consumer.py


# =============================================================================
# SECTION 14: USEFUL MONITORING & DEBUG COMMANDS
# =============================================================================

# Check all resources in kafka namespace
kubectl get all -n kafka

# View Kafka broker config
kubectl exec kafka-broker-0 -n kafka -- cat /bitnami/kafka/config/server.properties

# Check broker logs (live)
kubectl logs kafka-broker-0 -n kafka -f

# Check ZooKeeper logs (if running in ZooKeeper mode)
# kubectl logs kafka-zookeeper-0 -n kafka --tail=50

# Describe pod for events (useful if a pod is stuck or crashing)
kubectl describe pod kafka-broker-0 -n kafka
kubectl describe pod kafka-validation-app -n kafka

# Check Helm release status
helm status kafka -n kafka

# View what values are currently deployed
helm get values kafka -n kafka


# =============================================================================
# SECTION 15: CLEANUP
# =============================================================================

# 15.1 — Remove automated validation app only
kubectl delete -f main/kafka-test-deploy.yaml

# 15.2 — Remove manual demo pod
kubectl delete pod kafka-demo-pod -n test
kubectl delete pod kafka-client -n kafka --ignore-not-found

# 15.3 — Remove the entire Kafka cluster (DESTRUCTIVE — data will be lost!)
helm uninstall kafka -n kafka
kubectl delete pvc --all -n kafka
kubectl delete namespace kafka

# 15.4 — Remove test namespace
kubectl delete namespace test
