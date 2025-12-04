"""
Comprehensive Error Testing Suite
Tests all validation and error handling
"""
import requests
import json

API_URL = "https://ingestion-api-1092727309970.us-central1.run.app/ingest"

def test_case(name, method, url, headers, data, expected_status):
    """Run a single test case"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    
    try:
        if method == "POST":
            if headers.get("Content-Type") == "application/json":
                response = requests.post(url, json=data, headers=headers, timeout=5)
            else:
                response = requests.post(url, data=data, headers=headers, timeout=5)
        
        print(f"Expected Status: {expected_status}")
        print(f"Actual Status:   {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"✅ PASS")
            return True
        else:
            print(f"❌ FAIL")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def run_all_tests():
    """Run comprehensive test suite"""
    print("\n" + "="*60)
    print("🧪 COMPREHENSIVE ERROR HANDLING TEST SUITE")
    print("="*60)
    print(f"Target: {API_URL}")
    print("="*60)
    
    results = []
    
    # Test 1: Valid JSON (should work)
    results.append(test_case(
        "Valid JSON Request",
        "POST",
        API_URL,
        {"Content-Type": "application/json"},
        {"tenant_id": "test", "log_id": "valid-1", "text": "Valid message"},
        202
    ))
    
    # Test 2: Missing tenant_id in JSON
    results.append(test_case(
        "Missing tenant_id in JSON",
        "POST",
        API_URL,
        {"Content-Type": "application/json"},
        {"log_id": "test", "text": "No tenant"},
        400
    ))
    
    # Test 3: Malformed JSON
    results.append(test_case(
        "Malformed JSON",
        "POST",
        API_URL,
        {"Content-Type": "application/json"},
        "{bad json}",
        400
    ))
    
    # Test 4: Empty text
    results.append(test_case(
        "Empty Text Field",
        "POST",
        API_URL,
        {"Content-Type": "application/json"},
        {"tenant_id": "test", "text": ""},
        400
    ))
    
    # Test 5: Very long text
    results.append(test_case(
        "Text Exceeds Max Length (10,001 chars)",
        "POST",
        API_URL,
        {"Content-Type": "application/json"},
        {"tenant_id": "test", "text": "A" * 10001},
        400
    ))
    
    # Test 6: Invalid tenant_id format (special chars)
    results.append(test_case(
        "Invalid tenant_id with Special Characters",
        "POST",
        API_URL,
        {"Content-Type": "application/json"},
        {"tenant_id": "invalid@tenant!", "text": "Test"},
        400
    ))
    
    # Test 7: Valid TXT request
    results.append(test_case(
        "Valid TXT Request",
        "POST",
        API_URL,
        {"Content-Type": "text/plain", "X-Tenant-ID": "test"},
        "Valid text message",
        202
    ))
    
    # Test 8: Missing X-Tenant-ID for TXT
    results.append(test_case(
        "Missing X-Tenant-ID Header for TXT",
        "POST",
        API_URL,
        {"Content-Type": "text/plain"},
        "Text without tenant",
        400
    ))
    
    # Test 9: Invalid X-Tenant-ID format
    results.append(test_case(
        "Invalid X-Tenant-ID Format",
        "POST",
        API_URL,
        {"Content-Type": "text/plain", "X-Tenant-ID": "invalid tenant!"},
        "Text message",
        400
    ))
    
    # Test 10: Unsupported content type
    results.append(test_case(
        "Unsupported Content-Type (XML)",
        "POST",
        API_URL,
        {"Content-Type": "application/xml"},
        "<xml>data</xml>",
        415
    ))
    
    # Test 11: Empty TXT payload
    results.append(test_case(
        "Empty TXT Payload",
        "POST",
        API_URL,
        {"Content-Type": "text/plain", "X-Tenant-ID": "test"},
        "",
        400
    ))
    
    # Test 12: Long valid text (edge case - should work)
    results.append(test_case(
        "Long Valid Text (5000 chars)",
        "POST",
        API_URL,
        {"Content-Type": "application/json"},
        {"tenant_id": "test", "log_id": "long-1", "text": "A" * 5000},
        202
    ))
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    print("="*60)
    
    if passed == total:
        print("✅ ALL TESTS PASSED! System is robust!")
    else:
        print(f"⚠️ {total - passed} test(s) failed")
    
    print("="*60)

if __name__ == "__main__":
    run_all_tests()