"""
SAP WM Phase 2 - Enhanced APIs
Bin-to-bin transfer, Warehouse transfer, Physical Inventory completion, Storage Units, Bin Blocking
"""
from fastapi import APIRouter, HTTPException, Request, Query
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
import os
import uuid
from datetime import datetime, timezone, timedelta
from wm_enhanced_models import (
    StorageUnit, BinBlock, WarehouseTransfer,
    STORAGE_TYPES, STOCK_CATEGORY_CODES
)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create Phase 2 router
wm_phase2_router = APIRouter(prefix="/api/wm", tags=["WM Phase 2"])

# ===================== HELPER FUNCTIONS =====================

async def get_current_user_from_request(request: Request) -> dict:
    """Extract user from request"""
    user = await db.users.find_one({"email": "admin@warehouse.com"}, {"_id": 0})
    return user

def generate_number(prefix: str, collection_name: str) -> str:
    """Generate unique document numbers"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{timestamp}-{random_suffix}"

# ===================== BIN-TO-BIN TRANSFER =====================

@wm_phase2_router.post("/bin-to-bin-transfer")
async def bin_to_bin_transfer(
    source_bin_code: str,
    destination_bin_code: str,
    material_id: str,
    quantity: float,
    batch_number: Optional[str] = None,
    stock_category: str = "UNRES",
    reason: str = "",
    request: Request = None
):
    """
    Bin-to-bin transfer within same warehouse
    Movement type 999 (SAP WM)
    No IM posting required
    """
    user = await get_current_user_from_request(request)
    
    # Validate bins exist
    source_bin = await db.bins.find_one({"bin_code": source_bin_code}, {"_id": 0})
    dest_bin = await db.bins.find_one({"bin_code": destination_bin_code}, {"_id": 0})
    
    if not source_bin or not dest_bin:
        raise HTTPException(status_code=404, detail="Source or destination bin not found")
    
    # Find source quant
    query = {
        "material_id": material_id,
        "bin_code": source_bin_code,
        "stock_category": stock_category,
        "quantity": {"$gte": quantity}
    }
    if batch_number:
        query["batch_number"] = batch_number
    
    source_quant = await db.quants.find_one(query, {"_id": 0})
    
    if not source_quant:
        raise HTTPException(status_code=400, detail="Insufficient stock in source bin")
    
    # Create transfer TO
    to_number = generate_number("TO-BIN", "transfer_orders")
    
    to_item = {
        "item_number": 1,
        "material_id": material_id,
        "material_code": source_quant["material_code"],
        "material_name": source_quant.get("material_code", ""),
        "target_quantity": quantity,
        "confirmed_quantity": quantity,
        "difference_quantity": 0,
        "uom": source_quant["uom"],
        "source_bin_id": source_bin["bin_id"],
        "source_bin_code": source_bin_code,
        "source_quant_id": source_quant["quant_id"],
        "destination_bin_id": dest_bin["bin_id"],
        "destination_bin_code": destination_bin_code,
        "stock_category": stock_category,
        "batch_number": batch_number,
        "item_status": "CONFIRMED"
    }
    
    to_doc = {
        "to_number": to_number,
        "to_type": "STOCK_TRANSFER",
        "warehouse_number": "W001",
        "items": [to_item],
        "status": "CONFIRMED",
        "movement_type": "999",  # SAP WM bin-to-bin
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["user_id"],
        "confirmed_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.transfer_orders.insert_one(to_doc)
    
    # Update source quant - reduce quantity
    new_source_qty = source_quant["quantity"] - quantity
    
    if new_source_qty == 0:
        # Delete quant if empty
        await db.quants.delete_one({"quant_id": source_quant["quant_id"]})
    else:
        await db.quants.update_one(
            {"quant_id": source_quant["quant_id"]},
            {"$set": {"quantity": new_source_qty, "last_changed_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    # Create or update destination quant
    dest_quant = await db.quants.find_one({
        "material_id": material_id,
        "bin_code": destination_bin_code,
        "stock_category": stock_category,
        "batch_number": batch_number
    }, {"_id": 0})
    
    if dest_quant:
        # Update existing
        new_dest_qty = dest_quant["quantity"] + quantity
        await db.quants.update_one(
            {"quant_id": dest_quant["quant_id"]},
            {"$set": {"quantity": new_dest_qty, "last_changed_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        # Create new quant at destination
        quant_id = f"quant_{uuid.uuid4().hex[:12]}"
        new_quant = {
            "quant_id": quant_id,
            "material_id": material_id,
            "material_code": source_quant["material_code"],
            "bin_id": dest_bin["bin_id"],
            "bin_code": destination_bin_code,
            "warehouse_number": "W001",
            "storage_type": dest_bin.get("zone", "RACK"),
            "quantity": quantity,
            "uom": source_quant["uom"],
            "stock_category": stock_category,
            "batch_number": batch_number,
            "manufacturing_date": source_quant.get("manufacturing_date"),
            "shelf_life_expiry_date": source_quant.get("shelf_life_expiry_date"),
            "gr_date": source_quant.get("gr_date"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }
        await db.quants.insert_one(new_quant)
    
    # Create stock movement record
    movement_doc = {
        "movement_id": f"mov_{uuid.uuid4().hex[:12]}",
        "movement_type": "BIN_TO_BIN",
        "material_id": material_id,
        "material_code": source_quant["material_code"],
        "quantity": quantity,
        "uom": source_quant["uom"],
        "source_bin": source_bin_code,
        "destination_bin": destination_bin_code,
        "stock_category": stock_category,
        "batch_number": batch_number,
        "to_number": to_number,
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["user_id"]
    }
    await db.stock_movements.insert_one(movement_doc)
    
    return {
        "message": "Bin-to-bin transfer completed",
        "to_number": to_number,
        "source_bin": source_bin_code,
        "destination_bin": destination_bin_code,
        "quantity_transferred": quantity
    }

# ===================== WAREHOUSE-TO-WAREHOUSE TRANSFER =====================

@wm_phase2_router.post("/warehouse-transfer")
async def create_warehouse_transfer(
    transfer_type: str,  # SAME_PLANT or CROSS_PLANT
    source_warehouse: str,
    destination_warehouse: str,
    material_id: str,
    quantity: float,
    source_storage_type: Optional[str] = None,
    destination_storage_type: Optional[str] = None,
    request: Request = None
):
    """
    Create warehouse-to-warehouse transfer
    Supports same-plant and cross-plant STO (Stock Transport Order)
    """
    user = await get_current_user_from_request(request)
    
    # Get material
    material = await db.materials.find_one({"material_id": material_id}, {"_id": 0})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    transfer_id = generate_number("WHT", "warehouse_transfers")
    
    transfer_doc = {
        "transfer_id": transfer_id,
        "transfer_type": transfer_type,
        "source_warehouse": source_warehouse,
        "source_storage_type": source_storage_type,
        "destination_warehouse": destination_warehouse,
        "destination_storage_type": destination_storage_type,
        "material_id": material_id,
        "material_code": material["material_code"],
        "quantity": quantity,
        "uom": material["uom"],
        "status": "CREATED",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.warehouse_transfers.insert_one(transfer_doc)
    
    # Create source TO (picking/GI)
    source_to_number = generate_number("TO-SRC", "transfer_orders")
    source_to = {
        "to_number": source_to_number,
        "to_type": "PICKING",
        "warehouse_number": source_warehouse,
        "items": [{
            "item_number": 1,
            "material_id": material_id,
            "material_code": material["material_code"],
            "material_name": material["name"],
            "target_quantity": quantity,
            "uom": material["uom"],
            "item_status": "OPEN"
        }],
        "reference_doc_number": transfer_id,
        "status": "OPEN",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["user_id"]
    }
    await db.transfer_orders.insert_one(source_to)
    
    # Update transfer with TO number
    await db.warehouse_transfers.update_one(
        {"transfer_id": transfer_id},
        {"$set": {"source_to_number": source_to_number, "status": "IN_TRANSIT"}}
    )
    
    return {
        "message": "Warehouse transfer created",
        "transfer_id": transfer_id,
        "source_to": source_to_number,
        "status": "IN_TRANSIT"
    }

@wm_phase2_router.put("/warehouse-transfer/{transfer_id}/receive")
async def receive_warehouse_transfer(
    transfer_id: str,
    received_quantity: float,
    destination_bin_code: str,
    request: Request = None
):
    """Receive goods at destination warehouse"""
    user = await get_current_user_from_request(request)
    
    transfer = await db.warehouse_transfers.find_one({"transfer_id": transfer_id}, {"_id": 0})
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    if transfer["status"] != "IN_TRANSIT":
        raise HTTPException(status_code=400, detail="Transfer not in transit")
    
    # Create destination TO (putaway/GR)
    dest_to_number = generate_number("TO-DST", "transfer_orders")
    dest_to = {
        "to_number": dest_to_number,
        "to_type": "PUTAWAY",
        "warehouse_number": transfer["destination_warehouse"],
        "items": [{
            "item_number": 1,
            "material_id": transfer["material_id"],
            "material_code": transfer["material_code"],
            "material_name": transfer["material_code"],
            "target_quantity": received_quantity,
            "confirmed_quantity": received_quantity,
            "destination_bin_code": destination_bin_code,
            "uom": transfer["uom"],
            "item_status": "CONFIRMED"
        }],
        "reference_doc_number": transfer_id,
        "status": "CONFIRMED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["user_id"]
    }
    await db.transfer_orders.insert_one(dest_to)
    
    # Update transfer
    await db.warehouse_transfers.update_one(
        {"transfer_id": transfer_id},
        {
            "$set": {
                "destination_to_number": dest_to_number,
                "status": "RECEIVED",
                "received_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "message": "Warehouse transfer received",
        "transfer_id": transfer_id,
        "destination_to": dest_to_number
    }

# ===================== PHYSICAL INVENTORY - COMPLETE WORKFLOW =====================

@wm_phase2_router.put("/physical-inventory/{doc_number}/count")
async def enter_inventory_count(
    doc_number: str,
    count_item_id: str,
    counted_quantity: float,
    request: Request = None
):
    """Enter first count for an inventory item"""
    user = await get_current_user_from_request(request)
    
    # Update count item
    await db.inventory_count_items.update_one(
        {"count_item_id": count_item_id},
        {
            "$set": {
                "counted_quantity": counted_quantity,
                "count_status": "COUNTED",
                "counted_by": user["user_id"],
                "counted_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Calculate difference
    item = await db.inventory_count_items.find_one({"count_item_id": count_item_id}, {"_id": 0})
    difference = counted_quantity - item["book_quantity"]
    
    await db.inventory_count_items.update_one(
        {"count_item_id": count_item_id},
        {"$set": {"difference_quantity": difference}}
    )
    
    return {"message": "Count entered", "difference": difference}

@wm_phase2_router.put("/physical-inventory/{doc_number}/recount")
async def enter_inventory_recount(
    doc_number: str,
    count_item_id: str,
    recount_quantity: float,
    request: Request = None
):
    """Enter recount for items with differences"""
    user = await get_current_user_from_request(request)
    
    item = await db.inventory_count_items.find_one({"count_item_id": count_item_id}, {"_id": 0})
    
    if item["count_status"] != "COUNTED":
        raise HTTPException(status_code=400, detail="Item must be counted first")
    
    # Update with recount
    await db.inventory_count_items.update_one(
        {"count_item_id": count_item_id},
        {
            "$set": {
                "recount_quantity": recount_quantity,
                "count_status": "RECOUNTED",
                "recounted_by": user["user_id"],
                "difference_quantity": recount_quantity - item["book_quantity"]
            }
        }
    )
    
    return {"message": "Recount entered"}

@wm_phase2_router.put("/physical-inventory/{doc_number}/post")
async def post_inventory_differences(doc_number: str, request: Request = None):
    """Post inventory differences to update stock"""
    user = await get_current_user_from_request(request)
    
    pi_doc = await db.physical_inventory.find_one({"inventory_doc_number": doc_number}, {"_id": 0})
    if not pi_doc:
        raise HTTPException(status_code=404, detail="Inventory document not found")
    
    if pi_doc["status"] not in ["FROZEN", "DIFFERENCES_FOUND"]:
        raise HTTPException(status_code=400, detail="Cannot post inventory")
    
    # Get all count items with differences
    count_items = await db.inventory_count_items.find({
        "inventory_doc_number": doc_number,
        "difference_quantity": {"$ne": 0}
    }, {"_id": 0}).to_list(1000)
    
    differences_posted = 0
    
    for item in count_items:
        # Use recount quantity if available, else first count
        final_quantity = item.get("recount_quantity") or item.get("counted_quantity")
        difference = item["difference_quantity"]
        
        # Update quant
        await db.quants.update_one(
            {"quant_id": item["quant_id"]},
            {
                "$set": {
                    "quantity": final_quantity,
                    "last_changed_at": datetime.now(timezone.utc).isoformat(),
                    "last_changed_by": user["user_id"]
                }
            }
        )
        
        # Create adjustment movement
        movement_doc = {
            "movement_id": f"mov_{uuid.uuid4().hex[:12]}",
            "movement_type": "INVENTORY_ADJUSTMENT",
            "material_id": item["material_id"],
            "material_code": item["material_code"],
            "quantity": abs(difference),
            "adjustment_type": "INCREASE" if difference > 0 else "DECREASE",
            "bin_code": item["bin_code"],
            "batch_number": item.get("batch_number"),
            "reference_doc": doc_number,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }
        await db.stock_movements.insert_one(movement_doc)
        
        # Mark item as posted
        await db.inventory_count_items.update_one(
            {"count_item_id": item["count_item_id"]},
            {"$set": {"count_status": "POSTED"}}
        )
        
        differences_posted += 1
    
    # Update PI document
    await db.physical_inventory.update_one(
        {"inventory_doc_number": doc_number},
        {
            "$set": {
                "status": "POSTED",
                "is_stock_frozen": False,
                "items_with_differences": differences_posted,
                "posted_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "message": "Inventory differences posted",
        "differences_posted": differences_posted
    }

# ===================== STORAGE UNITS (PALLETS) =====================

@wm_phase2_router.post("/storage-units")
async def create_storage_unit(
    storage_unit_type: str,
    bin_code: Optional[str] = None,
    request: Request = None
):
    """Create new storage unit (pallet)"""
    user = await get_current_user_from_request(request)
    
    su_id = f"su_{uuid.uuid4().hex[:12]}"
    su_number = generate_number("SU", "storage_units")
    
    su_doc = {
        "storage_unit_id": su_id,
        "storage_unit_number": su_number,
        "storage_unit_type": storage_unit_type,
        "warehouse_number": "W001",
        "bin_code": bin_code,
        "status": "EMPTY" if not bin_code else "ACTIVE",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.storage_units.insert_one(su_doc)
    
    return {"message": "Storage unit created", "su_number": su_number, "su_id": su_id}

@wm_phase2_router.get("/storage-units")
async def get_storage_units(status: Optional[str] = None):
    """Get all storage units"""
    query = {}
    if status:
        query["status"] = status
    
    sus = await db.storage_units.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return {"total": len(sus), "storage_units": sus}

# ===================== BIN BLOCKING =====================

@wm_phase2_router.post("/bin-blocking")
async def create_bin_block(
    bin_code: str,
    block_type: str,  # PUTAWAY, PICKING, BOTH
    block_reason: str,
    valid_from: Optional[str] = None,
    valid_to: Optional[str] = None,
    request: Request = None
):
    """Block bin for putaway/picking operations"""
    user = await get_current_user_from_request(request)
    
    bin_doc = await db.bins.find_one({"bin_code": bin_code}, {"_id": 0})
    if not bin_doc:
        raise HTTPException(status_code=404, detail="Bin not found")
    
    block_id = f"block_{uuid.uuid4().hex[:12]}"
    
    block_doc = {
        "block_id": block_id,
        "bin_id": bin_doc["bin_id"],
        "bin_code": bin_code,
        "block_type": block_type,
        "block_reason": block_reason,
        "valid_from": valid_from or datetime.now(timezone.utc).isoformat(),
        "valid_to": valid_to,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["user_id"]
    }
    
    await db.bin_blocks.insert_one(block_doc)
    
    # Update bin status
    await db.bins.update_one(
        {"bin_code": bin_code},
        {"$set": {"status": "blocked"}}
    )
    
    return {"message": "Bin blocked", "block_id": block_id}

@wm_phase2_router.delete("/bin-blocking/{block_id}")
async def remove_bin_block(block_id: str):
    """Remove bin blocking"""
    block = await db.bin_blocks.find_one({"block_id": block_id}, {"_id": 0})
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    # Deactivate block
    await db.bin_blocks.update_one(
        {"block_id": block_id},
        {"$set": {"is_active": False}}
    )
    
    # Update bin status
    await db.bins.update_one(
        {"bin_code": block["bin_code"]},
        {"$set": {"status": "available"}}
    )
    
    return {"message": "Bin block removed"}

@wm_phase2_router.get("/bin-blocking")
async def get_bin_blocks(is_active: Optional[bool] = True):
    """Get all bin blocks"""
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    
    blocks = await db.bin_blocks.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return {"total": len(blocks), "bin_blocks": blocks}

# ===================== MIXED STORAGE CONTROL =====================

@wm_phase2_router.get("/mixed-storage/check")
async def check_mixed_storage(bin_code: str, material_id: str):
    """Check if material can be added to bin (mixed storage control)"""
    
    # Get bin
    bin_doc = await db.bins.find_one({"bin_code": bin_code}, {"_id": 0})
    if not bin_doc:
        raise HTTPException(status_code=404, detail="Bin not found")
    
    # Get storage type config
    storage_type = bin_doc.get("zone", "RACK")
    storage_config = STORAGE_TYPES.get(storage_type, {})
    
    # Check if mixed storage is allowed (default: allow)
    allow_mixed = storage_config.get("allow_mixed_storage", True)
    
    # Get existing quants in bin
    existing_quants = await db.quants.find({"bin_code": bin_code}, {"_id": 0}).to_list(100)
    
    if not existing_quants:
        return {"allowed": True, "reason": "Bin is empty"}
    
    # Check if different material already exists
    existing_materials = [q["material_id"] for q in existing_quants]
    
    if material_id in existing_materials:
        return {"allowed": True, "reason": "Same material already in bin"}
    
    if not allow_mixed and existing_materials:
        return {
            "allowed": False,
            "reason": f"Mixed storage not allowed for storage type {storage_type}",
            "existing_materials": existing_materials
        }
    
    return {"allowed": True, "reason": "Mixed storage allowed"}
