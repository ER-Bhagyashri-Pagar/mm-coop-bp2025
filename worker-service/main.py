"""
Worker Service for Cloud Run - Day 2
Receives messages from Pub/Sub via push subscription
Processes and stores to Firestore
"""
from fastapi import FastAPI, Request, HTTPException
from google.cloud import firestore
import base64
import json
import time
import re
from datetime import datetime, timezone
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Worker Service")

# Initialize Firestore
db = firestore.Client()


def redact_phone_numbers(text: str) -> str:
    """
    Redact phone numbers from text
    Supports multiple patterns: XXX-XXXX, XXX-XXX-XXXX, (XXX) XXX-XXXX
    """
    patterns = [
        r'\d{3}-\d{4}',              # 555-0199
        r'\d{3}-\d{3}-\d{4}',        # 555-123-4567
        r'\(\d{3}\)\s*\d{3}-\d{4}',  # (555) 123-4567
    ]
    
    result = text
    for pattern in patterns:
        result = re.sub(pattern, '[REDACTED]', result)
    
    return result


def simulate_heavy_processing(text: str) -> float:
    """
    Simulate CPU-bound processing
    Sleep for 0.05 seconds per character (PDF requirement)
    """
    char_count = len(text)
    sleep_duration = char_count * 0.05
    
    logger.info(f"Processing {char_count} characters, sleeping {sleep_duration:.2f}s")
    time.sleep(sleep_duration)
    
    return sleep_duration


def write_to_firestore(tenant_id: str, log_id: str, data: dict) -> bool:
    """
    Write processed data to Firestore with strict tenant isolation
    Path: tenants/{tenant_id}/processed_logs/{log_id}
    """
    try:
        # Multi-tenant path structure (CRITICAL for PDF requirement)
        doc_ref = db.collection('tenants').document(tenant_id).collection('processed_logs').document(log_id)
        
        # Prepare document
        doc_data = {
            "source": data.get("source", "unknown"),
            "original_text": data.get("text", ""),
            "modified_data": data.get("modified_text", ""),
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "received_at": data.get("received_at", ""),
            "processing_time": data.get("processing_time", 0),
            "char_count": len(data.get("text", ""))
        }
        
        # Write to Firestore
        doc_ref.set(doc_data)
        logger.info(f"✅ Stored to Firestore: tenants/{tenant_id}/processed_logs/{log_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to write to Firestore: {str(e)}")
        raise


def process_message(message_data: dict) -> bool:
    """
    Main processing pipeline
    1. Extract data
    2. Simulate heavy processing (0.05s per char)
    3. Transform data (redaction)
    4. Write to Firestore
    """
    try:
        tenant_id = message_data.get("tenant_id")
        log_id = message_data.get("log_id")
        text = message_data.get("text", "")
        
        if not tenant_id or not log_id:
            logger.error("Missing tenant_id or log_id")
            return False
        
        logger.info(f"📝 Processing log_id={log_id} for tenant={tenant_id}")
        
        # Step 1: Simulate heavy processing (PDF requirement)
        processing_time = simulate_heavy_processing(text)
        
        # Step 2: Transform data (redact phone numbers)
        modified_text = redact_phone_numbers(text)
        
        # Step 3: Prepare data for Firestore
        message_data["modified_text"] = modified_text
        message_data["processing_time"] = processing_time
        
        # Step 4: Write to Firestore with tenant isolation
        write_to_firestore(tenant_id, log_id, message_data)
        
        logger.info(f"✅ Successfully processed log {log_id} for tenant {tenant_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error processing message: {str(e)}")
        return False


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Log Worker Service",
        "version": "1.0.0"
    }


@app.post("/process")
async def process_pubsub_push(request: Request):
    """
    Endpoint for Pub/Sub push subscription
    Receives messages in Pub/Sub push format (base64 encoded)
    """
    try:
        # Parse Pub/Sub push message format
        envelope = await request.json()
        
        if "message" not in envelope:
            raise HTTPException(status_code=400, detail="Invalid Pub/Sub message format")
        
        pubsub_message = envelope["message"]
        
        # Decode base64 data
        if "data" not in pubsub_message:
            raise HTTPException(status_code=400, detail="No data in Pub/Sub message")
        
        message_data_str = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        message_data = json.loads(message_data_str)
        
        # Process the message
        success = process_message(message_data)
        
        if success:
            # Return 200 to acknowledge
            return {"status": "processed", "log_id": message_data.get("log_id")}
        else:
            # Return 500 to trigger retry
            raise HTTPException(status_code=500, detail="Processing failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Worker error: {str(e)}")
        # Return 500 to trigger Pub/Sub retry
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test Firestore connection
        db.collection('health_check').document('test').set({'timestamp': datetime.now(timezone.utc).isoformat()})
        
        return {
            "status": "healthy",
            "firestore": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)