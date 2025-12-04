"""
Final A-Z Verification - All PDF Requirements
"""
import requests
import time

API_URL = "https://ingestion-api-1092727309970.us-central1.run.app"

print("="*70)
print("FINAL A-Z VERIFICATION")
print("="*70)

tests_passed = 0
tests_total = 0

# Test 1: API is live and public
print("\n1. API Live on Public Internet")
tests_total += 1
try:
    r = requests.get(f"{API_URL}/", timeout=5)
    if r.status_code == 200:
        print(f"   ✅ PASS - API accessible from internet")
        tests_passed += 1
    else:
        print(f"   ❌ FAIL - Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ FAIL - {str(e)}")

# Test 2: Single /ingest endpoint (POST only)
print("\n2. Single POST /ingest Endpoint")
tests_total += 1
try:
    r = requests.get(f"{API_URL}/ingest", timeout=5)
    if r.status_code == 405:  # Method Not Allowed
        print(f"   ✅ PASS - GET rejected, only POST allowed")
        tests_passed += 1
    else:
        print(f"   ❌ FAIL - GET should return 405, got {r.status_code}")
except Exception as e:
    print(f"   ❌ FAIL - {str(e)}")

# Test 3: JSON ingestion (PDF Scenario 1)
print("\n3. JSON Payload Ingestion (PDF Scenario 1)")
tests_total += 1
try:
    payload = {"tenant_id": "final_verify", "log_id": "json-test", "text": "User 555-0199 logged in"}
    r = requests.post(f"{API_URL}/ingest", json=payload, headers={"Content-Type": "application/json"}, timeout=5)
    
    if r.status_code == 202:
        data = r.json()
        has_fields = "status" in data and "tenant_id" in data and "log_id" in data
        no_fake_id = "message_id" not in data  # Should NOT have fake message_id
        
        if has_fields and no_fake_id:
            print(f"   ✅ PASS - 202 Accepted, honest response (no fake message_id)")
            tests_passed += 1
        else:
            print(f"   ❌ FAIL - Response format issue")
            print(f"   Response: {data}")
    else:
        print(f"   ❌ FAIL - Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ FAIL - {str(e)}")

# Test 4: TXT ingestion (PDF Scenario 2)
print("\n4. TXT Payload Ingestion (PDF Scenario 2)")
tests_total += 1
try:
    r = requests.post(
        f"{API_URL}/ingest",
        data="Raw text log with 555-1234",
        headers={"Content-Type": "text/plain", "X-Tenant-ID": "final_verify"},
        timeout=5
    )
    
    if r.status_code == 202:
        print(f"   ✅ PASS - 202 Accepted for TXT")
        tests_passed += 1
    else:
        print(f"   ❌ FAIL - Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ FAIL - {str(e)}")

# Test 5: Non-blocking (Response < 1s)
print("\n5. Non-Blocking Response (<1 second)")
tests_total += 1
try:
    start = time.time()
    r = requests.post(
        f"{API_URL}/ingest",
        json={"tenant_id": "perf", "text": "Performance test"},
        timeout=5
    )
    duration = time.time() - start
    
    if r.status_code == 202 and duration < 1.0:
        print(f"   ✅ PASS - Response in {duration*1000:.0f}ms")
        tests_passed += 1
    else:
        print(f"   ❌ FAIL - Duration: {duration}s")
except Exception as e:
    print(f"   ❌ FAIL - {str(e)}")

# Test 6: Error handling - Missing tenant_id
print("\n6. Error Handling - Missing tenant_id")
tests_total += 1
try:
    r = requests.post(f"{API_URL}/ingest", json={"text": "No tenant"}, timeout=5)
    
    if r.status_code == 400:
        print(f"   ✅ PASS - Rejects missing tenant_id with 400")
        tests_passed += 1
    else:
        print(f"   ❌ FAIL - Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ FAIL - {str(e)}")

# Test 7: Error handling - Missing X-Tenant-ID
print("\n7. Error Handling - Missing X-Tenant-ID for TXT")
tests_total += 1
try:
    r = requests.post(f"{API_URL}/ingest", data="Text without tenant", headers={"Content-Type": "text/plain"}, timeout=5)
    
    if r.status_code == 400:
        print(f"   ✅ PASS - Rejects missing X-Tenant-ID with 400")
        tests_passed += 1
    else:
        print(f"   ❌ FAIL - Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ FAIL - {str(e)}")

# Test 8: Serverless deployment
print("\n8. Serverless Deployment (No Auth Required)")
tests_total += 1
try:
    # Call without any auth headers
    r = requests.post(f"{API_URL}/ingest", json={"tenant_id": "test", "text": "Test"}, timeout=5)
    
    if r.status_code == 202:
        print(f"   ✅ PASS - Works without authentication")
        tests_passed += 1
    else:
        print(f"   ❌ FAIL - Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ FAIL - {str(e)}")

# Summary
print("\n" + "="*70)
print(f"API LAYER TESTS: {tests_passed}/{tests_total} ({tests_passed/tests_total*100:.1f}%)")
print("="*70)

# Now wait for worker processing
print("\n⏳ Waiting 20 seconds for worker to process messages...")
time.sleep(20)

print("\n" + "="*70)
print("VERIFYING WORKER & STORAGE")
print("="*70)
print("\nManual verification required:")
print("1. Go to Firestore Console")
print("2. Check: tenants/final_verify/processed_logs/json-test")
print("3. Verify fields:")
print("   - source: json_upload")
print("   - original_text: User 555-0199 logged in")
print("   - modified_data: User [REDACTED] logged in")
print("   - processed_at: (timestamp)")
print("   - processing_time: ~1.25 (25 chars × 0.05)")
print("\n4. Check: tenants/final_verify/processed_logs/ (auto-generated ID)")
print("5. Verify text format log also processed")

print("\n" + "="*70)