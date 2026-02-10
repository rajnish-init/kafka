# Order Service

The Order Service is a microservice that handles order processing for an e-commerce platform.

## Purpose

This service is the entry point for customer orders. It:
- Receives new order requests from customers via REST API
- Validates order data to ensure it's complete and correct
- Coordinates with the Inventory Service to check stock availability
- Reserves inventory items to prevent over-selling
- Stores confirmed orders in memory for quick retrieval
- Triggers notifications through the Notification Service to inform customers

## Why It Exists

In a microservices architecture, the Order Service serves as the orchestrator for the order processing flow. It:
- Provides a single point of entry for creating orders
- Centralizes order validation logic
- Coordinates communication between different services
- Maintains order records for reference and tracking

## Technology Stack

- **Language**: Python 3.11
- **Framework**: FastAPI
- **HTTP Client**: httpx for making synchronous calls to other services
- **Logging**: Python's built-in logging module

## API Endpoints

### 1. `GET /health`
**Purpose**: Health check endpoint to verify the service is running correctly.

**Returns**: Service health status

### 2. `POST /orders`
**Purpose**: Creates a new order and initiates the order processing flow.

**Request Body**:
```json
{
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "items": [
    {
      "product_id": "PROD001",
      "quantity": 2,
      "price": 79.99
    }
  ]
}
```

**Flow**:
1. Generates a unique order ID
2. Calls Inventory Service to check stock for each item
3. Calls Inventory Service to reserve inventory items
4. Stores the order in memory
5. Calls Notification Service to send confirmation
6. Returns order confirmation to the client

**Returns**: Order confirmation with order ID and status

### 3. `GET /orders/{order_id}`
**Purpose**: Retrieves details of a specific order by its ID.

**Returns**: Full order details including items, status, and timestamp

### 4. `GET /orders`
**Purpose**: Lists all orders currently stored in memory.

**Returns**: List of all orders with count

## Data Flow

When a customer places an order:
1. Client sends POST request to `/orders` endpoint
2. Order Service validates the order data
3. Order Service checks inventory with Inventory Service (synchronous HTTP call)
4. Order Service reserves inventory items with Inventory Service (synchronous HTTP call)
5. Order Service stores the confirmed order in memory
6. Order Service triggers notification with Notification Service (synchronous HTTP call)
7. Order Service returns confirmation to client

## Dependencies

- **Inventory Service**: Must be available at `http://inventory-service:8081`
- **Notification Service**: Must be available at `http://notification-service:8082`

## Running Locally

### With Docker
```bash
docker build -t order-service .
docker run -p 8080:8080 order-service
```

### Directly with Python
```bash
pip install -r requirements.txt
python main.py
```

## Example Usage

Create a new order:
```bash
curl -X POST http://localhost:8080/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Alice Johnson",
    "customer_email": "alice@example.com",
    "items": [
      {
        "product_id": "PROD001",
        "quantity": 1,
        "price": 79.99
      },
      {
        "product_id": "PROD002",
        "quantity": 2,
        "price": 29.99
      }
    ]
  }'
```

Get order details:
```bash
curl http://localhost:8080/orders/{order_id}
```

List all orders:
```bash
curl http://localhost:8080/orders
```
