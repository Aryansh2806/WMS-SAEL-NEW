"""
Phase 1 SAP WM Features - Comprehensive Test Data Generation
Creates test data for: Quants, Transfer Orders, Physical Inventory, Stock Categories, SLED tracking
"""
import asyncio
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os
import jwt
import uuid
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def get_admin_token():
    """Get admin JWT token"""
    admin_user = await db.users.find_one({"email": "admin@warehouse.com"})
    if not admin_user:
        print("❌ Admin user not found")
        return None
    
    JWT_SECRET = os.environ.get('JWT_SECRET', 'warehouse-inventory-secret-key-2024')
    JWT_ALGORITHM = "HS256"
    expiration = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        "user_id": admin_user["user_id"],
        "email": admin_user["email"],
        "role": admin_user["role"],
        "exp": expiration
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

async def migrate_existing_stock_to_quants():
    """
    Migrate existing GRN stock data to Quant structure
    This preserves all existing solar manufacturing data
    """
    print("\n📦 Migrating Existing Stock to Quant Structure...")
    print("=" * 70)
    
    admin_user = await db.users.find_one({"email": "admin@warehouse.com"})
    admin_id = admin_user["user_id"]
    
    # Get all completed GRNs
    grns = await db.grn.find({"status": "completed"}, {"_id": 0}).to_list(1000)
    
    quants_created = 0
    
    for grn in grns:
        for item in grn.get("items", []):
            if item.get("accepted_quantity", 0) > 0:
                # Create quant for each accepted GRN item
                quant_id = f"quant_{uuid.uuid4().hex[:12]}"
                
                # Determine stock category based on quality status
                stock_category = "UNRES"  # Default: Unrestricted
                if item.get("quality_inspection_status") == "pending":
                    stock_category = "QINSP"  # Quality Inspection
                
                # Get bin details
                bin_code = item.get("bin_location", "SC-01-01-01")
                bin_doc = await db.bins.find_one({"bin_code": bin_code}, {"_id": 0})
                bin_id = bin_doc["bin_id"] if bin_doc else f"bin_{uuid.uuid4().hex[:8]}"
                storage_type = bin_doc.get("zone", "SC") if bin_doc else "SC"
                
                # Calculate SLED (if expiry date exists)
                sled = item.get("expiry_date")
                
                quant_doc = {
                    "quant_id": quant_id,
                    "material_id": item["material_id"],
                    "material_code": item["material_code"],
                    "bin_id": bin_id,
                    "bin_code": bin_code,
                    "warehouse_number": "W001",
                    "storage_type": storage_type,
                    "quantity": item["accepted_quantity"],
                    "uom": "PCS",  # Default
                    "stock_category": stock_category,
                    "batch_number": item.get("batch_number"),
                    "manufacturing_date": item.get("manufacturing_date"),
                    "shelf_life_expiry_date": sled,
                    "gr_date": grn.get("receipt_date", grn.get("created_at")),
                    "vendor_batch": item.get("batch_number"),
                    "grn_id": grn["grn_id"],
                    "grn_number": grn["grn_number"],
                    "storage_condition": item.get("storage_condition"),
                    "created_at": grn.get("created_at"),
                    "created_by": admin_id
                }
                
                # Check if quant already exists
                existing = await db.quants.find_one({
                    "material_code": item["material_code"],
                    "bin_code": bin_code,
                    "batch_number": item.get("batch_number"),
                    "grn_number": grn["grn_number"]
                })
                
                if not existing:
                    await db.quants.insert_one(quant_doc)
                    quants_created += 1
                    print(f"  ✅ Quant: {item['material_code']} | {item['accepted_quantity']} | {bin_code} | {stock_category}")
    
    print(f"\n✅ Created {quants_created} quants from existing GRNs")
    return quants_created

async def create_additional_test_quants():
    """Create additional test quants with different stock categories"""
    print("\n📦 Creating Additional Test Quants (Various Stock Categories)...")
    print("=" * 70)
    
    admin_user = await db.users.find_one({"email": "admin@warehouse.com"})
    admin_id = admin_user["user_id"]
    
    # Get some materials
    materials = await db.materials.find({}, {"_id": 0}).limit(5).to_list(5)
    bins = await db.bins.find({}, {"_id": 0}).limit(10).to_list(10)
    
    test_quants = []
    
    # Quality Inspection stock
    if len(materials) > 0 and len(bins) > 0:
        quant_id = f"quant_{uuid.uuid4().hex[:12]}"
        test_quants.append({
            "quant_id": quant_id,
            "material_id": materials[0]["material_id"],
            "material_code": materials[0]["material_code"],
            "bin_id": bins[0]["bin_id"],
            "bin_code": bins[0]["bin_code"],
            "warehouse_number": "W001",
            "storage_type": "QC",
            "quantity": 500,
            "uom": materials[0]["uom"],
            "stock_category": "QINSP",
            "batch_number": f"QA-BATCH-{datetime.now().strftime('%Y%m%d')}",
            "gr_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": admin_id
        })
        print(f"  ✅ QINSP: {materials[0]['material_code']} | 500 | QC Zone")
    
    # Blocked stock
    if len(materials) > 1 and len(bins) > 1:
        quant_id = f"quant_{uuid.uuid4().hex[:12]}"
        test_quants.append({
            "quant_id": quant_id,
            "material_id": materials[1]["material_id"],
            "material_code": materials[1]["material_code"],
            "bin_id": bins[1]["bin_id"],
            "bin_code": bins[1]["bin_code"],
            "warehouse_number": "W001",
            "storage_type": "BLOCK",
            "quantity": 200,
            "uom": materials[1]["uom"],
            "stock_category": "BLOCK",
            "batch_number": f"BLOCK-BATCH-{datetime.now().strftime('%Y%m%d')}",
            "is_blocked": True,
            "blocked_reason": "Quality issue - hold for investigation",
            "gr_date": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": admin_id
        })
        print(f"  ✅ BLOCK: {materials[1]['material_code']} | 200 | Blocked")
    
    # Returns stock
    if len(materials) > 2 and len(bins) > 2:
        quant_id = f"quant_{uuid.uuid4().hex[:12]}"
        test_quants.append({
            "quant_id": quant_id,
            "material_id": materials[2]["material_id"],
            "material_code": materials[2]["material_code"],
            "bin_id": bins[2]["bin_id"],
            "bin_code": bins[2]["bin_code"],
            "warehouse_number": "W001",
            "storage_type": "RETRN",
            "quantity": 100,
            "uom": materials[2]["uom"],
            "stock_category": "RETRN",
            "batch_number": f"RETRN-BATCH-{datetime.now().strftime('%Y%m%d')}",
            "gr_date": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": admin_id
        })
        print(f"  ✅ RETRN: {materials[2]['material_code']} | 100 | Returns")
    
    # Expiring soon (SLED tracking)
    if len(materials) > 3 and len(bins) > 3:
        quant_id = f"quant_{uuid.uuid4().hex[:12]}"
        expiry_soon = (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%Y-%m-%d")
        test_quants.append({
            "quant_id": quant_id,
            "material_id": materials[3]["material_id"],
            "material_code": materials[3]["material_code"],
            "bin_id": bins[3]["bin_id"],
            "bin_code": bins[3]["bin_code"],
            "warehouse_number": "W001",
            "storage_type": "SC",
            "quantity": 300,
            "uom": materials[3]["uom"],
            "stock_category": "UNRES",
            "batch_number": f"EXP-BATCH-{datetime.now().strftime('%Y%m%d')}",
            "manufacturing_date": (datetime.now(timezone.utc) - timedelta(days=350)).strftime("%Y-%m-%d"),
            "shelf_life_expiry_date": expiry_soon,
            "gr_date": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": admin_id
        })
        print(f"  ✅ SLED: {materials[3]['material_code']} | 300 | Expires {expiry_soon}")
    
    if test_quants:
        await db.quants.insert_many(test_quants)
        print(f"\n✅ Created {len(test_quants)} additional test quants")
    
    return len(test_quants)

async def create_transfer_requirements_and_orders():
    """Create test Transfer Requirements and Transfer Orders"""
    print("\n📋 Creating Transfer Requirements & Transfer Orders...")
    print("=" * 70)
    
    admin_user = await db.users.find_one({"email": "admin@warehouse.com"})
    admin_id = admin_user["user_id"]
    
    # Get some materials
    materials = await db.materials.find({}, {"_id": 0}).limit(3).to_list(3)
    bins = await db.bins.find({"status": "empty"}, {"_id": 0}).limit(3).to_list(3)
    
    tr_count = 0
    to_count = 0
    
    # Create TR for putaway (GR type)
    if materials and bins:
        print("\n  📦 Creating GR Transfer Requirement...")
        tr_number = f"TR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        
        tr_doc = {
            "tr_number": tr_number,
            "tr_type": "GR",
            "material_id": materials[0]["material_id"],
            "material_code": materials[0]["material_code"],
            "material_name": materials[0]["name"],
            "required_quantity": 1000,
            "open_quantity": 1000,
            "uom": materials[0]["uom"],
            "stock_category": "UNRES",
            "destination_bin": bins[0]["bin_code"] if bins else None,
            "storage_type": "RACK",
            "reference_doc_number": "GRN-TEST-001",
            "priority": 3,
            "status": "OPEN",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": admin_id
        }
        
        await db.transfer_requirements.insert_one(tr_doc)
        print(f"    ✅ TR Created: {tr_number}")
        tr_count += 1
        
        # Create TO from TR
        print(f"  📦 Creating Transfer Order from TR...")
        to_number = f"TO-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        
        to_item = {
            "item_number": 1,
            "material_id": materials[0]["material_id"],
            "material_code": materials[0]["material_code"],
            "material_name": materials[0]["name"],
            "target_quantity": 1000,
            "confirmed_quantity": 0,
            "difference_quantity": 0,
            "uom": materials[0]["uom"],
            "destination_bin_id": bins[0]["bin_id"] if bins else None,
            "destination_bin_code": bins[0]["bin_code"] if bins else None,
            "stock_category": "UNRES",
            "item_status": "OPEN"
        }
        
        to_doc = {
            "to_number": to_number,
            "to_type": "PUTAWAY",
            "warehouse_number": "W001",
            "storage_type": "RACK",
            "items": [to_item],
            "tr_number": tr_number,
            "reference_doc_number": "GRN-TEST-001",
            "priority": 3,
            "status": "OPEN",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": admin_id
        }
        
        await db.transfer_orders.insert_one(to_doc)
        print(f"    ✅ TO Created: {to_number}")
        to_count += 1
    
    # Create TR for picking (GI type)
    if len(materials) > 1:
        print("\n  📦 Creating GI Transfer Requirement...")
        tr_number = f"TR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        
        tr_doc = {
            "tr_number": tr_number,
            "tr_type": "GI",
            "material_id": materials[1]["material_id"],
            "material_code": materials[1]["material_code"],
            "material_name": materials[1]["name"],
            "required_quantity": 500,
            "open_quantity": 500,
            "uom": materials[1]["uom"],
            "stock_category": "UNRES",
            "storage_type": "PICK",
            "reference_doc_number": "DELIVERY-TEST-001",
            "priority": 2,
            "status": "OPEN",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": admin_id
        }
        
        await db.transfer_requirements.insert_one(tr_doc)
        print(f"    ✅ TR Created: {tr_number}")
        tr_count += 1
    
    print(f"\n✅ Created {tr_count} Transfer Requirements and {to_count} Transfer Orders")
    return tr_count, to_count

async def create_physical_inventory_test():
    """Create test Physical Inventory document"""
    print("\n📊 Creating Physical Inventory Test Data...")
    print("=" * 70)
    
    admin_user = await db.users.find_one({"email": "admin@warehouse.com"})
    admin_id = admin_user["user_id"]
    
    # Get some bins for cycle count
    bins = await db.bins.find({"status": {"$ne": "empty"}}, {"_id": 0}).limit(5).to_list(5)
    bin_codes = [b["bin_code"] for b in bins]
    
    if not bin_codes:
        print("  ⚠️ No occupied bins found for inventory")
        return 0
    
    print(f"\n  📦 Creating Cycle Count for {len(bin_codes)} bins...")
    
    doc_number = f"PI-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
    
    pi_doc = {
        "inventory_doc_number": doc_number,
        "inventory_type": "CYCLE_COUNT",
        "warehouse_number": "W001",
        "storage_type": "SC",
        "bin_codes": bin_codes,
        "material_codes": [],
        "status": "CREATED",
        "is_stock_frozen": False,
        "total_items_counted": 0,
        "items_with_differences": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": admin_id
    }
    
    await db.physical_inventory.insert_one(pi_doc)
    print(f"    ✅ Physical Inventory Created: {doc_number}")
    
    # Create count items
    quants = await db.quants.find({"bin_code": {"$in": bin_codes}}, {"_id": 0}).to_list(100)
    
    count_items = []
    for quant in quants:
        count_item = {
            "count_item_id": f"ci_{uuid.uuid4().hex[:12]}",
            "inventory_doc_number": doc_number,
            "bin_id": quant["bin_id"],
            "bin_code": quant["bin_code"],
            "quant_id": quant["quant_id"],
            "material_id": quant["material_id"],
            "material_code": quant["material_code"],
            "batch_number": quant.get("batch_number"),
            "book_quantity": quant["quantity"],
            "count_status": "PENDING"
        }
        count_items.append(count_item)
    
    if count_items:
        await db.inventory_count_items.insert_many(count_items)
        print(f"    ✅ Count Items Generated: {len(count_items)}")
    
    # Freeze the inventory
    await db.physical_inventory.update_one(
        {"inventory_doc_number": doc_number},
        {
            "$set": {
                "status": "FROZEN",
                "is_stock_frozen": True,
                "planned_count_date": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    print(f"    ✅ Inventory Frozen for Counting")
    
    return 1

async def generate_comprehensive_summary():
    """Generate comprehensive summary of all WM data"""
    print("\n" + "=" * 70)
    print("📊 SAP WM PHASE 1 - DATA SUMMARY")
    print("=" * 70)
    
    # Quants summary
    total_quants = await db.quants.count_documents({})
    quants_by_category = {}
    for cat in ["UNRES", "QINSP", "BLOCK", "RETRN"]:
        count = await db.quants.count_documents({"stock_category": cat})
        quants_by_category[cat] = count
    
    print(f"\n🔢 QUANTS (Bin-Level Stock Tracking):")
    print(f"   Total Quants: {total_quants}")
    print(f"   └─ Unrestricted (UNRES): {quants_by_category.get('UNRES', 0)}")
    print(f"   └─ Quality Inspection (QINSP): {quants_by_category.get('QINSP', 0)}")
    print(f"   └─ Blocked (BLOCK): {quants_by_category.get('BLOCK', 0)}")
    print(f"   └─ Returns (RETRN): {quants_by_category.get('RETRN', 0)}")
    
    # SLED tracking
    expired_quants = await db.quants.count_documents({
        "shelf_life_expiry_date": {"$lt": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "$ne": None}
    })
    expiring_soon = await db.quants.count_documents({
        "shelf_life_expiry_date": {
            "$gte": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "$lte": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
        }
    })
    print(f"\n📅 SHELF LIFE (SLED) Tracking:")
    print(f"   Expired: {expired_quants}")
    print(f"   Expiring in 30 days: {expiring_soon}")
    
    # Transfer Requirements
    tr_total = await db.transfer_requirements.count_documents({})
    tr_open = await db.transfer_requirements.count_documents({"status": "OPEN"})
    print(f"\n📋 TRANSFER REQUIREMENTS (TR):")
    print(f"   Total: {tr_total}")
    print(f"   Open: {tr_open}")
    
    # Transfer Orders
    to_total = await db.transfer_orders.count_documents({})
    to_open = await db.transfer_orders.count_documents({"status": "OPEN"})
    print(f"\n📦 TRANSFER ORDERS (TO):")
    print(f"   Total: {to_total}")
    print(f"   Open: {to_open}")
    
    # Physical Inventory
    pi_total = await db.physical_inventory.count_documents({})
    print(f"\n📊 PHYSICAL INVENTORY:")
    print(f"   Documents: {pi_total}")
    
    # Materials with stock
    materials_in_stock = await db.materials.count_documents({"current_stock": {"$gt": 0}})
    print(f"\n📦 MATERIALS:")
    print(f"   Materials in Stock: {materials_in_stock}")
    
    print("\n" + "=" * 70)
    print("✅ PHASE 1 SAP WM FEATURES - READY FOR TESTING!")
    print("=" * 70)
    
    print("\n🎯 Available Features:")
    print("   ✅ Quant-level stock tracking (material, qty, SLED, stock category, GR date)")
    print("   ✅ Stock categories (UNRES, QINSP, BLOCK, RETRN)")
    print("   ✅ SLED/expiry date tracking")
    print("   ✅ Transfer Requirements (TR) - planning layer")
    print("   ✅ Transfer Orders (TO) - execution documents")
    print("   ✅ Put-away strategies (next_empty, open_storage)")
    print("   ✅ Picking strategies (FIFO, LIFO)")
    print("   ✅ Physical Inventory (cycle count)")
    
    print("\n🌐 API Endpoints Available:")
    print("   📍 GET  /api/wm/quants")
    print("   📍 GET  /api/wm/quants/bin/{bin_code}")
    print("   📍 POST /api/wm/quants/stock-category/change")
    print("   📍 POST /api/wm/transfer-requirements")
    print("   📍 GET  /api/wm/transfer-requirements")
    print("   📍 POST /api/wm/transfer-orders/from-tr/{tr_number}")
    print("   📍 GET  /api/wm/transfer-orders")
    print("   📍 PUT  /api/wm/transfer-orders/{to_number}/confirm")
    print("   📍 POST /api/wm/physical-inventory")
    print("   📍 GET  /api/wm/config/stock-categories")
    print("   📍 GET  /api/wm/config/storage-types")
    
    print("\n🔐 Login: admin@warehouse.com / admin123")
    print("🌐 URL: https://emergent-extend.preview.emergentagent.com")
    print("\n" + "=" * 70)

async def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("☀️ SAP WM PHASE 1 - TEST DATA GENERATION")
    print("   Solar Manufacturing WMS Enhancement")
    print("=" * 70)
    
    # Step 1: Migrate existing stock to quants
    quants_migrated = await migrate_existing_stock_to_quants()
    
    # Step 2: Create additional test quants
    additional_quants = await create_additional_test_quants()
    
    # Step 3: Create TRs and TOs
    tr_count, to_count = await create_transfer_requirements_and_orders()
    
    # Step 4: Create Physical Inventory
    pi_count = await create_physical_inventory_test()
    
    # Step 5: Summary
    await generate_comprehensive_summary()

if __name__ == "__main__":
    asyncio.run(main())
