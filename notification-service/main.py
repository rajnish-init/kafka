from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime
import random
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service", version="1.0.0")

in_memory_notifications = []

class NotificationRequest(BaseModel):
    order_id: str
    customer_name: str
    customer_email: str
    status: str

class NotificationResponse(BaseModel):
    notification_id: str
    message: str
    type: str
    timestamp: str

@app.get("/health")
def health_check():
    logger.info("Health check endpoint called - verifies service is running")
    return {"status": "healthy", "service": "Notification Service"}

@app.post("/notify", response_model=NotificationResponse)
def send_notification(request: NotificationRequest):
    logger.info(f"Received notification request for order: {request.order_id}")
    logger.info(f"Customer: {request.customer_name}, Email: {request.customer_email}")
    logger.info(f"Order status: {request.status}")
    
    notification_id = f"NOTIF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
    timestamp = datetime.now().isoformat()
    
    logger.info(f"Step 1: Generated notification ID: {notification_id}")
    
    logger.info("Step 2: Preparing notification content")
    
    if request.status == "confirmed":
        email_subject = f"Order Confirmed - {request.order_id}"
        email_body = f"""
        Dear {request.customer_name},

        Your order {request.order_id} has been confirmed!

        We're pleased to inform you that your order is being processed and will be shipped soon.

        Order Details:
        - Order ID: {request.order_id}
        - Status: Confirmed
        - Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        Thank you for your purchase!

        Best regards,
        E-commerce Team
        """
        sms_message = f"Order Confirmed! Your order {request.order_id} has been confirmed. Thank you for your purchase!"
        notification_type = "order_confirmation"
        
        logger.info(f"Prepared {notification_type} notification for order {request.order_id}")
        
    elif request.status == "shipped":
        email_subject = f"Order Shipped - {request.order_id}"
        email_body = f"""
        Dear {request.customer_name},

        Great news! Your order {request.order_id} has been shipped!

        Your package is on its way to you. You can track your order using the order ID.

        Order Details:
        - Order ID: {request.order_id}
        - Status: Shipped
        - Shipping Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        Thank you for shopping with us!

        Best regards,
        E-commerce Team
        """
        sms_message = f"Order Shipped! Your order {request.order_id} is on its way. Track it using your order ID."
        notification_type = "order_shipped"
        
        logger.info(f"Prepared {notification_type} notification for order {request.order_id}")
        
    elif request.status == "delivered":
        email_subject = f"Order Delivered - {request.order_id}"
        email_body = f"""
        Dear {request.customer_name},

        Your order {request.order_id} has been delivered!

        We hope you enjoy your purchase. If you have any questions or concerns, please don't hesitate to contact us.

        Order Details:
        - Order ID: {request.order_id}
        - Status: Delivered
        - Delivery Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        Thank you for choosing us!

        Best regards,
        E-commerce Team
        """
        sms_message = f"Order Delivered! Your order {request.order_id} has been delivered successfully. Enjoy!"
        notification_type = "order_delivered"
        
        logger.info(f"Prepared {notification_type} notification for order {request.order_id}")
        
    else:
        email_subject = f"Order Update - {request.order_id}"
        email_body = f"""
        Dear {request.customer_name},

        Your order {request.order_id} status has been updated.

        Current Status: {request.status}

        If you have any questions, please contact our support team.

        Best regards,
        E-commerce Team
        """
        sms_message = f"Order Update: Your order {request.order_id} status is now {request.status}."
        notification_type = "order_update"
        
        logger.info(f"Prepared {notification_type} notification for order {request.order_id}")
    
    logger.info("Step 3: Simulating email sending")
    email_sent = send_email(request.customer_email, email_subject, email_body)
    
    logger.info("Step 4: Simulating SMS sending")
    sms_sent = send_sms(request.customer_email, sms_message)
    
    notification_record = {
        "notification_id": notification_id,
        "order_id": request.order_id,
        "customer_name": request.customer_name,
        "customer_email": request.customer_email,
        "type": notification_type,
        "status": request.status,
        "email_sent": email_sent,
        "sms_sent": sms_sent,
        "timestamp": timestamp
    }
    
    in_memory_notifications.append(notification_record)
    
    logger.info(f"Step 5: Notification record stored in memory with ID: {notification_id}")
    logger.info(f"Notification sent successfully via Email: {email_sent}, SMS: {sms_sent}")
    
    return NotificationResponse(
        notification_id=notification_id,
        message=f"Notification sent successfully for order {request.order_id}",
        type=notification_type,
        timestamp=timestamp
    )

def send_email(email: str, subject: str, body: str) -> bool:
    logger.info(f"Simulating email sending to: {email}")
    logger.info(f"Email Subject: {subject}")
    
    time.sleep(random.uniform(0.1, 0.3))
    
    success = random.random() > 0.05
    
    if success:
        logger.info(f"Email successfully sent to {email}")
    else:
        logger.warning(f"Failed to send email to {email}")
    
    return success

def send_sms(phone: str, message: str) -> bool:
    logger.info(f"Simulating SMS sending (using email as identifier): {phone}")
    logger.info(f"SMS Message: {message}")
    
    time.sleep(random.uniform(0.1, 0.2))
    
    success = random.random() > 0.05
    
    if success:
        logger.info(f"SMS successfully sent")
    else:
        logger.warning(f"Failed to send SMS")
    
    return success

@app.get("/notifications/{notification_id}")
def get_notification(notification_id: str):
    logger.info(f"Retrieving notification details for ID: {notification_id}")
    
    for notification in in_memory_notifications:
        if notification["notification_id"] == notification_id:
            logger.info(f"Notification {notification_id} found")
            return notification
    
    logger.warning(f"Notification {notification_id} not found")
    raise HTTPException(status_code=404, detail="Notification not found")

@app.get("/notifications")
def list_notifications():
    logger.info("Listing all notifications in memory")
    return {
        "count": len(in_memory_notifications),
        "notifications": in_memory_notifications
    }

@app.get("/notifications/order/{order_id}")
def get_order_notifications(order_id: str):
    logger.info(f"Retrieving notifications for order: {order_id}")
    
    order_notifications = [n for n in in_memory_notifications if n["order_id"] == order_id]
    
    logger.info(f"Found {len(order_notifications)} notifications for order {order_id}")
    
    return {
        "order_id": order_id,
        "count": len(order_notifications),
        "notifications": order_notifications
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Notification Service on port 8082")
    uvicorn.run(app, host="0.0.0.0", port=8082)
