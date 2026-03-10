# Kafka Producer-Consumer Setup on AKS

This guide provides complete documentation for deploying and testing a Kafka cluster with a Python producer-consumer application on Azure Kubernetes Service (AKS).

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [File Structure](#file-structure)
- [Step 1: Deploy Kafka Cluster](#step-1-deploy-kafka-cluster)
- [Step 2: Verify Kafka Cluster](#step-2-verify-kafka-cluster)
- [Step 3: Deploy the Test Application](#step-3-deploy-the-test-application)
- [Step 4: Validate Message Flow](#step-4-validate-message-flow)
- [Step 5: Advanced Testing](#step-5-advanced-testing)
- [Troubleshooting](#troubleshooting)
- [Cleanup](#cleanup)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         AKS Cluster                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  kafka namespace                     │   │
│  │                                                      │   │
│  │  ┌─────────────────┐     ┌─────────────────┐        │   │
│  │  │   ZooKeeper     │────▶│  Kafka Broker   │        │   │
│  │  │   (1 replica)   │     │   (3 replicas)  │        │   │
│  │  └─────────────────┘     └────────┬────────┘        │   │
│  │                                   │                  │   │
│  │                                   ▼                  │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │         kafka-validation-app (Pod)           │   │   │
│  │  │                                              │   │   │
│  │  │   ┌──────────────┐    ┌──────────────┐      │   │   │
│  │  │   │   Producer   │───▶│   Consumer   │      │   │   │
│  │  │   │   (Thread)   │    │   (Main)     │      │   │   │
│  │  │   └──────────────┘    └──────────────┘      │   │   │
│  │  │                                              │   │   │
│  │  │   Topic: test-pipeline                       │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

| Requirement | Version | Verification Command |
|------------|---------|---------------------|
| **kubectl** | 1.25+ | `kubectl version --client` |
| **Helm** | 3.x | `helm version` |
| **AKS Cluster** | Running | `kubectl get nodes` |

---

## File Structure

```
kafka/
├── README.md              # This documentation
├── app.py                 # Local Python producer-consumer script
├── kafka-test-deploy.yaml # Kubernetes manifest for test app
└── values.yaml            # Helm values for Bitnami Kafka chart
```

---

## Step 1: Deploy Kafka Cluster

### 1.1 Create the `kafka` Namespace

```bash
kubectl create namespace kafka
```

### 1.2 Add the Bitnami Helm Repository

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### 1.3 Deploy Kafka Using the Provided Values

```bash
# Navigate to the kafka folder
cd kafka

# Install/Upgrade Kafka
helm upgrade --install kafka bitnami/kafka \
  --namespace kafka \
  --values values.yaml \
  --wait --timeout 10m
```

> **Note:** The `values.yaml` uses **Zookeeper mode** with legacy images (KRaft is disabled). This is configured for dev/test environments with PLAINTEXT listeners.

---

## Step 2: Verify Kafka Cluster

### 2.1 Check Kafka Pods

```bash
kubectl get pods -n kafka -w
```

**Expected Output (wait until all are Running):**

```
NAME                   READY   STATUS    RESTARTS   AGE
kafka-broker-0         1/1     Running   0          2m
kafka-broker-1         1/1     Running   0          2m
kafka-broker-2         1/1     Running   0          2m
kafka-zookeeper-0      1/1     Running   0          3m
```

### 2.2 Check Kafka Services

```bash
kubectl get svc -n kafka
```

**Expected Output:**

```
NAME                TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
kafka               ClusterIP   10.0.xxx.xxx   <none>        9092/TCP         3m
kafka-headless      ClusterIP   None           <none>        9092/TCP         3m
kafka-zookeeper     ClusterIP   10.0.xxx.xxx   <none>        2181/TCP,2888/TCP,3888/TCP   3m
```

### 2.3 View Kafka Logs

```bash
# Check broker logs
kubectl logs kafka-broker-0 -n kafka --tail=50

# Check ZooKeeper logs
kubectl logs kafka-zookeeper-0 -n kafka --tail=50
```

---

## Step 3: Deploy the Test Application

### 3.1 Apply the Test Deployment

```bash
kubectl apply -f kafka-test-deploy.yaml
```

This creates:
1. **ConfigMap** (`kafka-test-app-code`) - Stores the Python script
2. **Pod** (`kafka-validation-app`) - Runs the producer-consumer app

### 3.2 Verify Pod is Running

```bash
kubectl get pods -n kafka -l app=kafka-tester
```

**Expected Output:**

```
NAME                    READY   STATUS    RESTARTS   AGE
kafka-validation-app    1/1     Running   0          1m
```

---

## Step 4: Validate Message Flow

### 4.1 Watch Live Logs (Primary Test)

```bash
kubectl logs kafka-validation-app -n kafka -f
```

**Expected Output:**

```
Starting Producer logic...
Starting Consumer logic...
 [PRODUCER] Sent: Validated message at Mon Jan 31 12:00:00 2026
 [CONSUMER] Received: Validated message at Mon Jan 31 12:00:00 2026
 [PRODUCER] Sent: Validated message at Mon Jan 31 12:01:00 2026
 [CONSUMER] Received: Validated message at Mon Jan 31 12:01:00 2026
...
```

> **Success Criteria:** You see both `[PRODUCER] Sent:` AND `[CONSUMER] Received:` messages appearing periodically (every 60 seconds).

### 4.2 Describe Pod for Events

```bash
kubectl describe pod kafka-validation-app -n kafka
```

---

## Step 5: Advanced Testing

### 5.1 Manual Producer/Consumer Test (Inside Cluster)

#### Create a Debug Pod

```bash
kubectl run kafka-client --restart='Never' \
  --image docker.io/bitnami/kafka:3.3.2-debian-11-r11 \
  --namespace kafka \
  --command -- sleep infinity
```

#### Connect to the Debug Pod

```bash
kubectl exec -it kafka-client -n kafka -- bash
```

#### Create a Topic Manually

```bash
kafka-topics.sh --create \
  --bootstrap-server kafka:9092 \
  --replication-factor 3 \
  --partitions 3 \
  --topic my-test-topic
```

#### List All Topics

```bash
kafka-topics.sh --list --bootstrap-server kafka:9092
```

#### Produce Messages

```bash
kafka-console-producer.sh --bootstrap-server kafka:9092 --topic my-test-topic
# Type messages and press Enter
> Hello Kafka!
> This is a test message
> ^C (Ctrl+C to exit)
```

#### Consume Messages (New Terminal)

```bash
kubectl exec -it kafka-client -n kafka -- bash

kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic my-test-topic \
  --from-beginning
```

**Expected Output:**

```
Hello Kafka!
This is a test message
```

### 5.2 Broker Failure Simulation

Test Kafka's fault tolerance by deleting a broker:

```bash
# Delete one broker
kubectl delete pod kafka-broker-1 -n kafka

# Watch pods (broker should restart automatically)
kubectl get pods -n kafka -w

# Check if consumer still receives messages
kubectl logs kafka-validation-app -n kafka -f
```

> **Expected:** The broker pod restarts, and the producer-consumer app continues working without data loss.

### 5.3 Check Topic Details

```bash
kubectl exec -it kafka-client -n kafka -- \
  kafka-topics.sh --describe --bootstrap-server kafka:9092 --topic test-pipeline
```

**Expected Output:**

```
Topic: test-pipeline    TopicId: xxxx    PartitionCount: 1    ReplicationFactor: 1
    Topic: test-pipeline    Partition: 0    Leader: 0    Replicas: 0    Isr: 0
```

---

## Troubleshooting

### Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| `NoBrokersAvailable` | Kafka not ready | Wait for all broker pods to be Running |
| `kafka-validation-app` in `CrashLoopBackOff` | Dependency install failed | Check logs: `kubectl logs kafka-validation-app -n kafka` |
| Producer sends but Consumer doesn't receive | Topic not created | Topics are auto-created on first message; check topic exists |
| `InvalidReplicationException` | Not enough brokers | Ensure all 3 brokers are running |

### Debug Commands

```bash
# Check all resources in kafka namespace
kubectl get all -n kafka

# View detailed pod events
kubectl describe pod <pod-name> -n kafka

# Check persistent volume claims
kubectl get pvc -n kafka

# View Kafka broker configuration
kubectl exec kafka-broker-0 -n kafka -- cat /bitnami/kafka/config/server.properties
```

### Restart Test App

```bash
kubectl delete pod kafka-validation-app -n kafka
kubectl apply -f kafka-test-deploy.yaml
```

---

## Cleanup

### Remove Test Application Only

```bash
kubectl delete -f kafka-test-deploy.yaml
kubectl delete pod kafka-client -n kafka --ignore-not-found
```

### Remove Entire Kafka Cluster

```bash
# Uninstall Helm release
helm uninstall kafka -n kafka

# Delete PVCs (data will be lost!)
kubectl delete pvc --all -n kafka

# Delete namespace
kubectl delete namespace kafka
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `kubectl get pods -n kafka` | List all Kafka pods |
| `kubectl logs kafka-validation-app -n kafka -f` | Watch test app logs |
| `kubectl exec -it kafka-client -n kafka -- bash` | Shell into debug pod |
| `helm upgrade --install kafka bitnami/kafka -n kafka -f values.yaml` | Deploy/Update Kafka |
| `kubectl delete pod kafka-broker-0 -n kafka` | Simulate broker failure |

---

## Configuration Reference

### Key `values.yaml` Settings

| Setting | Value | Description |
|---------|-------|-------------|
| `kraft.enabled` | `false` | Uses ZooKeeper mode (legacy) |
| `broker.replicaCount` | `3` | Number of Kafka brokers |
| `zookeeper.replicaCount` | `1` | ZooKeeper instances |
| `broker.persistence.size` | `10Gi` | Storage per broker |
| `broker.persistence.storageClass` | `managed-csi` | Azure CSI storage class |

### Kafka Endpoints

| Service | Endpoint | Port |
|---------|----------|------|
| Kafka Broker | `kafka:9092` | 9092 |
| ZooKeeper | `kafka-zookeeper:2181` | 2181 |

---

## Summary

✅ **Deploy:** `helm upgrade --install kafka bitnami/kafka -n kafka -f values.yaml`  
✅ **Deploy Test App:** `kubectl apply -f kafka-test-deploy.yaml`  
✅ **Verify:** `kubectl logs kafka-validation-app -n kafka -f`  
✅ **Success:** See `[PRODUCER] Sent` AND `[CONSUMER] Received` messages
