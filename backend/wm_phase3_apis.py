"""
SAP WM Phase 3 - Advanced Backend Features
Enhanced Reporting, Number Ranges, Quality Inspection, Storage Optimization
"""
from fastapi import APIRouter, HTTPException, Request, Query
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Any
import os
import uuid
from datetime import datetime, timezone, timedelta
from io import BytesIO
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create Phase 3 router
wm_phase3_router = APIRouter(prefix="/api/wm", tags=["WM Phase 3"])

# ===================== ENHANCED REPORTING SUITE =====================

@wm_phase3_router.get("/reports/quant-list")
async def quant_list_report(
    storage_type: Optional[str] = None,
    stock_category: Optional[str] = None,
    material_code: Optional[str] = None,
    expired_only: bool = False
):
    """LX03 - Quant List Report (Stock per bin)"""
    query = {}
    
    if storage_type:
        query["storage_type"] = storage_type
    if stock_category:
        query["stock_category"] = stock_category
    if material_code:
        query["material_code"] = {"$regex": material_code, "$options": "i"}
    if expired_only:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        query["shelf_life_expiry_date"] = {"$lt": today, "$ne": None}
    
    quants = await db.quants.find(query, {"_id": 0}).sort([("bin_code", 1), ("material_code", 1)]).to_list(10000)
    
    # Calculate totals
    total_quantity = sum(q.get("quantity", 0) for q in quants)
    by_category = {}
    for q in quants:
        cat = q.get("stock_category", "UNRES")
        if cat not in by_category:
            by_category[cat] = {"count": 0, "quantity": 0}
        by_category[cat]["count"] += 1
        by_category[cat]["quantity"] += q.get("quantity", 0)
    
    return {
        "report_name": "Quant List (LX03)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_quants": len(quants),
        "total_quantity": total_quantity,
        "by_category": by_category,
        "quants": quants
    }

@wm_phase3_router.get("/reports/bin-status")
async def bin_status_report(zone: Optional[str] = None):
    """LX02 - Bin Status Report"""
    query = {}
    if zone:
        query["zone"] = zone
    
    bins = await db.bins.find(query, {"_id": 0}).sort("bin_code", 1).to_list(10000)
    
    # Get quants for each bin
    bin_report = []
    for bin_doc in bins:
        quants = await db.quants.find({"bin_code": bin_doc["bin_code"]}, {"_id": 0}).to_list(100)
        
        total_qty = sum(q.get("quantity", 0) for q in quants)
        utilization = (total_qty / bin_doc.get("capacity", 1000)) * 100 if bin_doc.get("capacity") else 0
        
        bin_report.append({
            "bin_code": bin_doc["bin_code"],
            "zone": bin_doc.get("zone"),
            "status": bin_doc.get("status"),
            "capacity": bin_doc.get("capacity"),
            "current_stock": total_qty,
            "utilization_pct": round(utilization, 2),
            "material_count": len(quants),
            "materials": [{"code": q["material_code"], "qty": q["quantity"]} for q in quants]
        })
    
    # Summary
    total_bins = len(bins)
    empty_bins = len([b for b in bin_report if b["current_stock"] == 0])
    occupied_bins = total_bins - empty_bins
    avg_utilization = sum(b["utilization_pct"] for b in bin_report) / total_bins if total_bins > 0 else 0
    
    return {
        "report_name": "Bin Status Report (LX02)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_bins": total_bins,
            "empty_bins": empty_bins,
            "occupied_bins": occupied_bins,
            "avg_utilization": round(avg_utilization, 2)
        },
        "bins": bin_report
    }

@wm_phase3_router.get("/reports/stock-by-category")
async def stock_by_category_report():
    """Stock by Category Report"""
    categories = ["UNRES", "QINSP", "BLOCK", "RETRN"]
    
    report = []
    for cat in categories:
        quants = await db.quants.find({"stock_category": cat}, {"_id": 0}).to_list(10000)
        
        # Group by material
        material_summary = {}
        for q in quants:
            mat_code = q["material_code"]
            if mat_code not in material_summary:
                material_summary[mat_code] = {
                    "material_code": mat_code,
                    "total_quantity": 0,
                    "bins": 0,
                    "batches": set()
                }
            material_summary[mat_code]["total_quantity"] += q.get("quantity", 0)
            material_summary[mat_code]["bins"] += 1
            if q.get("batch_number"):
                material_summary[mat_code]["batches"].add(q["batch_number"])
        
        # Convert to list
        materials = []
        for mat in material_summary.values():
            mat["batch_count"] = len(mat["batches"])
            del mat["batches"]
            materials.append(mat)
        
        report.append({
            "category": cat,
            "category_name": {"UNRES": "Unrestricted", "QINSP": "Quality Inspection", 
                             "BLOCK": "Blocked", "RETRN": "Returns"}[cat],
            "total_quantity": sum(m["total_quantity"] for m in materials),
            "material_count": len(materials),
            "materials": materials
        })
    
    return {
        "report_name": "Stock by Category Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "categories": report
    }

@wm_phase3_router.get("/reports/expiry-alert")
async def expiry_alert_report(days_threshold: int = 30):
    """SLED Expiry Alert Report"""
    today = datetime.now(timezone.utc)
    threshold_date = (today + timedelta(days=days_threshold)).strftime("%Y-%m-%d")
    
    # Expired
    expired = await db.quants.find({
        "shelf_life_expiry_date": {"$lt": today.strftime("%Y-%m-%d"), "$ne": None}
    }, {"_id": 0}).to_list(10000)
    
    # Expiring soon
    expiring_soon = await db.quants.find({
        "shelf_life_expiry_date": {
            "$gte": today.strftime("%Y-%m-%d"),
            "$lte": threshold_date,
            "$ne": None
        }
    }, {"_id": 0}).to_list(10000)
    
    return {
        "report_name": "SLED Expiry Alert Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "threshold_days": days_threshold,
        "summary": {
            "expired_items": len(expired),
            "expiring_soon_items": len(expiring_soon),
            "total_expired_quantity": sum(q.get("quantity", 0) for q in expired),
            "total_expiring_quantity": sum(q.get("quantity", 0) for q in expiring_soon)
        },
        "expired": expired,
        "expiring_soon": expiring_soon
    }

@wm_phase3_router.get("/reports/transfer-order-list")
async def transfer_order_list_report(
    status: Optional[str] = None,
    to_type: Optional[str] = None,
    date_from: Optional[str] = None
):
    """LT21 - Transfer Order List"""
    query = {}
    if status:
        query["status"] = status
    if to_type:
        query["to_type"] = to_type
    if date_from:
        query["created_at"] = {"$gte": date_from}
    
    tos = await db.transfer_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
    
    # Calculate statistics
    total_items = sum(len(to.get("items", [])) for to in tos)
    total_quantity = sum(
        sum(item.get("target_quantity", 0) for item in to.get("items", []))
        for to in tos
    )
    confirmed_quantity = sum(
        sum(item.get("confirmed_quantity", 0) for item in to.get("items", []))
        for to in tos
    )
    
    return {
        "report_name": "Transfer Order List (LT21)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_tos": len(tos),
            "total_items": total_items,
            "total_quantity": total_quantity,
            "confirmed_quantity": confirmed_quantity,
            "difference": total_quantity - confirmed_quantity
        },
        "transfer_orders": tos
    }

@wm_phase3_router.get("/reports/stock-movement-history")
async def stock_movement_history(
    material_code: Optional[str] = None,
    bin_code: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """Stock Movement History Report"""
    query = {}
    if material_code:
        query["material_code"] = {"$regex": material_code, "$options": "i"}
    if bin_code:
        query["$or"] = [
            {"source_bin": bin_code},
            {"destination_bin": bin_code},
            {"bin_code": bin_code}
        ]
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to
        else:
            query["created_at"] = {"$lte": date_to}
    
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
    
    # Group by movement type
    by_type = {}
    for mov in movements:
        mtype = mov.get("movement_type", "UNKNOWN")
        if mtype not in by_type:
            by_type[mtype] = {"count": 0, "total_quantity": 0}
        by_type[mtype]["count"] += 1
        by_type[mtype]["total_quantity"] += mov.get("quantity", 0)
    
    return {
        "report_name": "Stock Movement History",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_movements": len(movements),
        "by_type": by_type,
        "movements": movements
    }

# ===================== NUMBER RANGE MANAGEMENT =====================

@wm_phase3_router.get("/number-ranges")
async def get_number_ranges():
    """Get all number range configurations"""
    ranges = await db.number_ranges.find({}, {"_id": 0}).to_list(100)
    
    if not ranges:
        # Initialize default ranges
        default_ranges = [
            {"range_id": "TR", "prefix": "TR", "current": 1000, "increment": 1},
            {"range_id": "TO", "prefix": "TO", "current": 1000, "increment": 1},
            {"range_id": "PI", "prefix": "PI", "current": 100, "increment": 1},
            {"range_id": "SU", "prefix": "SU", "current": 1000, "increment": 1},
            {"range_id": "QUANT", "prefix": "quant", "current": 10000, "increment": 1}
        ]
        await db.number_ranges.insert_many(default_ranges)
        ranges = default_ranges
    
    return {"number_ranges": ranges}

@wm_phase3_router.put("/number-ranges/{range_id}")
async def update_number_range(
    range_id: str,
    prefix: Optional[str] = None,
    current: Optional[int] = None,
    increment: Optional[int] = None
):
    """Update number range configuration"""
    update_data = {}
    if prefix:
        update_data["prefix"] = prefix
    if current is not None:
        update_data["current"] = current
    if increment is not None:
        update_data["increment"] = increment
    
    if update_data:
        await db.number_ranges.update_one(
            {"range_id": range_id},
            {"$set": update_data},
            upsert=True
        )
    
    return {"message": "Number range updated", "range_id": range_id}

# ===================== QUALITY INSPECTION AUTOMATION =====================

@wm_phase3_router.post("/quality-inspection/release")
async def qa_release_batch(
    material_code: str,
    batch_number: str,
    inspection_result: str,  # PASS, FAIL, PARTIAL
    approved_quantity: Optional[float] = None,
    rejected_quantity: Optional[float] = None,
    request: Request = None
):
    """Quality inspection release - auto change stock category"""
    user = await db.users.find_one({"email": "admin@warehouse.com"}, {"_id": 0})
    
    # Find all QINSP quants for this material/batch
    quants = await db.quants.find({
        "material_code": material_code,
        "batch_number": batch_number,
        "stock_category": "QINSP"
    }, {"_id": 0}).to_list(100)
    
    if not quants:
        raise HTTPException(status_code=404, detail="No quants in quality inspection")
    
    released_quants = 0
    blocked_quants = 0
    
    for quant in quants:
        if inspection_result == "PASS":
            # Move to UNRES
            await db.quants.update_one(
                {"quant_id": quant["quant_id"]},
                {
                    "$set": {
                        "stock_category": "UNRES",
                        "last_changed_at": datetime.now(timezone.utc).isoformat(),
                        "last_changed_by": user["user_id"]
                    }
                }
            )
            released_quants += 1
            
        elif inspection_result == "FAIL":
            # Move to BLOCK
            await db.quants.update_one(
                {"quant_id": quant["quant_id"]},
                {
                    "$set": {
                        "stock_category": "BLOCK",
                        "is_blocked": True,
                        "blocked_reason": "Failed quality inspection",
                        "last_changed_at": datetime.now(timezone.utc).isoformat(),
                        "last_changed_by": user["user_id"]
                    }
                }
            )
            blocked_quants += 1
    
    # Create audit log
    audit_doc = {
        "audit_id": f"aud_{uuid.uuid4().hex[:12]}",
        "action": "qa_release",
        "entity_type": "batch",
        "entity_id": batch_number,
        "details": {
            "material_code": material_code,
            "batch_number": batch_number,
            "inspection_result": inspection_result,
            "released_quants": released_quants,
            "blocked_quants": blocked_quants
        },
        "performed_by": user["user_id"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(audit_doc)
    
    return {
        "message": "QA release completed",
        "inspection_result": inspection_result,
        "released_quants": released_quants,
        "blocked_quants": blocked_quants
    }

@wm_phase3_router.get("/quality-inspection/pending")
async def get_pending_qa_items():
    """Get all items pending quality inspection"""
    quants = await db.quants.find(
        {"stock_category": "QINSP"},
        {"_id": 0}
    ).sort("gr_date", 1).to_list(1000)
    
    # Group by material and batch
    pending_batches = {}
    for q in quants:
        key = f"{q['material_code']}_{q.get('batch_number', 'NO_BATCH')}"
        if key not in pending_batches:
            pending_batches[key] = {
                "material_code": q["material_code"],
                "batch_number": q.get("batch_number"),
                "total_quantity": 0,
                "bins": [],
                "gr_date": q.get("gr_date"),
                "age_days": (datetime.now(timezone.utc) - datetime.fromisoformat(q.get("gr_date", datetime.now(timezone.utc).isoformat()))).days if q.get("gr_date") else 0
            }
        pending_batches[key]["total_quantity"] += q.get("quantity", 0)
        pending_batches[key]["bins"].append(q["bin_code"])
    
    return {
        "total_pending": len(quants),
        "unique_batches": len(pending_batches),
        "batches": list(pending_batches.values())
    }

# ===================== STORAGE OPTIMIZATION =====================

@wm_phase3_router.get("/storage-optimization/recommendations")
async def get_storage_optimization_recommendations():
    """Get recommendations for storage optimization"""
    
    recommendations = []
    
    # 1. Identify slow-moving items in fast-moving areas
    fast_areas = await db.quants.find({"storage_type": {"$in": ["PICK", "STAGE_OUT"]}}, {"_id": 0}).to_list(1000)
    
    for quant in fast_areas:
        # Check if material has recent movements
        recent_movements = await db.stock_movements.find({
            "material_code": quant["material_code"],
            "created_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()}
        }).to_list(10)
        
        if len(recent_movements) == 0:
            recommendations.append({
                "type": "RELOCATE_SLOW_MOVER",
                "priority": "MEDIUM",
                "material_code": quant["material_code"],
                "current_bin": quant["bin_code"],
                "current_storage_type": quant["storage_type"],
                "recommended_storage_type": "BULK",
                "reason": "No movement in 30 days, move to bulk storage"
            })
    
    # 2. Identify over-utilized bins
    bins = await db.bins.find({}, {"_id": 0}).to_list(1000)
    for bin_doc in bins:
        quants_in_bin = await db.quants.find({"bin_code": bin_doc["bin_code"]}, {"_id": 0}).to_list(100)
        total_qty = sum(q.get("quantity", 0) for q in quants_in_bin)
        
        if total_qty > bin_doc.get("capacity", 1000):
            recommendations.append({
                "type": "BIN_OVER_CAPACITY",
                "priority": "HIGH",
                "bin_code": bin_doc["bin_code"],
                "capacity": bin_doc.get("capacity"),
                "current_stock": total_qty,
                "excess": total_qty - bin_doc.get("capacity", 1000),
                "reason": "Bin over capacity, split stock"
            })
    
    # 3. Consolidation opportunities
    materials = await db.quants.aggregate([
        {"$group": {
            "_id": "$material_code",
            "bin_count": {"$sum": 1},
            "bins": {"$push": "$bin_code"}
        }},
        {"$match": {"bin_count": {"$gt": 3}}}
    ]).to_list(100)
    
    for mat in materials:
        recommendations.append({
            "type": "CONSOLIDATION",
            "priority": "LOW",
            "material_code": mat["_id"],
            "current_bins": mat["bin_count"],
            "bins": mat["bins"][:5],  # Show first 5
            "reason": f"Material scattered across {mat['bin_count']} bins, consider consolidation"
        })
    
    return {
        "total_recommendations": len(recommendations),
        "by_priority": {
            "HIGH": len([r for r in recommendations if r["priority"] == "HIGH"]),
            "MEDIUM": len([r for r in recommendations if r["priority"] == "MEDIUM"]),
            "LOW": len([r for r in recommendations if r["priority"] == "LOW"])
        },
        "recommendations": recommendations
    }

# ===================== DASHBOARD METRICS =====================

@wm_phase3_router.get("/dashboard/metrics")
async def get_wm_dashboard_metrics():
    """Get comprehensive WM dashboard metrics"""
    
    # Quants by category
    quants_total = await db.quants.count_documents({})
    quants_by_cat = {}
    for cat in ["UNRES", "QINSP", "BLOCK", "RETRN"]:
        quants_by_cat[cat] = await db.quants.count_documents({"stock_category": cat})
    
    # Transfer Orders
    to_open = await db.transfer_orders.count_documents({"status": "OPEN"})
    to_in_process = await db.transfer_orders.count_documents({"status": "IN_PROCESS"})
    to_confirmed = await db.transfer_orders.count_documents({"status": "CONFIRMED"})
    
    # Physical Inventory
    pi_active = await db.physical_inventory.count_documents({"status": {"$in": ["FROZEN", "CREATED"]}})
    
    # Expiry alerts
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    expired = await db.quants.count_documents({
        "shelf_life_expiry_date": {"$lt": today, "$ne": None}
    })
    expiring_30 = await db.quants.count_documents({
        "shelf_life_expiry_date": {
            "$gte": today,
            "$lte": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
        }
    })
    
    # Bin utilization
    total_bins = await db.bins.count_documents({})
    empty_bins = await db.bins.count_documents({"status": "empty"})
    blocked_bins = await db.bin_blocks.count_documents({"is_active": True})
    
    # Storage units
    total_pallets = await db.storage_units.count_documents({})
    active_pallets = await db.storage_units.count_documents({"status": "ACTIVE"})
    
    return {
        "quants": {
            "total": quants_total,
            "by_category": quants_by_cat
        },
        "transfer_orders": {
            "open": to_open,
            "in_process": to_in_process,
            "confirmed": to_confirmed,
            "total": to_open + to_in_process + to_confirmed
        },
        "physical_inventory": {
            "active": pi_active
        },
        "expiry_alerts": {
            "expired": expired,
            "expiring_30_days": expiring_30
        },
        "bins": {
            "total": total_bins,
            "empty": empty_bins,
            "occupied": total_bins - empty_bins,
            "blocked": blocked_bins,
            "utilization_pct": round(((total_bins - empty_bins) / total_bins * 100), 2) if total_bins > 0 else 0
        },
        "storage_units": {
            "total": total_pallets,
            "active": active_pallets
        }
    }
