"""
SAP WM Enhanced Models for Solar Manufacturing WMS
Core enterprise warehouse management features
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime

# ===================== STOCK CATEGORIES (SAP WM) =====================

# Stock categories as per SAP WM
STOCK_CATEGORIES = {
    "UNRES": "Unrestricted Use",  # Available for use
    "QINSP": "Quality Inspection",  # In QA
    "BLOCK": "Blocked",  # Blocked stock
    "RETRN": "Returns"  # Returns stock
}

STOCK_CATEGORY_CODES = ["UNRES", "QINSP", "BLOCK", "RETRN"]

# ===================== STORAGE TYPES =====================

STORAGE_TYPES = {
    "BULK": {"name": "Bulk Storage", "put_away_strategy": "next_empty", "picking_strategy": "fifo"},
    "RACK": {"name": "Rack Storage", "put_away_strategy": "open_storage", "picking_strategy": "fifo"},
    "PICK": {"name": "Picking Area", "put_away_strategy": "fixed_bin", "picking_strategy": "lifo"},
    "STGE": {"name": "High Bay Storage", "put_away_strategy": "next_empty", "picking_strategy": "fifo"},
    "QUAR": {"name": "Quarantine Area", "put_away_strategy": "fixed_bin", "picking_strategy": "fifo"},
    "INTERIM": {"name": "Interim Storage", "put_away_strategy": "fixed_bin", "picking_strategy": "lifo"}
}

PUTAWAY_STRATEGIES = ["next_empty", "open_storage", "fixed_bin", "addition_to_stock"]
PICKING_STRATEGIES = ["fifo", "lifo", "fefo", "fixed_bin", "partial_pallet"]

# ===================== QUANT MODEL =====================

class Quant(BaseModel):
    """
    Quant = Quantity at bin level (SAP WM concept)
    Tracks exact quantity, batch, SLED, stock category per bin
    """
    model_config = ConfigDict(extra="ignore")
    
    quant_id: str
    material_id: str
    material_code: str
    bin_id: str
    bin_code: str
    warehouse_number: str = "W001"  # Warehouse
    storage_type: str  # BULK, RACK, PICK, etc.
    
    # Quantity tracking
    quantity: float
    uom: str
    
    # Stock category
    stock_category: Literal["UNRES", "QINSP", "BLOCK", "RETRN"] = "UNRES"
    
    # Batch & SLED
    batch_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    shelf_life_expiry_date: Optional[str] = None  # SLED
    
    # Receipt details
    gr_date: Optional[datetime] = None  # Goods Receipt date
    vendor_batch: Optional[str] = None
    
    # Reference documents
    grn_id: Optional[str] = None
    grn_number: Optional[str] = None
    
    # Storage unit (pallet)
    storage_unit_id: Optional[str] = None
    pallet_number: Optional[str] = None
    
    # Status
    is_blocked: bool = False
    blocked_reason: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    created_by: str
    last_changed_at: Optional[datetime] = None
    last_changed_by: Optional[str] = None

# ===================== TRANSFER REQUIREMENT (TR) =====================

class TransferRequirement(BaseModel):
    """
    Transfer Requirement = Planning layer before Transfer Order
    Auto-generated from GR/GI or created manually
    """
    model_config = ConfigDict(extra="ignore")
    
    tr_number: str
    tr_type: Literal["GR", "GI", "STOCK_TRANSFER", "MANUAL"]
    
    # Material details
    material_id: str
    material_code: str
    material_name: str
    
    # Quantity
    required_quantity: float
    open_quantity: float  # Not yet processed
    uom: str
    
    # Source/Destination
    source_location: Optional[str] = None  # For GI
    destination_bin: Optional[str] = None  # For GR
    storage_type: Optional[str] = None
    
    # Stock category
    stock_category: str = "UNRES"
    
    # Reference
    reference_doc_type: Optional[str] = None  # GRN, Delivery, etc.
    reference_doc_number: Optional[str] = None
    
    # Priority
    priority: int = 5  # 1=highest, 9=lowest
    
    # Status
    status: Literal["OPEN", "IN_PROCESS", "COMPLETED", "CANCELLED"] = "OPEN"
    
    # Timestamps
    created_at: datetime
    created_by: str
    completed_at: Optional[datetime] = None

# ===================== TRANSFER ORDER (TO) =====================

class TransferOrderItem(BaseModel):
    """Individual item in a Transfer Order"""
    model_config = ConfigDict(extra="ignore")
    
    item_number: int
    material_id: str
    material_code: str
    material_name: str
    
    # Quantity
    target_quantity: float
    confirmed_quantity: float = 0
    difference_quantity: float = 0
    uom: str
    
    # Batch & SLED
    batch_number: Optional[str] = None
    shelf_life_expiry_date: Optional[str] = None
    
    # Source & Destination
    source_bin_id: Optional[str] = None
    source_bin_code: Optional[str] = None
    source_quant_id: Optional[str] = None
    
    destination_bin_id: str
    destination_bin_code: str
    
    # Stock category
    stock_category: str = "UNRES"
    
    # Storage unit
    storage_unit_id: Optional[str] = None
    
    # Status per item
    item_status: Literal["OPEN", "IN_PROCESS", "CONFIRMED", "CANCELLED"] = "OPEN"

class TransferOrder(BaseModel):
    """
    Transfer Order (TO) = Execution document for warehouse movements
    3-step process: Create → Execute → Confirm
    """
    model_config = ConfigDict(extra="ignore")
    
    to_number: str
    to_type: Literal["PUTAWAY", "PICKING", "STOCK_TRANSFER", "REPLENISHMENT"]
    
    warehouse_number: str = "W001"
    storage_type: Optional[str] = None
    
    # Items
    items: List[TransferOrderItem]
    
    # Reference
    tr_number: Optional[str] = None  # Link to Transfer Requirement
    reference_doc_type: Optional[str] = None
    reference_doc_number: Optional[str] = None
    
    # Priority
    priority: int = 5
    
    # Status
    status: Literal["OPEN", "IN_PROCESS", "CONFIRMED", "CANCELLED"] = "OPEN"
    
    # Execution details
    assigned_to: Optional[str] = None  # User assigned
    started_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    
    # Difference handling
    has_differences: bool = False
    difference_notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    created_by: str
    last_changed_at: Optional[datetime] = None

# ===================== PHYSICAL INVENTORY =====================

class PhysicalInventoryDocument(BaseModel):
    """
    Physical Inventory Document
    10-step process: Create → Count → Recount → Post differences
    """
    model_config = ConfigDict(extra="ignore")
    
    inventory_doc_number: str
    inventory_type: Literal["FULL", "CYCLE_COUNT", "SPOT_CHECK"]
    
    warehouse_number: str = "W001"
    storage_type: Optional[str] = None
    
    # Scope
    bin_codes: List[str] = []  # Specific bins
    material_codes: List[str] = []  # Specific materials
    
    # Count details
    planned_count_date: Optional[datetime] = None
    first_count_date: Optional[datetime] = None
    recount_date: Optional[datetime] = None
    
    # Status
    status: Literal[
        "CREATED", "FROZEN", "COUNTED", "RECOUNTED", 
        "DIFFERENCES_FOUND", "POSTED", "CANCELLED"
    ] = "CREATED"
    
    # Freeze stock (during count)
    is_stock_frozen: bool = False
    
    # Results
    total_items_counted: int = 0
    items_with_differences: int = 0
    
    # Timestamps
    created_at: datetime
    created_by: str
    posted_at: Optional[datetime] = None

class InventoryCountItem(BaseModel):
    """Individual count record for a bin"""
    model_config = ConfigDict(extra="ignore")
    
    count_item_id: str
    inventory_doc_number: str
    
    # Location
    bin_id: str
    bin_code: str
    quant_id: str
    
    # Material
    material_id: str
    material_code: str
    batch_number: Optional[str] = None
    
    # Book quantity (system)
    book_quantity: float
    
    # Counted quantity
    counted_quantity: Optional[float] = None
    recount_quantity: Optional[float] = None
    
    # Difference
    difference_quantity: float = 0
    
    # Status
    count_status: Literal["PENDING", "COUNTED", "RECOUNTED", "POSTED"] = "PENDING"
    
    # Counter
    counted_by: Optional[str] = None
    counted_at: Optional[datetime] = None
    recounted_by: Optional[str] = None

# ===================== INTERIM STORAGE AREAS =====================

INTERIM_STORAGE_TYPES = [
    "GR_AREA",      # Goods Receipt Area
    "GI_AREA",      # Goods Issue Area
    "QA_AREA",      # Quality Assurance Area
    "DIFF_AREA",    # Differences Area
    "BLOCK_AREA",   # Blocked Stock Area
    "RETRN_AREA",   # Returns Area
    "STAGE_IN",     # Staging Inbound
    "STAGE_OUT",    # Staging Outbound
    "POSTING_CHG",  # Posting Change Zone
    "CROSS_DOCK",   # Cross-docking Area
]

# ===================== STORAGE UNIT (PALLET) =====================

class StorageUnit(BaseModel):
    """
    Storage Unit = Pallet/Container
    1 pallet = 1 bin concept
    """
    model_config = ConfigDict(extra="ignore")
    
    storage_unit_id: str
    storage_unit_number: str  # External pallet number
    storage_unit_type: Literal["EURO_PALLET", "IND_PALLET", "CRATE", "CONTAINER"]
    
    # Current location
    warehouse_number: str = "W001"
    storage_type: Optional[str] = None
    bin_id: Optional[str] = None
    bin_code: Optional[str] = None
    
    # Physical properties
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    max_weight_kg: Optional[float] = None
    
    # Contents
    quant_ids: List[str] = []  # Quants in this pallet
    is_mixed: bool = False  # Mixed materials
    
    # Status
    status: Literal["ACTIVE", "EMPTY", "BLOCKED", "IN_TRANSIT"] = "ACTIVE"
    
    # QR code
    qr_code_url: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    last_movement_at: Optional[datetime] = None

# ===================== BIN BLOCKING =====================

class BinBlock(BaseModel):
    """Bin blocking for put-away/picking"""
    model_config = ConfigDict(extra="ignore")
    
    block_id: str
    bin_id: str
    bin_code: str
    
    block_type: Literal["PUTAWAY", "PICKING", "BOTH"]
    block_reason: str
    
    # Validity
    valid_from: datetime
    valid_to: Optional[datetime] = None
    
    is_active: bool = True
    
    created_at: datetime
    created_by: str

# ===================== WAREHOUSE TRANSFER =====================

class WarehouseTransfer(BaseModel):
    """Cross-warehouse or cross-plant transfer"""
    model_config = ConfigDict(extra="ignore")
    
    transfer_id: str
    transfer_type: Literal["SAME_PLANT", "CROSS_PLANT"]
    
    # Source
    source_warehouse: str
    source_storage_type: Optional[str] = None
    
    # Destination
    destination_warehouse: str
    destination_storage_type: Optional[str] = None
    
    # Material
    material_id: str
    material_code: str
    quantity: float
    uom: str
    
    # Status
    status: Literal["CREATED", "IN_TRANSIT", "RECEIVED", "CANCELLED"] = "CREATED"
    
    # Documents
    source_to_number: Optional[str] = None
    destination_to_number: Optional[str] = None
    
    created_at: datetime
    received_at: Optional[datetime] = None
