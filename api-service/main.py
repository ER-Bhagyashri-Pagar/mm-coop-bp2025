"""
Unified Ingestion API - Day 1
Handles JSON and TXT payloads, publishes to Pub/Sub
"""
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from google.cloud import pubsub_v1
import json
import os
import uuid
from datetime import datetime
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Unified Ingestion API")

# GCP Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "memory-machines-project")
TOPIC_ID = os.getenv("PUBSUB_TOPIC_ID", "log-ingestion-topic")

# Initialize Pub/Sub Publisher
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)


def normalize_to_internal_format(data: dict, source_type: str) -> dict:
    """
    Normalize JSON or TXT input to internal flat format
    """
    normalized = {
        "tenant_id": data.get("tenant_id"),
        "log_id": data.get("log_id", str(uuid.uuid4())),
        "text": data.get("text", ""),
        "source": source_type,
        "received_at": datetime.utcnow().isoformat()
    }
    return normalized


def publish_to_pubsub(message_data: dict) -> str:
    """
    Publish normalized message to Pub/Sub
    Returns: message_id
    """
    try:
        # Convert to JSON bytes
        message_bytes = json.dumps(message_data).encode("utf-8")
        
        # Publish with tenant_id as attribute
        future = publisher.publish(
            topic_path,
            message_bytes,
            tenant_id=message_data["tenant_id"]
        )
        
        message_id = future.result(timeout=10)
        logger.info(f"Published message {message_id} for tenant {message_data['tenant_id']}")
        return message_id
        
    except Exception as e:
        logger.error(f"Failed to publish message: {str(e)}")
        raise


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Unified Ingestion API",
        "version": "1.0.0"
    }


@app.post("/ingest")
async def ingest(
    request: Request,
    content_type: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """
    Unified ingestion endpoint
    Handles both JSON and TXT payloads
    Returns 202 Accepted immediately (non-blocking)
    """
    try:
        # Determine content type
        if content_type is None:
            content_type = request.headers.get("content-type", "").lower()
        else:
            content_type = content_type.lower()
        
        # Process based on content type
        if "application/json" in content_type:
            # Scenario 1: JSON payload
            try:
                body = await request.json()
                
                # Validate required fields
                if "tenant_id" not in body:
                    raise HTTPException(
                        status_code=400,
                        detail="Missing tenant_id in JSON payload"
                    )
                
                normalized = normalize_to_internal_format(body, "json_upload")
                
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        elif "text/plain" in content_type:
            # Scenario 2: Raw text payload
            if not x_tenant_id:
                raise HTTPException(
                    status_code=400,
                    detail="Missing X-Tenant-ID header for text/plain"
                )
            
            body_bytes = await request.body()
            text = body_bytes.decode("utf-8")
            
            normalized = normalize_to_internal_format({
                "tenant_id": x_tenant_id,
                "text": text
            }, "text_upload")
        
        else:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported content type: {content_type}"
            )
        
        # Publish to Pub/Sub (async, non-blocking)
        message_id = publish_to_pubsub(normalized)
        
        # Return 202 Accepted immediately
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "message_id": message_id,
                "tenant_id": normalized["tenant_id"],
                "log_id": normalized["log_id"]
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "pubsub_topic": topic_path,
        "project_id": PROJECT_ID,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))