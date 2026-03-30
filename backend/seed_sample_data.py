"""
Seed script to create comprehensive sample data for WMS Pro testing
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os
import uuid
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def seed_sample_data():
    """Create comprehensive sample data for testing"""
    
    print("🌱 Starting sample data seeding...")
    
    # Get admin user
    admin_user = await db.users.find_one({"email": "admin@warehouse.com"})
    if not admin_user:
        print("❌ Admin user not found. Please run seed_users.py first.")
        return
    
    admin_id = admin_user["user_id"]
    now = datetime.now(timezone.utc).isoformat()
    
    # ========== MATERIALS ==========
    print("\n📦 Creating sample materials...")
    
    materials_data = [
        # Electronics
        {"code": "ELEC-001", "name": "LED Display 15.6\"", "category": "Electronics", "uom": "PCS", "stock_method": "FIFO", "min": 10, "max": 100, "reorder": 20},
        {"code": "ELEC-002", "name": "Laptop Battery Li-ion", "category": "Electronics", "uom": "PCS", "stock_method": "FIFO", "min": 20, "max": 200, "reorder": 50},
        {"code": "ELEC-003", "name": "USB Type-C Cable", "category": "Electronics", "uom": "PCS", "stock_method": "LIFO", "min": 50, "max": 500, "reorder": 100},
        {"code": "ELEC-004", "name": "Wireless Mouse", "category": "Electronics", "uom": "PCS", "stock_method": "FIFO", "min": 30, "max": 300, "reorder": 60},
        
        # Raw Materials
        {"code": "RAW-001", "name": "Aluminum Sheet 2mm", "category": "Raw Materials", "uom": "KG", "stock_method": "FIFO", "min": 100, "max": 1000, "reorder": 200},
        {"code": "RAW-002", "name": "Steel Coil Grade A", "category": "Raw Materials", "uom": "TON", "stock_method": "FIFO", "min": 5, "max": 50, "reorder": 10},
        {"code": "RAW-003", "name": "Plastic Pellets HDPE", "category": "Raw Materials", "uom": "KG", "stock_method": "LIFO", "min": 200, "max": 2000, "reorder": 400},
        
        # Packaging
        {"code": "PKG-001", "name": "Corrugated Box Medium", "category": "Packaging", "uom": "PCS", "stock_method": "LIFO", "min": 100, "max": 1000, "reorder": 200},
        {"code": "PKG-002", "name": "Bubble Wrap Roll", "category": "Packaging", "uom": "ROLL", "stock_method": "FIFO", "min": 20, "max": 200, "reorder": 50},
        {"code": "PKG-003", "name": "Packing Tape 48mm", "category": "Packaging", "uom": "ROLL", "stock_method": "LIFO", "min": 50, "max": 500, "reorder": 100},
        
        # Components
        {"code": "COMP-001", "name": "PCB Board 10x10cm", "category": "Components", "uom": "PCS", "stock_method": "FIFO", "min": 50, "max": 500, "reorder": 100},
        {"code": "COMP-002", "name": "Resistor 10K Ohm", "category": "Components", "uom": "PCS", "stock_method": "LIFO", "min": 500, "max": 5000, "reorder": 1000},
        {"code": "COMP-003", "name": "Capacitor 100uF", "category": "Components", "uom": "PCS", "stock_method": "FIFO", "min": 300, "max": 3000, "reorder": 600},
    ]
    
    material_ids = {}
    for mat in materials_data:
        existing = await db.materials.find_one({"material_code": mat["code"]})
        if not existing:
            material_id = f"mat_{uuid.uuid4().hex[:12]}"
            material_doc = {
                "material_id": material_id,
                "material_code": mat["code"],
                "name": mat["name"],
                "description": f"Sample {mat['name']} for testing",
                "category": mat["category"],
                "uom": mat["uom"],
                "stock_method": mat["stock_method"],
                "min_stock_level": mat["min"],
                "max_stock_level": mat["max"],
                "reorder_point": mat["reorder"],
                "current_stock": 0,
                "created_at": now,
                "updated_at": now,
                "created_by": admin_id
            }
            await db.materials.insert_one(material_doc)
            material_ids[mat["code"]] = material_id
            print(f"  ✅ Created material: {mat['code']} - {mat['name']}")
        else:
            material_ids[mat["code"]] = existing["material_id"]
            print(f"  ⏭️  Material exists: {mat['code']}")
    
    # ========== BIN LOCATIONS ==========
    print("\n📍 Creating bin locations...")
    
    bins_data = [
        # Zone A - Storage
        {"code": "A-01-01-01", "zone": "A", "aisle": "01", "rack": "01", "level": "01", "capacity": 100, "type": "storage"},
        {"code": "A-01-01-02", "zone": "A", "aisle": "01", "rack": "01", "level": "02", "capacity": 100, "type": "storage"},
        {"code": "A-01-02-01", "zone": "A", "aisle": "01", "rack": "02", "level": "01", "capacity": 150, "type": "storage"},
        {"code": "A-02-01-01", "zone": "A", "aisle": "02", "rack": "01", "level": "01", "capacity": 120, "type": "storage"},
        
        # Zone B - Picking
        {"code": "B-01-01-01", "zone": "B", "aisle": "01", "rack": "01", "level": "01", "capacity": 80, "type": "picking"},
        {"code": "B-01-02-01", "zone": "B", "aisle": "01", "rack": "02", "level": "01", "capacity": 80, "type": "picking"},
        {"code": "B-02-01-01", "zone": "B", "aisle": "02", "rack": "01", "level": "01", "capacity": 80, "type": "picking"},
        
        # Zone C - Staging
        {"code": "C-01-01-01", "zone": "C", "aisle": "01", "rack": "01", "level": "01", "capacity": 200, "type": "staging"},
        {"code": "C-01-02-01", "zone": "C", "aisle": "01", "rack": "02", "level": "01", "capacity": 200, "type": "staging"},
        
        # Zone Q - Quarantine
        {"code": "Q-01-01-01", "zone": "Q", "aisle": "01", "rack": "01", "level": "01", "capacity": 100, "type": "quarantine"},
    ]
    
    bin_ids = {}
    for bin_data in bins_data:
        existing = await db.bins.find_one({"bin_code": bin_data["code"]})
        if not existing:
            bin_id = f"bin_{uuid.uuid4().hex[:12]}"
            bin_doc = {
                "bin_id": bin_id,
                "bin_code": bin_data["code"],
                "zone": bin_data["zone"],
                "aisle": bin_data["aisle"],
                "rack": bin_data["rack"],
                "level": bin_data["level"],
                "capacity": bin_data["capacity"],
                "bin_type": bin_data["type"],
                "current_stock": 0,
                "status": "empty",
                "material_id": None,
                "material_code": None,
                "created_at": now,
                "updated_at": now
            }
            await db.bins.insert_one(bin_doc)
            bin_ids[bin_data["code"]] = bin_id
            print(f"  ✅ Created bin: {bin_data['code']} ({bin_data['type']})")
        else:
            bin_ids[bin_data["code"]] = existing["bin_id"]
            print(f"  ⏭️  Bin exists: {bin_data['code']}")
    
    print("\n✅ Sample data seeding completed!")
    print(f"\n📊 Summary:")
    print(f"   - Materials created: {len(material_ids)}")
    print(f"   - Bin locations created: {len(bin_ids)}")
    print(f"\n🎯 Ready for testing:")
    print(f"   1. Create GRN with sample materials")
    print(f"   2. Test quality inspection")
    print(f"   3. Complete GRN and verify stock")
    print(f"   4. Test putaway to bins")
    print(f"   5. Test material issues")
    print(f"   6. View reports and analytics")

if __name__ == "__main__":
    asyncio.run(seed_sample_data())
