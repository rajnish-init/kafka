from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import logging
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Inventory Service", version="1.0.0")

in_memory_inventory = {
    "PROD001": {"product_id": "PROD001", "name": "Wireless Headphones", "quantity": 50, "price": 79.99},
    "PROD002": {"product_id": "PROD002", "name": "USB-C Charger", "quantity": 100, "price": 29.99},
    "PROD003": {"product_id": "PROD003", "name": "Bluetooth Speaker", "quantity": 30, "price": 149.99},
    "PROD004": {"product_id": "PROD004", "name": "Laptop Stand", "quantity": 25, "price": 49.99},
    "PROD005": {"product_id": "PROD005", "name": "Webcam 1080p", "quantity": 40, "price": 89.99}
}

class InventoryItem(BaseModel):
    product_id: str
    name: str
    quantity: int
    price: float

class ReserveRequest(BaseModel):
    quantity: int

class ReplenishRequest(BaseModel):
    quantity: int

@app.get("/health")
def health_check():
    logger.info("Health check endpoint called - verifies service is running")
    return {"status": "healthy", "service": "Inventory Service"}

@app.get("/inventory/{product_id}")
def get_inventory(product_id: str):
    logger.info(f"Received request to check inventory for product: {product_id}")
    
    if product_id not in in_memory_inventory:
        logger.warning(f"Product {product_id} not found in inventory")
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    
    product = in_memory_inventory[product_id]
    logger.info(f"Found product {product_id}: {product['name']}, Stock: {product['quantity']}")
    
    return {
        "product_id": product["product_id"],
        "name": product["name"],
        "quantity": product["quantity"],
        "price": product["price"]
    }

@app.put("/inventory/{product_id}/reserve")
def reserve_inventory(product_id: str, request: ReserveRequest):
    logger.info(f"Received request to reserve {request.quantity} units of product: {product_id}")
    
    if product_id not in in_memory_inventory:
        logger.warning(f"Product {product_id} not found in inventory")
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    
    current_quantity = in_memory_inventory[product_id]["quantity"]
    
    if current_quantity < request.quantity:
        logger.warning(f"Insufficient stock for {product_id}. Requested: {request.quantity}, Available: {current_quantity}")
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {current_quantity}, Requested: {request.quantity}"
        )
    
    new_quantity = current_quantity - request.quantity
    in_memory_inventory[product_id]["quantity"] = new_quantity
    
    logger.info(f"Successfully reserved {request.quantity} units of {product_id}. New stock: {new_quantity}")
    
    return {
        "product_id": product_id,
        "name": in_memory_inventory[product_id]["name"],
        "previous_quantity": current_quantity,
        "reserved_quantity": request.quantity,
        "remaining_quantity": new_quantity,
        "timestamp": datetime.now().isoformat()
    }

@app.put("/inventory/{product_id}/replenish")
def replenish_inventory(product_id: str, request: ReplenishRequest):
    logger.info(f"Received request to replenish {request.quantity} units of product: {product_id}")
    
    if product_id not in in_memory_inventory:
        logger.warning(f"Product {product_id} not found in inventory")
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    
    current_quantity = in_memory_inventory[product_id]["quantity"]
    new_quantity = current_quantity + request.quantity
    in_memory_inventory[product_id]["quantity"] = new_quantity
    
    logger.info(f"Successfully replenished {request.quantity} units of {product_id}. New stock: {new_quantity}")
    
    return {
        "product_id": product_id,
        "name": in_memory_inventory[product_id]["name"],
        "previous_quantity": current_quantity,
        "replenished_quantity": request.quantity,
        "new_quantity": new_quantity,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/inventory")
def list_inventory():
    logger.info("Listing all products in inventory")
    return {
        "count": len(in_memory_inventory),
        "products": list(in_memory_inventory.values())
    }

@app.post("/inventory")
def add_product(product: InventoryItem):
    logger.info(f"Adding new product to inventory: {product.product_id}")
    
    if product.product_id in in_memory_inventory:
        logger.warning(f"Product {product.product_id} already exists")
        raise HTTPException(status_code=400, detail=f"Product {product.product_id} already exists")
    
    in_memory_inventory[product.product_id] = product.dict()
    logger.info(f"Successfully added product {product.product_id}")
    
    return {
        "message": "Product added successfully",
        "product": product.dict()
    }

@app.get("/inventory/{product_id}/status")
def get_stock_status(product_id: str):
    logger.info(f"Checking stock status for product: {product_id}")
    
    if product_id not in in_memory_inventory:
        logger.warning(f"Product {product_id} not found in inventory")
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    
    quantity = in_memory_inventory[product_id]["quantity"]
    
    if quantity == 0:
        status = "out_of_stock"
        logger.warning(f"Product {product_id} is out of stock")
    elif quantity < 10:
        status = "low_stock"
        logger.warning(f"Product {product_id} has low stock: {quantity}")
    else:
        status = "in_stock"
        logger.info(f"Product {product_id} is in stock: {quantity}")
    
    return {
        "product_id": product_id,
        "name": in_memory_inventory[product_id]["name"],
        "quantity": quantity,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Inventory Service on port 8081")
    logger.info(f"Initial inventory loaded with {len(in_memory_inventory)} products")
    uvicorn.run(app, host="0.0.0.0", port=8081)
