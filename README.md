# Multi-Tenant Log Processor

Event-driven backend system for high-throughput log ingestion with strict tenant isolation.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![GCP](https://img.shields.io/badge/GCP-Cloud%20Run-orange.svg)](https://cloud.google.com/run)
[![Status](https://img.shields.io/badge/Status-Live-success.svg)](https://ingestion-api-1092727309970.us-central1.run.app)

**Built for:** Memory Machines Backend Engineering Assignment  
**By:** Bhagyashri Pagar

---

## 🚀 Live Demo

**API Endpoint:** https://ingestion-api-1092727309970.us-central1.run.app  
**Demo Video:** `[Add your video link here]`

---

## 📖 Overview

### The Problem
Ingest high-volume log streams from multiple tenants, process them asynchronously, and store results with complete data isolation.

### The Solution
Event-driven pipeline using Cloud Run, Pub/Sub, and Firestore that:
- Handles **1000+ requests/minute** without blocking
- Processes messages asynchronously with automatic retries
- Isolates tenant data at the database level
- Scales to zero when idle (serverless)

---

## 🏗️ Architecture

```
┌─────────┐
│ Client  │
└────┬────┘
     │ POST /ingest
     ▼
┌──────────────────┐
│  Ingestion API   │  ← Public endpoint (Cloud Run)
│  • Validates      │
│  • Normalizes     │
│  • Returns 202    │
└────┬─────────────┘
     │ Publish
     ▼
┌──────────────────┐
│   Cloud Pub/Sub  │  ← Message queue
│  • Buffers msgs   │
│  • Auto-retry     │
└────┬─────────────┘
     │ Push trigger
     ▼
┌──────────────────┐
│  Worker Service  │  ← Internal processor (Cloud Run)
│  • Processes      │
│  • Transforms     │
│  • Stores         │
└────┬─────────────┘
     │ Write
     ▼
┌──────────────────┐
│    Firestore     │  ← Multi-tenant storage
│  tenants/        │
│   └─ {id}/       │
│      └─ logs/    │
└──────────────────┘
```

**Key Design Decisions:**
- **Non-blocking API:** Returns 202 immediately, processes async
- **Event-driven:** Pub/Sub decouples ingestion from processing
- **Physical isolation:** Firestore sub-collections per tenant
- **Automatic recovery:** Failed messages auto-retry via Pub/Sub

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| API | FastAPI | Async support, auto docs, type validation |
| Compute | Cloud Run | Serverless, scales to zero, long timeouts |
| Queue | Pub/Sub | Managed, reliable, push subscriptions |
| Database | Firestore | NoSQL, sub-collections for isolation |
| Language | Python 3.11 | Fast development, rich ecosystem |

---

## 📡 API

### POST /ingest

Accepts JSON or plain text logs.

**JSON Example:**
```bash
curl -X POST <api-url>/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "acme_corp",
    "log_id": "log-123",
    "data": "User 555-0199 accessed dashboard at 10:30 AM"
  }'
```

**Text Example:**
```bash
curl -X POST <api-url>/ingest \
  -H "Content-Type: text/plain" \
  -d "tenant_id: beta_inc
log_id: log-456
data: System alert: Connection timeout 555-1234"
```

**Response:**
```json
{
  "status": "accepted",
  "message_id": "1712120978...",
  "tenant_id": "acme_corp",
  "log_id": "log-123"
}
```

---

## 💾 Data Model

**Storage Structure:**
```
firestore/
└── tenants/
    ├── acme_corp/
    │   └── processed_logs/
    │       └── log-123/
    │           ├── source: "json_upload"
    │           ├── original_text: "User 555-0199..."
    │           ├── modified_data: "User [REDACTED]..."
    │           ├── processed_at: "2025-12-04T01:25:32Z"
    │           └── processing_time: 2.2
    └── beta_inc/
        └── processed_logs/
            └── log-456/
```

**Why Sub-Collections?**
- Physical data separation (no cross-tenant queries)
- Scales independently per tenant
- Natural security boundary
- Efficient indexing

---

## ✅ Features

- [x] Single unified endpoint (`/ingest`)
- [x] Multi-format support (JSON + Text)
- [x] Non-blocking async (202 Accepted)
- [x] 1000+ RPM throughput
- [x] Heavy processing (0.05s per character)
- [x] Phone number redaction
- [x] Multi-tenant isolation
- [x] Automatic crash recovery
- [x] Serverless (scales to zero)

---

## 🧪 Testing

**Load Test Results:**
```
Requests:    1000 in 60s
Success:     100%
Avg latency: <200ms
Errors:      0
```

**Processing Accuracy:**
```
44 chars  → 2.20s ✓
100 chars → 5.00s ✓
(exact 0.05s per character)
```

**Phone Redaction:**
```
555-0199          → [REDACTED] ✓
555-123-4567      → [REDACTED] ✓
(555) 123-4567    → [REDACTED] ✓
```

**Multi-Tenancy:**
```
acme_corp data in: tenants/acme_corp/processed_logs/ ✓
beta_inc data in:  tenants/beta_inc/processed_logs/  ✓
No cross-contamination ✓
```

---

## 📁 Project Structure

```
.
├── api-service/
│   ├── main.py                 # FastAPI ingestion service
│   ├── Dockerfile              # Container config
│   ├── requirements.txt        # Dependencies
│   └── .dockerignore
│
├── worker-service/
│   ├── main.py                 # FastAPI worker (Cloud Run)
│   ├── worker.py               # Local test script
│   ├── Dockerfile
│   └── requirements.txt
│
├── Test cases/
│   ├── comprehensive_test_suite.py
│   ├── load_test.py
│   ├── create_demo_data.py
│   └── cleanup_firestore.py
│
├── README.md
└── DOCUMENTATION.md            # Detailed technical docs
```

---

## 🚀 Quick Start

**Prerequisites:**
- GCP account with billing
- gcloud CLI installed
- Python 3.11+

**Deploy:**
```bash
# 1. Clone repo
git clone https://github.com/ER-Bhagyashri-Pagar/mm-coop-bp2025.git
cd mm-coop-bp2025

# 2. Set project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# 3. Deploy (see DOCUMENTATION.md for detailed steps)
cd api-service
gcloud builds submit --tag gcr.io/$PROJECT_ID/ingestion-api
gcloud run deploy ingestion-api --image gcr.io/$PROJECT_ID/ingestion-api ...
```

**Full deployment guide:** [DOCUMENTATION.md](DOCUMENTATION.md)

---

## 🎯 Design Highlights

### 1. Event-Driven Architecture
Decouples API from processing. API publishes to queue and returns immediately. Worker processes asynchronously. This enables high throughput without blocking.

### 2. Crash Recovery
If worker crashes mid-processing, Pub/Sub automatically redelivers message after 300s timeout. Firestore writes are idempotent (same document ID), so reprocessing is safe.

### 3. Multi-Tenant Isolation
Sub-collection structure provides **physical separation**:
```
tenants/{tenant_id}/processed_logs/{log_id}
```
Impossible to accidentally query across tenants. Each tenant's data in separate sub-collection.

### 4. Serverless Scaling
Cloud Run scales from 0 to 10 instances automatically. Pay only for actual usage. No idle costs.

---

## 📚 Documentation

**[DOCUMENTATION.md](DOCUMENTATION.md)** - Complete technical guide:
- Detailed architecture explanation
- Step-by-step deployment
- Crash recovery scenarios
- Design trade-offs
- Performance analysis
- Monitoring and debugging

---

## 👤 Author

**Bhagyashri Avinash Pagar**

- Email: bpagar14@gmail.com
- LinkedIn: [bhagyashri-pagar](https://www.linkedin.com/in/bhagyashri-pagar/)
- GitHub: [ER-Bhagyashri-Pagar](https://github.com/ER-Bhagyashri-Pagar)

---

## 📄 License

This project was built as a take-home assignment for Memory Machines Backend Engineering Co-Op position (January 2026).

---

**Memory Machines Backend Engineering Assignment | December 2024**
