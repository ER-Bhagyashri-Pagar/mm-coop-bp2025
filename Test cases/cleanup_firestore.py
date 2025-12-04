"""
Clean up all test data from Firestore
"""
from google.cloud import firestore
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'api-service\service-account-key.json'
db = firestore.Client(project='memory-machines-project')

# List of all test tenants
test_tenants = [
    'acme', 'beta_inc', 'load_test', 'concurrent_test', 
    'qa_test', 'e2e_test', 'perf', 'perf_test', 
    'tenant_a', 'tenant_b', 'test', 'verify', 
    'final_verify', 'edge_test', 'idempotency_test',
    'speed_test', 'debug_test', 'demo'
]

print("🗑️ Cleaning up test data from Firestore...")
print("=" * 60)

total_deleted = 0

for tenant in test_tenants:
    try:
        # Get all logs for this tenant
        logs_ref = db.collection('tenants').document(tenant).collection('processed_logs')
        docs = logs_ref.stream()
        
        count = 0
        for doc in docs:
            doc.reference.delete()
            count += 1
        
        if count > 0:
            # Delete the tenant document itself
            db.collection('tenants').document(tenant).delete()
            print(f"✅ Deleted {count} logs for tenant: {tenant}")
            total_deleted += count
        
    except Exception as e:
        print(f"⚠️ Error deleting {tenant}: {str(e)}")

print("=" * 60)
print(f"🎉 Cleanup complete! Deleted {total_deleted} documents total")
print("=" * 60)