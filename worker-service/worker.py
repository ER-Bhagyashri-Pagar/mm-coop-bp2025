"""
Worker Service - Day 2
Continuously pulls messages from Pub/Sub, processes them, writes to Firestore
"""
import os
import json
import time
import re
from datetime import datetime
from google.cloud import pubsub_v1
from google.cloud import firestore

# --- Load environment variables ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
SUBSCRIPTION_ID = os.getenv("PUBSUB_SUBSCRIPTION_ID")

if not PROJECT_ID or not SUBSCRIPTION_ID:
    raise Exception("Environment variables GCP_PROJECT_ID or PUBSUB_SUBSCRIPTION_ID not set")

# Pub/Sub subscriber client
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

# Firestore client
db = firestore.Client()

# --- Helper: redact phone numbers ---
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


# --- Main message processor ---
def process_message(message_json: dict):
    """
    Process a single message:
    1. Extract data
    2. Simulate heavy processing (0.05s per character)
    3. Redact phone numbers
    4. Write to Firestore with tenant isolation
    """
    tenant_id = message_json["tenant_id"]
    log_id = message_json["log_id"]
    text = message_json["text"]
    source = message_json["source"]
    received_at = message_json["received_at"]
    
    # Simulate heavy compute (PDF requirement: 0.05s per character)
    char_count = len(text)
    sleep_time = char_count * 0.05
    print(f"\n📝 Processing log_id={log_id} for tenant={tenant_id}")
    print(f"   Characters: {char_count} | Sleep time: {sleep_time:.2f}s")
    time.sleep(sleep_time)
    
    # Transform data (redact phone numbers)
    modified_text = redact_phone_numbers(text)
    
    # Prepare document for Firestore
    processed_data = {
        "source": source,
        "original_text": text,
        "modified_data": modified_text,
        "received_at": received_at,
        "processed_at": datetime.utcnow().isoformat(),
        "processing_time": sleep_time,
        "char_count": char_count
    }
    
    # Write to Firestore with strict tenant isolation
    # Path: tenants/{tenant_id}/processed_logs/{log_id}
    doc_ref = (
        db.collection("tenants")
        .document(tenant_id)
        .collection("processed_logs")
        .document(log_id)
    )
    doc_ref.set(processed_data)
    
    print(f"✅ Stored to Firestore: tenants/{tenant_id}/processed_logs/{log_id}")


# --- Streaming Pull callback ---
def callback(message: pubsub_v1.subscriber.message.Message):
    """
    Callback function for each message received from Pub/Sub
    """
    try:
        # Decode and parse message
        message_data = json.loads(message.data.decode("utf-8"))
        
        # Process the message
        process_message(message_data)
        
        # Acknowledge successful processing
        message.ack()
        print("✅ Message acknowledged\n")
        
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        # Do NOT acknowledge - Pub/Sub will retry
        # message.nack()  # Optional: explicitly reject


# --- Worker main loop ---
def start_worker():
    """
    Start the worker with streaming pull
    Continuously listens for messages until interrupted
    """
    print("=" * 60)
    print("🚀 Worker Service Started")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print(f"Subscription: {SUBSCRIPTION_ID}")
    print(f"Listening on: {subscription_path}")
    print("=" * 60)
    print("\nWaiting for messages... (Press Ctrl+C to stop)\n")
    
    # Start streaming pull
    streaming_pull = subscriber.subscribe(subscription_path, callback=callback)
    
    try:
        # Block and wait for messages (runs continuously)
        streaming_pull.result()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping worker...")
        streaming_pull.cancel()
        print("✅ Worker stopped\n")


if __name__ == "__main__":
    start_worker()