"""
Cleanup Script: Remove all dummy data while preserving Material Master and Users
Created for Solar Manufacturing WMS
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections to KEEP
KEEP_COLLECTIONS = ['users', 'materials']

# Collections to DELETE
DELETE_COLLECTIONS = [
    'grn',
    'transfer_orders',
    'transfer_requirements',
    'quants',
    'bins',
    'bin_blocks',
    'labels',
    'issues',
    'stock_movements',
    'audit_logs',
    'warehouse_transfers',
    'physical_inventory',
    'inventory_count_items',
    'storage_units',
    'print_logs'
]

def cleanup_dummy_data():
    print("=" * 70)
    print("WMS DUMMY DATA CLEANUP")
    print("=" * 70)
    print()
    
    # Get all existing collections
    existing_collections = db.list_collection_names()
    print(f"📊 Current collections in database '{DB_NAME}':")
    for coll in existing_collections:
        count = db[coll].count_documents({})
        print(f"   - {coll}: {count} documents")
    print()
    
    # Show what will be kept
    print("✅ COLLECTIONS TO KEEP:")
    for coll in KEEP_COLLECTIONS:
        if coll in existing_collections:
            count = db[coll].count_documents({})
            print(f"   - {coll}: {count} documents")
    print()
    
    # Show what will be deleted
    print("🗑️  COLLECTIONS TO DELETE:")
    collections_to_remove = []
    for coll in DELETE_COLLECTIONS:
        if coll in existing_collections:
            count = db[coll].count_documents({})
            collections_to_remove.append(coll)
            print(f"   - {coll}: {count} documents")
    print()
    
    # Confirm deletion
    confirmation = input("⚠️  Proceed with deletion? (yes/no): ")
    if confirmation.lower() != 'yes':
        print("❌ Cleanup cancelled.")
        return
    
    print()
    print("🔄 Starting cleanup...")
    print()
    
    # Delete collections
    deleted_count = 0
    for coll in collections_to_remove:
        try:
            result = db[coll].delete_many({})
            print(f"   ✓ Deleted {result.deleted_count} documents from '{coll}'")
            deleted_count += 1
        except Exception as e:
            print(f"   ✗ Error deleting '{coll}': {e}")
    
    print()
    print("=" * 70)
    print("CLEANUP SUMMARY")
    print("=" * 70)
    print(f"✅ Collections deleted: {deleted_count}")
    print(f"✅ Collections preserved: {len(KEEP_COLLECTIONS)}")
    print()
    
    # Final state
    print("📊 Final state:")
    remaining_collections = db.list_collection_names()
    for coll in remaining_collections:
        count = db[coll].count_documents({})
        print(f"   - {coll}: {count} documents")
    print()
    
    print("✅ Cleanup complete! Material Master and Users preserved.")
    print("=" * 70)

if __name__ == "__main__":
    cleanup_dummy_data()
