"""
Create Professional Demo Data - PDF Aligned
Perfect for video demonstration and final verification
"""
import requests
import time

API_URL = "https://ingestion-api-1092727309970.us-central1.run.app/ingest"

print("=" * 70)
print("🎬 CREATING PROFESSIONAL DEMO DATA")
print("=" * 70)
print(f"Target: {API_URL}")
print("=" * 70)

messages_sent = 0

# ===== TENANT 1: acme_corp (PDF uses this name!) =====
print("\n📦 Creating data for tenant: acme_corp")
print("-" * 70)

# Message 1: PDF Example (Page 2)
print("1. PDF Example - User access log")
r1 = requests.post(
    API_URL,
    json={"tenant_id": "acme_corp", "log_id": "001", "text": "User 555-0199 accessed dashboard at 10:30 AM"},
    headers={"Content-Type": "application/json"}
)
print(f"   Status: {r1.status_code} - {r1.json()}")
messages_sent += 1

# Message 2: Business log with multiple phones
print("2. Customer service log with phone")
r2 = requests.post(
    API_URL,
    json={"tenant_id": "acme_corp", "log_id": "002", "text": "Customer called support at 555-123-4567 regarding invoice #12345"},
    headers={"Content-Type": "application/json"}
)
print(f"   Status: {r2.status_code} - {r2.json()}")
messages_sent += 1

# Message 3: System event
print("3. System event log")
r3 = requests.post(
    API_URL,
    json={"tenant_id": "acme_corp", "log_id": "003", "text": "Database backup completed successfully at 2025-12-03 08:00:00"},
    headers={"Content-Type": "application/json"}
)
print(f"   Status: {r3.status_code} - {r3.json()}")
messages_sent += 1

# Message 4: Text format log (PDF Scenario 2)
print("4. Text format - raw log dump")
r4 = requests.post(
    API_URL,
    data="ERROR: Payment processing failed for transaction #TX-9876. Contact (555) 987-6543 for support.",
    headers={"Content-Type": "text/plain", "X-Tenant-ID": "acme_corp"}
)
print(f"   Status: {r4.status_code} - {r4.json()}")
messages_sent += 1

# ===== TENANT 2: beta_inc (PDF uses this name!) =====
print("\n📦 Creating data for tenant: beta_inc")
print("-" * 70)

# Message 5: JSON format
print("5. User authentication log")
r5 = requests.post(
    API_URL,
    json={"tenant_id": "beta_inc", "log_id": "B001", "text": "Admin user logged in from IP 192.168.1.100"},
    headers={"Content-Type": "application/json"}
)
print(f"   Status: {r5.status_code} - {r5.json()}")
messages_sent += 1

# Message 6: Text format with phone
print("6. Text format - incident report")
r6 = requests.post(
    API_URL,
    data="INCIDENT: Server crash detected at 14:30. On-call engineer 555-2468 notified immediately.",
    headers={"Content-Type": "text/plain", "X-Tenant-ID": "beta_inc"}
)
print(f"   Status: {r6.status_code} - {r6.json()}")
messages_sent += 1

# Message 7: Order processing
print("7. Order fulfillment log")
r7 = requests.post(
    API_URL,
    json={"tenant_id": "beta_inc", "log_id": "B002", "text": "Order #ORD-45678 shipped via FedEx tracking 1Z999AA10123456784"},
    headers={"Content-Type": "application/json"}
)
print(f"   Status: {r7.status_code} - {r7.json()}")
messages_sent += 1

# Message 8: Long message to show processing time
print("8. Long message - API error log")
long_message = "CRITICAL ERROR: Database connection pool exhausted after 300 seconds. Attempted reconnection 15 times. Server load at 95%. Memory usage critical at 8.7GB of 10GB available. Immediate intervention required."
r8 = requests.post(
    API_URL,
    data=long_message,
    headers={"Content-Type": "text/plain", "X-Tenant-ID": "beta_inc"}
)
print(f"   Status: {r8.status_code} - {r8.json()}")
print(f"   (This message has {len(long_message)} chars = {len(long_message)*0.05:.1f}s processing)")
messages_sent += 1

# Summary
print("\n" + "=" * 70)
print(f"✅ DEMO DATA CREATED: {messages_sent} messages sent")
print("=" * 70)
print("\nMessages sent to:")
print("  - acme_corp: 4 messages (3 JSON, 1 TXT)")
print("  - beta_inc:  4 messages (2 JSON, 2 TXT)")
print("\n⏳ Waiting 30 seconds for all messages to process...")
time.sleep(30)

print("\n" + "=" * 70)
print("🔍 VERIFICATION CHECKLIST")
print("=" * 70)
print("\n1. Go to Firestore Console:")
print("   https://console.cloud.google.com/firestore/data?project=memory-machines-project")
print("\n2. Check acme_corp tenant:")
print("   Path: tenants/acme_corp/processed_logs/")
print("   Should have 4 documents:")
print("     - 001: Phone 555-0199 → [REDACTED]")
print("     - 002: Phone 555-123-4567 → [REDACTED]")
print("     - 003: No phone (no redaction)")
print("     - <uuid>: Phone (555) 987-6543 → [REDACTED]")
print("\n3. Check beta_inc tenant:")
print("   Path: tenants/beta_inc/processed_logs/")
print("   Should have 4 documents:")
print("     - B001: No phone")
print("     - B002: No phone")
print("     - <uuid>: Phone 555-2468 → [REDACTED]")
print("     - <uuid>: Long message (~206 chars = 10.3s processing)")
print("\n4. Verify PDF Requirements:")
print("   ✅ Multi-tenant isolation: acme_corp ≠ beta_inc")
print("   ✅ Sub-collection structure: tenants/{id}/processed_logs/{id}")
print("   ✅ Phone redaction working")
print("   ✅ Processing time accurate (0.05s/char)")
print("   ✅ Both JSON and TXT formats")
print("\n" + "=" * 70)
print("🎥 READY FOR VIDEO DEMONSTRATION!")
print("=" * 70)