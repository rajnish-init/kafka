# E-Commerce Order Processing System - Architecture

## System Overview

This is a microservices-based e-commerce order processing system consisting of three interconnected services that work together to process customer orders, manage inventory, and send notifications.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT / CUSTOMER                                  │
│                                                                              │
│                    Web Browser / Mobile App / cURL                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ HTTP POST /orders
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORDER SERVICE (Port 8080)                            │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  POST /orders                                                        │  │
│  │    - Receives order request                                          │  │
│  │    - Validates order data                                            │  │
│  │    - Generates unique order ID                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    │ 1. Check Stock                         │
│                                    │ GET /inventory/{product_id}            │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  INVENTORY SERVICE (Port 8081)                                       │  │
│  │    - Manages product inventory                                       │  │
│  │    - Checks stock availability                                       │  │
│  │    - Returns stock status                                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    │ Stock Available                        │
│                                    │                                         │
│                                    │ 2. Reserve Inventory                   │
│                                    │ PUT /inventory/{product_id}/reserve     │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  INVENTORY SERVICE (Port 8081)                                       │  │
│  │    - Reserves inventory items                                        │  │
│  │    - Deducts stock quantity                                          │  │
│  │    - Returns updated stock                                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    │ Reserved                               │
│                                    │                                         │
│                                    │ 3. Store Order                         │
│                                    │ (In-memory storage)                    │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ORDER STORAGE                                                        │  │
│  │    - Stores confirmed orders                                         │  │
│  │    - Quick retrieval by order ID                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    │ 4. Send Notification                   │
│                                    │ POST /notify                           │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  NOTIFICATION SERVICE (Port 8082)                                    │  │
│  │    - Prepares notification content                                    │  │
│  │    - Simulates email sending                                         │  │
│  │    - Simulates SMS sending                                           │  │
│  │    - Logs notification events                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    │ Notification Sent                      │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ORDER CONFIRMATION                                                   │  │
│  │    - Returns to client with order ID                                 │  │
│  │    - Includes order status and timestamp                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Service Details

### Order Service (Port 8080)

**Purpose**: Orchestrates the order processing flow

**Responsibilities**:
- Receives and validates customer orders
- Coordinates with Inventory Service to check and reserve stock
- Stores confirmed orders in memory
- Triggers notifications through Notification Service
- Returns order confirmation to the customer

**Key Endpoints**:
- `POST /orders` - Create a new order
- `GET /orders/{order_id}` - Retrieve order details
- `GET /orders` - List all orders
- `GET /health` - Health check

**Dependencies**:
- Inventory Service (http://inventory-service:8081)
- Notification Service (http://notification-service:8082)

### Inventory Service (Port 8081)

**Purpose**: Manages product inventory and stock levels

**Responsibilities**:
- Maintains current stock levels for all products
- Provides stock availability information
- Reserves inventory items when orders are placed
- Tracks stock status (in stock, low stock, out of stock)
- Allows restocking and adding new products

**Key Endpoints**:
- `GET /inventory/{product_id}` - Get product details
- `PUT /inventory/{product_id}/reserve` - Reserve inventory
- `PUT /inventory/{product_id}/replenish` - Add stock
- `GET /inventory/{product_id}/status` - Check stock status
- `GET /inventory` - List all products
- `POST /inventory` - Add new product
- `GET /health` - Health check

**Data Store**: In-memory storage with 5 pre-loaded products

### Notification Service (Port 8082)

**Purpose**: Handles customer notifications

**Responsibilities**:
- Sends order confirmation notifications
- Sends status update notifications (shipped, delivered)
- Simulates email and SMS delivery
- Logs all notification events
- Tracks notification history per order

**Key Endpoints**:
- `POST /notify` - Send a notification
- `GET /notifications/{notification_id}` - Get notification details
- `GET /notifications` - List all notifications
- `GET /notifications/order/{order_id}` - Get order notifications
- `GET /health` - Health check

**Data Store**: In-memory storage of notification history

## Data Flow

### Order Processing Flow (Step by Step)

1. **Customer Request**
   - Customer places an order via `POST /orders`
   - Request includes customer info and order items

2. **Order Validation**
   - Order Service validates the order data
   - Generates a unique order ID

3. **Stock Check**
   - Order Service calls Inventory Service for each item
   - `GET /inventory/{product_id}` checks if stock is available
   - If any item is out of stock, order is rejected

4. **Inventory Reservation**
   - Order Service calls Inventory Service to reserve items
   - `PUT /inventory/{product_id}/reserve` deducts stock
   - Items are now reserved and cannot be sold to others

5. **Order Storage**
   - Order Service stores the confirmed order in memory
   - Order includes all details, status, and timestamp

6. **Notification**
   - Order Service calls Notification Service
   - `POST /notify` triggers email and SMS to customer
   - Notification Service logs the event

7. **Confirmation**
   - Order Service returns confirmation to customer
   - Response includes order ID, status, and timestamp

## Technology Stack

- **Language**: Python 3.11
- **Framework**: FastAPI
- **HTTP Client**: httpx (Order Service)
- **Containerization**: Docker
- **Orchestration**: Docker Compose

## Network Architecture

All services communicate through a Docker bridge network called `e-commerce-network`:

```
┌─────────────────────────────────────────────────┐
│           Docker Network: e-commerce            │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐    ┌──────────────┐          │
│  │ Order Service│───▶│ Inventory    │          │
│  │   :8080      │    │   Service    │          │
│  │              │◀───│    :8081     │          │
│  └──────────────┘    └──────────────┘          │
│         │                   │                   │
│         │                   │                   │
│         ▼                   │                   │
│  ┌──────────────┐           │                   │
│  │ Notification │           │                   │
│  │   Service    │           │                   │
│  │    :8082     │           │                   │
│  └──────────────┘           │                   │
│         │                   │                   │
└─────────┼───────────────────┼───────────────────┘
          │                   │
          │                   │
     ┌────┴────┐        ┌─────┴─────┐
     │  Host    │        │   Host    │
     │  :8080   │        │   :8081   │
     └─────────┘        │   :8082   │
                        └───────────┘
```

## Deployment

### Local Development

```bash
# Build and start all services
docker-compose up --build

# Services will be available at:
# - Order Service:    http://localhost:8080
# - Inventory Service: http://localhost:8081
# - Notification Service: http://localhost:8082
```

### Service Dependencies

The services have the following dependencies:

1. **Order Service** depends on:
   - Inventory Service (must be healthy)
   - Notification Service (must be healthy)

2. **Inventory Service** - No dependencies
3. **Notification Service** - No dependencies

Docker Compose ensures services start in the correct order using health checks.

## Scaling Considerations

Each service can be scaled independently:

```bash
# Scale Order Service to handle more requests
docker-compose up --scale order-service=3

# Scale Inventory Service for high-traffic periods
docker-compose up --scale inventory-service=2
```

Note: The current implementation uses in-memory storage, so scaling requires additional considerations for data consistency.

## Security Considerations

In a production environment, you would add:
- Authentication and authorization
- API rate limiting
- Input sanitization and validation
- HTTPS/TLS encryption
- Secrets management
- Network policies and firewalls

## Future Enhancements

Potential improvements:
- Add a database for persistent storage (PostgreSQL, MongoDB)
- Implement asynchronous messaging (Kafka, RabbitMQ)
- Add an API Gateway
- Implement distributed tracing (Jaeger, Zipkin)
- Add monitoring and alerting (Prometheus, Grafana)
- Implement circuit breakers for resilience
- Add retry mechanisms for failed HTTP calls
- Implement idempotent operations
- Add authentication and authorization
