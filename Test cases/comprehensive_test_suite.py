"""
Professional QA Test Suite - Memory Machines Assignment
Tests all requirements from PDF with expert-level thoroughness
"""
import requests
import time
import json
from datetime import datetime
from google.cloud import firestore
import os

API_URL = "https://ingestion-api-1092727309970.us-central1.run.app/ingest"
PROJECT_ID = "memory-machines-project"

# Initialize Firestore for verification
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'api-service\service-account-key.json'
db = firestore.Client(project=PROJECT_ID)

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def add(self, test_name, passed, details=""):
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print("\n" + "="*70)
        print("📊 FINAL TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Success Rate: {self.passed/(self.passed+self.failed)*100:.1f}%")
        print("="*70)
        
        if self.failed > 0:
            print("\n❌ Failed Tests:")
            for r in self.results:
                if not r["passed"]:
                    print(f"  - {r['test']}: {r['details']}")
        
        print("\n" + "="*70)
        if self.failed == 0:
            print("🎉 ALL TESTS PASSED! SYSTEM IS PRODUCTION READY!")
        else:
            print(f"⚠️ {self.failed} test(s) need attention")
        print("="*70)

results = TestResults()

# ===== CATEGORY 1: FUNCTIONAL CORRECTNESS =====
print("\n" + "="*70)
print("CATEGORY 1: FUNCTIONAL CORRECTNESS")
print("="*70)

# Test 1.1: Valid JSON request
print("\nTest 1.1: Valid JSON Request")
try:
    r = requests.post(API_URL, json={"tenant_id": "qa_test", "log_id": "func-1", "text": "Functional test"}, timeout=5)
    passed = r.status_code == 202
    results.add("Valid JSON Request", passed, f"Status: {r.status_code}")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Status: {r.status_code}")
except Exception as e:
    results.add("Valid JSON Request", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# Test 1.2: Valid TXT request
print("\nTest 1.2: Valid TXT Request")
try:
    r = requests.post(API_URL, data="Functional test TXT", headers={"Content-Type": "text/plain", "X-Tenant-ID": "qa_test"}, timeout=5)
    passed = r.status_code == 202
    results.add("Valid TXT Request", passed, f"Status: {r.status_code}")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Status: {r.status_code}")
except Exception as e:
    results.add("Valid TXT Request", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# Test 1.3: Response format correctness
print("\nTest 1.3: Response Format Validation")
try:
    r = requests.post(API_URL, json={"tenant_id": "qa_test", "text": "Format test"}, timeout=5)
    data = r.json()
    has_fields = all(k in data for k in ["status", "message_id", "tenant_id", "log_id"])
    passed = r.status_code == 202 and has_fields
    results.add("Response Format", passed, f"Has all fields: {has_fields}")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Fields present: {has_fields}")
except Exception as e:
    results.add("Response Format", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# ===== CATEGORY 2: ERROR HANDLING =====
print("\n" + "="*70)
print("CATEGORY 2: ERROR HANDLING")
print("="*70)

# Test 2.1: Missing tenant_id
print("\nTest 2.1: Missing tenant_id")
try:
    r = requests.post(API_URL, json={"text": "No tenant"}, timeout=5)
    passed = r.status_code == 400
    results.add("Reject Missing tenant_id", passed, f"Status: {r.status_code}")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Status: {r.status_code}")
except Exception as e:
    results.add("Reject Missing tenant_id", False, str(e))

# Test 2.2: Empty text
print("\nTest 2.2: Empty Text")
try:
    r = requests.post(API_URL, json={"tenant_id": "qa_test", "text": ""}, timeout=5)
    passed = r.status_code == 400
    results.add("Reject Empty Text", passed, f"Status: {r.status_code}")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Status: {r.status_code}")
except Exception as e:
    results.add("Reject Empty Text", False, str(e))

# Test 2.3: Text too long
print("\nTest 2.3: Text Exceeds Max Length")
try:
    r = requests.post(API_URL, json={"tenant_id": "qa_test", "text": "A" * 10001}, timeout=5)
    passed = r.status_code == 400
    results.add("Reject Oversized Text", passed, f"Status: {r.status_code}")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Status: {r.status_code}")
except Exception as e:
    results.add("Reject Oversized Text", False, str(e))

# Test 2.4: Invalid tenant_id format
print("\nTest 2.4: Invalid tenant_id Format")
try:
    r = requests.post(API_URL, json={"tenant_id": "invalid@tenant!", "text": "Test"}, timeout=5)
    passed = r.status_code == 400
    results.add("Reject Invalid tenant_id", passed, f"Status: {r.status_code}")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Status: {r.status_code}")
except Exception as e:
    results.add("Reject Invalid tenant_id", False, str(e))

# Test 2.5: Missing X-Tenant-ID header
print("\nTest 2.5: Missing X-Tenant-ID for TXT")
try:
    r = requests.post(API_URL, data="Text", headers={"Content-Type": "text/plain"}, timeout=5)
    passed = r.status_code == 400
    results.add("Reject Missing X-Tenant-ID", passed, f"Status: {r.status_code}")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Status: {r.status_code}")
except Exception as e:
    results.add("Reject Missing X-Tenant-ID", False, str(e))

# Test 2.6: Unsupported content type
print("\nTest 2.6: Unsupported Content Type")
try:
    r = requests.post(API_URL, data="<xml/>", headers={"Content-Type": "application/xml"}, timeout=5)
    passed = r.status_code == 415
    results.add("Reject Unsupported Content-Type", passed, f"Status: {r.status_code}")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Status: {r.status_code}")
except Exception as e:
    results.add("Reject Unsupported Content-Type", False, str(e))

# ===== CATEGORY 3: DATA INTEGRITY =====
print("\n" + "="*70)
print("CATEGORY 3: DATA INTEGRITY (End-to-End)")
print("="*70)

# Test 3.1: Data reaches Firestore
print("\nTest 3.1: Data Persists to Firestore")
test_log_id = f"integrity-test-{int(time.time())}"
try:
    r = requests.post(API_URL, json={"tenant_id": "qa_test", "log_id": test_log_id, "text": "Data integrity test 555-1111"}, timeout=5)
    
    if r.status_code == 202:
        # Wait for processing
        print("  Waiting 5 seconds for processing...")
        time.sleep(5)
        
        # Check Firestore
        doc_ref = db.collection('tenants').document('qa_test').collection('processed_logs').document(test_log_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            print(f"  ✅ Document found in Firestore")
            results.add("Data Persists to Firestore", True, "Document created")
        else:
            print(f"  ❌ Document NOT found in Firestore")
            results.add("Data Persists to Firestore", False, "Document missing")
    else:
        results.add("Data Persists to Firestore", False, f"API returned {r.status_code}")
except Exception as e:
    results.add("Data Persists to Firestore", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# Test 3.2: Processing time accuracy
print("\nTest 3.2: Processing Time Accuracy (0.05s per char)")
test_log_id = f"timing-test-{int(time.time())}"
test_text = "A" * 100  # 100 chars = 5.0 seconds expected
try:
    r = requests.post(API_URL, json={"tenant_id": "qa_test", "log_id": test_log_id, "text": test_text}, timeout=5)
    
    if r.status_code == 202:
        print("  Waiting 10 seconds for processing...")
        time.sleep(10)
        
        doc_ref = db.collection('tenants').document('qa_test').collection('processed_logs').document(test_log_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            processing_time = data.get('processing_time', 0)
            expected_time = 100 * 0.05  # 5.0 seconds
            
            # Allow 0.1s tolerance
            passed = abs(processing_time - expected_time) < 0.1
            print(f"  Expected: {expected_time}s, Actual: {processing_time}s")
            print(f"  {'✅ PASS' if passed else '❌ FAIL'}")
            results.add("Processing Time Accuracy", passed, f"Expected {expected_time}s, got {processing_time}s")
        else:
            results.add("Processing Time Accuracy", False, "Document not found")
    else:
        results.add("Processing Time Accuracy", False, f"API error: {r.status_code}")
except Exception as e:
    results.add("Processing Time Accuracy", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# Test 3.3: Phone redaction correctness
print("\nTest 3.3: Phone Number Redaction")
test_log_id = f"redaction-test-{int(time.time())}"
try:
    r = requests.post(API_URL, json={"tenant_id": "qa_test", "log_id": test_log_id, "text": "Contact 555-1234 or 555-987-6543"}, timeout=5)
    
    if r.status_code == 202:
        print("  Waiting 5 seconds for processing...")
        time.sleep(5)
        
        doc_ref = db.collection('tenants').document('qa_test').collection('processed_logs').document(test_log_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            original = data.get('original_text', '')
            modified = data.get('modified_data', '')
            
            # Check both phone numbers are redacted
            has_original_phones = '555-1234' in original and '555-987-6543' in original
            phones_redacted = '[REDACTED]' in modified and '555-1234' not in modified and '555-987-6543' not in modified
            
            passed = has_original_phones and phones_redacted
            print(f"  Original preserved: {has_original_phones}")
            print(f"  Phones redacted: {phones_redacted}")
            print(f"  {'✅ PASS' if passed else '❌ FAIL'}")
            results.add("Phone Redaction", passed, f"Redacted: {phones_redacted}")
        else:
            results.add("Phone Redaction", False, "Document not found")
    else:
        results.add("Phone Redaction", False, f"API error: {r.status_code}")
except Exception as e:
    results.add("Phone Redaction", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# Test 3.4: Firestore schema compliance
print("\nTest 3.4: Firestore Schema Compliance (PDF Page 3)")
try:
    doc_ref = db.collection('tenants').document('qa_test').collection('processed_logs').limit(1).stream()
    doc = next(doc_ref)
    data = doc.to_dict()
    
    # PDF required fields
    required_fields = ["source", "original_text", "modified_data", "processed_at"]
    has_all = all(field in data for field in required_fields)
    
    print(f"  Required fields present: {has_all}")
    print(f"  Fields: {list(data.keys())}")
    print(f"  {'✅ PASS' if has_all else '❌ FAIL'}")
    results.add("Schema Compliance", has_all, f"Has all PDF fields: {has_all}")
except Exception as e:
    results.add("Schema Compliance", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# ===== CATEGORY 4: MULTI-TENANT ISOLATION =====
print("\n" + "="*70)
print("CATEGORY 4: MULTI-TENANT ISOLATION (PDF Page 4)")
print("="*70)

# Test 4.1: Physical separation
print("\nTest 4.1: Tenant Data Physical Separation")
try:
    # Send to tenant A
    r1 = requests.post(API_URL, json={"tenant_id": "tenant_a", "log_id": "iso-a", "text": "Data A"}, timeout=5)
    # Send to tenant B
    r2 = requests.post(API_URL, json={"tenant_id": "tenant_b", "log_id": "iso-b", "text": "Data B"}, timeout=5)
    
    if r1.status_code == 202 and r2.status_code == 202:
        time.sleep(5)
        
        # Check tenant A path
        doc_a = db.collection('tenants').document('tenant_a').collection('processed_logs').document('iso-a').get()
        # Check tenant B path
        doc_b = db.collection('tenants').document('tenant_b').collection('processed_logs').document('iso-b').get()
        
        # Try to access tenant B data from tenant A path (should not exist)
        wrong_path = db.collection('tenants').document('tenant_a').collection('processed_logs').document('iso-b').get()
        
        passed = doc_a.exists and doc_b.exists and not wrong_path.exists
        print(f"  Tenant A document exists in correct path: {doc_a.exists}")
        print(f"  Tenant B document exists in correct path: {doc_b.exists}")
        print(f"  Tenant B document NOT in tenant A path: {not wrong_path.exists}")
        print(f"  {'✅ PASS' if passed else '❌ FAIL'}")
        results.add("Physical Tenant Separation", passed, f"Proper isolation: {passed}")
    else:
        results.add("Physical Tenant Separation", False, "API requests failed")
except Exception as e:
    results.add("Physical Tenant Separation", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# Test 4.2: Collection structure matches PDF
print("\nTest 4.2: Collection Structure (tenants/{id}/processed_logs/{id})")
try:
    # Check if structure matches PDF exactly
    tenants_ref = db.collection('tenants')
    tenants = list(tenants_ref.limit(1).stream())
    
    if tenants:
        tenant_doc = tenants[0]
        logs_ref = tenant_doc.reference.collection('processed_logs')
        logs = list(logs_ref.limit(1).stream())
        
        structure_correct = len(logs) > 0
        print(f"  Structure: tenants/{tenant_doc.id}/processed_logs/{logs[0].id if logs else 'N/A'}")
        print(f"  {'✅ PASS' if structure_correct else '❌ FAIL'}")
        results.add("Collection Structure", structure_correct, "Matches PDF schema")
    else:
        results.add("Collection Structure", False, "No tenants found")
except Exception as e:
    results.add("Collection Structure", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# ===== CATEGORY 5: PERFORMANCE =====
print("\n" + "="*70)
print("CATEGORY 5: PERFORMANCE (PDF Page 4 - 1000 RPM)")
print("="*70)

# Test 5.1: Response time (non-blocking)
print("\nTest 5.1: Non-Blocking Response (<1s)")
try:
    start = time.time()
    r = requests.post(API_URL, json={"tenant_id": "perf_test", "text": "Performance test"}, timeout=5)
    duration = time.time() - start
    
    passed = r.status_code == 202 and duration < 1.0
    print(f"  Response time: {duration*1000:.0f}ms")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Target: <1000ms")
    results.add("Non-Blocking Response", passed, f"{duration*1000:.0f}ms")
except Exception as e:
    results.add("Non-Blocking Response", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# Test 5.2: Concurrent requests
print("\nTest 5.2: Concurrent Mixed Requests (50 JSON + 50 TXT)")
try:
    import concurrent.futures
    
    def send_request(i):
        if i % 2 == 0:
            return requests.post(API_URL, json={"tenant_id": "concurrent_test", "text": f"Concurrent {i}"}, timeout=5)
        else:
            return requests.post(API_URL, data=f"Concurrent TXT {i}", headers={"Content-Type": "text/plain", "X-Tenant-ID": "concurrent_test"}, timeout=5)
    
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(send_request, i) for i in range(100)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]
    duration = time.time() - start
    
    success_count = sum(1 for r in responses if r.status_code == 202)
    passed = success_count >= 95  # 95% success rate
    
    print(f"  Requests: 100, Success: {success_count}, Duration: {duration:.2f}s")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Success rate: {success_count}%")
    results.add("Concurrent Requests", passed, f"{success_count}/100 succeeded")
except Exception as e:
    results.add("Concurrent Requests", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# ===== CATEGORY 6: EDGE CASES =====
print("\n" + "="*70)
print("CATEGORY 6: EDGE CASES")
print("="*70)

# Test 6.1: Unicode and special characters
print("\nTest 6.1: Unicode Text (Emoji, Chinese, etc.)")
try:
    r = requests.post(API_URL, json={"tenant_id": "edge_test", "text": "Hello 世界 🚀 Test"}, timeout=5)
    passed = r.status_code == 202
    results.add("Unicode Support", passed, f"Status: {r.status_code}")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Status: {r.status_code}")
except Exception as e:
    results.add("Unicode Support", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# Test 6.2: Very long text (near limit)
print("\nTest 6.2: Large Text Payload (9999 chars)")
try:
    r = requests.post(API_URL, json={"tenant_id": "edge_test", "text": "X" * 9999}, timeout=5)
    passed = r.status_code == 202
    results.add("Large Text Handling", passed, f"Status: {r.status_code}")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Status: {r.status_code}")
except Exception as e:
    results.add("Large Text Handling", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# Test 6.3: Minimum text length
print("\nTest 6.3: Minimum Text Length (1 char)")
try:
    r = requests.post(API_URL, json={"tenant_id": "edge_test", "text": "A"}, timeout=5)
    passed = r.status_code == 202
    results.add("Minimum Text Length", passed, f"Status: {r.status_code}")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} - Status: {r.status_code}")
except Exception as e:
    results.add("Minimum Text Length", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# Test 6.4: Duplicate log_id (idempotency)
print("\nTest 6.4: Duplicate log_id (Idempotency)")
duplicate_id = f"duplicate-test-{int(time.time())}"
try:
    # Send same log_id twice
    r1 = requests.post(API_URL, json={"tenant_id": "idempotency_test", "log_id": duplicate_id, "text": "First"}, timeout=5)
    r2 = requests.post(API_URL, json={"tenant_id": "idempotency_test", "log_id": duplicate_id, "text": "Second"}, timeout=5)
    
    both_accepted = r1.status_code == 202 and r2.status_code == 202
    print(f"  Both requests accepted: {both_accepted}")
    
    if both_accepted:
        time.sleep(5)
        # Check Firestore - should only have ONE document (or latest overwrites)
        doc_ref = db.collection('tenants').document('idempotency_test').collection('processed_logs').document(duplicate_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            # Should have "Second" text (latest)
            has_latest = "Second" in data.get('original_text', '')
            print(f"  Document has latest data: {has_latest}")
            print(f"  {'✅ PASS' if has_latest else '⚠️ WARNING'} - Idempotent writes")
            results.add("Idempotency", has_latest, "Latest data preserved")
        else:
            results.add("Idempotency", False, "Document not found")
    else:
        results.add("Idempotency", False, "Requests failed")
except Exception as e:
    results.add("Idempotency", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# ===== CATEGORY 7: INTEGRATION =====
print("\n" + "="*70)
print("CATEGORY 7: END-TO-END INTEGRATION")
print("="*70)

# Test 7.1: Complete flow JSON
print("\nTest 7.1: Full Flow - JSON Request → Firestore")
flow_log_id = f"e2e-json-{int(time.time())}"
try:
    # Step 1: Send request
    r = requests.post(API_URL, json={"tenant_id": "e2e_test", "log_id": flow_log_id, "text": "End-to-end JSON test 555-0000"}, timeout=5)
    api_success = r.status_code == 202
    
    # Step 2: Wait for processing
    time.sleep(5)
    
    # Step 3: Verify in Firestore
    doc = db.collection('tenants').document('e2e_test').collection('processed_logs').document(flow_log_id).get()
    
    # Step 4: Verify all fields
    if doc.exists:
        data = doc.to_dict()
        has_source = data.get('source') == 'json_upload'
        has_redaction = '[REDACTED]' in data.get('modified_data', '')
        has_timestamp = 'processed_at' in data
        
        passed = api_success and has_source and has_redaction and has_timestamp
        print(f"  API accepted: {api_success}")
        print(f"  Source correct: {has_source}")
        print(f"  Redaction applied: {has_redaction}")
        print(f"  Timestamp present: {has_timestamp}")
        print(f"  {'✅ PASS' if passed else '❌ FAIL'}")
        results.add("E2E JSON Flow", passed, "Complete flow verified")
    else:
        results.add("E2E JSON Flow", False, "Document not created")
except Exception as e:
    results.add("E2E JSON Flow", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# Test 7.2: Complete flow TXT
print("\nTest 7.2: Full Flow - TXT Request → Firestore")
flow_log_id = f"e2e-txt-{int(time.time())}"
try:
    # Send TXT request
    r = requests.post(API_URL, data="End-to-end TXT test 555-9999", headers={"Content-Type": "text/plain", "X-Tenant-ID": "e2e_test"}, timeout=5)
    api_success = r.status_code == 202
    response_data = r.json()
    log_id = response_data.get('log_id')  # Get auto-generated ID
    
    time.sleep(5)
    
    # Verify in Firestore using auto-generated log_id
    doc = db.collection('tenants').document('e2e_test').collection('processed_logs').document(log_id).get()
    
    if doc.exists:
        data = doc.to_dict()
        has_source = data.get('source') == 'text_upload'
        has_redaction = '[REDACTED]' in data.get('modified_data', '')
        
        passed = api_success and has_source and has_redaction
        print(f"  API accepted: {api_success}")
        print(f"  Source correct: {has_source}")
        print(f"  Redaction applied: {has_redaction}")
        print(f"  {'✅ PASS' if passed else '❌ FAIL'}")
        results.add("E2E TXT Flow", passed, "Complete flow verified")
    else:
        results.add("E2E TXT Flow", False, "Document not created")
except Exception as e:
    results.add("E2E TXT Flow", False, str(e))
    print(f"  ❌ FAIL - {str(e)}")

# Print final summary
results.print_summary()
