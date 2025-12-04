"""
Worker Service - Professional Production Ready
Fully configurable via environment variables
"""
from fastapi import FastAPI, Request, HTTPException
from google.cloud import firestore
import base64
import json
import time
import re
import os
from datetime import datetime, timezone
import logging

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Worker Service")

# ===== CONFIGURATION (All from Environment Variables) =====
# Processing configuration (PDF requires 0.05, but make it configurable)
PROCESSING_RATE_PER_CHAR = float(os.getenv("PROCESSING_RATE_PER_CHAR", "0.05"))

# Redaction patterns (configurable via comma-separated regex)
REDACTION_PATTERNS_STR = os.getenv(
    "REDACTION_PATTERNS",
    r'\d{3}-\d{4},\d{3}-\d{3}-\d{4},\(\d{3}\)\s*\d{3}-\d{4}'
)
REDACTION_PATTERNS = [p.strip() for p in REDACTION_PATTERNS_STR.split(',')]

# Firestore collection names (configurable)
TENANTS_COLLECTION = os.getenv("TENANTS_COLLECTION", "tenants")
LOGS_COLLECTION = os.getenv("LOGS_COLLECTION", "processed_logs")

# Initialize Firestore
db = firestore.Client()

logger.info(f"Worker initialized with PROCESSING_RATE={PROCESSING_RATE_PER_CHAR}s/char")
logger.info(f"Redaction patterns: {len(REDACTION_PATTERNS)} loaded")
logger.info(f"Firestore structure: {TENANTS_COLLECTION}/{'{tenant_id}'}/{LOGS_COLLECTION}/{'{log_id}'}")


def redact_phone_numbers(text: str) -> str:
    """
    Redact phone numbers using configurable patterns
    """
    result = text
    for pattern in REDACTION_PATTERNS:
        try:
            result = re.sub(pattern, '[REDACTED]', result)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
    
    return result


def simulate_heavy_processing(text: str) -> float:
    """
    Simulate CPU-bound processing using configurable rate
    Default: 0.05s per character (PDF requirement)
    """
    char_count = len(text)
    sleep_duration = char_count * PROCESSING_RATE_PER_CHAR
    
    logger.info(f"Processing {char_count} characters at {PROCESSING_RATE_PER_CHAR}s/char = {sleep_duration:.2f}s")
    time.sleep(sleep_duration)
    
    return sleep_duration


def write_to_firestore(tenant_id: str, log_id: str, data: dict) -> bool:
    """
    Write to Firestore using configurable collection names
    Path: {TENANTS_COLLECTION}/{tenant_id}/{LOGS_COLLECTION}/{log_id}
    """
    try:
        doc_ref = (db.collection(TENANTS_COLLECTION)
                    .document(tenant_id)
                    .collection(LOGS_COLLECTION)
                    .document(log_id))
        
        doc_data = {
            "source": data.get("source", "unknown"),
            "original_text": data.get("text", ""),
            "modified_data": data.get("modified_text", ""),
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "received_at": data.get("received_at", ""),
            "processing_time": data.get("processing_time", 0),
            "char_count": len(data.get("text", ""))
        }
        
        doc_ref.set(doc_data)
        logger.info(f"✅ Stored: {TENANTS_COLLECTION}/{tenant_id}/{LOGS_COLLECTION}/{log_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Firestore write failed: {str(e)}")
        raise


def process_message(message_data: dict) -> bool:
    """
    Main processing pipeline
    """
    try:
        tenant_id = message_data.get("tenant_id")
        log_id = message_data.get("log_id")
        text = message_data.get("text", "")
        
        if not tenant_id or not log_id:
            logger.error("Missing tenant_id or log_id")
            return False
        
        logger.info(f"📝 Processing log_id={log_id} for tenant={tenant_id}")
        
        # Step 1: Simulate heavy processing (configurable rate)
        processing_time = simulate_heavy_processing(text)
        
        # Step 2: Transform data (configurable patterns)
        modified_text = redact_phone_numbers(text)
        
        # Step 3: Prepare for storage
        message_data["modified_text"] = modified_text
        message_data["processing_time"] = processing_time
        
        # Step 4: Write to Firestore (configurable paths)
        write_to_firestore(tenant_id, log_id, message_data)
        
        logger.info(f"✅ Successfully processed log {log_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Processing error: {str(e)}")
        return False


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Log Worker Service",
        "version": "2.0.0",
        "config": {
            "processing_rate": PROCESSING_RATE_PER_CHAR,
            "redaction_patterns_count": len(REDACTION_PATTERNS)
        }
    }


@app.post("/process")
async def process_pubsub_push(request: Request):
    """
    Pub/Sub push endpoint
    """
    try:
        envelope = await request.json()
        
        if "message" not in envelope:
            raise HTTPException(status_code=400, detail="Invalid Pub/Sub message format")
        
        pubsub_message = envelope["message"]
        
        if "data" not in pubsub_message:
            raise HTTPException(status_code=400, detail="No data in Pub/Sub message")
        
        message_data_str = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        message_data = json.loads(message_data_str)
        
        success = process_message(message_data)
        
        if success:
            return {"status": "processed", "log_id": message_data.get("log_id")}
        else:
            raise HTTPException(status_code=500, detail="Processing failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Worker error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        db.collection('health_check').document('test').set({
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        firestore_status = "connected"
    except Exception as e:
        logger.error(f"Firestore health check failed: {str(e)}")
        firestore_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if firestore_status == "connected" else "degraded",
        "firestore_status": firestore_status,
        "config": {
            "processing_rate": PROCESSING_RATE_PER_CHAR,
            "collections": f"{TENANTS_COLLECTION}/{{id}}/{LOGS_COLLECTION}/{{id}}"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)