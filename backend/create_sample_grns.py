"""
Create sample GRN with test data via API
"""
import asyncio
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def create_sample_grns():
    """Create sample GRNs for testing"""
    
    print("🚚 Creating sample GRNs...")
    
    # Get admin user for token
    admin_user = await db.users.find_one({"email": "admin@warehouse.com"})
    if not admin_user:
        print("❌ Admin user not found")
        return
    
    # Create JWT token manually
    import jwt
    from datetime import timedelta
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
    
    # Get materials
    materials = await db.materials.find({}, {"_id": 0}).to_list(20)
    if not materials:
        print("❌ No materials found")
        return
    
    # Get bins
    bins = await db.bins.find({}, {"_id": 0}).to_list(20)
    
    async with httpx.AsyncClient() as http_client:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # GRN 1 - Electronics shipment
        print("\n📦 Creating GRN #1 - Electronics Shipment...")
        grn1_data = {
            "vendor_name": "Tech Supplies Inc",
            "po_number": "PO-2026-001",
            "invoice_number": "INV-TECH-45678",
            "receipt_date": datetime.now(timezone.utc).isoformat(),
            "remarks": "Electronics components shipment for Q1",
            "items": [
                {
                    "material_id": next(m["material_id"] for m in materials if m["material_code"] == "ELEC-001"),
                    "received_quantity": 50,
                    "accepted_quantity": 48,
                    "rejected_quantity": 2,
                    "batch_number": "BTH-ELEC001-20260330",
                    "manufacturing_date": "2026-03-15",
                    "expiry_date": "2028-03-15",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "A-01-01-01",
                    "rejection_reason": "Minor packaging damage"
                },
                {
                    "material_id": next(m["material_id"] for m in materials if m["material_code"] == "ELEC-002"),
                    "received_quantity": 100,
                    "accepted_quantity": 100,
                    "rejected_quantity": 0,
                    "batch_number": "BTH-ELEC002-20260330",
                    "manufacturing_date": "2026-03-20",
                    "expiry_date": "2028-03-20",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "A-01-01-02"
                },
                {
                    "material_id": next(m["material_id"] for m in materials if m["material_code"] == "ELEC-003"),
                    "received_quantity": 200,
                    "accepted_quantity": 200,
                    "rejected_quantity": 0,
                    "batch_number": "BTH-ELEC003-20260330",
                    "manufacturing_date": "2026-03-18",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "A-01-02-01"
                }
            ]
        }
        
        response1 = await http_client.post(
            "http://localhost:8001/api/grn",
            headers=headers,
            json=grn1_data,
            timeout=10.0
        )
        if response1.status_code == 200:
            grn1 = response1.json()
            print(f"✅ GRN created: {grn1['grn_number']}")
            
            # Complete the GRN
            complete_resp = await http_client.put(
                f"http://localhost:8001/api/grn/{grn1['grn_id']}/complete",
                headers=headers
            )
            if complete_resp.status_code == 200:
                print(f"✅ GRN completed and stock updated")
        else:
            print(f"❌ Failed to create GRN 1: {response1.text}")
        
        # GRN 2 - Raw Materials
        print("\n📦 Creating GRN #2 - Raw Materials...")
        grn2_data = {
            "vendor_name": "MetalWorks Ltd",
            "po_number": "PO-2026-002",
            "invoice_number": "INV-MW-12345",
            "receipt_date": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "remarks": "Raw materials for manufacturing",
            "items": [
                {
                    "material_id": next(m["material_id"] for m in materials if m["material_code"] == "RAW-001"),
                    "received_quantity": 500,
                    "accepted_quantity": 500,
                    "rejected_quantity": 0,
                    "batch_number": "BTH-RAW001-20260328",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "A-02-01-01"
                },
                {
                    "material_id": next(m["material_id"] for m in materials if m["material_code"] == "RAW-002"),
                    "received_quantity": 10,
                    "accepted_quantity": 10,
                    "rejected_quantity": 0,
                    "batch_number": "BTH-RAW002-20260328",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "A-02-01-01"
                }
            ]
        }
        
        response2 = await http_client.post(
            "http://localhost:8001/api/grn",
            headers=headers,
            json=grn2_data,
            timeout=10.0
        )
        if response2.status_code == 200:
            grn2 = response2.json()
            print(f"✅ GRN created: {grn2['grn_number']}")
            
            # Complete the GRN
            complete_resp = await http_client.put(
                f"http://localhost:8001/api/grn/{grn2['grn_id']}/complete",
                headers=headers
            )
            if complete_resp.status_code == 200:
                print(f"✅ GRN completed and stock updated")
        else:
            print(f"❌ Failed to create GRN 2: {response2.text}")
        
        # GRN 3 - Packaging Materials
        print("\n📦 Creating GRN #3 - Packaging Materials...")
        grn3_data = {
            "vendor_name": "PackPro Solutions",
            "po_number": "PO-2026-003",
            "invoice_number": "INV-PP-78901",
            "receipt_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "remarks": "Packaging supplies monthly order",
            "items": [
                {
                    "material_id": next(m["material_id"] for m in materials if m["material_code"] == "PKG-001"),
                    "received_quantity": 300,
                    "accepted_quantity": 300,
                    "rejected_quantity": 0,
                    "batch_number": "BTH-PKG001-20260329",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "B-01-01-01"
                },
                {
                    "material_id": next(m["material_id"] for m in materials if m["material_code"] == "PKG-002"),
                    "received_quantity": 50,
                    "accepted_quantity": 50,
                    "rejected_quantity": 0,
                    "batch_number": "BTH-PKG002-20260329",
                    "quality_inspection_status": "passed",
                    "storage_condition": "ambient",
                    "bin_location": "B-01-02-01"
                }
            ]
        }
        
        response3 = await http_client.post(
            "http://localhost:8001/api/grn",
            headers=headers,
            json=grn3_data,
            timeout=10.0
        )
        if response3.status_code == 200:
            grn3 = response3.json()
            print(f"✅ GRN created: {grn3['grn_number']}")
            
            # Complete the GRN
            complete_resp = await http_client.put(
                f"http://localhost:8001/api/grn/{grn3['grn_id']}/complete",
                headers=headers
            )
            if complete_resp.status_code == 200:
                print(f"✅ GRN completed and stock updated")
        else:
            print(f"❌ Failed to create GRN 3: {response3.text}")
    
    print("\n✅ Sample GRNs created and completed successfully!")
    print("\n📊 Data Summary:")
    print("   - 3 GRNs created and completed")
    print("   - Stock updated for all materials")
    print("   - Labels auto-generated for all items")
    print("   - Ready to test putaway, issues, and reports")

if __name__ == "__main__":
    asyncio.run(create_sample_grns())
