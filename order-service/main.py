from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
import logging
import uuid
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Order Service", version="1.0.0")

in_memory_orders = {}

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class Order(BaseModel):
    customer_name: str
    customer_email: str
    items: List[OrderItem]

class OrderResponse(BaseModel):
    order_id: str
    status: str
    message: str
    timestamp: str

@app.get("/health")
def health_check():
    logger.info("Health check endpoint called - verifies service is running")
    return {"status": "healthy", "service": "Order Service"}

@app.post("/orders", response_model=OrderResponse)
async def create_order(order: Order):
    logger.info(f"Received new order request from customer: {order.customer_name}")
    logger.info(f"Order contains {len(order.items)} items")
    
    order_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    logger.info(f"Step 1: Generated order ID: {order_id}")
    
    try:
        async with httpx.AsyncClient() as client:
            logger.info("Step 2: Connecting to Inventory Service to check stock")
            
            for item in order.items:
                inventory_url = f"http://inventory-service:8081/inventory/{item.product_id}"
                logger.info(f"Checking inventory for product: {item.product_id}, quantity: {item.quantity}")
                
                response = await client.get(inventory_url)
                if response.status_code != 200:
                    logger.error(f"Inventory check failed for product {item.product_id}")
                    raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
                
                inventory_data = response.json()
                logger.info(f"Current stock for product {item.product_id}: {inventory_data['quantity']}")
                
                if inventory_data['quantity'] < item.quantity:
                    logger.warning(f"Insufficient stock for product {item.product_id}. Requested: {item.quantity}, Available: {inventory_data['quantity']}")
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Insufficient stock for product {item.product_id}. Available: {inventory_data['quantity']}, Requested: {item.quantity}"
                    )
            
            logger.info("Step 3: All items have sufficient stock, proceeding to reserve inventory")
            
            for item in order.items:
                update_url = f"http://inventory-service:8081/inventory/{item.product_id}/reserve"
                logger.info(f"Reserving {item.quantity} units of product {item.product_id}")
                
                response = await client.put(update_url, json={"quantity": item.quantity})
                if response.status_code != 200:
                    logger.error(f"Failed to reserve inventory for product {item.product_id}")
                    raise HTTPException(status_code=500, detail=f"Failed to reserve product {item.product_id}")
                
                logger.info(f"Successfully reserved inventory for product {item.product_id}")
            
            logger.info("Step 4: Inventory reservation complete, storing order in memory")
            
            in_memory_orders[order_id] = {
                "order_id": order_id,
                "customer_name": order.customer_name,
                "customer_email": order.customer_email,
                "items": [item.dict() for item in order.items],
                "total_amount": sum(item.price * item.quantity for item in order.items),
                "status": "confirmed",
                "timestamp": timestamp
            }
            
            logger.info(f"Order {order_id} stored successfully in memory")
            
            logger.info("Step 5: Connecting to Notification Service to send confirmation")
            
            notification_url = "http://notification-service:8082/notify"
            notification_data = {
                "order_id": order_id,
                "customer_name": order.customer_name,
                "customer_email": order.customer_email,
                "status": "confirmed"
            }
            
            notification_response = await client.post(notification_url, json=notification_data)
            
            if notification_response.status_code == 200:
                logger.info(f"Order confirmation notification sent successfully to {order.customer_email}")
            else:
                logger.warning(f"Notification service returned status {notification_response.status_code}")
            
            logger.info(f"Order {order_id} processing completed successfully")
            
            return OrderResponse(
                order_id=order_id,
                status="confirmed",
                message=f"Order {order_id} has been confirmed and notification sent",
                timestamp=timestamp
            )
            
    except httpx.RequestError as e:
        logger.error(f"Network error when calling external services: {str(e)}")
        raise HTTPException(status_code=503, detail="External service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error processing order: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    logger.info(f"Retrieving order details for order ID: {order_id}")
    
    if order_id not in in_memory_orders:
        logger.warning(f"Order {order_id} not found in memory")
        raise HTTPException(status_code=404, detail="Order not found")
    
    logger.info(f"Order {order_id} found, returning details")
    return in_memory_orders[order_id]

@app.get("/orders")
def list_orders():
    logger.info("Listing all orders in memory")
    return {
        "count": len(in_memory_orders),
        "orders": list(in_memory_orders.values())
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Order Service on port 8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
