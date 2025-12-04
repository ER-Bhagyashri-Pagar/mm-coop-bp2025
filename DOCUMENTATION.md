# Technical Documentation

Multi-Tenant Log Processor | v1.0.0 | December 2024

---

## Overview

Event-driven pipeline that ingests logs via HTTP, processes asynchronously, and stores with strict tenant isolation.

**Key Stats:**
- 1000+ requests/minute
- <200ms API response
- Zero-downtime auto-scaling
- Automatic crash recovery

**Stack:** Python 3.11, FastAPI, Cloud Run, Pub/Sub, Firestore

---

## Architecture

```
┌──────────┐
│  Client  │
└─────┬────┘
      │ POST /ingest (JSON/Text)
      ▼
┌─────────────────────┐
│  Ingestion API      │  Public endpoint
│  • Validates         │  Returns 202 immediately
│  • Normalizes        │  Publishes to queue
│  • Returns 202       │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│  Cloud Pub/Sub      │  Message queue
│  • Buffers msgs     │  10-min retention
│  • Auto-retry       │  Push to worker
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│  Worker Service     │  Internal processor
│  • 0.05s/char       │  Redacts phones
│  • Transforms       │  Writes to DB
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│  Firestore          │  Multi-tenant storage
│  tenants/           │  Physical isolation
│    {tenant_id}/     │  Sub-collections
│      processed_logs/│
└─────────────────────┘
```

**Why This Design:**
- **Decoupled:** API never waits for processing
- **Scalable:** Queue buffers traffic spikes
- **Resilient:** Auto-retry on failure
- **Isolated:** Physical tenant separation

---

## Components

### Ingestion API

**Role:** HTTP entry point

**Accepts:**
- JSON: `{"tenant_id":"acme","log_id":"123","data":"..."}`
- Text: `tenant_id: acme\nlog_id: 123\ndata: ...`

**Returns:** 202 Accepted + message_id

**Config:**
- Memory: 512Mi, CPU: 1
- Max instances: 10
- Public (no auth)

### Pub/Sub Queue

**Role:** Message broker

**Settings:**
- Topic: `log-ingestion-topic`
- Ack deadline: 300s
- Retention: 10 min
- Push to worker

### Worker Service

**Role:** Async processor

**Does:**
1. Receive message (base64)
2. Process (0.05s per char)
3. Redact phones (555-0199 → [REDACTED])
4. Write to Firestore
5. Acknowledge

**Config:**
- Memory: 512Mi, CPU: 1
- Max instances: 10
- Timeout: 300s
- Internal only

### Firestore

**Structure:**
```
tenants/{tenant_id}/processed_logs/{log_id}
```

**Document:**
```json
{
  "source": "json_upload",
  "original_text": "User 555-0199...",
  "modified_data": "User [REDACTED]...",
  "processed_at": "2025-12-04T01:25:32Z",
  "processing_time": 2.2,
  "char_count": 44
}
```

---

## Multi-Tenant Isolation

**Strategy:** Firestore sub-collections

**Why:**
- Physical data separation
- No cross-tenant queries possible
- Scales independently
- Natural security boundary

**Example:**
```
tenants/acme_corp/processed_logs/log-001
tenants/beta_inc/processed_logs/log-001
```

Each tenant = separate sub-collection. No way to accidentally mix data.

---

## API Reference

### POST /ingest

**URL:** `https://ingestion-api-1092727309970.us-central1.run.app/ingest`

**JSON Request:**
```bash
curl -X POST <api-url>/ingest \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"acme","log_id":"123","data":"message"}'
```

**Text Request:**
```bash
curl -X POST <api-url>/ingest \
  -H "Content-Type: text/plain" \
  -d "tenant_id: acme
log_id: 123
data: message"
```

**Response:**
```json
{
  "status": "accepted",
  "message_id": "1712120978643574",
  "tenant_id": "acme",
  "log_id": "123"
}
```

**Status Codes:**
- `202` - Success
- `400` - Invalid input
- `500` - Server error

---

## Deployment

### Prerequisites
```bash
# Install
gcloud CLI, Python 3.11+

# Set project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID
```

### Quick Deploy

**1. Enable APIs:**
```bash
gcloud services enable run.googleapis.com pubsub.googleapis.com \
  firestore.googleapis.com cloudbuild.googleapis.com
```

**2. Create infrastructure:**
```bash
# Pub/Sub
gcloud pubsub topics create log-ingestion-topic

# Firestore (via console)
# Navigate to: https://console.cloud.google.com/firestore
# Create Database → Native mode → us-central1
```

**3. Deploy services:**
```bash
# API
cd api-service
gcloud builds submit --tag gcr.io/$PROJECT_ID/ingestion-api
gcloud run deploy ingestion-api \
  --image gcr.io/$PROJECT_ID/ingestion-api \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID,PUBSUB_TOPIC_ID=log-ingestion-topic

# Worker
cd ../worker-service
gcloud builds submit --tag gcr.io/$PROJECT_ID/log-worker
gcloud run deploy log-worker \
  --image gcr.io/$PROJECT_ID/log-worker \
  --no-allow-unauthenticated \
  --timeout 300s \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID
```

**4. Connect Pub/Sub to worker:**
```bash
# Create service account
gcloud iam service-accounts create pubsub-invoker

# Grant permissions
gcloud run services add-iam-policy-binding log-worker \
  --member="serviceAccount:pubsub-invoker@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# Create push subscription
WORKER_URL=$(gcloud run services describe log-worker --format 'value(status.url)')
gcloud pubsub subscriptions create log-worker-push-sub \
  --topic=log-ingestion-topic \
  --push-endpoint="$WORKER_URL/process" \
  --push-auth-service-account="pubsub-invoker@$PROJECT_ID.iam.gserviceaccount.com" \
  --ack-deadline=300
```

**5. Verify:**
```bash
curl -X POST $(gcloud run services describe ingestion-api --format 'value(status.url)')/ingest \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"test","log_id":"001","data":"Deploy test"}'

# Check Firestore: tenants/test/processed_logs/001
```

---

## Testing

### Functional Tests

**JSON:**
```bash
curl -X POST <api-url>/ingest -H "Content-Type: application/json" \
  -d '{"tenant_id":"acme","log_id":"t1","data":"Test 555-0199"}'
```

**Text:**
```bash
curl -X POST <api-url>/ingest -H "Content-Type: text/plain" \
  -d "tenant_id: beta\nlog_id: t2\ndata: Call 555-1234"
```

**Verify:**
- Response: 202 Accepted
- Firestore: Document exists with phone redacted
- Processing time: char_count × 0.05 seconds

### Load Test

**Result:** 1000 RPM, 100% success, <200ms avg latency

---

## Error Handling

### Worker Crash Recovery

**What happens:**
1. Worker crashes mid-processing
2. Pub/Sub waits 300s for ack
3. No ack received
4. Message auto-redelivered
5. New worker processes successfully

**Why safe:**
- Firestore writes idempotent (same doc ID)
- No data loss
- Fully automatic

### Traffic Spike

**What happens:**
1. 1000 req/min hits API
2. API auto-scales, all return 202
3. Pub/Sub queues messages
4. Workers process at own pace
5. Queue drains in ~10 min

**Result:** Zero failures, all processed

---

## Monitoring

### Cloud Console
- **Services:** https://console.cloud.google.com/run?project=memory-machines-project
- **Pub/Sub:** https://console.cloud.google.com/cloudpubsub?project=memory-machines-project
- **Firestore:** https://console.cloud.google.com/firestore?project=memory-machines-project
- **Logs:** https://console.cloud.google.com/logs?project=memory-machines-project

### Commands

```bash
# API logs
gcloud logging read "resource.labels.service_name=ingestion-api" --limit 50

# Worker logs
gcloud logging read "resource.labels.service_name=log-worker" --limit 50

# Errors only
gcloud logging read "resource.labels.service_name=log-worker severity>=ERROR"

# Real-time
gcloud logging tail "resource.labels.service_name=log-worker"
```

### Key Metrics
- Request rate & latency
- Queue depth
- Error rate
- Processing time

---

## Troubleshooting

### API returns 500
**Cause:** Pub/Sub topic missing or IAM issue  
**Fix:** 
```bash
gcloud pubsub topics describe log-ingestion-topic
gcloud logging read "resource.labels.service_name=ingestion-api severity>=ERROR"
```

### Messages not processing
**Cause:** Worker not running or subscription missing  
**Fix:**
```bash
gcloud run services describe log-worker
gcloud pubsub subscriptions describe log-worker-push-sub
```

### High latency
**Cause:** Cold starts  
**Fix:**
```bash
gcloud run services update ingestion-api --min-instances=1
```

---

## Performance

**Current:**
- API: 6000+ RPM capacity
- Worker: ~200 msg/min
- Latency: <200ms

**Free tier limits:** 10 instances per service

**To scale:** Request quota increase, add regions

---

## Security

**Current (Testing):**
- API: Public (no auth)
- Worker: Internal only
- Firestore: Open rules

**Production:**
- Add API key auth
- Rate limiting per tenant
- Firestore security rules
- VPC configuration

---

## Contact

Bhagyashri Pagar  
📧 bpagar14@gmail.com  
🔗 [LinkedIn](https://www.linkedin.com/in/bhagyashri-pagar/)

---

**v1.0.0 | December 2024**
