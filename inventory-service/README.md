# Inventory Service

The Inventory Service is a microservice that manages product inventory for an e-commerce platform.

## Purpose

This service is responsible for:
- Maintaining the current stock levels of all products
- Providing stock availability information
- Reserving inventory items when orders are placed
- Replenishing inventory when stock is added
- Tracking stock status (in stock, low stock, out of stock)

## Why It Exists

In a microservices architecture, the Inventory Service centralizes inventory management logic:
- Provides a single source of truth for stock levels
- Prevents race conditions when multiple orders try to reserve the same items
- Offers a dedicated API for inventory operations
- Enables independent scaling of inventory-related operations

## Technology Stack

- **Language**: Python 3.11
- **Framework**: FastAPI
- **Data Storage**: In-memory storage (for demonstration purposes)
- **Logging**: Python's built-in logging module

## API Endpoints

### 1. `GET /health`
**Purpose**: Health check endpoint to verify the service is running correctly.

**Returns**: Service health status

### 2. `GET /inventory/{product_id}`
**Purpose**: Retrieves the current inventory details for a specific product.

**Purpose**: This endpoint is called by the Order Service to check if enough stock is available before accepting an order.

**Returns**: Product details including current stock quantity and price

### 3. `PUT /inventory/{product_id}/reserve`
**Purpose**: Reserves a specified quantity of a product from inventory.

**Purpose**: This endpoint is called by the Order Service to actually remove items from stock after confirming availability. This ensures items are not sold twice.

**Request Body**:
```json
{
  "quantity": 5
}
```

**Returns**: Reservation confirmation with previous and remaining quantities

### 4. `PUT /inventory/{product_id}/replenish`
**Purpose**: Adds stock back to inventory (e.g., when new shipments arrive).

**Purpose**: This endpoint allows restocking products and increasing available inventory.

**Request Body**:
```json
{
  "quantity": 100
}
```

**Returns**: Replenishment confirmation with previous and new quantities

### 5. `GET /inventory`
**Purpose**: Lists all products currently in inventory.

**Returns**: List of all products with their current stock levels

### 6. `POST /inventory`
**Purpose**: Adds a new product to the inventory system.

**Request Body**:
```json
{
  "product_id": "PROD006",
  "name": "Product Name",
  "quantity": 50,
  "price": 99.99
}
```

**Returns**: Confirmation with the newly added product details

### 7. `GET /inventory/{product_id}/status`
**Purpose**: Checks the stock status of a product (in stock, low stock, or out of stock).

**Purpose**: This endpoint is useful for:
- Displaying stock status on product pages
- Triggering reordering for low stock items
- Alerting customers about availability

**Returns**: Stock status with current quantity and status category

## Initial Inventory

The service starts with 5 pre-loaded products:
- PROD001: Wireless Headphones (50 units, $79.99)
- PROD002: USB-C Charger (100 units, $29.99)
- PROD003: Bluetooth Speaker (30 units, $149.99)
- PROD004: Laptop Stand (25 units, $49.99)
- PROD005: Webcam 1080p (40 units, $89.99)

## Stock Status Logic

- **out_of_stock**: Quantity = 0
- **low_stock**: Quantity < 10
- **in_stock**: Quantity >= 10

## Data Flow in Order Processing

1. Order Service calls `GET /inventory/{product_id}` to check stock availability
2. If stock is sufficient, Order Service calls `PUT /inventory/{product_id}/reserve` to reserve items
3. Inventory Service deducts reserved items from available stock
4. Inventory Service returns updated stock information

## Running Locally

### With Docker
```bash
docker build -t inventory-service .
docker run -p 8081:8081 inventory-service
```

### Directly with Python
```bash
pip install -r requirements.txt
python main.py
```

## Example Usage

Check inventory for a product:
```bash
curl http://localhost:8081/inventory/PROD001
```

Reserve inventory:
```bash
curl -X PUT http://localhost:8081/inventory/PROD001/reserve \
  -H "Content-Type: application/json" \
  -d '{"quantity": 5}'
```

Check stock status:
```bash
curl http://localhost:8081/inventory/PROD001/status
```

List all products:
```bash
curl http://localhost:8081/inventory
```

Add new product:
```bash
curl -X POST http://localhost:8081/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PROD006",
    "name": "Mechanical Keyboard",
    "quantity": 30,
    "price": 129.99
  }'
```

Replenish inventory:
```bash
curl -X PUT http://localhost:8081/inventory/PROD001/replenish \
  -H "Content-Type: application/json" \
  -d '{"quantity": 50}'
```
