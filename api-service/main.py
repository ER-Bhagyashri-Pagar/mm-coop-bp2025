"""
Unified Ingestion API - Professional Production Ready
Fully configurable via environment variables
"""
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from google.cloud import pubsub_v1
import json
import os
import uuid
import re
from datetime import datetime
from typing import Optional
import logging

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Unified Ingestion API")

# ===== CONFIGURATION (All from Environment Variables) =====
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
TOPIC_ID = os.getenv("PUBSUB_TOPIC_ID")

if not PROJECT_ID or not TOPIC_ID:
    raise ValueError("GCP_PROJECT_ID and PUBSUB_TOPIC_ID environment variables must be set")

# Validation Configuration (configurable via env vars)
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "10000"))
MIN_TEXT_LENGTH = int(os.getenv("MIN_TEXT_LENGTH", "1"))
MAX_TENANT_ID_LENGTH = int(os.getenv("MAX_TENANT_ID_LENGTH", "100"))
MAX_LOG_ID_LENGTH = int(os.getenv("MAX_LOG_ID_LENGTH", "200"))
TENANT_ID_PATTERN = os.getenv("TENANT_ID_PATTERN", r'^[a-zA-Z0-9_-]+$')

# Initialize Pub/Sub Publisher
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

logger.info(f"API initialized with PROJECT_ID={PROJECT_ID}, TOPIC_ID={TOPIC_ID}")
logger.info(f"Validation limits: TEXT({MIN_TEXT_LENGTH}-{MAX_TEXT_LENGTH}), TENANT_ID(max {MAX_TENANT_ID_LENGTH})")


# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors"""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request format"}
    )


def validate_tenant_id(tenant_id: str) -> bool:
    """
    Validate tenant_id format using configurable pattern
    """
    if not tenant_id or not isinstance(tenant_id, str):
        return False
    
    if len(tenant_id) > MAX_TENANT_ID_LENGTH:
        return False
    
    if not re.match(TENANT_ID_PATTERN, tenant_id):
        return False
    
    return True


def validate_text(text: str) -> tuple[bool, str]:
    """
    Validate text content using configurable limits
    """
    if not isinstance(text, str):
        return False, "Text must be a string"
    
    if len(text) < MIN_TEXT_LENGTH:
        return False, f"Text must be at least {MIN_TEXT_LENGTH} character(s)"
    
    if len(text) > MAX_TEXT_LENGTH:
        return False, f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters"
    
    return True, ""


def normalize_to_internal_format(data: dict, source_type: str) -> dict:
    """
    Normalize JSON or TXT input to internal format
    """
    normalized = {
        "tenant_id": data.get("tenant_id"),
        "log_id": data.get("log_id", str(uuid.uuid4())),
        "text": data.get("text", ""),
        "source": source_type,
        "received_at": datetime.utcnow().isoformat()
    }
    return normalized

def publish_to_pubsub(message_data: dict):  # ← No return type
    """
    Publish message to Pub/Sub (fire-and-forget)
    """
    try:
        message_bytes = json.dumps(message_data).encode("utf-8")
        
        future = publisher.publish(
            topic_path,
            message_bytes,
            tenant_id=message_data["tenant_id"]
        )
        
        # Async callback for logging only
        def callback(f):
            try:
                result = f.result()
                logger.info(f"Published message {result} for tenant {message_data['tenant_id']}")
            except Exception as e:
                logger.error(f"Publish callback error: {str(e)}")
        
        future.add_done_callback(callback)
        # No return - fire and forget
        
    except Exception as e:
        logger.error(f"Failed to publish: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to queue message for processing")

@app.get("/")
async def root():
    """Root health check"""
    return {
        "status": "healthy",
        "service": "Unified Ingestion API",
        "version": "2.0.0"
    }


@app.post("/ingest")
async def ingest(
    request: Request,
    content_type: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """
    Unified ingestion endpoint with comprehensive validation
    """
    try:
        if content_type is None:
            content_type = request.headers.get("content-type", "").lower()
        else:
            content_type = content_type.lower()
        
        if "application/json" in content_type:
            # JSON payload
            try:
                body = await request.json()
            except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as e:
                logger.warning(f"Invalid JSON: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid JSON payload")
            except Exception as e:
                logger.warning(f"JSON parse error: {type(e).__name__}: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid JSON payload")
            
            # Type check
            if not isinstance(body, dict):
                logger.warning(f"JSON parsed to {type(body)}, expected dict")
                raise HTTPException(status_code=400, detail="Invalid JSON payload: expected object")
            
            # Validate tenant_id
            tenant_id = body.get("tenant_id")
            if not tenant_id:
                raise HTTPException(status_code=400, detail="Missing required field: tenant_id")
            
            if not validate_tenant_id(tenant_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid tenant_id format. Must match pattern, max {MAX_TENANT_ID_LENGTH} chars"
                )
            
            # Validate text
            text = body.get("text", "")
            is_valid, error_msg = validate_text(text)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            
            # Validate log_id if provided
            log_id = body.get("log_id")
            if log_id and len(str(log_id)) > MAX_LOG_ID_LENGTH:
                raise HTTPException(
                    status_code=400,
                    detail=f"log_id exceeds maximum length of {MAX_LOG_ID_LENGTH} characters"
                )
            
            normalized = normalize_to_internal_format(body, "json_upload")
        
        elif "text/plain" in content_type:
            # Text payload
            if not x_tenant_id:
                raise HTTPException(status_code=400, detail="Missing required header: X-Tenant-ID")
            
            if not validate_tenant_id(x_tenant_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid X-Tenant-ID format. Max {MAX_TENANT_ID_LENGTH} chars"
                )
            
            try:
                body_bytes = await request.body()
                text = body_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Text payload must be valid UTF-8")
            
            is_valid, error_msg = validate_text(text)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            
            normalized = normalize_to_internal_format({
                "tenant_id": x_tenant_id,
                "text": text
            }, "text_upload")
        
        else:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported content type. Use 'application/json' or 'text/plain'"
            )
        
        # Publish to Pub/Sub (async, non-blocking)
        publish_to_pubsub(normalized)  # ← No return value
        
        # Return 202 Accepted immediately
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "tenant_id": normalized["tenant_id"],
                "log_id": normalized["log_id"]
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check with Pub/Sub connectivity test"""
    try:
        publisher.get_topic(request={"topic": topic_path})
        pubsub_status = "connected"
    except Exception as e:
        logger.error(f"Pub/Sub health check failed: {str(e)}")
        pubsub_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if pubsub_status == "connected" else "degraded",
        "pubsub_topic": topic_path,
        "pubsub_status": pubsub_status,
        "project_id": PROJECT_ID,
        "config": {
            "max_text_length": MAX_TEXT_LENGTH,
            "min_text_length": MIN_TEXT_LENGTH,
            "max_tenant_id_length": MAX_TENANT_ID_LENGTH
        },
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)