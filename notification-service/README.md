# Notification Service

The Notification Service is a microservice that handles customer notifications for an e-commerce platform.

## Purpose

This service is responsible for:
- Sending order confirmation notifications to customers
- Sending notifications for order status updates (shipped, delivered, etc.)
- Simulating both email and SMS delivery
- Logging all notification events for audit purposes
- Tracking notification history per order

## Why It Exists

In a microservices architecture, the Notification Service centralizes all communication with customers:
- Decouples notification logic from the core order processing flow
- Allows independent scaling of notification operations
- Provides a single point for managing notification templates
- Enables easy addition of new notification channels (email, SMS, push notifications, etc.)
- Maintains notification history for troubleshooting and compliance

## Technology Stack

- **Language**: Python 3.11
- **Framework**: FastAPI
- **Data Storage**: In-memory storage (for demonstration purposes)
- **Logging**: Python's built-in logging module

## API Endpoints

### 1. `GET /health`
**Purpose**: Health check endpoint to verify the service is running correctly.

**Returns**: Service health status

### 2. `POST /notify`
**Purpose**: Sends a notification to a customer about their order.

**Purpose**: This endpoint is called by the Order Service after an order is confirmed. It simulates sending both email and SMS notifications.

**Request Body**:
```json
{
  "order_id": "abc-123-def",
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "status": "confirmed"
}
```

**Flow**:
1. Generates a unique notification ID
2. Prepares notification content based on order status
3. Simulates email sending (with 95% success rate)
4. Simulates SMS sending (with 95% success rate)
5. Stores notification record in memory
6. Returns notification confirmation

**Returns**: Notification confirmation with notification ID and type

### 3. `GET /notifications/{notification_id}`
**Purpose**: Retrieves details of a specific notification.

**Returns**: Full notification details including order ID, customer info, and delivery status

### 4. `GET /notifications`
**Purpose**: Lists all notifications in the system.

**Returns**: List of all notifications with count

### 5. `GET /notifications/order/{order_id}`
**Purpose**: Retrieves all notifications sent for a specific order.

**Purpose**: This endpoint is useful for tracking the communication history with a customer about their order.

**Returns**: List of notifications for the specified order

## Notification Types

The service handles different types of notifications based on order status:

### 1. Order Confirmation (`status: "confirmed"`)
- Email: Order confirmation with order details
- SMS: Brief confirmation message

### 2. Order Shipped (`status: "shipped"`)
- Email: Shipment notification with tracking info
- SMS: Brief shipping notification

### 3. Order Delivered (`status: "delivered"`)
- Email: Delivery confirmation and thank you message
- SMS: Brief delivery notification

### 4. Order Update (`status: any other value`)
- Email: Generic status update
- SMS: Brief status update

## Notification Simulation

Since this is a demonstration service:
- Email sending is simulated (no actual emails are sent)
- SMS sending is simulated (no actual SMS messages are sent)
- Each method has a 95% success rate to simulate real-world failures
- All notification events are logged for tracking

## Data Flow in Order Processing

1. Order Service calls `POST /notify` with order details
2. Notification Service determines the notification type based on order status
3. Notification Service prepares email and SMS content
4. Notification Service simulates sending email
5. Notification Service simulates sending SMS
6. Notification Service stores the notification record
7. Notification Service returns confirmation to Order Service

## Running Locally

### With Docker
```bash
docker build -t notification-service .
docker run -p 8082:8082 notification-service
```

### Directly with Python
```bash
pip install -r requirements.txt
python main.py
```

## Example Usage

Send order confirmation:
```bash
curl -X POST http://localhost:8082/notify \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORDER-123",
    "customer_name": "Alice Johnson",
    "customer_email": "alice@example.com",
    "status": "confirmed"
  }'
```

Get notification details:
```bash
curl http://localhost:8082/notifications/{notification_id}
```

List all notifications:
```bash
curl http://localhost:8082/notifications
```

Get notifications for a specific order:
```bash
curl http://localhost:8082/notifications/order/ORDER-123
```

Send shipping notification:
```bash
curl -X POST http://localhost:8082/notify \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORDER-123",
    "customer_name": "Alice Johnson",
    "customer_email": "alice@example.com",
    "status": "shipped"
  }'
```

Send delivery notification:
```bash
curl -X POST http://localhost:8082/notify \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORDER-123",
    "customer_name": "Alice Johnson",
    "customer_email": "alice@example.com",
    "status": "delivered"
  }'
```
