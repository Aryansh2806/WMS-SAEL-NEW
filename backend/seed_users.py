"""
Seed script to create initial users for WMS Pro
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os
import bcrypt
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

async def seed_users():
    """Create initial users if they don't exist"""
    
    # Check if admin exists
    existing_admin = await db.users.find_one({"email": "admin@warehouse.com"})
    
    if existing_admin:
        print("✅ Admin user already exists")
    else:
        # Create admin user
        admin_id = f"user_{uuid.uuid4().hex[:12]}"
        admin_doc = {
            "user_id": admin_id,
            "email": "admin@warehouse.com",
            "name": "Admin User",
            "role": "Admin",
            "password": hash_password("admin123"),
            "auth_type": "local",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(admin_doc)
        print("✅ Admin user created: admin@warehouse.com / admin123")
    
    # Check if warehouse operator exists
    existing_operator = await db.users.find_one({"email": "operator@test.com"})
    
    if existing_operator:
        print("✅ Warehouse Operator already exists")
    else:
        # Create warehouse operator
        operator_id = f"user_{uuid.uuid4().hex[:12]}"
        operator_doc = {
            "user_id": operator_id,
            "email": "operator@test.com",
            "name": "Warehouse Operator",
            "role": "Warehouse Operator",
            "password": hash_password("test123"),
            "auth_type": "local",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(operator_doc)
        print("✅ Warehouse Operator created: operator@test.com / test123")
    
    # Check if Store In-Charge exists
    existing_store = await db.users.find_one({"email": "store@test.com"})
    
    if existing_store:
        print("✅ Store In-Charge already exists")
    else:
        # Create Store In-Charge
        store_id = f"user_{uuid.uuid4().hex[:12]}"
        store_doc = {
            "user_id": store_id,
            "email": "store@test.com",
            "name": "Store In-Charge",
            "role": "Store In-Charge",
            "password": hash_password("test123"),
            "auth_type": "local",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(store_doc)
        print("✅ Store In-Charge created: store@test.com / test123")
    
    # Check if Inventory Controller exists
    existing_controller = await db.users.find_one({"email": "controller@test.com"})
    
    if existing_controller:
        print("✅ Inventory Controller already exists")
    else:
        # Create Inventory Controller
        controller_id = f"user_{uuid.uuid4().hex[:12]}"
        controller_doc = {
            "user_id": controller_id,
            "email": "controller@test.com",
            "name": "Inventory Controller",
            "role": "Inventory Controller",
            "password": hash_password("test123"),
            "auth_type": "local",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(controller_doc)
        print("✅ Inventory Controller created: controller@test.com / test123")
    
    print("\n🎉 User seeding completed successfully!")
    print("\n📝 Available test users:")
    print("   - Admin: admin@warehouse.com / admin123")
    print("   - Warehouse Operator: operator@test.com / test123")
    print("   - Store In-Charge: store@test.com / test123")
    print("   - Inventory Controller: controller@test.com / test123")

if __name__ == "__main__":
    asyncio.run(seed_users())
