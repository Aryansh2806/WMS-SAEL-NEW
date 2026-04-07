"""
SAP WM Enhanced APIs for Solar Manufacturing WMS
Phase 1: Core Features Implementation
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
import os
import uuid
from datetime import datetime, timezone, timedelta
from wm_enhanced_models import (
    Quant, TransferRequirement, TransferOrder, TransferOrderItem,
    PhysicalInventoryDocument, InventoryCountItem, StorageUnit,
    BinBlock, WarehouseTransfer,
    STOCK_CATEGORIES, STOCK_CATEGORY_CODES, STORAGE_TYPES,
    PUTAWAY_STRATEGIES, PICKING_STRATEGIES, INTERIM_STORAGE_TYPES
)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create enhanced router
wm_router = APIRouter(prefix="/api/wm", tags=["WM Enhanced"])

# ===================== HELPER FUNCTIONS =====================

async def get_current_user_from_request(request: Request) -> dict:
    """Extract user from request"""
    # This will be integrated with main auth system
    # For now, return admin user
    user = await db.users.find_one({"email": "admin@warehouse.com"}, {"_id": 0})
    return user

def generate_number(prefix: str, collection_name: str) -> str:
    """Generate unique document numbers"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{timestamp}-{random_suffix}"

# ===================== QUANT MANAGEMENT =====================

@wm_router.get("/quants")
async def get_quants(
    material_code: Optional[str] = None,
    bin_code: Optional[str] = None,
    stock_category: Optional[str] = None,
    storage_type: Optional[str] = None,
    expired_only: bool = False
):
    """Get quants with filters"""
    query = {}
    
    if material_code:
        query["material_code"] = {"$regex": material_code, "$options": "i"}
    if bin_code:
        query["bin_code"] = {"$regex": bin_code, "$options": "i"}
    if stock_category:
        query["stock_category"] = stock_category
    if storage_type:
        query["storage_type"] = storage_type
    
    if expired_only:
        today = datetime.now(timezone.utc).isoformat()
        query["shelf_life_expiry_date"] = {"$lt": today, "$ne": None}
    
    quants = await db.quants.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return {"total": len(quants), "quants": quants}

@wm_router.get("/quants/bin/{bin_code}")
async def get_quants_by_bin(bin_code: str):
    """Get all quants in a specific bin"""
    quants = await db.quants.find({"bin_code": bin_code}, {"_id": 0}).to_list(100)
    
    # Calculate total quantity by stock category
    summary = {
        "bin_code": bin_code,
        "total_quants": len(quants),
        "by_category": {}
    }
    
    for cat in STOCK_CATEGORY_CODES:
        cat_quants = [q for q in quants if q.get("stock_category") == cat]
        summary["by_category"][cat] = {
            "count": len(cat_quants),
            "total_quantity": sum(q.get("quantity", 0) for q in cat_quants)
        }
    
    return {"summary": summary, "quants": quants}

@wm_router.post("/quants/stock-category/change")
async def change_stock_category(
    quant_id: str,
    new_category: str,
    reason: str,
    request: Request
):
    """Change stock category of a quant (e.g., QA release: QINSP → UNRES)"""
    if new_category not in STOCK_CATEGORY_CODES:
        raise HTTPException(status_code=400, detail=f"Invalid stock category. Must be one of: {STOCK_CATEGORY_CODES}")
    
    user = await get_current_user_from_request(request)
    
    quant = await db.quants.find_one({"quant_id": quant_id}, {"_id": 0})
    if not quant:
        raise HTTPException(status_code=404, detail="Quant not found")
    
    old_category = quant.get("stock_category")
    
    # Update quant
    await db.quants.update_one(
        {"quant_id": quant_id},
        {
            "$set": {
                "stock_category": new_category,
                "last_changed_at": datetime.now(timezone.utc).isoformat(),
                "last_changed_by": user["user_id"]
            }
        }
    )
    
    # Create audit log
    audit_doc = {
        "audit_id": f"aud_{uuid.uuid4().hex[:12]}",
        "action": "stock_category_change",
        "entity_type": "quant",
        "entity_id": quant_id,
        "old_values": {"stock_category": old_category},
        "new_values": {"stock_category": new_category},
        "reason": reason,
        "performed_by": user["user_id"],
        "performed_by_name": user.get("name", "Unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(audit_doc)
    
    return {"message": "Stock category changed", "old": old_category, "new": new_category}

# ===================== TRANSFER REQUIREMENTS (TR) =====================

@wm_router.post("/transfer-requirements")
async def create_transfer_requirement(
    tr_type: str,
    material_id: str,
    required_quantity: float,
    stock_category: str = "UNRES",
    destination_bin: Optional[str] = None,
    storage_type: Optional[str] = None,
    reference_doc_number: Optional[str] = None,
    priority: int = 5,
    request: Request = None
):
    """Create Transfer Requirement (TR)"""
    user = await get_current_user_from_request(request)
    
    # Get material details
    material = await db.materials.find_one({"material_id": material_id}, {"_id": 0})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    tr_number = generate_number("TR", "transfer_requirements")
    
    tr_doc = {
        "tr_number": tr_number,
        "tr_type": tr_type,
        "material_id": material_id,
        "material_code": material["material_code"],
        "material_name": material["name"],
        "required_quantity": required_quantity,
        "open_quantity": required_quantity,
        "uom": material["uom"],
        "stock_category": stock_category,
        "destination_bin": destination_bin,
        "storage_type": storage_type,
        "reference_doc_number": reference_doc_number,
        "priority": priority,
        "status": "OPEN",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["user_id"]
    }
    
    await db.transfer_requirements.insert_one(tr_doc)
    
    return {"message": "Transfer Requirement created", "tr_number": tr_number, "data": tr_doc}

@wm_router.get("/transfer-requirements")
async def get_transfer_requirements(
    status: Optional[str] = None,
    tr_type: Optional[str] = None,
    material_code: Optional[str] = None
):
    """Get all Transfer Requirements"""
    query = {}
    if status:
        query["status"] = status
    if tr_type:
        query["tr_type"] = tr_type
    if material_code:
        query["material_code"] = {"$regex": material_code, "$options": "i"}
    
    trs = await db.transfer_requirements.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return {"total": len(trs), "transfer_requirements": trs}

# ===================== TRANSFER ORDERS (TO) =====================

@wm_router.post("/transfer-orders/from-tr/{tr_number}")
async def create_transfer_order_from_tr(tr_number: str, request: Request):
    """Create Transfer Order from Transfer Requirement"""
    user = await get_current_user_from_request(request)
    
    # Get TR
    tr = await db.transfer_requirements.find_one({"tr_number": tr_number}, {"_id": 0})
    if not tr:
        raise HTTPException(status_code=404, detail="Transfer Requirement not found")
    
    if tr["status"] != "OPEN":
        raise HTTPException(status_code=400, detail="TR is not open")
    
    to_number = generate_number("TO", "transfer_orders")
    
    # Determine TO type based on TR type
    to_type_map = {
        "GR": "PUTAWAY",
        "GI": "PICKING",
        "STOCK_TRANSFER": "STOCK_TRANSFER",
        "MANUAL": "PUTAWAY"
    }
    to_type = to_type_map.get(tr["tr_type"], "PUTAWAY")
    
    # For putaway: find source bin (GR area) and destination based on strategy
    destination_bin = tr.get("destination_bin")
    if not destination_bin and to_type == "PUTAWAY":
        # Apply put-away strategy
        destination_bin = await apply_putaway_strategy(
            tr["material_id"],
            tr["required_quantity"],
            tr.get("storage_type", "RACK")
        )
    
    # Create TO item
    to_item = {
        "item_number": 1,
        "material_id": tr["material_id"],
        "material_code": tr["material_code"],
        "material_name": tr["material_name"],
        "target_quantity": tr["required_quantity"],
        "confirmed_quantity": 0,
        "difference_quantity": 0,
        "uom": tr["uom"],
        "destination_bin_id": destination_bin,
        "destination_bin_code": destination_bin,
        "stock_category": tr["stock_category"],
        "item_status": "OPEN"
    }
    
    to_doc = {
        "to_number": to_number,
        "to_type": to_type,
        "warehouse_number": "W001",
        "storage_type": tr.get("storage_type"),
        "items": [to_item],
        "tr_number": tr_number,
        "reference_doc_number": tr.get("reference_doc_number"),
        "priority": tr["priority"],
        "status": "OPEN",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["user_id"]
    }
    
    await db.transfer_orders.insert_one(to_doc)
    
    # Update TR status
    await db.transfer_requirements.update_one(
        {"tr_number": tr_number},
        {"$set": {"status": "IN_PROCESS"}}
    )
    
    return {"message": "Transfer Order created", "to_number": to_number, "data": to_doc}

@wm_router.get("/transfer-orders")
async def get_transfer_orders(
    status: Optional[str] = None,
    to_type: Optional[str] = None,
    assigned_to: Optional[str] = None
):
    """Get all Transfer Orders"""
    query = {}
    if status:
        query["status"] = status
    if to_type:
        query["to_type"] = to_type
    if assigned_to:
        query["assigned_to"] = assigned_to
    
    tos = await db.transfer_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return {"total": len(tos), "transfer_orders": tos}

@wm_router.put("/transfer-orders/{to_number}/confirm")
async def confirm_transfer_order(
    to_number: str,
    confirmed_quantities: dict,  # item_number: quantity
    request: Request
):
    """Confirm Transfer Order (Step 3 of TO workflow)"""
    user = await get_current_user_from_request(request)
    
    to_doc = await db.transfer_orders.find_one({"to_number": to_number}, {"_id": 0})
    if not to_doc:
        raise HTTPException(status_code=404, detail="Transfer Order not found")
    
    if to_doc["status"] not in ["OPEN", "IN_PROCESS"]:
        raise HTTPException(status_code=400, detail="TO cannot be confirmed")
    
    now = datetime.now(timezone.utc)
    has_differences = False
    
    # Update items with confirmed quantities
    updated_items = []
    for item in to_doc["items"]:
        item_num = item["item_number"]
        confirmed_qty = confirmed_quantities.get(str(item_num), item["target_quantity"])
        
        item["confirmed_quantity"] = confirmed_qty
        item["difference_quantity"] = confirmed_qty - item["target_quantity"]
        item["item_status"] = "CONFIRMED"
        
        if item["difference_quantity"] != 0:
            has_differences = True
        
        updated_items.append(item)
        
        # Create or update quant at destination
        if confirmed_qty > 0:
            await create_or_update_quant(
                material_id=item["material_id"],
                material_code=item["material_code"],
                bin_id=item["destination_bin_id"],
                bin_code=item["destination_bin_code"],
                quantity=confirmed_qty,
                uom=item["uom"],
                stock_category=item["stock_category"],
                user=user,
                reference_doc="TO",
                reference_number=to_number
            )
    
    # Update TO
    await db.transfer_orders.update_one(
        {"to_number": to_number},
        {
            "$set": {
                "items": updated_items,
                "status": "CONFIRMED",
                "confirmed_at": now.isoformat(),
                "has_differences": has_differences,
                "last_changed_at": now.isoformat()
            }
        }
    )
    
    # Update linked TR if exists
    if to_doc.get("tr_number"):
        await db.transfer_requirements.update_one(
            {"tr_number": to_doc["tr_number"]},
            {
                "$set": {
                    "status": "COMPLETED",
                    "open_quantity": 0,
                    "completed_at": now.isoformat()
                }
            }
        )
    
    return {"message": "Transfer Order confirmed", "has_differences": has_differences}

# ===================== PUT-AWAY STRATEGIES =====================

async def apply_putaway_strategy(material_id: str, quantity: float, storage_type: str) -> str:
    """Apply put-away strategy to find destination bin"""
    strategy = STORAGE_TYPES.get(storage_type, {}).get("put_away_strategy", "next_empty")
    
    if strategy == "next_empty":
        # Find first empty bin in storage type
        bin_doc = await db.bins.find_one(
            {"zone": storage_type, "status": "empty"},
            {"_id": 0}
        )
        if bin_doc:
            return bin_doc["bin_code"]
    
    elif strategy == "open_storage":
        # Find bin with same material and available capacity
        bins = await db.bins.find(
            {
                "zone": storage_type,
                "material_code": {"$exists": True},
                "status": "available"
            },
            {"_id": 0}
        ).to_list(100)
        
        for bin_doc in bins:
            if bin_doc.get("current_stock", 0) + quantity <= bin_doc.get("capacity", 1000):
                return bin_doc["bin_code"]
        
        # If no suitable bin, use next empty
        bin_doc = await db.bins.find_one(
            {"zone": storage_type, "status": "empty"},
            {"_id": 0}
        )
        if bin_doc:
            return bin_doc["bin_code"]
    
    # Default: return first available bin
    bin_doc = await db.bins.find_one({"zone": storage_type}, {"_id": 0})
    return bin_doc["bin_code"] if bin_doc else None

async def apply_picking_strategy(material_id: str, quantity: float, storage_type: str) -> List[dict]:
    """Apply picking strategy to find source bins"""
    strategy = STORAGE_TYPES.get(storage_type, {}).get("picking_strategy", "fifo")
    
    # Get all quants for material
    quants = await db.quants.find(
        {
            "material_id": material_id,
            "stock_category": "UNRES",
            "quantity": {"$gt": 0}
        },
        {"_id": 0}
    ).to_list(100)
    
    if not quants:
        return []
    
    # Sort based on strategy
    if strategy == "fifo":
        # First In First Out - oldest first
        quants.sort(key=lambda x: x.get("gr_date", ""))
    elif strategy == "lifo":
        # Last In First Out - newest first
        quants.sort(key=lambda x: x.get("gr_date", ""), reverse=True)
    elif strategy == "fefo":
        # First Expired First Out
        quants.sort(key=lambda x: x.get("shelf_life_expiry_date", "9999-12-31"))
    
    # Build pick list
    picks = []
    remaining = quantity
    
    for quant in quants:
        if remaining <= 0:
            break
        
        pick_qty = min(quant["quantity"], remaining)
        picks.append({
            "quant_id": quant["quant_id"],
            "bin_code": quant["bin_code"],
            "quantity": pick_qty,
            "batch_number": quant.get("batch_number"),
            "sled": quant.get("shelf_life_expiry_date")
        })
        remaining -= pick_qty
    
    return picks

# ===================== QUANT HELPER FUNCTIONS =====================

async def create_or_update_quant(
    material_id: str,
    material_code: str,
    bin_id: str,
    bin_code: str,
    quantity: float,
    uom: str,
    stock_category: str,
    user: dict,
    batch_number: Optional[str] = None,
    sled: Optional[str] = None,
    reference_doc: Optional[str] = None,
    reference_number: Optional[str] = None
):
    """Create new quant or update existing one"""
    
    # Check if quant exists for same material, bin, batch, stock category
    existing_quant = await db.quants.find_one({
        "material_id": material_id,
        "bin_code": bin_code,
        "batch_number": batch_number,
        "stock_category": stock_category
    }, {"_id": 0})
    
    if existing_quant:
        # Update existing quant
        new_quantity = existing_quant["quantity"] + quantity
        await db.quants.update_one(
            {"quant_id": existing_quant["quant_id"]},
            {
                "$set": {
                    "quantity": new_quantity,
                    "last_changed_at": datetime.now(timezone.utc).isoformat(),
                    "last_changed_by": user["user_id"]
                }
            }
        )
        return existing_quant["quant_id"]
    
    else:
        # Create new quant
        quant_id = f"quant_{uuid.uuid4().hex[:12]}"
        
        # Get storage type from bin
        bin_doc = await db.bins.find_one({"bin_code": bin_code}, {"_id": 0})
        storage_type = bin_doc.get("zone", "RACK") if bin_doc else "RACK"
        
        quant_doc = {
            "quant_id": quant_id,
            "material_id": material_id,
            "material_code": material_code,
            "bin_id": bin_id,
            "bin_code": bin_code,
            "warehouse_number": "W001",
            "storage_type": storage_type,
            "quantity": quantity,
            "uom": uom,
            "stock_category": stock_category,
            "batch_number": batch_number,
            "shelf_life_expiry_date": sled,
            "gr_date": datetime.now(timezone.utc).isoformat(),
            "grn_number": reference_number if reference_doc == "GRN" else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }
        
        await db.quants.insert_one(quant_doc)
        return quant_id

# ===================== PHYSICAL INVENTORY =====================

@wm_router.post("/physical-inventory")
async def create_physical_inventory(
    inventory_type: str,
    storage_type: Optional[str] = None,
    bin_codes: List[str] = [],
    material_codes: List[str] = [],
    request: Request = None
):
    """Create Physical Inventory Document"""
    user = await get_current_user_from_request(request)
    
    doc_number = generate_number("PI", "physical_inventory")
    
    pi_doc = {
        "inventory_doc_number": doc_number,
        "inventory_type": inventory_type,
        "warehouse_number": "W001",
        "storage_type": storage_type,
        "bin_codes": bin_codes,
        "material_codes": material_codes,
        "status": "CREATED",
        "is_stock_frozen": False,
        "total_items_counted": 0,
        "items_with_differences": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["user_id"]
    }
    
    await db.physical_inventory.insert_one(pi_doc)
    
    # Create count items for selected bins/materials
    count_items = await generate_inventory_count_items(doc_number, bin_codes, material_codes)
    
    if count_items:
        await db.inventory_count_items.insert_many(count_items)
    
    return {
        "message": "Physical Inventory created",
        "doc_number": doc_number,
        "count_items": len(count_items)
    }

async def generate_inventory_count_items(doc_number: str, bin_codes: List[str], material_codes: List[str]) -> List[dict]:
    """Generate count items from quants"""
    query = {}
    
    if bin_codes:
        query["bin_code"] = {"$in": bin_codes}
    if material_codes:
        query["material_code"] = {"$in": material_codes}
    
    quants = await db.quants.find(query, {"_id": 0}).to_list(1000)
    
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
    
    return count_items

@wm_router.get("/physical-inventory")
async def get_physical_inventories(status: Optional[str] = None):
    """Get all Physical Inventory documents"""
    query = {}
    if status:
        query["status"] = status
    
    docs = await db.physical_inventory.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"total": len(docs), "documents": docs}

@wm_router.put("/physical-inventory/{doc_number}/freeze")
async def freeze_inventory(doc_number: str, request: Request):
    """Freeze stock for counting"""
    user = await get_current_user_from_request(request)
    
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
    
    return {"message": "Inventory frozen for counting"}

# ===================== CONFIGURATION ENDPOINTS =====================

@wm_router.get("/config/stock-categories")
async def get_stock_categories():
    """Get all stock categories"""
    return STOCK_CATEGORIES

@wm_router.get("/config/storage-types")
async def get_storage_types():
    """Get all storage types"""
    return STORAGE_TYPES

@wm_router.get("/config/strategies")
async def get_strategies():
    """Get all put-away and picking strategies"""
    return {
        "putaway_strategies": PUTAWAY_STRATEGIES,
        "picking_strategies": PICKING_STRATEGIES
    }

@wm_router.get("/config/interim-storage")
async def get_interim_storage_types():
    """Get interim storage area types"""
    return INTERIM_STORAGE_TYPES
