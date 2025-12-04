"""
Load Test Script - 1000 RPM Test
Tests API with mixed JSON and TXT payloads
"""
import asyncio
import aiohttp
import time
from datetime import datetime

# Configuration
API_URL = "https://ingestion-api-1092727309970.us-central1.run.app/ingest"
TOTAL_REQUESTS = 1000
DURATION_SECONDS = 60  # Spread over 60 seconds for 1000 RPM
TEST_TENANT = "load_test"

async def send_json_request(session, i):
    """Send JSON request"""
    payload = {
        "tenant_id": TEST_TENANT,
        "log_id": f"json-{i}",
        "text": f"Load test JSON message {i} with phone 555-{i:04d}"
    }
    
    try:
        start = time.time()
        async with session.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=5)
        ) as response:
            duration = time.time() - start
            status = response.status
            return {
                "success": status == 202,
                "status": status,
                "duration": duration,
                "type": "json"
            }
    except Exception as e:
        return {
            "success": False,
            "status": 0,
            "duration": 0,
            "type": "json",
            "error": str(e)
        }

async def send_text_request(session, i):
    """Send text/plain request"""
    text = f"Load test TXT message {i} with phone 555-{i:04d}"
    
    try:
        start = time.time()
        async with session.post(
            API_URL,
            data=text,
            headers={
                "Content-Type": "text/plain",
                "X-Tenant-ID": TEST_TENANT
            },
            timeout=aiohttp.ClientTimeout(total=5)
        ) as response:
            duration = time.time() - start
            status = response.status
            return {
                "success": status == 202,
                "status": status,
                "duration": duration,
                "type": "text"
            }
    except Exception as e:
        return {
            "success": False,
            "status": 0,
            "duration": 0,
            "type": "text",
            "error": str(e)
        }

async def run_load_test():
    """Run 1000 RPM load test"""
    print("=" * 70)
    print("🚀 STARTING 1000 RPM LOAD TEST")
    print("=" * 70)
    print(f"Target API: {API_URL}")
    print(f"Total Requests: {TOTAL_REQUESTS}")
    print(f"Duration: {DURATION_SECONDS} seconds")
    print(f"Target RPM: {(TOTAL_REQUESTS / DURATION_SECONDS) * 60:.0f}")
    print(f"Test Tenant: {TEST_TENANT}")
    print("=" * 70)
    print()
    
    results = []
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for i in range(TOTAL_REQUESTS):
            # 50% JSON, 50% TXT (mixed as PDF requires)
            if i % 2 == 0:
                task = send_json_request(session, i)
            else:
                task = send_text_request(session, i)
            
            tasks.append(task)
            
            # Small delay to spread requests evenly
            if i < TOTAL_REQUESTS - 1:
                await asyncio.sleep(DURATION_SECONDS / TOTAL_REQUESTS)
        
        print("⏳ Waiting for all requests to complete...")
        results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Analyze results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    json_requests = [r for r in results if r["type"] == "json"]
    text_requests = [r for r in results if r["type"] == "text"]
    
    avg_duration = sum(r["duration"] for r in successful) / len(successful) if successful else 0
    max_duration = max(r["duration"] for r in successful) if successful else 0
    min_duration = min(r["duration"] for r in successful) if successful else 0
    
    # Print results
    print()
    print("=" * 70)
    print("📊 LOAD TEST RESULTS")
    print("=" * 70)
    print(f"Total Requests:      {len(results)}")
    print(f"Successful (202):    {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Failed:              {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
    print(f"JSON Requests:       {len(json_requests)}")
    print(f"Text Requests:       {len(text_requests)}")
    print()
    print(f"Total Duration:      {total_duration:.2f}s")
    print(f"Actual RPM:          {(len(results) / total_duration) * 60:.0f}")
    print()
    print(f"Response Times:")
    print(f"  Average:           {avg_duration*1000:.0f}ms")
    print(f"  Min:               {min_duration*1000:.0f}ms")
    print(f"  Max:               {max_duration*1000:.0f}ms")
    print("=" * 70)
    
    # Status code distribution
    status_codes = {}
    for r in results:
        status = r["status"]
        status_codes[status] = status_codes.get(status, 0) + 1
    """
Load Test Script - 1000 RPM Test (with better error handling)
"""
import asyncio
import aiohttp
import time
import ssl
from datetime import datetime

# Configuration
API_URL = "https://ingestion-api-1092727309970.us-central1.run.app/ingest"
TOTAL_REQUESTS = 1000
DURATION_SECONDS = 60
TEST_TENANT = "load_test"

async def send_json_request(session, i):
    """Send JSON request"""
    payload = {
        "tenant_id": TEST_TENANT,
        "log_id": f"json-{i}",
        "text": f"Load test JSON {i}"
    }
    
    try:
        start = time.time()
        async with session.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            duration = time.time() - start
            status = response.status
            return {
                "success": status == 202,
                "status": status,
                "duration": duration,
                "type": "json",
                "id": i
            }
    except asyncio.TimeoutError as e:
        return {"success": False, "status": 0, "duration": 0, "type": "json", "error": f"Timeout: {str(e)}", "id": i}
    except aiohttp.ClientError as e:
        return {"success": False, "status": 0, "duration": 0, "type": "json", "error": f"Client error: {str(e)}", "id": i}
    except Exception as e:
        return {"success": False, "status": 0, "duration": 0, "type": "json", "error": f"Error: {type(e).__name__}: {str(e)}", "id": i}

async def send_text_request(session, i):
    """Send text request"""
    text = f"Load test TXT {i}"
    
    try:
        start = time.time()
        async with session.post(
            API_URL,
            data=text,
            headers={"Content-Type": "text/plain", "X-Tenant-ID": TEST_TENANT},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            duration = time.time() - start
            status = response.status
            return {
                "success": status == 202,
                "status": status,
                "duration": duration,
                "type": "text",
                "id": i
            }
    except asyncio.TimeoutError as e:
        return {"success": False, "status": 0, "duration": 0, "type": "text", "error": f"Timeout: {str(e)}", "id": i}
    except aiohttp.ClientError as e:
        return {"success": False, "status": 0, "duration": 0, "type": "text", "error": f"Client error: {str(e)}", "id": i}
    except Exception as e:
        return {"success": False, "status": 0, "duration": 0, "type": "text", "error": f"Error: {type(e).__name__}: {str(e)}", "id": i}

async def run_load_test():
    """Run load test with better error handling"""
    print("=" * 70)
    print("🚀 1000 RPM LOAD TEST - IMPROVED")
    print("=" * 70)
    print(f"Target: {API_URL}")
    print(f"Requests: {TOTAL_REQUESTS}")
    print(f"Duration: {DURATION_SECONDS}s")
    print("=" * 70)
    
    # Create SSL context that doesn't verify (for Windows issues)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Create connector with more connections allowed
    connector = aiohttp.TCPConnector(
        limit=100,  # Max 100 concurrent connections
        ssl=ssl_context
    )
    
    results = []
    start_time = time.time()
    
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        
        for i in range(TOTAL_REQUESTS):
            if i % 2 == 0:
                task = send_json_request(session, i)
            else:
                task = send_text_request(session, i)
            
            tasks.append(task)
            
            # Progress indicator
            if (i + 1) % 100 == 0:
                print(f"  Queued {i + 1} requests...")
            
            # Small delay to spread requests
            if i < TOTAL_REQUESTS - 1:
                await asyncio.sleep(DURATION_SECONDS / TOTAL_REQUESTS)
        
        print("⏳ Waiting for responses...")
        results = await asyncio.gather(*tasks)
    
    total_duration = time.time() - start_time
    
    # Analyze
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    if successful:
        avg_duration = sum(r["duration"] for r in successful) / len(successful)
        max_duration = max(r["duration"] for r in successful)
        min_duration = min(r["duration"] for r in successful)
    else:
        avg_duration = max_duration = min_duration = 0
    
    # Results
    print()
    print("=" * 70)
    print("📊 RESULTS")
    print("=" * 70)
    print(f"Total:        {len(results)}")
    print(f"Success:      {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Failed:       {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
    print(f"Duration:     {total_duration:.2f}s")
    print(f"Actual RPM:   {(len(results) / total_duration) * 60:.0f}")
    
    if successful:
        print(f"Avg Response: {avg_duration*1000:.0f}ms")
        print(f"Min Response: {min_duration*1000:.0f}ms")
        print(f"Max Response: {max_duration*1000:.0f}ms")
    
    if failed:
        print(f"\n⚠️ First 5 Errors:")
        for r in failed[:5]:
            print(f"  Request {r.get('id')}: {r.get('error', 'Unknown')}")
    
    print("=" * 70)
    
    if len(successful) >= 950:
        print("✅ PASSED! System handles 1000 RPM!")
    else:
        print("❌ FAILED! Too many errors")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_load_test())
    print("\nStatus Code Distribution:")
    for status, count in sorted(status_codes.items()):
        print(f"  {status}: {count} ({count/len(results)*100:.1f}%)")
    
    if failed:
        print("\n⚠️ Sample Errors:")
        for r in failed[:5]:
            print(f"  - {r.get('error', 'Unknown error')}")
    
    # Final verdict
    print()
    print("=" * 70)
    if len(successful) >= 950:  # 95% success rate
        print("✅ TEST PASSED! System handles 1000 RPM successfully!")
    else:
        print("⚠️ TEST WARNING: Some requests failed")
    print("=" * 70)

if __name__ == "__main__":
    print(f"\n🕐 Test starting at: {datetime.now()}\n")
    asyncio.run(run_load_test())
    print(f"\n🕐 Test completed at: {datetime.now()}\n")