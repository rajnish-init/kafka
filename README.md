# E-Commerce Order Processing System

A microservices-based e-commerce order processing system built with Python, FastAPI, and Docker.

## Overview

This project demonstrates a microservices architecture with three interconnected services that work together to process customer orders, manage inventory, and send notifications.

## Services

| Service | Port | Purpose |
|---------|------|---------|
| Order Service | 8080 | Orchestrates order processing, validates orders, coordinates with other services |
| Inventory Service | 8081 | Manages product inventory, checks stock, reserves items |
| Notification Service | 8082 | Sends order confirmations and status updates to customers |

## Architecture

For a detailed architecture diagram and explanation, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Quick Start

### Prerequisites

- Docker
- Docker Compose

### Running the System

1. Clone the repository
2. Navigate to the project directory
3. Run:

```bash
docker-compose up --build
```

This will start all three services. The services will be available at:
- Order Service: http://localhost:8080
- Inventory Service: http://localhost:8081
- Notification Service: http://localhost:8082

### Testing the System

#### 1. Check Service Health

```bash
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health
```

#### 2. View Available Inventory

```bash
curl http://localhost:8081/inventory
```

#### 3. Create an Order

```bash
curl -X POST http://localhost:8080/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "items": [
      {
        "product_id": "PROD001",
        "quantity": 2,
        "price": 79.99
      },
      {
        "product_id": "PROD002",
        "quantity": 1,
        "price": 29.99
      }
    ]
  }'
```

#### 4. Retrieve Order Details

Replace `{order_id}` with the actual order ID returned from step 3:

```bash
curl http://localhost:8080/orders/{order_id}
```

#### 5. List All Orders

```bash
curl http://localhost:8080/orders
```

#### 6. View All Notifications

```bash
curl http://localhost:8082/notifications
```

## How It Works

When you place an order:

1. **Order Service** receives the order request and validates the data
2. **Order Service** calls **Inventory Service** to check stock availability for each item
3. If stock is available, **Order Service** calls **Inventory Service** to reserve the items
4. **Order Service** stores the confirmed order in memory
5. **Order Service** calls **Notification Service** to send confirmation to the customer
6. **Order Service** returns the order confirmation to you

Each step is logged, allowing you to trace the flow of data through the system.

## Directory Structure

```
.
├── order-service/
│   ├── main.py              # Order Service implementation
│   ├── Dockerfile           # Docker configuration
│   ├── requirements.txt    # Python dependencies
│   └── README.md           # Service documentation
├── inventory-service/
│   ├── main.py              # Inventory Service implementation
│   ├── Dockerfile           # Docker configuration
│   ├── requirements.txt    # Python dependencies
│   └── README.md           # Service documentation
├── notification-service/
│   ├── main.py              # Notification Service implementation
│   ├── Dockerfile           # Docker configuration
│   ├── requirements.txt    # Python dependencies
│   └── README.md           # Service documentation
├── docker-compose.yml       # Docker Compose orchestration
├── ARCHITECTURE.md          # Detailed architecture documentation
└── README.md               # This file
```

## Technology Stack

- **Language**: Python 3.11
- **Framework**: FastAPI
- **HTTP Client**: httpx (for synchronous calls between services)
- **Containerization**: Docker
- **Orchestration**: Docker Compose

## Features

- Microservices architecture with independent, scalable services
- RESTful API design
- In-memory data storage for demonstration purposes
- Comprehensive logging at each step
- Health checks for all services
- Order validation and inventory reservation
- Email and SMS notification simulation
- Docker support for easy deployment

## Learning Objectives

This project is designed to help you learn:

1. **Microservices Architecture**: How to break down a system into independent services
2. **Service Communication**: How services communicate via synchronous HTTP calls
3. **API Design**: RESTful API design principles with FastAPI
4. **Containerization**: How to containerize applications with Docker
5. **Orchestration**: How to manage multiple services with Docker Compose
6. **Service Coordination**: How one service orchestrates the flow of data through other services
7. **Error Handling**: How to handle failures and communicate errors between services

## Service-Specific Documentation

- [Order Service Documentation](order-service/README.md)
- [Inventory Service Documentation](inventory-service/README.md)
- [Notification Service Documentation](notification-service/README.md)

## Development

### Running Services Individually

Each service can be run independently for development:

```bash
# Order Service
cd order-service
pip install -r requirements.txt
python main.py

# Inventory Service
cd inventory-service
pip install -r requirements.txt
python main.py

# Notification Service
cd notification-service
pip install -r requirements.txt
python main.py
```

### Building Individual Docker Images

```bash
# Build Order Service
docker build -t order-service ./order-service

# Build Inventory Service
docker build -t inventory-service ./inventory-service

# Build Notification Service
docker build -t notification-service ./notification-service
```

## Stopping the System

```bash
docker-compose down
```

To stop and remove all containers, networks, and volumes:

```bash
docker-compose down -v
```

## Viewing Logs

View logs for all services:
```bash
docker-compose logs
```

View logs for a specific service:
```bash
docker-compose logs order-service
docker-compose logs inventory-service
docker-compose logs notification-service
```

Follow logs in real-time:
```bash
docker-compose logs -f
```

## Limitations

This is a demonstration project with the following limitations:

- **In-memory storage**: Data is lost when containers restart. In production, use a database.
- **No authentication**: APIs are not secured. In production, add authentication and authorization.
- **Synchronous communication**: Services communicate synchronously. In production, consider asynchronous messaging.
- **No retry logic**: Failed HTTP calls are not retried. In production, implement retry mechanisms.
- **No distributed tracing**: Tracing requests across services requires additional tools.
- **Single instance scaling**: Current implementation doesn't support stateless scaling with in-memory storage.

## Future Enhancements

- Add persistent database storage
- Implement asynchronous messaging with Kafka or RabbitMQ
- Add an API Gateway
- Implement distributed tracing
- Add monitoring and alerting
- Implement circuit breakers for resilience
- Add retry mechanisms
- Implement idempotent operations
- Add authentication and authorization

## License

This is a learning project. Feel free to use it for educational purposes.
