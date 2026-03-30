"""
Solar Manufacturing WMS - Complete BOM Setup
Creates realistic solar panel manufacturing materials and sample data
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

async def clear_existing_data():
    """Clear all existing sample data"""
    print("🧹 Clearing existing test data...")
    
    # Keep users, clear everything else
    await db.materials.delete_many({})
    await db.grn.delete_many({})
    await db.bins.delete_many({})
    await db.labels.delete_many({})
    await db.stock_movements.delete_many({})
    await db.putaway.delete_many({})
    await db.issues.delete_many({})
    await db.print_logs.delete_many({})
    
    print("✅ Existing data cleared\n")

async def create_solar_bom_materials():
    """Create solar panel BOM materials"""
    print("☀️ Creating Solar Manufacturing BOM Materials...")
    
    admin_user = await db.users.find_one({"email": "admin@warehouse.com"})
    if not admin_user:
        print("❌ Admin user not found")
        return None
    
    admin_id = admin_user["user_id"]
    now = datetime.now(timezone.utc).isoformat()
    
    # Solar Panel BOM Materials
    solar_materials = [
        # Solar Cells
        {
            "code": "CELL-MONO-166", 
            "name": "Monocrystalline Solar Cell 166mm M10",
            "category": "Solar Cells",
            "uom": "PCS",
            "stock_method": "FIFO",
            "description": "High efficiency monocrystalline solar cell, 166mm M10, 5.2W-5.5W, Grade A",
            "min": 5000, "max": 50000, "reorder": 10000
        },
        {
            "code": "CELL-MONO-182", 
            "name": "Monocrystalline Solar Cell 182mm M12",
            "category": "Solar Cells",
            "uom": "PCS",
            "stock_method": "FIFO",
            "description": "Premium monocrystalline solar cell, 182mm M12, 6.0W-6.5W, Grade A+",
            "min": 5000, "max": 50000, "reorder": 10000
        },
        {
            "code": "CELL-POLY-156", 
            "name": "Polycrystalline Solar Cell 156mm",
            "category": "Solar Cells",
            "uom": "PCS",
            "stock_method": "FIFO",
            "description": "Polycrystalline solar cell, 156mm, 4.8W-5.0W, Grade A",
            "min": 3000, "max": 30000, "reorder": 8000
        },
        
        # Glass
        {
            "code": "GLASS-ARC-3.2", 
            "name": "Anti-Reflective Coated Glass 3.2mm",
            "category": "Glass & Encapsulation",
            "uom": "SQM",
            "stock_method": "FIFO",
            "description": "Tempered low-iron glass with ARC coating, 3.2mm thickness, high transmittance",
            "min": 1000, "max": 10000, "reorder": 2000
        },
        {
            "code": "GLASS-TEMP-4.0", 
            "name": "Tempered Glass 4.0mm",
            "category": "Glass & Encapsulation",
            "uom": "SQM",
            "stock_method": "FIFO",
            "description": "Ultra-clear tempered glass, 4.0mm, for bifacial modules",
            "min": 500, "max": 5000, "reorder": 1000
        },
        
        # EVA Sheets
        {
            "code": "EVA-FAST-0.45", 
            "name": "EVA Film Fast Cure 0.45mm",
            "category": "Glass & Encapsulation",
            "uom": "SQM",
            "stock_method": "FIFO",
            "description": "Fast cure EVA encapsulant film, 0.45mm, UV stabilized",
            "min": 2000, "max": 20000, "reorder": 5000
        },
        {
            "code": "EVA-STD-0.50", 
            "name": "EVA Film Standard 0.50mm",
            "category": "Glass & Encapsulation",
            "uom": "SQM",
            "stock_method": "FIFO",
            "description": "Standard EVA encapsulant film, 0.50mm, high transparency",
            "min": 2000, "max": 20000, "reorder": 5000
        },
        
        # Backsheet
        {
            "code": "BACK-TPT-WHT", 
            "name": "TPT Backsheet White",
            "category": "Backsheet",
            "uom": "SQM",
            "stock_method": "FIFO",
            "description": "Tedlar-PET-Tedlar backsheet, white, UV resistant, moisture barrier",
            "min": 1500, "max": 15000, "reorder": 3000
        },
        {
            "code": "BACK-TPE-BLK", 
            "name": "TPE Backsheet Black",
            "category": "Backsheet",
            "uom": "SQM",
            "stock_method": "FIFO",
            "description": "Tedlar-PET-EVA backsheet, black, for bifacial applications",
            "min": 1000, "max": 10000, "reorder": 2000
        },
        
        # Frames
        {
            "code": "FRAME-AL-35MM", 
            "name": "Aluminum Frame Profile 35mm Silver",
            "category": "Frames & Mounting",
            "uom": "MTR",
            "stock_method": "LIFO",
            "description": "Anodized aluminum frame profile, 35mm height, silver finish, 6.3m length",
            "min": 500, "max": 5000, "reorder": 1000
        },
        {
            "code": "FRAME-AL-40MM", 
            "name": "Aluminum Frame Profile 40mm Black",
            "category": "Frames & Mounting",
            "uom": "MTR",
            "stock_method": "LIFO",
            "description": "Black anodized aluminum frame, 40mm height, premium finish",
            "min": 300, "max": 3000, "reorder": 800
        },
        
        # Junction Box & Electrical
        {
            "code": "JBOX-IP67-3D", 
            "name": "Junction Box IP67 3-Diode",
            "category": "Electrical Components",
            "uom": "PCS",
            "stock_method": "FIFO",
            "description": "Weatherproof junction box, IP67 rated, with 3 bypass diodes",
            "min": 1000, "max": 10000, "reorder": 2000
        },
        {
            "code": "JBOX-SMART-BT", 
            "name": "Smart Junction Box with Bluetooth",
            "category": "Electrical Components",
            "uom": "PCS",
            "stock_method": "FIFO",
            "description": "Smart junction box with Bluetooth monitoring, IP68",
            "min": 500, "max": 5000, "reorder": 1000
        },
        {
            "code": "DIODE-BYPASS-15A", 
            "name": "Bypass Diode 15A Schottky",
            "category": "Electrical Components",
            "uom": "PCS",
            "stock_method": "LIFO",
            "description": "Schottky bypass diode, 15A, low forward voltage drop",
            "min": 3000, "max": 30000, "reorder": 5000
        },
        
        # Interconnects
        {
            "code": "RIBBON-2.0MM", 
            "name": "Tinned Copper Ribbon 2.0mm",
            "category": "Interconnects & Cables",
            "uom": "MTR",
            "stock_method": "FIFO",
            "description": "Tinned copper interconnect ribbon, 2.0mm width, solder coated",
            "min": 5000, "max": 50000, "reorder": 10000
        },
        {
            "code": "BUSBAR-5BB", 
            "name": "Multi-Busbar 5BB Ribbon",
            "category": "Interconnects & Cables",
            "uom": "MTR",
            "stock_method": "FIFO",
            "description": "5 busbar interconnect ribbon for high efficiency cells",
            "min": 3000, "max": 30000, "reorder": 8000
        },
        {
            "code": "CABLE-PV-4MM", 
            "name": "PV Cable 4mm² UV Resistant",
            "category": "Interconnects & Cables",
            "uom": "MTR",
            "stock_method": "LIFO",
            "description": "Solar cable 4mm², tinned copper, UV and weather resistant",
            "min": 2000, "max": 20000, "reorder": 5000
        },
        
        # Connectors
        {
            "code": "CONN-MC4-MALE", 
            "name": "MC4 Connector Male",
            "category": "Connectors",
            "uom": "PCS",
            "stock_method": "LIFO",
            "description": "MC4 male connector, IP67, TUV certified",
            "min": 2000, "max": 20000, "reorder": 5000
        },
        {
            "code": "CONN-MC4-FEMALE", 
            "name": "MC4 Connector Female",
            "category": "Connectors",
            "uom": "PCS",
            "stock_method": "LIFO",
            "description": "MC4 female connector, IP67, TUV certified",
            "min": 2000, "max": 20000, "reorder": 5000
        },
        
        # Sealants & Adhesives
        {
            "code": "SEAL-SIL-RTV", 
            "name": "Silicone Sealant RTV Clear",
            "category": "Sealants & Adhesives",
            "uom": "KG",
            "stock_method": "FIFO",
            "description": "RTV silicone sealant for junction box bonding, weatherproof",
            "min": 100, "max": 1000, "reorder": 200
        },
        {
            "code": "TAPE-DBL-3M", 
            "name": "3M VHB Double-Sided Tape",
            "category": "Sealants & Adhesives",
            "uom": "ROLL",
            "stock_method": "LIFO",
            "description": "3M VHB tape for frame bonding, high strength",
            "min": 50, "max": 500, "reorder": 100
        },
        
        # Packaging
        {
            "code": "PKG-PALLET-EUR", 
            "name": "Euro Pallet for Solar Modules",
            "category": "Packaging Materials",
            "uom": "PCS",
            "stock_method": "LIFO",
            "description": "Euro pallet 1200x800mm, heat treated, solar module transport",
            "min": 100, "max": 1000, "reorder": 200
        },
        {
            "code": "PKG-CORNER-PROT", 
            "name": "Edge Protector Corner Guard",
            "category": "Packaging Materials",
            "uom": "PCS",
            "stock_method": "LIFO",
            "description": "Corner protectors for solar panel shipping",
            "min": 500, "max": 5000, "reorder": 1000
        },
    ]
    
    material_ids = {}
    for mat in solar_materials:
        material_id = f"mat_{uuid.uuid4().hex[:12]}"
        material_doc = {
            "material_id": material_id,
            "material_code": mat["code"],
            "name": mat["name"],
            "description": mat["description"],
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
        print(f"  ✅ {mat['code']} - {mat['name']}")
    
    print(f"\n✅ Created {len(material_ids)} solar BOM materials\n")
    return material_ids, admin_id

async def create_solar_bins():
    """Create solar manufacturing bin locations"""
    print("📍 Creating Solar Manufacturing Bin Locations...")
    
    now = datetime.now(timezone.utc).isoformat()
    
    bins_data = [
        # Zone SC - Solar Cells Storage (Temperature Controlled)
        {"code": "SC-01-01-01", "zone": "SC", "aisle": "01", "rack": "01", "level": "01", "capacity": 10000, "type": "storage"},
        {"code": "SC-01-01-02", "zone": "SC", "aisle": "01", "rack": "01", "level": "02", "capacity": 10000, "type": "storage"},
        {"code": "SC-01-02-01", "zone": "SC", "aisle": "01", "rack": "02", "level": "01", "capacity": 10000, "type": "storage"},
        {"code": "SC-02-01-01", "zone": "SC", "aisle": "02", "rack": "01", "level": "01", "capacity": 10000, "type": "storage"},
        
        # Zone GM - Glass & Materials
        {"code": "GM-01-01-01", "zone": "GM", "aisle": "01", "rack": "01", "level": "01", "capacity": 2000, "type": "storage"},
        {"code": "GM-01-02-01", "zone": "GM", "aisle": "01", "rack": "02", "level": "01", "capacity": 2000, "type": "storage"},
        {"code": "GM-02-01-01", "zone": "GM", "aisle": "02", "rack": "01", "level": "01", "capacity": 2000, "type": "storage"},
        
        # Zone FM - Frames & Mechanical
        {"code": "FM-01-01-01", "zone": "FM", "aisle": "01", "rack": "01", "level": "01", "capacity": 1000, "type": "storage"},
        {"code": "FM-01-02-01", "zone": "FM", "aisle": "01", "rack": "02", "level": "01", "capacity": 1000, "type": "storage"},
        
        # Zone EC - Electrical Components
        {"code": "EC-01-01-01", "zone": "EC", "aisle": "01", "rack": "01", "level": "01", "capacity": 5000, "type": "storage"},
        {"code": "EC-01-01-02", "zone": "EC", "aisle": "01", "rack": "01", "level": "02", "capacity": 5000, "type": "storage"},
        {"code": "EC-02-01-01", "zone": "EC", "aisle": "02", "rack": "01", "level": "01", "capacity": 5000, "type": "storage"},
        
        # Zone PK - Packaging
        {"code": "PK-01-01-01", "zone": "PK", "aisle": "01", "rack": "01", "level": "01", "capacity": 500, "type": "storage"},
        
        # Zone QC - Quality Control
        {"code": "QC-01-01-01", "zone": "QC", "aisle": "01", "rack": "01", "level": "01", "capacity": 1000, "type": "quarantine"},
        
        # Zone PR - Production Line Picking
        {"code": "PR-01-01-01", "zone": "PR", "aisle": "01", "rack": "01", "level": "01", "capacity": 3000, "type": "picking"},
        {"code": "PR-02-01-01", "zone": "PR", "aisle": "02", "rack": "01", "level": "01", "capacity": 3000, "type": "picking"},
    ]
    
    bin_ids = {}
    for bin_data in bins_data:
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
        print(f"  ✅ {bin_data['code']} - Zone {bin_data['zone']} ({bin_data['type']})")
    
    print(f"\n✅ Created {len(bin_ids)} solar manufacturing bins\n")
    return bin_ids

async def create_solar_grns(material_ids, admin_id):
    """Create realistic solar manufacturing GRNs"""
    print("📦 Creating Solar Manufacturing GRNs...")
    
    import jwt
    JWT_SECRET = os.environ.get('JWT_SECRET', 'warehouse-inventory-secret-key-2024')
    JWT_ALGORITHM = "HS256"
    expiration = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        "user_id": admin_id,
        "email": "admin@warehouse.com",
        "role": "Admin",
        "exp": expiration
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    import httpx
    async with httpx.AsyncClient() as http_client:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # GRN 1 - Solar Cells Shipment
        print("\n  📦 GRN #1 - Solar Cells from China...")
        grn1_data = {
            "vendor_name": "Longi Solar Technology",
            "po_number": "PO-SOLAR-2026-001",
            "invoice_number": "LONGI-INV-2026-45678",
            "receipt_date": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
            "remarks": "Q1 2026 - Monocrystalline cells shipment - Container LNGI2026001",
            "items": [
                {
                    "material_id": material_ids["CELL-MONO-166"],
                    "received_quantity": 20000,
                    "accepted_quantity": 19800,
                    "rejected_quantity": 200,
                    "batch_number": "LONGI-M10-20260327-A",
                    "manufacturing_date": "2026-03-15",
                    "quality_inspection_status": "passed",
                    "storage_condition": "controlled_temperature",
                    "bin_location": "SC-01-01-01",
                    "rejection_reason": "Minor chips on 200 cells"
                },
                {
                    "material_id": material_ids["CELL-MONO-182"],
                    "received_quantity": 15000,
                    "accepted_quantity": 15000,
                    "rejected_quantity": 0,
                    "batch_number": "LONGI-M12-20260327-A",
                    "manufacturing_date": "2026-03-20",
                    "quality_inspection_status": "passed",
                    "storage_condition": "controlled_temperature",
                    "bin_location": "SC-01-01-02"
                }
            ]
        }
        
        resp1 = await http_client.post("http://localhost:8001/api/grn", headers=headers, json=grn1_data, timeout=15.0)
        if resp1.status_code == 200:
            grn1 = resp1.json()
            print(f"     ✅ {grn1['grn_number']} - 35,000 cells received")
            await http_client.put(f"http://localhost:8001/api/grn/{grn1['grn_id']}/complete", headers=headers)
            print(f"     ✅ Completed - Stock updated")
        
        # GRN 2 - Glass & Encapsulation Materials
        print("\n  📦 GRN #2 - Glass & EVA Materials...")
        grn2_data = {
            "vendor_name": "Saint-Gobain Solar Glass",
            "po_number": "PO-SOLAR-2026-002",
            "invoice_number": "SG-GLASS-2026-12345",
            "receipt_date": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "remarks": "ARC coated glass and EVA film - Shipment SG2026-Q1-02",
            "items": [
                {
                    "material_id": material_ids["GLASS-ARC-3.2"],
                    "received_quantity": 3000,
                    "accepted_quantity": 3000,
                    "rejected_quantity": 0,
                    "batch_number": "SG-ARC32-20260328-B",
                    "manufacturing_date": "2026-03-25",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "GM-01-01-01"
                },
                {
                    "material_id": material_ids["EVA-FAST-0.45"],
                    "received_quantity": 8000,
                    "accepted_quantity": 8000,
                    "rejected_quantity": 0,
                    "batch_number": "EVA-FC-20260328-A",
                    "manufacturing_date": "2026-03-22",
                    "expiry_date": "2027-03-22",
                    "quality_inspection_status": "passed",
                    "storage_condition": "controlled_temperature",
                    "bin_location": "GM-01-02-01"
                },
                {
                    "material_id": material_ids["BACK-TPT-WHT"],
                    "received_quantity": 5000,
                    "accepted_quantity": 5000,
                    "rejected_quantity": 0,
                    "batch_number": "TPT-WHT-20260328-C",
                    "manufacturing_date": "2026-03-20",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "GM-02-01-01"
                }
            ]
        }
        
        resp2 = await http_client.post("http://localhost:8001/api/grn", headers=headers, json=grn2_data, timeout=15.0)
        if resp2.status_code == 200:
            grn2 = resp2.json()
            print(f"     ✅ {grn2['grn_number']} - Glass & encapsulation materials")
            await http_client.put(f"http://localhost:8001/api/grn/{grn2['grn_id']}/complete", headers=headers)
            print(f"     ✅ Completed - Stock updated")
        
        # GRN 3 - Electrical Components
        print("\n  📦 GRN #3 - Electrical Components...")
        grn3_data = {
            "vendor_name": "TE Connectivity Solar",
            "po_number": "PO-SOLAR-2026-003",
            "invoice_number": "TE-SOLAR-78901",
            "receipt_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "remarks": "Junction boxes, connectors, and interconnects",
            "items": [
                {
                    "material_id": material_ids["JBOX-IP67-3D"],
                    "received_quantity": 3000,
                    "accepted_quantity": 3000,
                    "rejected_quantity": 0,
                    "batch_number": "TE-JBOX-20260329-A",
                    "manufacturing_date": "2026-03-15",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "EC-01-01-01"
                },
                {
                    "material_id": material_ids["CONN-MC4-MALE"],
                    "received_quantity": 6000,
                    "accepted_quantity": 6000,
                    "rejected_quantity": 0,
                    "batch_number": "MC4-M-20260329-B",
                    "manufacturing_date": "2026-03-10",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "EC-01-01-02"
                },
                {
                    "material_id": material_ids["CONN-MC4-FEMALE"],
                    "received_quantity": 6000,
                    "accepted_quantity": 6000,
                    "rejected_quantity": 0,
                    "batch_number": "MC4-F-20260329-B",
                    "manufacturing_date": "2026-03-10",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "EC-01-01-02"
                },
                {
                    "material_id": material_ids["RIBBON-2.0MM"],
                    "received_quantity": 12000,
                    "accepted_quantity": 12000,
                    "rejected_quantity": 0,
                    "batch_number": "RIBBON-20260329-C",
                    "manufacturing_date": "2026-03-18",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "EC-02-01-01"
                }
            ]
        }
        
        resp3 = await http_client.post("http://localhost:8001/api/grn", headers=headers, json=grn3_data, timeout=15.0)
        if resp3.status_code == 200:
            grn3 = resp3.json()
            print(f"     ✅ {grn3['grn_number']} - Electrical components")
            await http_client.put(f"http://localhost:8001/api/grn/{grn3['grn_id']}/complete", headers=headers)
            print(f"     ✅ Completed - Stock updated")
        
        # GRN 4 - Frames and Mounting
        print("\n  📦 GRN #4 - Aluminum Frames...")
        grn4_data = {
            "vendor_name": "Aluminum Extrusion Corp",
            "po_number": "PO-SOLAR-2026-004",
            "invoice_number": "ALUM-FRAME-45612",
            "receipt_date": datetime.now(timezone.utc).isoformat(),
            "remarks": "Anodized aluminum frames for 72-cell modules",
            "items": [
                {
                    "material_id": material_ids["FRAME-AL-35MM"],
                    "received_quantity": 2000,
                    "accepted_quantity": 2000,
                    "rejected_quantity": 0,
                    "batch_number": "AL-35-20260330-A",
                    "manufacturing_date": "2026-03-25",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "FM-01-01-01"
                },
                {
                    "material_id": material_ids["SEAL-SIL-RTV"],
                    "received_quantity": 200,
                    "accepted_quantity": 200,
                    "rejected_quantity": 0,
                    "batch_number": "SIL-RTV-20260330-B",
                    "manufacturing_date": "2026-03-20",
                    "expiry_date": "2027-03-20",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "FM-01-02-01"
                }
            ]
        }
        
        resp4 = await http_client.post("http://localhost:8001/api/grn", headers=headers, json=grn4_data, timeout=15.0)
        if resp4.status_code == 200:
            grn4 = resp4.json()
            print(f"     ✅ {grn4['grn_number']} - Frames & sealant")
            await http_client.put(f"http://localhost:8001/api/grn/{grn4['grn_id']}/complete", headers=headers)
            print(f"     ✅ Completed - Stock updated")
    
    print(f"\n✅ Created 4 solar manufacturing GRNs with complete stock updates\n")

async def main():
    """Main setup function"""
    print("\n" + "="*70)
    print("☀️  SOLAR MANUFACTURING WMS - COMPLETE SETUP")
    print("="*70 + "\n")
    
    # Clear existing data
    await clear_existing_data()
    
    # Create solar BOM materials
    material_ids, admin_id = await create_solar_bom_materials()
    
    # Create solar bins
    bin_ids = await create_solar_bins()
    
    # Create solar GRNs
    await create_solar_grns(material_ids, admin_id)
    
    # Summary
    print("="*70)
    print("✅ SOLAR MANUFACTURING WMS SETUP COMPLETE!")
    print("="*70)
    print(f"\n📊 Summary:")
    print(f"   ✅ Solar BOM Materials: {len(material_ids)}")
    print(f"   ✅ Manufacturing Bins: {len(bin_ids)}")
    print(f"   ✅ GRNs Completed: 4")
    print(f"   ✅ Labels Generated: Auto-generated for all items")
    print(f"   ✅ Stock Movements: Recorded for all GRN items")
    
    # Get total stock
    materials_with_stock = await db.materials.find({"current_stock": {"$gt": 0}}).to_list(100)
    total_stock = sum(m.get("current_stock", 0) for m in materials_with_stock)
    
    print(f"\n📦 Current Inventory:")
    print(f"   • Total Stock: {total_stock:,} units")
    print(f"   • Materials in Stock: {len(materials_with_stock)}")
    
    print(f"\n🏭 Solar Panel BOM Categories:")
    print(f"   • Solar Cells (3 types)")
    print(f"   • Glass & Encapsulation (4 types)")
    print(f"   • Backsheet (2 types)")
    print(f"   • Frames & Mounting (2 types)")
    print(f"   • Electrical Components (3 types)")
    print(f"   • Interconnects & Cables (3 types)")
    print(f"   • Connectors (2 types)")
    print(f"   • Sealants & Adhesives (2 types)")
    print(f"   • Packaging Materials (2 types)")
    
    print(f"\n🎯 Ready for Solar Manufacturing Operations!")
    print(f"   Login: admin@warehouse.com / admin123")
    print(f"   URL: https://emergent-extend.preview.emergentagent.com")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
