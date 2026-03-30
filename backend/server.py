from fastapi import FastAPI, APIRouter, HTTPException, Depends, Response, Request, Query
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import httpx
from io import BytesIO
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from openpyxl import Workbook

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'warehouse-inventory-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="Warehouse Inventory Management System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===================== MODELS =====================

# User roles with permissions
ROLES = ["Admin", "Warehouse Operator", "Store In-Charge", "Inventory Controller", "Auditor", "Management Viewer"]

# Role-based permissions matrix
ROLE_PERMISSIONS = {
    "Admin": {
        "dashboard": True, "materials": "full", "grn": "full", "labels": "full",
        "bins": "full", "putaway": "full", "issues": "full", "reports": True,
        "users": "full", "audit": True, "master_data": True
    },
    "Warehouse Operator": {
        "dashboard": True, "materials": "read", "grn": "full", "labels": "full",
        "bins": "read", "putaway": "full", "issues": "full", "reports": False,
        "users": False, "audit": False, "master_data": False
    },
    "Store In-Charge": {
        "dashboard": True, "materials": "full", "grn": "full", "labels": "full",
        "bins": "full", "putaway": "full", "issues": "full", "reports": True,
        "users": False, "audit": True, "master_data": False  # Can do operations but not master data changes
    },
    "Inventory Controller": {
        "dashboard": True, "materials": "read", "grn": "read", "labels": "read",
        "bins": "read", "putaway": "read", "issues": "read", "reports": True,
        "users": False, "audit": True, "master_data": False
    },
    "Auditor": {
        "dashboard": True, "materials": "read", "grn": "read", "labels": "read",
        "bins": "read", "putaway": "read", "issues": "read", "reports": True,
        "users": "read", "audit": True, "master_data": False
    },
    "Management Viewer": {
        "dashboard": True, "materials": False, "grn": False, "labels": False,
        "bins": False, "putaway": False, "issues": False, "reports": True,
        "users": False, "audit": False, "master_data": False
    }
}

# Stock statuses
STOCK_STATUSES = ["available", "blocked", "quality_hold"]

# Bin statuses
BIN_STATUSES = ["available", "blocked", "quality_hold", "empty"]

# Audit action types
AUDIT_ACTIONS = ["create", "update", "delete", "complete", "cancel", "override", "login", "logout", "role_change", "status_change"]

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str = Field(..., description="One of: Admin, Warehouse Operator, Store In-Charge, Inventory Controller, Auditor, Management Viewer")

class UserCreate(UserBase):
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    picture: Optional[str] = None
    auth_type: str = "local"  # local or google
    created_at: datetime
    is_active: bool = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# Material Models
class MaterialBase(BaseModel):
    material_code: str
    name: str
    description: Optional[str] = None
    category: str
    uom: str  # Unit of Measure
    stock_method: Literal["FIFO", "LIFO"] = "FIFO"
    min_stock_level: int = 0
    max_stock_level: int = 1000
    reorder_point: int = 100

class MaterialCreate(MaterialBase):
    pass

class Material(MaterialBase):
    model_config = ConfigDict(extra="ignore")
    material_id: str
    current_stock: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: str

# GRN Models - Enhanced with full details
QUALITY_INSPECTION_STATUS = ["pending", "passed", "failed", "partial"]
STORAGE_CONDITIONS = ["ambient", "cold_storage", "frozen", "controlled_temperature", "humidity_controlled", "hazardous"]

class GRNItemCreate(BaseModel):
    material_id: str
    received_quantity: int
    accepted_quantity: int = 0
    rejected_quantity: int = 0
    batch_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quality_inspection_status: Literal["pending", "passed", "failed", "partial"] = "pending"
    storage_condition: Optional[str] = None
    bin_location: Optional[str] = None
    rejection_reason: Optional[str] = None

class GRNItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    item_id: Optional[str] = None
    material_id: str
    material_code: str
    material_name: str
    # Support old 'quantity' field as fallback for received_quantity
    quantity: Optional[int] = None  # Legacy field
    received_quantity: Optional[int] = None
    accepted_quantity: int = 0
    rejected_quantity: int = 0
    pending_quantity: int = 0
    batch_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quality_inspection_status: str = "pending"
    storage_condition: Optional[str] = None
    bin_location: Optional[str] = None
    rejection_reason: Optional[str] = None
    is_partial: bool = False
    
    def model_post_init(self, __context):
        # Migrate old quantity field to received_quantity
        if self.received_quantity is None and self.quantity is not None:
            object.__setattr__(self, 'received_quantity', self.quantity)
        elif self.received_quantity is None:
            object.__setattr__(self, 'received_quantity', 0)

class GRNCreate(BaseModel):
    vendor_name: str
    po_number: Optional[str] = None
    invoice_number: Optional[str] = None
    items: List[GRNItemCreate]
    remarks: Optional[str] = None
    receipt_date: Optional[str] = None  # If not provided, uses current datetime

class GRNUpdateItem(BaseModel):
    item_id: str
    accepted_quantity: int
    rejected_quantity: int
    quality_inspection_status: Literal["pending", "passed", "failed", "partial"]
    rejection_reason: Optional[str] = None
    bin_location: Optional[str] = None

class GRN(BaseModel):
    model_config = ConfigDict(extra="ignore")
    grn_id: str
    grn_number: str
    # Support both vendor_name and old supplier_name
    vendor_name: Optional[str] = None
    supplier_name: Optional[str] = None  # Legacy field
    po_number: Optional[str] = None
    invoice_number: Optional[str] = None
    items: List[GRNItem]
    # Support old total_quantity field
    total_quantity: Optional[int] = None  # Legacy field
    total_received_quantity: Optional[int] = None
    total_accepted_quantity: int = 0
    total_rejected_quantity: int = 0
    total_pending_quantity: int = 0
    status: str = "pending"  # Changed from Literal to allow any status
    remarks: Optional[str] = None
    receipt_date: Optional[datetime] = None
    created_at: datetime
    created_by: str
    receiving_user_name: Optional[str] = None
    completed_at: Optional[datetime] = None
    has_partial_receipts: bool = False
    
    def model_post_init(self, __context):
        # Migrate old fields
        if self.vendor_name is None and self.supplier_name is not None:
            object.__setattr__(self, 'vendor_name', self.supplier_name)
        if self.total_received_quantity is None and self.total_quantity is not None:
            object.__setattr__(self, 'total_received_quantity', self.total_quantity)
        elif self.total_received_quantity is None:
            object.__setattr__(self, 'total_received_quantity', 0)
        if self.receipt_date is None:
            object.__setattr__(self, 'receipt_date', self.created_at)
        if self.receiving_user_name is None:
            object.__setattr__(self, 'receiving_user_name', 'Unknown')

# Bin Location Models
class BinLocationBase(BaseModel):
    bin_code: str
    zone: str
    aisle: str
    rack: str
    level: str
    capacity: int = 100
    bin_type: Literal["storage", "picking", "staging", "quarantine"] = "storage"

class BinLocationCreate(BinLocationBase):
    pass

class BinLocation(BinLocationBase):
    model_config = ConfigDict(extra="ignore")
    bin_id: str
    current_stock: int = 0
    status: str = "empty"  # empty, available, blocked, quality_hold
    material_id: Optional[str] = None
    material_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Stock Movement Models
class StockMovement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    movement_id: str
    movement_type: Literal["inward", "outward", "transfer", "adjustment"]
    material_id: str
    material_code: str
    quantity: int
    from_bin: Optional[str] = None
    to_bin: Optional[str] = None
    reference_type: Optional[str] = None  # GRN, Issue, Transfer
    reference_id: Optional[str] = None
    batch_number: Optional[str] = None
    created_at: datetime
    created_by: str
    remarks: Optional[str] = None

# Putaway Models
class PutawayCreate(BaseModel):
    grn_id: str
    material_id: str
    quantity: int
    bin_id: str

class Putaway(BaseModel):
    model_config = ConfigDict(extra="ignore")
    putaway_id: str
    grn_id: str
    material_id: str
    material_code: str
    quantity: int
    bin_id: str
    bin_code: str
    status: Literal["pending", "completed"] = "pending"
    created_at: datetime
    completed_at: Optional[datetime] = None
    created_by: str

# Material Issue Models
class MaterialIssueItem(BaseModel):
    material_id: str
    material_code: str
    material_name: str
    quantity: int
    from_bin: Optional[str] = None

class MaterialIssueCreate(BaseModel):
    department: str
    requisition_number: Optional[str] = None
    items: List[MaterialIssueItem]
    remarks: Optional[str] = None

class MaterialIssue(BaseModel):
    model_config = ConfigDict(extra="ignore")
    issue_id: str
    issue_number: str
    department: str
    requisition_number: Optional[str] = None
    items: List[MaterialIssueItem]
    total_quantity: int
    status: Literal["pending", "completed", "cancelled"] = "pending"
    remarks: Optional[str] = None
    created_at: datetime
    created_by: str
    completed_at: Optional[datetime] = None

# Label Models - Enhanced with print logging
class LabelCreate(BaseModel):
    material_id: str
    grn_id: Optional[str] = None
    grn_item_id: Optional[str] = None  # Link to specific GRN item
    batch_number: Optional[str] = None
    quantity: int
    uom: Optional[str] = None
    bin_location: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    storage_condition: Optional[str] = None

class Label(BaseModel):
    model_config = ConfigDict(extra="ignore")
    label_id: str
    material_id: str
    material_code: str
    material_name: str
    material_description: Optional[str] = None
    grn_id: Optional[str] = None
    grn_number: Optional[str] = None
    grn_item_id: Optional[str] = None
    batch_number: Optional[str] = None
    quantity: int
    uom: str = "PCS"
    bin_location: Optional[str] = None
    date_of_receipt: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    storage_condition: Optional[str] = None
    qr_data: str
    barcode_data: str
    created_at: datetime
    created_by: str
    created_by_name: str = "Unknown"
    print_count: int = 0
    last_printed_at: Optional[datetime] = None
    last_printed_by: Optional[str] = None

class PrintLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    log_id: str
    label_id: str
    label_ids: Optional[List[str]] = None  # For bulk prints
    action: str  # "print" or "reprint"
    reason: Optional[str] = None  # Required for reprint
    printed_at: datetime
    printed_by: str
    printed_by_name: str
    quantity_printed: int = 1  # Number of copies

class ReprintRequest(BaseModel):
    label_id: str
    reason: str  # Mandatory reason for reprint
    copies: int = 1

class BulkPrintRequest(BaseModel):
    label_ids: List[str]
    copies: int = 1

# ===================== AUTHENTICATION =====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str, role: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    # Check cookie first, then Authorization header, then query param (for file downloads)
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    # Check query param for file downloads
    if not token:
        token = request.query_params.get("token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if it's a session token (Google OAuth) or JWT
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if session:
        # Validate session expiry
        expires_at = session.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired")
        
        user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
        if user:
            return user
    
    # Try JWT token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
        if user:
            return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        pass
    
    raise HTTPException(status_code=401, detail="Invalid token")

# Role-based access decorator helper
def require_roles(allowed_roles: List[str]):
    async def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

# Get user from query token (for file downloads)
async def get_user_from_token(token: Optional[str] = Query(None)):
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
        if user:
            return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        pass
    
    raise HTTPException(status_code=401, detail="Invalid token")

# Master data restriction - only Admin can modify
def require_master_data_access():
    async def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] != "Admin":
            raise HTTPException(status_code=403, detail="Only Admin can modify master data")
        return user
    return role_checker

# ===================== AUDIT TRAIL =====================

class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    audit_id: str
    action: str  # create, update, delete, complete, cancel, override, login, logout, role_change, status_change
    entity_type: str  # material, grn, bin, putaway, issue, label, user
    entity_id: str
    entity_name: Optional[str] = None
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    reason: Optional[str] = None
    performed_by: str  # user_id
    performed_by_name: str
    performed_by_role: str
    ip_address: Optional[str] = None
    timestamp: datetime

async def create_audit_log(
    action: str,
    entity_type: str,
    entity_id: str,
    user: dict,
    entity_name: Optional[str] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    reason: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """Create an audit trail entry"""
    audit_doc = {
        "audit_id": f"aud_{uuid.uuid4().hex[:12]}",
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "old_values": old_values,
        "new_values": new_values,
        "reason": reason,
        "performed_by": user["user_id"],
        "performed_by_name": user.get("name", "Unknown"),
        "performed_by_role": user.get("role", "Unknown"),
        "ip_address": ip_address,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(audit_doc)
    return audit_doc

# ===================== AUTH ENDPOINTS =====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if email exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if user_data.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {ROLES}")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    hashed_pw = hash_password(user_data.password)
    
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "role": user_data.role,
        "password": hashed_pw,
        "auth_type": "local",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_jwt_token(user_id, user_data.email, user_data.role)
    user_response = {k: v for k, v in user_doc.items() if k != "password"}
    
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, response: Response):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user.get("auth_type") == "google":
        raise HTTPException(status_code=400, detail="Please use Google login for this account")
    
    if not verify_password(credentials.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user["user_id"], user["email"], user["role"])
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=JWT_EXPIRATION_HOURS * 3600
    )
    
    user_response = {k: v for k, v in user.items() if k != "password"}
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/session")
async def process_google_session(request: Request, response: Response):
    """Process Google OAuth session_id from Emergent Auth"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Call Emergent Auth to get session data
    async with httpx.AsyncClient() as client:
        try:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            session_data = auth_response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Auth service unavailable")
    
    email = session_data.get("email")
    name = session_data.get("name")
    picture = session_data.get("picture")
    session_token = session_data.get("session_token")
    
    # Check if user exists
    user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if not user:
        # Create new user with default role
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "role": "Warehouse Operator",  # Default role for new Google users
            "auth_type": "google",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
    else:
        user_id = user["user_id"]
        # Update picture if changed
        if picture and picture != user.get("picture"):
            await db.users.update_one({"user_id": user_id}, {"$set": {"picture": picture}})
    
    # Store session
    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 3600
    )
    
    user_response = {k: v for k, v in user.items() if k not in ["password", "_id"]}
    return {"user": user_response}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {k: v for k, v in user.items() if k != "password"}

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    
    response.delete_cookie(key="session_token", path="/", secure=True, samesite="none")
    return {"message": "Logged out successfully"}

# ===================== USER MANAGEMENT =====================

@api_router.get("/users", response_model=List[User])
async def get_users(user: dict = Depends(require_roles(["Admin", "Auditor"]))):
    """Get all users - Admin (full) and Auditor (read-only)"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users

@api_router.post("/users", response_model=User)
async def create_user(user_data: UserCreate, request: Request, user: dict = Depends(require_roles(["Admin"]))):
    """Create a new user - Admin only"""
    # Check if email exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if user_data.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {ROLES}")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    hashed_pw = hash_password(user_data.password)
    
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "role": user_data.role,
        "password": hashed_pw,
        "auth_type": "local",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["user_id"]
    }
    
    await db.users.insert_one(user_doc)
    
    # Audit log
    await create_audit_log(
        action="create",
        entity_type="user",
        entity_id=user_id,
        entity_name=user_data.name,
        user=user,
        new_values={"email": user_data.email, "name": user_data.name, "role": user_data.role},
        ip_address=request.client.host if request.client else None
    )
    
    user_response = {k: v for k, v in user_doc.items() if k != "password"}
    return User(**user_response)

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, name: str = None, email: str = None, request: Request = None, user: dict = Depends(require_roles(["Admin"]))):
    """Update user details - Admin only"""
    existing = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {}
    old_values = {}
    
    if name:
        old_values["name"] = existing.get("name")
        update_data["name"] = name
    if email:
        # Check if email conflicts
        if email != existing["email"]:
            conflict = await db.users.find_one({"email": email, "user_id": {"$ne": user_id}})
            if conflict:
                raise HTTPException(status_code=400, detail="Email already exists")
        old_values["email"] = existing.get("email")
        update_data["email"] = email
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.users.update_one({"user_id": user_id}, {"$set": update_data})
        
        # Audit log
        await create_audit_log(
            action="update",
            entity_type="user",
            entity_id=user_id,
            entity_name=existing.get("name"),
            user=user,
            old_values=old_values,
            new_values={k: v for k, v in update_data.items() if k != "updated_at"},
            ip_address=request.client.host if request and request.client else None
        )
    
    return {"message": "User updated successfully"}

@api_router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, request: Request, user: dict = Depends(require_roles(["Admin"]))):
    """Update user role - Admin only"""
    if role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {ROLES}")
    
    existing = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_role = existing.get("role")
    
    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"role": role, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Audit log
    await create_audit_log(
        action="role_change",
        entity_type="user",
        entity_id=user_id,
        entity_name=existing.get("name"),
        user=user,
        old_values={"role": old_role},
        new_values={"role": role},
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": "Role updated successfully"}

@api_router.put("/users/{user_id}/status")
async def toggle_user_status(user_id: str, request: Request, user: dict = Depends(require_roles(["Admin"]))):
    """Toggle user active status - Admin only"""
    existing = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_status = existing.get("is_active", True)
    new_status = not old_status
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_active": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Audit log
    await create_audit_log(
        action="status_change",
        entity_type="user",
        entity_id=user_id,
        entity_name=existing.get("name"),
        user=user,
        old_values={"is_active": old_status},
        new_values={"is_active": new_status},
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": f"User {'activated' if new_status else 'deactivated'} successfully"}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, request: Request, user: dict = Depends(require_roles(["Admin"]))):
    """Delete user - Admin only"""
    existing = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Cannot delete self
    if user_id == user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    await db.users.delete_one({"user_id": user_id})
    
    # Audit log
    await create_audit_log(
        action="delete",
        entity_type="user",
        entity_id=user_id,
        entity_name=existing.get("name"),
        user=user,
        old_values={"email": existing.get("email"), "name": existing.get("name"), "role": existing.get("role")},
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": "User deleted successfully"}

@api_router.get("/users/roles")
async def get_roles(user: dict = Depends(get_current_user)):
    """Get list of available roles"""
    return {"roles": ROLES, "permissions": ROLE_PERMISSIONS}

# ===================== AUDIT TRAIL =====================

@api_router.get("/audit-logs")
async def get_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    performed_by: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    skip: int = Query(default=0, ge=0),
    user: dict = Depends(require_roles(["Admin", "Auditor", "Store In-Charge", "Inventory Controller"]))
):
    """Get audit logs with optional filters"""
    query = {}
    
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id
    if action:
        query["action"] = action
    if performed_by:
        query["performed_by"] = performed_by
    if start_date:
        query["timestamp"] = {"$gte": start_date}
    if end_date:
        if "timestamp" in query:
            query["timestamp"]["$lte"] = end_date
        else:
            query["timestamp"] = {"$lte": end_date}
    
    total = await db.audit_logs.count_documents(query)
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    return {"total": total, "logs": logs}

@api_router.get("/audit-logs/entity/{entity_type}/{entity_id}")
async def get_entity_audit_history(
    entity_type: str,
    entity_id: str,
    user: dict = Depends(require_roles(["Admin", "Auditor", "Store In-Charge", "Inventory Controller"]))
):
    """Get complete audit history for a specific entity"""
    logs = await db.audit_logs.find(
        {"entity_type": entity_type, "entity_id": entity_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(1000)
    return logs

@api_router.get("/audit-logs/summary")
async def get_audit_summary(
    days: int = Query(default=7, le=30),
    user: dict = Depends(require_roles(["Admin", "Auditor"]))
):
    """Get audit summary statistics"""
    from_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    pipeline = [
        {"$match": {"timestamp": {"$gte": from_date}}},
        {"$group": {
            "_id": {"action": "$action", "entity_type": "$entity_type"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    
    stats = await db.audit_logs.aggregate(pipeline).to_list(100)
    
    # Recent activities
    recent = await db.audit_logs.find(
        {"timestamp": {"$gte": from_date}},
        {"_id": 0}
    ).sort("timestamp", -1).limit(20).to_list(20)
    
    # Top users by activity
    user_pipeline = [
        {"$match": {"timestamp": {"$gte": from_date}}},
        {"$group": {
            "_id": {"user_id": "$performed_by", "user_name": "$performed_by_name"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_users = await db.audit_logs.aggregate(user_pipeline).to_list(10)
    
    return {
        "period_days": days,
        "action_stats": stats,
        "recent_activities": recent,
        "top_users": top_users
    }

# ===================== MATERIAL MASTER =====================

@api_router.post("/materials", response_model=Material)
async def create_material(material: MaterialCreate, request: Request, user: dict = Depends(require_roles(["Admin"]))):
    """Create new material - Admin only (master data)"""
    # Check if material code exists
    existing = await db.materials.find_one({"material_code": material.material_code})
    if existing:
        raise HTTPException(status_code=400, detail="Material code already exists")
    
    material_id = f"mat_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    material_doc = {
        "material_id": material_id,
        **material.model_dump(),
        "current_stock": 0,
        "created_at": now,
        "updated_at": now,
        "created_by": user["user_id"]
    }
    
    await db.materials.insert_one(material_doc)
    
    # Audit log
    await create_audit_log(
        action="create",
        entity_type="material",
        entity_id=material_id,
        entity_name=f"{material.material_code} - {material.name}",
        user=user,
        new_values=material.model_dump(),
        ip_address=request.client.host if request.client else None
    )
    
    return Material(**material_doc)

@api_router.get("/materials", response_model=List[Material])
async def get_materials(
    category: Optional[str] = None,
    search: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"material_code": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}}
        ]
    
    materials = await db.materials.find(query, {"_id": 0}).to_list(1000)
    return materials

@api_router.get("/materials/{material_id}", response_model=Material)
async def get_material(material_id: str, user: dict = Depends(get_current_user)):
    material = await db.materials.find_one({"material_id": material_id}, {"_id": 0})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return Material(**material)

@api_router.put("/materials/{material_id}", response_model=Material)
async def update_material(material_id: str, material: MaterialCreate, request: Request, user: dict = Depends(require_roles(["Admin"]))):
    """Update material - Admin only (master data)"""
    existing = await db.materials.find_one({"material_id": material_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Check if new code conflicts with another material
    if material.material_code != existing["material_code"]:
        conflict = await db.materials.find_one({"material_code": material.material_code, "material_id": {"$ne": material_id}})
        if conflict:
            raise HTTPException(status_code=400, detail="Material code already exists")
    
    # Store old values for audit
    old_values = {k: v for k, v in existing.items() if k not in ["_id", "material_id", "created_at", "created_by", "current_stock"]}
    
    update_doc = {
        **material.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.materials.update_one({"material_id": material_id}, {"$set": update_doc})
    
    # Audit log
    await create_audit_log(
        action="update",
        entity_type="material",
        entity_id=material_id,
        entity_name=f"{material.material_code} - {material.name}",
        user=user,
        old_values=old_values,
        new_values=material.model_dump(),
        ip_address=request.client.host if request.client else None
    )
    
    updated = await db.materials.find_one({"material_id": material_id}, {"_id": 0})
    return Material(**updated)

@api_router.delete("/materials/{material_id}")
async def delete_material(material_id: str, request: Request, user: dict = Depends(require_roles(["Admin"]))):
    """Delete material - Admin only (master data)"""
    # Check if material has stock
    material = await db.materials.find_one({"material_id": material_id}, {"_id": 0})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    if material.get("current_stock", 0) > 0:
        raise HTTPException(status_code=400, detail="Cannot delete material with existing stock")
    
    await db.materials.delete_one({"material_id": material_id})
    
    # Audit log
    await create_audit_log(
        action="delete",
        entity_type="material",
        entity_id=material_id,
        entity_name=f"{material.get('material_code')} - {material.get('name')}",
        user=user,
        old_values={k: v for k, v in material.items() if k not in ["_id"]},
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": "Material deleted successfully"}

@api_router.get("/materials/categories/list")
async def get_material_categories(user: dict = Depends(get_current_user)):
    categories = await db.materials.distinct("category")
    return categories

# ===================== GRN (GOODS RECEIPT NOTE) - Enhanced =====================

@api_router.post("/grn", response_model=GRN)
async def create_grn(grn: GRNCreate, user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Warehouse Operator"]))):
    grn_id = f"grn_{uuid.uuid4().hex[:12]}"
    grn_number = f"GRN-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.now(timezone.utc)
    
    # Process items and validate materials
    processed_items = []
    total_received = 0
    total_accepted = 0
    total_rejected = 0
    
    for item in grn.items:
        material = await db.materials.find_one({"material_id": item.material_id}, {"_id": 0})
        if not material:
            raise HTTPException(status_code=404, detail=f"Material {item.material_id} not found")
        
        item_id = f"item_{uuid.uuid4().hex[:8]}"
        pending_qty = item.received_quantity - item.accepted_quantity - item.rejected_quantity
        
        processed_item = {
            "item_id": item_id,
            "material_id": item.material_id,
            "material_code": material["material_code"],
            "material_name": material["name"],
            "received_quantity": item.received_quantity,
            "accepted_quantity": item.accepted_quantity,
            "rejected_quantity": item.rejected_quantity,
            "pending_quantity": pending_qty,
            "batch_number": item.batch_number or f"BTH-{now.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}",
            "manufacturing_date": item.manufacturing_date,
            "expiry_date": item.expiry_date,
            "quality_inspection_status": item.quality_inspection_status,
            "storage_condition": item.storage_condition,
            "bin_location": item.bin_location,
            "rejection_reason": item.rejection_reason,
            "is_partial": pending_qty > 0
        }
        processed_items.append(processed_item)
        
        total_received += item.received_quantity
        total_accepted += item.accepted_quantity
        total_rejected += item.rejected_quantity
    
    total_pending = total_received - total_accepted - total_rejected
    receipt_date = grn.receipt_date or now.isoformat()
    
    grn_doc = {
        "grn_id": grn_id,
        "grn_number": grn_number,
        "vendor_name": grn.vendor_name,
        "po_number": grn.po_number,
        "invoice_number": grn.invoice_number,
        "items": processed_items,
        "total_received_quantity": total_received,
        "total_accepted_quantity": total_accepted,
        "total_rejected_quantity": total_rejected,
        "total_pending_quantity": total_pending,
        "status": "pending" if total_pending > 0 else ("partial" if total_rejected > 0 else "pending"),
        "remarks": grn.remarks,
        "receipt_date": receipt_date,
        "created_at": now.isoformat(),
        "created_by": user["user_id"],
        "receiving_user_name": user["name"],
        "has_partial_receipts": total_pending > 0
    }
    
    await db.grn.insert_one(grn_doc)
    
    # Auto-generate labels for each GRN item
    for item in processed_items:
        material = await db.materials.find_one({"material_id": item["material_id"]}, {"_id": 0})
        
        label_id = f"lbl_{uuid.uuid4().hex[:12]}"
        
        # Use JSON format for QR code - universally scannable
        import json as json_lib
        qr_json = {
            "type": "WMS_LABEL",
            "material": item['material_code'],
            "grn": grn_number,
            "batch": item['batch_number'],
            "qty": item['received_quantity'],
            "uom": material.get("uom", "PCS"),
            "bin": item.get('bin_location') or "",
            "expiry": item.get('expiry_date') or ""
        }
        qr_data = json_lib.dumps(qr_json, separators=(',', ':'))
        barcode_data = f"{item['material_code']}-{item['batch_number']}"
        
        label_doc = {
            "label_id": label_id,
            "material_id": item["material_id"],
            "material_code": item["material_code"],
            "material_name": item["material_name"],
            "material_description": material.get("description", ""),
            "grn_id": grn_id,
            "grn_number": grn_number,
            "grn_item_id": item["item_id"],
            "batch_number": item["batch_number"],
            "quantity": item["received_quantity"],
            "uom": material.get("uom", "PCS"),
            "bin_location": item.get("bin_location"),
            "date_of_receipt": receipt_date,
            "manufacturing_date": item.get("manufacturing_date"),
            "expiry_date": item.get("expiry_date"),
            "storage_condition": item.get("storage_condition"),
            "qr_data": qr_data,
            "barcode_data": barcode_data,
            "created_at": now.isoformat(),
            "created_by": user["user_id"],
            "created_by_name": user["name"],
            "print_count": 0,
            "last_printed_at": None,
            "last_printed_by": None
        }
        await db.labels.insert_one(label_doc)
    
    return GRN(**grn_doc)

@api_router.get("/grn", response_model=List[GRN])
async def get_grns(
    status: Optional[str] = None,
    vendor_name: Optional[str] = None,
    po_number: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    if vendor_name:
        query["vendor_name"] = {"$regex": vendor_name, "$options": "i"}
    if po_number:
        query["po_number"] = {"$regex": po_number, "$options": "i"}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    
    grns = await db.grn.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return grns

@api_router.get("/grn/{grn_id}", response_model=GRN)
async def get_grn(grn_id: str, user: dict = Depends(get_current_user)):
    grn = await db.grn.find_one({"grn_id": grn_id}, {"_id": 0})
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    return GRN(**grn)

@api_router.put("/grn/{grn_id}/inspect")
async def update_grn_inspection(
    grn_id: str,
    updates: List[GRNUpdateItem],
    user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Inventory Controller"]))
):
    """Update quality inspection status and quantities for GRN items"""
    grn = await db.grn.find_one({"grn_id": grn_id}, {"_id": 0})
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    
    if grn["status"] == "completed":
        raise HTTPException(status_code=400, detail="GRN is already completed")
    
    # Update items
    updated_items = grn["items"]
    total_accepted = 0
    total_rejected = 0
    total_pending = 0
    
    for update in updates:
        for i, item in enumerate(updated_items):
            if item["item_id"] == update.item_id:
                # Validate quantities
                if update.accepted_quantity + update.rejected_quantity > item["received_quantity"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Accepted + Rejected cannot exceed received quantity for item {item['material_code']}"
                    )
                
                updated_items[i]["accepted_quantity"] = update.accepted_quantity
                updated_items[i]["rejected_quantity"] = update.rejected_quantity
                updated_items[i]["pending_quantity"] = item["received_quantity"] - update.accepted_quantity - update.rejected_quantity
                updated_items[i]["quality_inspection_status"] = update.quality_inspection_status
                updated_items[i]["rejection_reason"] = update.rejection_reason
                updated_items[i]["bin_location"] = update.bin_location
                updated_items[i]["is_partial"] = updated_items[i]["pending_quantity"] > 0
                break
    
    # Recalculate totals
    for item in updated_items:
        total_accepted += item["accepted_quantity"]
        total_rejected += item["rejected_quantity"]
        total_pending += item["pending_quantity"]
    
    # Determine status
    total_received = grn["total_received_quantity"]
    if total_pending > 0:
        new_status = "partial"
    elif total_accepted + total_rejected == total_received:
        new_status = "partial" if total_rejected > 0 else "pending"  # Still need to complete
    else:
        new_status = "pending"
    
    await db.grn.update_one(
        {"grn_id": grn_id},
        {"$set": {
            "items": updated_items,
            "total_accepted_quantity": total_accepted,
            "total_rejected_quantity": total_rejected,
            "total_pending_quantity": total_pending,
            "status": new_status,
            "has_partial_receipts": total_pending > 0
        }}
    )
    
    return {"message": "GRN inspection updated successfully", "status": new_status}

@api_router.put("/grn/{grn_id}/complete")
async def complete_grn(grn_id: str, user: dict = Depends(require_roles(["Admin", "Store In-Charge"]))):
    """Complete GRN and update stock for accepted quantities only"""
    grn = await db.grn.find_one({"grn_id": grn_id}, {"_id": 0})
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    
    if grn["status"] == "completed":
        raise HTTPException(status_code=400, detail="GRN is already completed")
    
    # Check if there are pending inspections
    has_pending = any(item.get("quality_inspection_status") == "pending" and item.get("pending_quantity", 0) > 0 for item in grn["items"])
    if has_pending:
        raise HTTPException(status_code=400, detail="Complete quality inspection for all items first")
    
    now = datetime.now(timezone.utc)
    
    # Update stock only for accepted quantities
    for item in grn["items"]:
        accepted_qty = item.get("accepted_quantity", 0)
        if accepted_qty > 0:
            # Update material stock
            await db.materials.update_one(
                {"material_id": item["material_id"]},
                {"$inc": {"current_stock": accepted_qty}}
            )
            
            # Create stock movement for accepted goods
            movement = {
                "movement_id": f"mov_{uuid.uuid4().hex[:12]}",
                "movement_type": "inward",
                "material_id": item["material_id"],
                "material_code": item["material_code"],
                "quantity": accepted_qty,
                "to_bin": item.get("bin_location"),
                "reference_type": "GRN",
                "reference_id": grn_id,
                "batch_number": item.get("batch_number"),
                "remarks": f"GRN: {grn['grn_number']}, Batch: {item.get('batch_number')}, Expiry: {item.get('expiry_date', 'N/A')}",
                "created_at": now.isoformat(),
                "created_by": user["user_id"]
            }
            await db.stock_movements.insert_one(movement)
            
            # Update bin if specified
            if item.get("bin_location"):
                bin_doc = await db.bins.find_one({"bin_code": item["bin_location"]}, {"_id": 0})
                if bin_doc:
                    await db.bins.update_one(
                        {"bin_code": item["bin_location"]},
                        {
                            "$inc": {"current_stock": accepted_qty},
                            "$set": {
                                "status": "available",
                                "material_id": item["material_id"],
                                "material_code": item["material_code"],
                                "updated_at": now.isoformat()
                            }
                        }
                    )
    
    await db.grn.update_one(
        {"grn_id": grn_id},
        {"$set": {"status": "completed", "completed_at": now.isoformat()}}
    )
    
    return {
        "message": "GRN completed successfully",
        "accepted_quantity": grn["total_accepted_quantity"],
        "rejected_quantity": grn["total_rejected_quantity"]
    }

@api_router.get("/grn/by-material/{material_id}")
async def get_grns_by_material(material_id: str, user: dict = Depends(get_current_user)):
    """Get all GRNs containing a specific material"""
    grns = await db.grn.find(
        {"items.material_id": material_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    return grns

@api_router.get("/grn/vendors/list")
async def get_grn_vendors(user: dict = Depends(get_current_user)):
    """Get list of all vendors from GRNs"""
    vendors = await db.grn.distinct("vendor_name")
    return vendors

# ===================== BIN LOCATIONS =====================

@api_router.post("/bins", response_model=BinLocation)
async def create_bin(bin_data: BinLocationCreate, request: Request, user: dict = Depends(require_roles(["Admin"]))):
    """Create new bin location - Admin only (master data)"""
    existing = await db.bins.find_one({"bin_code": bin_data.bin_code})
    if existing:
        raise HTTPException(status_code=400, detail="Bin code already exists")
    
    bin_id = f"bin_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    bin_doc = {
        "bin_id": bin_id,
        **bin_data.model_dump(),
        "current_stock": 0,
        "status": "empty",
        "material_id": None,
        "material_code": None,
        "created_at": now,
        "updated_at": now
    }
    
    await db.bins.insert_one(bin_doc)
    
    # Audit log
    await create_audit_log(
        action="create",
        entity_type="bin",
        entity_id=bin_id,
        entity_name=bin_data.bin_code,
        user=user,
        new_values=bin_data.model_dump(),
        ip_address=request.client.host if request.client else None
    )
    
    return BinLocation(**bin_doc)

@api_router.get("/bins", response_model=List[BinLocation])
async def get_bins(
    zone: Optional[str] = None,
    status: Optional[str] = None,
    bin_type: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if zone:
        query["zone"] = zone
    if status:
        query["status"] = status
    if bin_type:
        query["bin_type"] = bin_type
    
    bins = await db.bins.find(query, {"_id": 0}).to_list(1000)
    return bins

@api_router.get("/bins/{bin_id}", response_model=BinLocation)
async def get_bin(bin_id: str, user: dict = Depends(get_current_user)):
    bin_doc = await db.bins.find_one({"bin_id": bin_id}, {"_id": 0})
    if not bin_doc:
        raise HTTPException(status_code=404, detail="Bin not found")
    return BinLocation(**bin_doc)

@api_router.put("/bins/{bin_id}", response_model=BinLocation)
async def update_bin(bin_id: str, bin_data: BinLocationCreate, request: Request, user: dict = Depends(require_roles(["Admin"]))):
    """Update bin location - Admin only (master data)"""
    existing = await db.bins.find_one({"bin_id": bin_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Bin not found")
    
    # Store old values for audit
    old_values = {k: v for k, v in existing.items() if k not in ["_id", "bin_id", "created_at", "current_stock", "material_id", "material_code"]}
    
    update_doc = {
        **bin_data.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bins.update_one({"bin_id": bin_id}, {"$set": update_doc})
    
    # Audit log
    await create_audit_log(
        action="update",
        entity_type="bin",
        entity_id=bin_id,
        entity_name=bin_data.bin_code,
        user=user,
        old_values=old_values,
        new_values=bin_data.model_dump(),
        ip_address=request.client.host if request.client else None
    )
    
    updated = await db.bins.find_one({"bin_id": bin_id}, {"_id": 0})
    return BinLocation(**updated)

@api_router.put("/bins/{bin_id}/status")
async def update_bin_status(bin_id: str, status: str, request: Request, user: dict = Depends(require_roles(["Admin", "Store In-Charge"]))):
    """Update bin status - Admin and Store In-Charge only"""
    if status not in BIN_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {BIN_STATUSES}")
    
    bin_doc = await db.bins.find_one({"bin_id": bin_id}, {"_id": 0})
    if not bin_doc:
        raise HTTPException(status_code=404, detail="Bin not found")
    
    old_status = bin_doc.get("status")
    
    result = await db.bins.update_one(
        {"bin_id": bin_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Audit log
    await create_audit_log(
        action="status_change",
        entity_type="bin",
        entity_id=bin_id,
        entity_name=bin_doc.get("bin_code"),
        user=user,
        old_values={"status": old_status},
        new_values={"status": status},
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": "Bin status updated successfully"}

@api_router.get("/bins/zones/list")
async def get_bin_zones(user: dict = Depends(get_current_user)):
    zones = await db.bins.distinct("zone")
    return zones

# ===================== PUTAWAY MANAGEMENT =====================

@api_router.post("/putaway", response_model=Putaway)
async def create_putaway(putaway: PutawayCreate, user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Warehouse Operator"]))):
    # Validate GRN
    grn = await db.grn.find_one({"grn_id": putaway.grn_id}, {"_id": 0})
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    
    # Validate material
    material = await db.materials.find_one({"material_id": putaway.material_id}, {"_id": 0})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Validate bin
    bin_doc = await db.bins.find_one({"bin_id": putaway.bin_id}, {"_id": 0})
    if not bin_doc:
        raise HTTPException(status_code=404, detail="Bin not found")
    
    if bin_doc["status"] == "blocked":
        raise HTTPException(status_code=400, detail="Bin is blocked")
    
    if bin_doc["current_stock"] + putaway.quantity > bin_doc["capacity"]:
        raise HTTPException(status_code=400, detail="Bin capacity exceeded")
    
    putaway_id = f"put_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    putaway_doc = {
        "putaway_id": putaway_id,
        "grn_id": putaway.grn_id,
        "material_id": putaway.material_id,
        "material_code": material["material_code"],
        "quantity": putaway.quantity,
        "bin_id": putaway.bin_id,
        "bin_code": bin_doc["bin_code"],
        "status": "pending",
        "created_at": now,
        "created_by": user["user_id"]
    }
    
    await db.putaway.insert_one(putaway_doc)
    return Putaway(**putaway_doc)

@api_router.get("/putaway", response_model=List[Putaway])
async def get_putaways(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query["status"] = status
    
    putaways = await db.putaway.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return putaways

@api_router.put("/putaway/{putaway_id}/complete")
async def complete_putaway(putaway_id: str, user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Warehouse Operator"]))):
    putaway = await db.putaway.find_one({"putaway_id": putaway_id}, {"_id": 0})
    if not putaway:
        raise HTTPException(status_code=404, detail="Putaway not found")
    
    if putaway["status"] != "pending":
        raise HTTPException(status_code=400, detail="Putaway is not pending")
    
    # Update bin stock
    await db.bins.update_one(
        {"bin_id": putaway["bin_id"]},
        {
            "$inc": {"current_stock": putaway["quantity"]},
            "$set": {
                "status": "available",
                "material_id": putaway["material_id"],
                "material_code": putaway["material_code"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Create stock movement
    movement = {
        "movement_id": f"mov_{uuid.uuid4().hex[:12]}",
        "movement_type": "transfer",
        "material_id": putaway["material_id"],
        "material_code": putaway["material_code"],
        "quantity": putaway["quantity"],
        "to_bin": putaway["bin_code"],
        "reference_type": "Putaway",
        "reference_id": putaway_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["user_id"]
    }
    await db.stock_movements.insert_one(movement)
    
    # Update putaway status
    await db.putaway.update_one(
        {"putaway_id": putaway_id},
        {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Putaway completed successfully"}

# ===================== FIFO/LIFO RULE ENGINE =====================

class FIFOLIFOException(BaseModel):
    model_config = ConfigDict(extra="ignore")
    exception_id: str
    material_id: str
    material_code: str
    stock_method: str  # FIFO or LIFO
    recommended_batch: str
    selected_batch: str
    recommended_receipt_date: str
    selected_receipt_date: str
    override_reason: str
    issue_id: Optional[str] = None
    issue_number: Optional[str] = None
    created_by: str
    created_by_name: str
    created_at: str

@api_router.get("/fifo-lifo/recommendation/{material_id}")
async def get_stock_recommendation(
    material_id: str,
    quantity_needed: int = Query(..., gt=0),
    user: dict = Depends(get_current_user)
):
    """Get FIFO/LIFO recommendation for a material based on its configured stock method"""
    
    material = await db.materials.find_one({"material_id": material_id}, {"_id": 0})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    stock_method = material.get("stock_method", "FIFO")
    material_code = material.get("material_code")
    
    # Get all batches with stock for this material from completed GRNs
    grns = await db.grn.find(
        {"status": "completed", "items.material_code": material_code},
        {"_id": 0}
    ).to_list(10000)
    
    # Build batch inventory from GRN items
    batches = []
    for grn in grns:
        for item in grn.get("items", []):
            if item.get("material_code") == material_code and item.get("accepted_quantity", 0) > 0:
                batches.append({
                    "grn_id": grn.get("grn_id"),
                    "grn_number": grn.get("grn_number"),
                    "batch_number": item.get("batch_number"),
                    "quantity": item.get("accepted_quantity", 0),
                    "receipt_date": grn.get("receipt_date") or grn.get("created_at"),
                    "manufacturing_date": item.get("manufacturing_date"),
                    "expiry_date": item.get("expiry_date"),
                    "bin_location": item.get("bin_location"),
                    "storage_condition": item.get("storage_condition")
                })
    
    if not batches:
        return {
            "material_id": material_id,
            "material_code": material_code,
            "stock_method": stock_method,
            "quantity_needed": quantity_needed,
            "available_stock": 0,
            "recommended_batches": [],
            "all_batches": [],
            "message": "No stock available for this material"
        }
    
    # Sort batches based on stock method
    if stock_method == "FIFO":
        # Oldest first (earliest receipt date)
        batches.sort(key=lambda x: x.get("receipt_date", "9999"))
    else:  # LIFO
        # Newest first (latest receipt date)
        batches.sort(key=lambda x: x.get("receipt_date", "0000"), reverse=True)
    
    # Build recommendation - select batches to fulfill quantity
    recommended_batches = []
    remaining_qty = quantity_needed
    
    for batch in batches:
        if remaining_qty <= 0:
            break
        
        available = batch.get("quantity", 0)
        pick_qty = min(available, remaining_qty)
        
        if pick_qty > 0:
            recommended_batches.append({
                **batch,
                "pick_quantity": pick_qty,
                "is_recommended": True,
                "sequence": len(recommended_batches) + 1
            })
            remaining_qty -= pick_qty
    
    # Mark all batches with their recommendation status
    all_batches_with_status = []
    for i, batch in enumerate(batches):
        is_recommended = any(rb["batch_number"] == batch["batch_number"] for rb in recommended_batches)
        all_batches_with_status.append({
            **batch,
            "sequence": i + 1,
            "is_recommended": is_recommended,
            "recommendation_reason": f"{'Oldest' if stock_method == 'FIFO' else 'Newest'} batch - should be issued {'first' if i == 0 else f'#{i+1}'}"
        })
    
    total_available = sum(b.get("quantity", 0) for b in batches)
    
    return {
        "material_id": material_id,
        "material_code": material_code,
        "material_name": material.get("name"),
        "stock_method": stock_method,
        "quantity_needed": quantity_needed,
        "available_stock": total_available,
        "can_fulfill": total_available >= quantity_needed,
        "recommended_batches": recommended_batches,
        "all_batches": all_batches_with_status,
        "rule_description": f"{'FIFO: Issue oldest stock first' if stock_method == 'FIFO' else 'LIFO: Issue newest stock first'}"
    }

@api_router.post("/fifo-lifo/validate-selection")
async def validate_batch_selection(
    material_id: str = Query(...),
    selected_batch: str = Query(...),
    quantity: int = Query(..., gt=0),
    user: dict = Depends(get_current_user)
):
    """Validate if selected batch follows FIFO/LIFO rules"""
    
    material = await db.materials.find_one({"material_id": material_id}, {"_id": 0})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    stock_method = material.get("stock_method", "FIFO")
    material_code = material.get("material_code")
    
    # Get recommendation
    recommendation = await get_stock_recommendation(material_id, quantity, user)
    
    if not recommendation["recommended_batches"]:
        return {
            "valid": False,
            "reason": "No stock available",
            "requires_override": False
        }
    
    # Check if selected batch is the recommended one
    recommended_batch = recommendation["recommended_batches"][0]["batch_number"]
    
    if selected_batch == recommended_batch:
        return {
            "valid": True,
            "follows_rule": True,
            "stock_method": stock_method,
            "message": f"Selection follows {stock_method} rule"
        }
    
    # Find the selected batch in all batches
    selected_batch_info = None
    recommended_batch_info = None
    
    for batch in recommendation["all_batches"]:
        if batch["batch_number"] == selected_batch:
            selected_batch_info = batch
        if batch["batch_number"] == recommended_batch:
            recommended_batch_info = batch
    
    if not selected_batch_info:
        return {
            "valid": False,
            "reason": "Selected batch not found",
            "requires_override": False
        }
    
    # Calculate the violation severity
    selected_date = selected_batch_info.get("receipt_date", "")
    recommended_date = recommended_batch_info.get("receipt_date", "") if recommended_batch_info else ""
    
    return {
        "valid": True,
        "follows_rule": False,
        "stock_method": stock_method,
        "violation": True,
        "requires_override": True,
        "recommended_batch": recommended_batch,
        "recommended_receipt_date": recommended_date,
        "selected_batch": selected_batch,
        "selected_receipt_date": selected_date,
        "warning_message": f"{stock_method} violation: Batch {recommended_batch} (received {recommended_date[:10] if recommended_date else 'N/A'}) should be issued before {selected_batch} (received {selected_date[:10] if selected_date else 'N/A'})",
        "action_required": "Override reason required to proceed"
    }

@api_router.post("/fifo-lifo/log-exception")
async def log_fifo_lifo_exception(
    material_id: str = Query(...),
    selected_batch: str = Query(...),
    recommended_batch: str = Query(...),
    override_reason: str = Query(..., min_length=10),
    issue_id: Optional[str] = None,
    issue_number: Optional[str] = None,
    request: Request = None,
    user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Warehouse Operator"]))
):
    """Log a FIFO/LIFO exception when user overrides the recommendation"""
    
    material = await db.materials.find_one({"material_id": material_id}, {"_id": 0})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    stock_method = material.get("stock_method", "FIFO")
    
    # Get batch dates for logging
    recommendation = await get_stock_recommendation(material_id, 1, user)
    
    selected_date = ""
    recommended_date = ""
    for batch in recommendation.get("all_batches", []):
        if batch["batch_number"] == selected_batch:
            selected_date = batch.get("receipt_date", "")
        if batch["batch_number"] == recommended_batch:
            recommended_date = batch.get("receipt_date", "")
    
    exception_id = f"exc_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    exception_doc = {
        "exception_id": exception_id,
        "material_id": material_id,
        "material_code": material.get("material_code"),
        "stock_method": stock_method,
        "recommended_batch": recommended_batch,
        "selected_batch": selected_batch,
        "recommended_receipt_date": recommended_date,
        "selected_receipt_date": selected_date,
        "override_reason": override_reason,
        "issue_id": issue_id,
        "issue_number": issue_number,
        "created_by": user["user_id"],
        "created_by_name": user.get("name", "Unknown"),
        "created_at": now
    }
    
    await db.fifo_lifo_exceptions.insert_one(exception_doc)
    
    # Also log to audit trail
    await create_audit_log(
        action="override",
        entity_type="fifo_lifo",
        entity_id=exception_id,
        entity_name=f"{stock_method} Exception - {material.get('material_code')}",
        user=user,
        old_values={"recommended_batch": recommended_batch, "recommended_date": recommended_date},
        new_values={"selected_batch": selected_batch, "selected_date": selected_date, "reason": override_reason},
        ip_address=request.client.host if request and request.client else None
    )
    
    return {
        "exception_id": exception_id,
        "message": f"{stock_method} exception logged successfully",
        "warning": f"User bypassed {stock_method} rule. Reason: {override_reason}"
    }

@api_router.get("/fifo-lifo/exceptions")
async def get_fifo_lifo_exceptions(
    material_code: Optional[str] = None,
    stock_method: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Auditor", "Inventory Controller"]))
):
    """Get all FIFO/LIFO exceptions with optional filters"""
    query = {}
    
    if material_code:
        query["material_code"] = {"$regex": material_code, "$options": "i"}
    if stock_method:
        query["stock_method"] = stock_method
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    
    total = await db.fifo_lifo_exceptions.count_documents(query)
    exceptions = await db.fifo_lifo_exceptions.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "total": total,
        "exceptions": exceptions
    }

@api_router.get("/fifo-lifo/exceptions/summary")
async def get_fifo_lifo_exception_summary(
    days: int = Query(default=30, le=90),
    user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Auditor"]))
):
    """Get summary of FIFO/LIFO exceptions"""
    from_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    # Count by stock method
    pipeline = [
        {"$match": {"created_at": {"$gte": from_date}}},
        {"$group": {
            "_id": "$stock_method",
            "count": {"$sum": 1}
        }}
    ]
    by_method = await db.fifo_lifo_exceptions.aggregate(pipeline).to_list(10)
    
    # Top materials with exceptions
    material_pipeline = [
        {"$match": {"created_at": {"$gte": from_date}}},
        {"$group": {
            "_id": "$material_code",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_materials = await db.fifo_lifo_exceptions.aggregate(material_pipeline).to_list(10)
    
    # Top users with exceptions
    user_pipeline = [
        {"$match": {"created_at": {"$gte": from_date}}},
        {"$group": {
            "_id": {"user_id": "$created_by", "user_name": "$created_by_name"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_users = await db.fifo_lifo_exceptions.aggregate(user_pipeline).to_list(10)
    
    # Recent exceptions
    recent = await db.fifo_lifo_exceptions.find(
        {"created_at": {"$gte": from_date}},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    total_count = await db.fifo_lifo_exceptions.count_documents({"created_at": {"$gte": from_date}})
    
    return {
        "period_days": days,
        "total_exceptions": total_count,
        "by_method": {item["_id"]: item["count"] for item in by_method},
        "top_materials": top_materials,
        "top_users": top_users,
        "recent_exceptions": recent
    }

@api_router.get("/fifo-lifo/material-config/{material_id}")
async def get_material_fifo_lifo_config(material_id: str, user: dict = Depends(get_current_user)):
    """Get FIFO/LIFO configuration for a specific material"""
    material = await db.materials.find_one({"material_id": material_id}, {"_id": 0})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    stock_method = material.get("stock_method", "FIFO")
    
    # Get exception count for this material
    exception_count = await db.fifo_lifo_exceptions.count_documents({"material_id": material_id})
    
    return {
        "material_id": material_id,
        "material_code": material.get("material_code"),
        "material_name": material.get("name"),
        "stock_method": stock_method,
        "rule_description": f"{'Issue oldest stock first (First In, First Out)' if stock_method == 'FIFO' else 'Issue newest stock first (Last In, First Out)'}",
        "exception_count": exception_count,
        "enforcement_level": "warn_and_log"  # Options: strict_block, warn_and_log, log_only
    }

@api_router.put("/fifo-lifo/material-config/{material_id}")
async def update_material_fifo_lifo_config(
    material_id: str,
    stock_method: str = Query(..., regex="^(FIFO|LIFO)$"),
    request: Request = None,
    user: dict = Depends(require_roles(["Admin"]))
):
    """Update FIFO/LIFO configuration for a material - Admin only"""
    material = await db.materials.find_one({"material_id": material_id}, {"_id": 0})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    old_method = material.get("stock_method", "FIFO")
    
    if old_method != stock_method:
        await db.materials.update_one(
            {"material_id": material_id},
            {"$set": {"stock_method": stock_method, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Audit log
        await create_audit_log(
            action="update",
            entity_type="material",
            entity_id=material_id,
            entity_name=f"{material.get('material_code')} - Stock Method Change",
            user=user,
            old_values={"stock_method": old_method},
            new_values={"stock_method": stock_method},
            ip_address=request.client.host if request and request.client else None
        )
    
    return {
        "material_id": material_id,
        "material_code": material.get("material_code"),
        "old_method": old_method,
        "new_method": stock_method,
        "message": f"Stock method updated from {old_method} to {stock_method}"
    }

# ===================== MATERIAL ISSUE =====================

@api_router.post("/issues", response_model=MaterialIssue)
async def create_material_issue(issue: MaterialIssueCreate, user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Warehouse Operator"]))):
    issue_id = f"iss_{uuid.uuid4().hex[:12]}"
    issue_number = f"ISS-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.now(timezone.utc).isoformat()
    
    # Validate materials and check stock
    for item in issue.items:
        material = await db.materials.find_one({"material_id": item.material_id}, {"_id": 0})
        if not material:
            raise HTTPException(status_code=404, detail=f"Material {item.material_id} not found")
        if material.get("current_stock", 0) < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {material['material_code']}")
    
    total_quantity = sum(item.quantity for item in issue.items)
    
    issue_doc = {
        "issue_id": issue_id,
        "issue_number": issue_number,
        "department": issue.department,
        "requisition_number": issue.requisition_number,
        "items": [item.model_dump() for item in issue.items],
        "total_quantity": total_quantity,
        "status": "pending",
        "remarks": issue.remarks,
        "created_at": now,
        "created_by": user["user_id"]
    }
    
    await db.issues.insert_one(issue_doc)
    return MaterialIssue(**issue_doc)

@api_router.get("/issues", response_model=List[MaterialIssue])
async def get_issues(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query["status"] = status
    
    issues = await db.issues.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return issues

@api_router.get("/issues/{issue_id}", response_model=MaterialIssue)
async def get_issue(issue_id: str, user: dict = Depends(get_current_user)):
    issue = await db.issues.find_one({"issue_id": issue_id}, {"_id": 0})
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return MaterialIssue(**issue)

@api_router.put("/issues/{issue_id}/complete")
async def complete_issue(issue_id: str, user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Warehouse Operator"]))):
    issue = await db.issues.find_one({"issue_id": issue_id}, {"_id": 0})
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    if issue["status"] != "pending":
        raise HTTPException(status_code=400, detail="Issue is not pending")
    
    # Get material stock method and process accordingly
    for item in issue["items"]:
        material = await db.materials.find_one({"material_id": item["material_id"]}, {"_id": 0})
        stock_method = material.get("stock_method", "FIFO")
        
        # Deduct from material stock
        await db.materials.update_one(
            {"material_id": item["material_id"]},
            {"$inc": {"current_stock": -item["quantity"]}}
        )
        
        # If from_bin specified, deduct from bin
        if item.get("from_bin"):
            await db.bins.update_one(
                {"bin_code": item["from_bin"]},
                {"$inc": {"current_stock": -item["quantity"]}}
            )
        else:
            # Auto-select bins based on FIFO/LIFO
            remaining_qty = item["quantity"]
            sort_order = 1 if stock_method == "FIFO" else -1
            
            bins_with_material = await db.bins.find(
                {"material_id": item["material_id"], "current_stock": {"$gt": 0}},
                {"_id": 0}
            ).sort("updated_at", sort_order).to_list(100)
            
            for bin_doc in bins_with_material:
                if remaining_qty <= 0:
                    break
                
                deduct = min(bin_doc["current_stock"], remaining_qty)
                new_stock = bin_doc["current_stock"] - deduct
                
                await db.bins.update_one(
                    {"bin_id": bin_doc["bin_id"]},
                    {
                        "$set": {
                            "current_stock": new_stock,
                            "status": "empty" if new_stock == 0 else "available",
                            "material_id": None if new_stock == 0 else bin_doc["material_id"],
                            "material_code": None if new_stock == 0 else bin_doc["material_code"],
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                remaining_qty -= deduct
        
        # Create stock movement
        movement = {
            "movement_id": f"mov_{uuid.uuid4().hex[:12]}",
            "movement_type": "outward",
            "material_id": item["material_id"],
            "material_code": item["material_code"],
            "quantity": item["quantity"],
            "from_bin": item.get("from_bin"),
            "reference_type": "Issue",
            "reference_id": issue_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }
        await db.stock_movements.insert_one(movement)
    
    await db.issues.update_one(
        {"issue_id": issue_id},
        {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Issue completed successfully"}

# ===================== LABELS - Enhanced with Print Logging =====================

@api_router.post("/labels", response_model=Label)
async def create_label(label: LabelCreate, user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Warehouse Operator"]))):
    """Create a manual label (labels are also auto-created when GRN is saved)"""
    material = await db.materials.find_one({"material_id": label.material_id}, {"_id": 0})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    grn_number = None
    date_of_receipt = None
    if label.grn_id:
        grn = await db.grn.find_one({"grn_id": label.grn_id}, {"_id": 0})
        if grn:
            grn_number = grn.get("grn_number")
            date_of_receipt = grn.get("receipt_date") or grn.get("created_at")
    
    now = datetime.now(timezone.utc)
    label_id = f"lbl_{uuid.uuid4().hex[:12]}"
    batch_number = label.batch_number or f"BTH-{now.strftime('%Y%m%d%H%M%S')}"
    
    # Generate QR data as JSON - universally scannable
    import json as json_lib
    qr_json = {
        "type": "WMS_LABEL",
        "material": material['material_code'],
        "grn": grn_number or "",
        "batch": batch_number,
        "qty": label.quantity,
        "uom": label.uom or material.get("uom", "PCS"),
        "bin": label.bin_location or "",
        "expiry": label.expiry_date or ""
    }
    qr_data = json_lib.dumps(qr_json, separators=(',', ':'))
    barcode_data = f"{material['material_code']}-{batch_number}"
    
    label_doc = {
        "label_id": label_id,
        "material_id": label.material_id,
        "material_code": material["material_code"],
        "material_name": material["name"],
        "material_description": material.get("description", ""),
        "grn_id": label.grn_id,
        "grn_number": grn_number,
        "grn_item_id": label.grn_item_id,
        "batch_number": batch_number,
        "quantity": label.quantity,
        "uom": label.uom or material.get("uom", "PCS"),
        "bin_location": label.bin_location,
        "date_of_receipt": date_of_receipt or now.isoformat(),
        "manufacturing_date": label.manufacturing_date,
        "expiry_date": label.expiry_date,
        "storage_condition": label.storage_condition,
        "qr_data": qr_data,
        "barcode_data": barcode_data,
        "created_at": now.isoformat(),
        "created_by": user["user_id"],
        "created_by_name": user["name"],
        "print_count": 0,
        "last_printed_at": None,
        "last_printed_by": None
    }
    
    await db.labels.insert_one(label_doc)
    return Label(**label_doc)

@api_router.get("/labels", response_model=List[Label])
async def get_labels(
    material_id: Optional[str] = None,
    grn_id: Optional[str] = None,
    batch_number: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if material_id:
        query["material_id"] = material_id
    if grn_id:
        query["grn_id"] = grn_id
    if batch_number:
        query["batch_number"] = {"$regex": batch_number, "$options": "i"}
    
    labels = await db.labels.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return labels

@api_router.get("/labels/{label_id}", response_model=Label)
async def get_label(label_id: str, user: dict = Depends(get_current_user)):
    label = await db.labels.find_one({"label_id": label_id}, {"_id": 0})
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    return Label(**label)

@api_router.post("/labels/{label_id}/print")
async def log_label_print(label_id: str, copies: int = 1, user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Warehouse Operator"]))):
    """Log a print action for a label"""
    label = await db.labels.find_one({"label_id": label_id}, {"_id": 0})
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    now = datetime.now(timezone.utc)
    
    # Create print log
    log_doc = {
        "log_id": f"plog_{uuid.uuid4().hex[:12]}",
        "label_id": label_id,
        "action": "print",
        "reason": None,
        "printed_at": now.isoformat(),
        "printed_by": user["user_id"],
        "printed_by_name": user["name"],
        "quantity_printed": copies
    }
    await db.print_logs.insert_one(log_doc)
    
    # Update label print count
    new_count = label.get("print_count", 0) + 1
    await db.labels.update_one(
        {"label_id": label_id},
        {"$set": {
            "print_count": new_count,
            "last_printed_at": now.isoformat(),
            "last_printed_by": user["name"]
        }}
    )
    
    return {"message": "Print logged successfully", "print_count": new_count}

@api_router.post("/labels/{label_id}/reprint")
async def log_label_reprint(label_id: str, request: ReprintRequest, user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Warehouse Operator"]))):
    """Log a reprint action with mandatory reason"""
    if not request.reason or len(request.reason.strip()) < 3:
        raise HTTPException(status_code=400, detail="Reprint reason is required (minimum 3 characters)")
    
    label = await db.labels.find_one({"label_id": label_id}, {"_id": 0})
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    now = datetime.now(timezone.utc)
    
    # Create reprint log
    log_doc = {
        "log_id": f"plog_{uuid.uuid4().hex[:12]}",
        "label_id": label_id,
        "action": "reprint",
        "reason": request.reason.strip(),
        "printed_at": now.isoformat(),
        "printed_by": user["user_id"],
        "printed_by_name": user["name"],
        "quantity_printed": request.copies
    }
    await db.print_logs.insert_one(log_doc)
    
    # Update label print count
    new_count = label.get("print_count", 0) + 1
    await db.labels.update_one(
        {"label_id": label_id},
        {"$set": {
            "print_count": new_count,
            "last_printed_at": now.isoformat(),
            "last_printed_by": user["name"]
        }}
    )
    
    return {"message": "Reprint logged successfully", "print_count": new_count}

@api_router.post("/labels/bulk-print")
async def log_bulk_print(request: BulkPrintRequest, user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Warehouse Operator"]))):
    """Log bulk print action for multiple labels"""
    if not request.label_ids:
        raise HTTPException(status_code=400, detail="No labels selected")
    
    now = datetime.now(timezone.utc)
    printed_count = 0
    
    for label_id in request.label_ids:
        label = await db.labels.find_one({"label_id": label_id}, {"_id": 0})
        if label:
            # Create print log for each label
            log_doc = {
                "log_id": f"plog_{uuid.uuid4().hex[:12]}",
                "label_id": label_id,
                "label_ids": request.label_ids,  # Reference to bulk print
                "action": "print",
                "reason": "Bulk print",
                "printed_at": now.isoformat(),
                "printed_by": user["user_id"],
                "printed_by_name": user["name"],
                "quantity_printed": request.copies
            }
            await db.print_logs.insert_one(log_doc)
            
            # Update label print count
            new_count = label.get("print_count", 0) + 1
            await db.labels.update_one(
                {"label_id": label_id},
                {"$set": {
                    "print_count": new_count,
                    "last_printed_at": now.isoformat(),
                    "last_printed_by": user["name"]
                }}
            )
            printed_count += 1
    
    return {"message": f"Bulk print logged for {printed_count} labels", "labels_printed": printed_count}

@api_router.get("/labels/{label_id}/print-history")
async def get_label_print_history(label_id: str, user: dict = Depends(get_current_user)):
    """Get print history for a specific label"""
    logs = await db.print_logs.find(
        {"label_id": label_id},
        {"_id": 0}
    ).sort("printed_at", -1).to_list(100)
    return logs

@api_router.get("/print-logs")
async def get_all_print_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    action: Optional[str] = None,
    user: dict = Depends(require_roles(["Admin", "Store In-Charge", "Inventory Controller"]))
):
    """Get all print logs with optional filters"""
    query = {}
    if action:
        query["action"] = action
    if start_date:
        query["printed_at"] = {"$gte": start_date}
    if end_date:
        if "printed_at" in query:
            query["printed_at"]["$lte"] = end_date
        else:
            query["printed_at"] = {"$lte": end_date}
    
    logs = await db.print_logs.find(query, {"_id": 0}).sort("printed_at", -1).to_list(1000)
    return logs

@api_router.get("/labels/by-grn/{grn_id}")
async def get_labels_by_grn(grn_id: str, user: dict = Depends(get_current_user)):
    """Get all labels generated for a specific GRN"""
    labels = await db.labels.find({"grn_id": grn_id}, {"_id": 0}).to_list(100)
    return labels

@api_router.post("/labels/regenerate-qr")
async def regenerate_all_qr_codes(user: dict = Depends(require_roles(["Admin"]))):
    """Regenerate QR codes for all existing labels to use JSON format"""
    import json as json_lib
    
    labels = await db.labels.find({}, {"_id": 0}).to_list(10000)
    updated_count = 0
    
    for label in labels:
        qr_json = {
            "type": "WMS_LABEL",
            "material": label.get('material_code', ''),
            "grn": label.get('grn_number') or "",
            "batch": label.get('batch_number', ''),
            "qty": label.get('quantity', 0),
            "uom": label.get('uom', 'PCS'),
            "bin": label.get('bin_location') or "",
            "expiry": label.get('expiry_date') or ""
        }
        new_qr_data = json_lib.dumps(qr_json, separators=(',', ':'))
        
        await db.labels.update_one(
            {"label_id": label["label_id"]},
            {"$set": {"qr_data": new_qr_data}}
        )
        updated_count += 1
    
    return {"message": f"Regenerated QR codes for {updated_count} labels"}

# ===================== STOCK MOVEMENTS =====================

@api_router.get("/movements", response_model=List[StockMovement])
async def get_stock_movements(
    movement_type: Optional[str] = None,
    material_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if movement_type:
        query["movement_type"] = movement_type
    if material_id:
        query["material_id"] = material_id
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return movements

# ===================== DASHBOARD =====================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    total_materials = await db.materials.count_documents({})
    total_bins = await db.bins.count_documents({})
    available_bins = await db.bins.count_documents({"status": "available"})
    empty_bins = await db.bins.count_documents({"status": "empty"})
    blocked_bins = await db.bins.count_documents({"status": "blocked"})
    
    pending_grns = await db.grn.count_documents({"status": "pending"})
    pending_issues = await db.issues.count_documents({"status": "pending"})
    pending_putaways = await db.putaway.count_documents({"status": "pending"})
    
    # Low stock materials
    low_stock_materials = await db.materials.find(
        {"$expr": {"$lt": ["$current_stock", "$reorder_point"]}},
        {"_id": 0}
    ).to_list(100)
    
    # Recent movements
    recent_movements = await db.stock_movements.find(
        {}, {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Total stock value (count)
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$current_stock"}}}]
    total_stock_result = await db.materials.aggregate(pipeline).to_list(1)
    total_stock = total_stock_result[0]["total"] if total_stock_result else 0
    
    return {
        "total_materials": total_materials,
        "total_bins": total_bins,
        "available_bins": available_bins,
        "empty_bins": empty_bins,
        "blocked_bins": blocked_bins,
        "pending_grns": pending_grns,
        "pending_issues": pending_issues,
        "pending_putaways": pending_putaways,
        "low_stock_count": len(low_stock_materials),
        "low_stock_materials": low_stock_materials,
        "recent_movements": recent_movements,
        "total_stock": total_stock
    }

# ===================== STOCK DASHBOARD APIs =====================

@api_router.get("/dashboard/stock-summary")
async def get_stock_dashboard_summary(user: dict = Depends(get_current_user)):
    """Comprehensive stock dashboard summary for management view"""
    
    # Total stock by status
    materials = await db.materials.find({}, {"_id": 0}).to_list(10000)
    total_available = sum(m.get("current_stock", 0) for m in materials)
    
    # Stock by material category
    category_pipeline = [
        {"$group": {
            "_id": "$category",
            "total_stock": {"$sum": "$current_stock"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total_stock": -1}}
    ]
    stock_by_category = await db.materials.aggregate(category_pipeline).to_list(20)
    
    # Bin status summary
    bins = await db.bins.find({}, {"_id": 0}).to_list(10000)
    bin_summary = {
        "total": len(bins),
        "empty": len([b for b in bins if b.get("status") == "empty" or b.get("current_stock", 0) == 0]),
        "occupied": len([b for b in bins if b.get("current_stock", 0) > 0]),
        "available": len([b for b in bins if b.get("status") == "available"]),
        "blocked": len([b for b in bins if b.get("status") == "blocked"]),
        "quality_hold": len([b for b in bins if b.get("status") == "quality_hold"])
    }
    
    # Stock status breakdown (from bins)
    stock_status = {
        "available": sum(b.get("current_stock", 0) for b in bins if b.get("status") == "available"),
        "blocked": sum(b.get("current_stock", 0) for b in bins if b.get("status") == "blocked"),
        "quality_hold": sum(b.get("current_stock", 0) for b in bins if b.get("status") == "quality_hold")
    }
    
    # Overstock and understock indicators
    overstock = []
    understock = []
    for m in materials:
        current = m.get("current_stock", 0)
        max_level = m.get("max_stock_level", 1000)
        min_level = m.get("min_stock_level", 0)
        reorder = m.get("reorder_point", 50)
        
        if current > max_level:
            overstock.append({
                "material_code": m["material_code"],
                "name": m["name"],
                "current_stock": current,
                "max_level": max_level,
                "excess": current - max_level
            })
        elif current < min_level or current <= reorder:
            understock.append({
                "material_code": m["material_code"],
                "name": m["name"],
                "current_stock": current,
                "min_level": min_level,
                "reorder_point": reorder,
                "shortage": max(min_level - current, reorder - current)
            })
    
    # FIFO materials with pending stock
    fifo_materials = [m for m in materials if m.get("stock_method") == "FIFO" and m.get("current_stock", 0) > 0]
    
    return {
        "total_stock": total_available,
        "total_materials": len(materials),
        "materials_with_stock": len([m for m in materials if m.get("current_stock", 0) > 0]),
        "stock_by_category": stock_by_category,
        "bin_summary": bin_summary,
        "stock_status": stock_status,
        "overstock_count": len(overstock),
        "understock_count": len(understock),
        "overstock_items": overstock[:10],
        "understock_items": understock[:10],
        "fifo_materials_count": len(fifo_materials)
    }

@api_router.get("/dashboard/stock-aging")
async def get_stock_aging_dashboard(user: dict = Depends(get_current_user)):
    """Stock aging analysis for dashboard"""
    now = datetime.now(timezone.utc)
    
    # Get all completed GRNs with items
    grns = await db.grn.find({"status": "completed"}, {"_id": 0}).to_list(10000)
    
    aging_buckets = {
        "0-30": {"count": 0, "quantity": 0, "items": []},
        "31-60": {"count": 0, "quantity": 0, "items": []},
        "61-90": {"count": 0, "quantity": 0, "items": []},
        "90+": {"count": 0, "quantity": 0, "items": []}
    }
    
    expiring_soon = []
    
    for grn in grns:
        receipt_date = grn.get("receipt_date") or grn.get("created_at")
        if isinstance(receipt_date, str):
            try:
                receipt_dt = datetime.fromisoformat(receipt_date.replace('Z', '+00:00'))
            except:
                continue
        else:
            receipt_dt = receipt_date
        
        if receipt_dt.tzinfo is None:
            receipt_dt = receipt_dt.replace(tzinfo=timezone.utc)
        
        age_days = (now - receipt_dt).days
        
        for item in grn.get("items", []):
            qty = item.get("accepted_quantity", 0)
            if qty <= 0:
                continue
            
            item_data = {
                "material_code": item.get("material_code"),
                "batch_number": item.get("batch_number"),
                "quantity": qty,
                "age_days": age_days,
                "expiry_date": item.get("expiry_date")
            }
            
            if age_days <= 30:
                aging_buckets["0-30"]["count"] += 1
                aging_buckets["0-30"]["quantity"] += qty
                if len(aging_buckets["0-30"]["items"]) < 5:
                    aging_buckets["0-30"]["items"].append(item_data)
            elif age_days <= 60:
                aging_buckets["31-60"]["count"] += 1
                aging_buckets["31-60"]["quantity"] += qty
                if len(aging_buckets["31-60"]["items"]) < 5:
                    aging_buckets["31-60"]["items"].append(item_data)
            elif age_days <= 90:
                aging_buckets["61-90"]["count"] += 1
                aging_buckets["61-90"]["quantity"] += qty
                if len(aging_buckets["61-90"]["items"]) < 5:
                    aging_buckets["61-90"]["items"].append(item_data)
            else:
                aging_buckets["90+"]["count"] += 1
                aging_buckets["90+"]["quantity"] += qty
                if len(aging_buckets["90+"]["items"]) < 5:
                    aging_buckets["90+"]["items"].append(item_data)
            
            # Check expiry
            expiry = item.get("expiry_date")
            if expiry:
                try:
                    if isinstance(expiry, str):
                        expiry_dt = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
                    else:
                        expiry_dt = expiry
                    if expiry_dt.tzinfo is None:
                        expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
                    
                    days_to_expiry = (expiry_dt - now).days
                    if 0 < days_to_expiry <= 30:
                        expiring_soon.append({
                            **item_data,
                            "days_to_expiry": days_to_expiry
                        })
                except:
                    pass
    
    return {
        "aging_buckets": aging_buckets,
        "expiring_soon": sorted(expiring_soon, key=lambda x: x.get("days_to_expiry", 999))[:10]
    }

@api_router.get("/dashboard/slow-moving")
async def get_slow_moving_dashboard(days_threshold: int = 60, user: dict = Depends(get_current_user)):
    """Slow-moving and non-moving stock analysis"""
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_threshold)).isoformat()
    non_moving_cutoff = (datetime.now(timezone.utc) - timedelta(days=days_threshold * 2)).isoformat()
    
    materials = await db.materials.find({"current_stock": {"$gt": 0}}, {"_id": 0}).to_list(1000)
    
    slow_moving = []
    non_moving = []
    
    for mat in materials:
        last_movement = await db.stock_movements.find_one(
            {"material_code": mat["material_code"], "movement_type": "outward"},
            {"_id": 0}
        )
        
        if not last_movement:
            # No outward movement ever - non-moving
            non_moving.append({
                "material_code": mat["material_code"],
                "name": mat["name"],
                "current_stock": mat.get("current_stock", 0),
                "last_movement": None,
                "days_idle": 999
            })
        else:
            last_date = last_movement.get("created_at")
            if last_date and last_date < non_moving_cutoff:
                non_moving.append({
                    "material_code": mat["material_code"],
                    "name": mat["name"],
                    "current_stock": mat.get("current_stock", 0),
                    "last_movement": last_date,
                    "days_idle": (datetime.now(timezone.utc) - datetime.fromisoformat(last_date.replace('Z', '+00:00'))).days if isinstance(last_date, str) else 999
                })
            elif last_date and last_date < cutoff_date:
                slow_moving.append({
                    "material_code": mat["material_code"],
                    "name": mat["name"],
                    "current_stock": mat.get("current_stock", 0),
                    "last_movement": last_date,
                    "days_idle": (datetime.now(timezone.utc) - datetime.fromisoformat(last_date.replace('Z', '+00:00'))).days if isinstance(last_date, str) else 999
                })
    
    return {
        "slow_moving_count": len(slow_moving),
        "non_moving_count": len(non_moving),
        "slow_moving_items": sorted(slow_moving, key=lambda x: x.get("days_idle", 0), reverse=True)[:10],
        "non_moving_items": sorted(non_moving, key=lambda x: x.get("days_idle", 0), reverse=True)[:10],
        "total_slow_moving_stock": sum(s.get("current_stock", 0) for s in slow_moving),
        "total_non_moving_stock": sum(n.get("current_stock", 0) for n in non_moving)
    }

@api_router.get("/dashboard/bin-utilization")
async def get_bin_utilization_dashboard(user: dict = Depends(get_current_user)):
    """Bin utilization analysis"""
    bins = await db.bins.find({}, {"_id": 0}).to_list(10000)
    
    # Group by zone
    zones = {}
    for bin_doc in bins:
        zone = bin_doc.get("zone", "Unknown")
        if zone not in zones:
            zones[zone] = {
                "total": 0, "occupied": 0, "empty": 0,
                "total_capacity": 0, "used_capacity": 0
            }
        zones[zone]["total"] += 1
        zones[zone]["total_capacity"] += bin_doc.get("capacity", 0)
        zones[zone]["used_capacity"] += bin_doc.get("current_stock", 0)
        
        if bin_doc.get("current_stock", 0) > 0:
            zones[zone]["occupied"] += 1
        else:
            zones[zone]["empty"] += 1
    
    # Calculate utilization percentages
    zone_summary = []
    for zone, data in zones.items():
        utilization = round((data["used_capacity"] / data["total_capacity"]) * 100, 1) if data["total_capacity"] > 0 else 0
        zone_summary.append({
            "zone": zone,
            **data,
            "utilization_percent": utilization
        })
    
    # High utilization bins (>80%)
    high_util_bins = [
        {
            "bin_code": b.get("bin_code"),
            "zone": b.get("zone"),
            "capacity": b.get("capacity", 0),
            "current_stock": b.get("current_stock", 0),
            "utilization": round((b.get("current_stock", 0) / b.get("capacity", 1)) * 100, 1)
        }
        for b in bins if b.get("capacity", 0) > 0 and (b.get("current_stock", 0) / b.get("capacity", 1)) > 0.8
    ]
    
    return {
        "zone_summary": sorted(zone_summary, key=lambda x: x["zone"]),
        "high_utilization_bins": sorted(high_util_bins, key=lambda x: x["utilization"], reverse=True)[:10],
        "overall_utilization": round(
            (sum(b.get("current_stock", 0) for b in bins) / sum(b.get("capacity", 1) for b in bins)) * 100, 1
        ) if bins else 0
    }

@api_router.get("/dashboard/fifo-alerts")
async def get_fifo_alerts_dashboard(user: dict = Depends(get_current_user)):
    """FIFO compliance alerts"""
    # Get FIFO materials
    fifo_materials = await db.materials.find(
        {"stock_method": "FIFO", "current_stock": {"$gt": 0}},
        {"_id": 0}
    ).to_list(1000)
    
    alerts = []
    
    for mat in fifo_materials:
        # Get oldest batch for this material
        oldest_grn = await db.grn.find_one(
            {
                "status": "completed",
                "items.material_code": mat["material_code"]
            },
            {"_id": 0}
        )
        
        if oldest_grn:
            for item in oldest_grn.get("items", []):
                if item.get("material_code") == mat["material_code"]:
                    alerts.append({
                        "material_code": mat["material_code"],
                        "name": mat["name"],
                        "current_stock": mat.get("current_stock", 0),
                        "oldest_batch": item.get("batch_number"),
                        "oldest_grn": oldest_grn.get("grn_number"),
                        "receipt_date": oldest_grn.get("receipt_date") or oldest_grn.get("created_at")
                    })
                    break
    
    return {
        "fifo_materials_count": len(fifo_materials),
        "alerts": alerts[:20]
    }

@api_router.get("/dashboard/material-stock")
async def get_material_stock_dashboard(user: dict = Depends(get_current_user)):
    """Detailed material stock visibility"""
    materials = await db.materials.find({}, {"_id": 0}).to_list(1000)
    
    # Top 10 by stock
    top_stock = sorted(materials, key=lambda x: x.get("current_stock", 0), reverse=True)[:10]
    
    # Stock by method (FIFO vs LIFO)
    fifo_stock = sum(m.get("current_stock", 0) for m in materials if m.get("stock_method") == "FIFO")
    lifo_stock = sum(m.get("current_stock", 0) for m in materials if m.get("stock_method") == "LIFO")
    
    return {
        "top_stock_materials": [
            {
                "material_code": m["material_code"],
                "name": m["name"],
                "category": m.get("category"),
                "current_stock": m.get("current_stock", 0),
                "uom": m.get("uom"),
                "stock_method": m.get("stock_method")
            }
            for m in top_stock
        ],
        "stock_by_method": {
            "FIFO": fifo_stock,
            "LIFO": lifo_stock
        },
        "total_materials": len(materials),
        "materials_with_stock": len([m for m in materials if m.get("current_stock", 0) > 0]),
        "zero_stock_materials": len([m for m in materials if m.get("current_stock", 0) == 0])
    }

# ===================== REPORTS =====================

# Report types enum
REPORT_TYPES = [
    "grn-stock", "batch-stock", "bin-stock", "movement-history", 
    "fifo-compliance", "non-fifo-exceptions", "putaway-pending",
    "stock-aging", "dead-slow-stock", "daily-summary", 
    "user-activity", "reprint-log", "stock-reconciliation"
]

@api_router.get("/reports/grn-stock")
async def get_grn_stock_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    vendor: Optional[str] = None,
    material_code: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """GRN-wise stock report showing all GRNs with item details"""
    query = {}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    if vendor:
        query["vendor_name"] = {"$regex": vendor, "$options": "i"}
    
    grns = await db.grn.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
    
    # Filter by material if specified
    if material_code:
        grns = [g for g in grns if any(item.get("material_code", "").upper() == material_code.upper() for item in g.get("items", []))]
    
    return {"data": grns, "total": len(grns)}

@api_router.get("/reports/batch-stock")
async def get_batch_stock_report(
    material_code: Optional[str] = None,
    batch_number: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Batch-wise stock report showing all batches with quantities"""
    query = {"status": "completed"}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    
    grns = await db.grn.find(query, {"_id": 0}).to_list(10000)
    
    # Flatten to batch level
    batches = []
    for grn in grns:
        for item in grn.get("items", []):
            if material_code and item.get("material_code", "").upper() != material_code.upper():
                continue
            if batch_number and batch_number.upper() not in item.get("batch_number", "").upper():
                continue
            
            batches.append({
                "grn_number": grn.get("grn_number"),
                "vendor_name": grn.get("vendor_name"),
                "material_code": item.get("material_code"),
                "material_name": item.get("material_name"),
                "batch_number": item.get("batch_number"),
                "received_quantity": item.get("received_quantity", 0),
                "accepted_quantity": item.get("accepted_quantity", 0),
                "rejected_quantity": item.get("rejected_quantity", 0),
                "manufacturing_date": item.get("manufacturing_date"),
                "expiry_date": item.get("expiry_date"),
                "storage_condition": item.get("storage_condition"),
                "bin_location": item.get("bin_location"),
                "receipt_date": grn.get("receipt_date")
            })
    
    return {"data": batches, "total": len(batches)}

@api_router.get("/reports/bin-stock")
async def get_bin_stock_report(
    zone: Optional[str] = None,
    bin_code: Optional[str] = None,
    status: Optional[str] = None,
    material_code: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Bin-wise stock report showing all bins with current contents"""
    query = {}
    if zone:
        query["zone"] = zone
    if bin_code:
        query["bin_code"] = {"$regex": bin_code, "$options": "i"}
    if status:
        query["status"] = status
    if material_code:
        query["material_code"] = {"$regex": material_code, "$options": "i"}
    
    bins = await db.bins.find(query, {"_id": 0}).sort("bin_code", 1).to_list(10000)
    
    # Calculate utilization
    for bin_doc in bins:
        capacity = bin_doc.get("capacity", 1)
        current = bin_doc.get("current_stock", 0)
        bin_doc["utilization_percent"] = round((current / capacity) * 100, 2) if capacity > 0 else 0
    
    return {"data": bins, "total": len(bins)}

@api_router.get("/reports/movement-history")
async def get_movement_history_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    movement_type: Optional[str] = None,
    material_code: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Material movement history report"""
    query = {}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    if movement_type:
        query["movement_type"] = movement_type
    if material_code:
        query["material_code"] = {"$regex": material_code, "$options": "i"}
    
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
    return {"data": movements, "total": len(movements)}

@api_router.get("/reports/fifo-compliance")
async def get_fifo_compliance_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    material_code: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """FIFO compliance report - materials configured for FIFO with issue sequence analysis"""
    # Get FIFO materials
    mat_query = {"stock_method": "FIFO"}
    if material_code:
        mat_query["material_code"] = {"$regex": material_code, "$options": "i"}
    
    fifo_materials = await db.materials.find(mat_query, {"_id": 0}).to_list(1000)
    
    # Get issues for these materials
    mov_query = {"movement_type": "outward"}
    if start_date:
        mov_query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in mov_query:
            mov_query["created_at"]["$lte"] = end_date
        else:
            mov_query["created_at"] = {"$lte": end_date}
    
    fifo_codes = [m["material_code"] for m in fifo_materials]
    mov_query["material_code"] = {"$in": fifo_codes}
    
    movements = await db.stock_movements.find(mov_query, {"_id": 0}).sort("created_at", -1).to_list(10000)
    
    # Analyze compliance (simplified - actual FIFO tracking would need batch-level data)
    compliance_data = []
    for mat in fifo_materials:
        mat_movements = [m for m in movements if m.get("material_code") == mat["material_code"]]
        compliance_data.append({
            "material_code": mat["material_code"],
            "material_name": mat["name"],
            "stock_method": "FIFO",
            "current_stock": mat.get("current_stock", 0),
            "total_issues": len(mat_movements),
            "total_quantity_issued": sum(m.get("quantity", 0) for m in mat_movements),
            "compliance_status": "Compliant"  # Would need batch tracking for actual compliance
        })
    
    return {"data": compliance_data, "total": len(compliance_data)}

@api_router.get("/reports/non-fifo-exceptions")
async def get_non_fifo_exceptions_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Non-FIFO exception report - instances where FIFO was not followed"""
    # This would require batch-level tracking to identify actual exceptions
    # For now, return materials that are FIFO but have manual bin overrides
    
    query = {}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    
    # Check for issues with specific bin selection (potential override)
    query["movement_type"] = "outward"
    query["from_bin"] = {"$ne": None}
    
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
    
    # Get FIFO materials
    fifo_mats = await db.materials.find({"stock_method": "FIFO"}, {"_id": 0, "material_code": 1}).to_list(1000)
    fifo_codes = [m["material_code"] for m in fifo_mats]
    
    # Filter to FIFO materials only
    exceptions = [m for m in movements if m.get("material_code") in fifo_codes]
    
    return {"data": exceptions, "total": len(exceptions), "note": "Shows FIFO materials with manual bin selection"}

@api_router.get("/reports/putaway-pending")
async def get_putaway_pending_report(
    material_code: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Putaway pending report - items received but not yet put away"""
    query = {"status": "pending"}
    
    putaways = await db.putaway.find(query, {"_id": 0}).sort("created_at", 1).to_list(10000)
    
    if material_code:
        putaways = [p for p in putaways if material_code.upper() in p.get("material_code", "").upper()]
    
    # Enrich with GRN info
    for p in putaways:
        grn = await db.grn.find_one({"grn_id": p.get("grn_id")}, {"_id": 0, "grn_number": 1, "vendor_name": 1})
        if grn:
            p["grn_number"] = grn.get("grn_number")
            p["vendor_name"] = grn.get("vendor_name")
    
    return {"data": putaways, "total": len(putaways)}

@api_router.get("/reports/stock-aging")
async def get_stock_aging_report(
    aging_days: int = Query(default=30),
    material_code: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Stock aging report - batches by age category"""
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=aging_days)).isoformat()
    
    # Get completed GRNs with batches
    grns = await db.grn.find({"status": "completed"}, {"_id": 0}).to_list(10000)
    
    aging_data = []
    now = datetime.now(timezone.utc)
    
    for grn in grns:
        receipt_date = grn.get("receipt_date") or grn.get("created_at")
        if isinstance(receipt_date, str):
            try:
                receipt_dt = datetime.fromisoformat(receipt_date.replace('Z', '+00:00'))
            except:
                continue
        else:
            receipt_dt = receipt_date
        
        if receipt_dt.tzinfo is None:
            receipt_dt = receipt_dt.replace(tzinfo=timezone.utc)
        
        age_days = (now - receipt_dt).days
        
        for item in grn.get("items", []):
            if material_code and material_code.upper() not in item.get("material_code", "").upper():
                continue
            
            # Determine aging bucket
            if age_days <= 30:
                bucket = "0-30 days"
            elif age_days <= 60:
                bucket = "31-60 days"
            elif age_days <= 90:
                bucket = "61-90 days"
            else:
                bucket = "90+ days"
            
            aging_data.append({
                "grn_number": grn.get("grn_number"),
                "material_code": item.get("material_code"),
                "material_name": item.get("material_name"),
                "batch_number": item.get("batch_number"),
                "quantity": item.get("accepted_quantity", 0),
                "receipt_date": receipt_date,
                "age_days": age_days,
                "aging_bucket": bucket,
                "expiry_date": item.get("expiry_date"),
                "bin_location": item.get("bin_location")
            })
    
    # Sort by age descending
    aging_data.sort(key=lambda x: x["age_days"], reverse=True)
    
    return {"data": aging_data, "total": len(aging_data)}

@api_router.get("/reports/dead-slow-stock")
async def get_dead_slow_stock_report(
    days_threshold: int = Query(default=90),
    material_code: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Dead/slow-moving stock report - materials with no movement in specified days"""
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_threshold)).isoformat()
    
    # Get all materials with stock
    mat_query = {"current_stock": {"$gt": 0}}
    if material_code:
        mat_query["material_code"] = {"$regex": material_code, "$options": "i"}
    
    materials = await db.materials.find(mat_query, {"_id": 0}).to_list(1000)
    
    dead_slow = []
    for mat in materials:
        # Check last movement
        last_movement = await db.stock_movements.find_one(
            {"material_code": mat["material_code"]},
            {"_id": 0, "created_at": 1}
        )
        
        last_date = last_movement.get("created_at") if last_movement else mat.get("created_at")
        
        if isinstance(last_date, str):
            try:
                last_dt = datetime.fromisoformat(last_date.replace('Z', '+00:00'))
            except:
                continue
        else:
            last_dt = last_date if last_date else datetime.now(timezone.utc)
        
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        
        days_since = (datetime.now(timezone.utc) - last_dt).days
        
        if days_since >= days_threshold:
            status = "Dead Stock" if days_since >= days_threshold * 2 else "Slow Moving"
            dead_slow.append({
                "material_code": mat["material_code"],
                "material_name": mat["name"],
                "category": mat.get("category"),
                "current_stock": mat.get("current_stock", 0),
                "last_movement_date": last_date,
                "days_since_movement": days_since,
                "status": status
            })
    
    # Sort by days since movement descending
    dead_slow.sort(key=lambda x: x["days_since_movement"], reverse=True)
    
    return {"data": dead_slow, "total": len(dead_slow)}

@api_router.get("/reports/daily-summary")
async def get_daily_summary_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Daily inward and outward summary report"""
    if not start_date:
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = datetime.now(timezone.utc).isoformat()
    
    # Get all movements in range
    movements = await db.stock_movements.find(
        {"created_at": {"$gte": start_date, "$lte": end_date}},
        {"_id": 0}
    ).to_list(100000)
    
    # Group by date
    daily_data = {}
    for mov in movements:
        date_str = mov.get("created_at", "")[:10]
        if date_str not in daily_data:
            daily_data[date_str] = {
                "date": date_str,
                "inward_count": 0, "inward_qty": 0,
                "outward_count": 0, "outward_qty": 0,
                "transfer_count": 0, "transfer_qty": 0
            }
        
        qty = mov.get("quantity", 0)
        mov_type = mov.get("movement_type", "")
        
        if mov_type == "inward":
            daily_data[date_str]["inward_count"] += 1
            daily_data[date_str]["inward_qty"] += qty
        elif mov_type == "outward":
            daily_data[date_str]["outward_count"] += 1
            daily_data[date_str]["outward_qty"] += qty
        elif mov_type == "transfer":
            daily_data[date_str]["transfer_count"] += 1
            daily_data[date_str]["transfer_qty"] += qty
    
    # Sort by date descending
    summary = sorted(daily_data.values(), key=lambda x: x["date"], reverse=True)
    
    return {"data": summary, "total": len(summary)}

@api_router.get("/reports/user-activity")
async def get_user_activity_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None,
    user: dict = Depends(require_roles(["Admin", "Auditor", "Store In-Charge"]))
):
    """User activity log report from audit trail"""
    query = {}
    if start_date:
        query["timestamp"] = {"$gte": start_date}
    if end_date:
        if "timestamp" in query:
            query["timestamp"]["$lte"] = end_date
        else:
            query["timestamp"] = {"$lte": end_date}
    if user_id:
        query["performed_by"] = user_id
    
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).to_list(10000)
    
    return {"data": logs, "total": len(logs)}

@api_router.get("/reports/reprint-log")
async def get_reprint_log_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(require_roles(["Admin", "Auditor", "Store In-Charge"]))
):
    """Reprint sticker log report"""
    query = {"action": "reprint"}
    if start_date:
        query["printed_at"] = {"$gte": start_date}
    if end_date:
        if "printed_at" in query:
            query["printed_at"]["$lte"] = end_date
        else:
            query["printed_at"] = {"$lte": end_date}
    
    logs = await db.print_logs.find(query, {"_id": 0}).sort("printed_at", -1).to_list(10000)
    
    # Enrich with label info
    for log in logs:
        label = await db.labels.find_one({"label_id": log.get("label_id")}, {"_id": 0})
        if label:
            log["material_code"] = label.get("material_code")
            log["batch_number"] = label.get("batch_number")
            log["grn_number"] = label.get("grn_number")
    
    return {"data": logs, "total": len(logs)}

@api_router.get("/reports/stock-reconciliation")
async def get_stock_reconciliation_report(
    material_code: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Stock reconciliation report - system stock vs bin stock"""
    mat_query = {"current_stock": {"$gt": 0}}
    if material_code:
        mat_query["material_code"] = {"$regex": material_code, "$options": "i"}
    
    materials = await db.materials.find(mat_query, {"_id": 0}).to_list(1000)
    
    reconciliation = []
    for mat in materials:
        # Get total in bins
        bin_stock = await db.bins.aggregate([
            {"$match": {"material_code": mat["material_code"]}},
            {"$group": {"_id": None, "total": {"$sum": "$current_stock"}}}
        ]).to_list(1)
        
        bin_total = bin_stock[0]["total"] if bin_stock else 0
        system_total = mat.get("current_stock", 0)
        variance = system_total - bin_total
        
        reconciliation.append({
            "material_code": mat["material_code"],
            "material_name": mat["name"],
            "system_stock": system_total,
            "bin_stock": bin_total,
            "variance": variance,
            "variance_percent": round((variance / system_total) * 100, 2) if system_total > 0 else 0,
            "status": "Match" if variance == 0 else ("Excess" if variance > 0 else "Shortage")
        })
    
    # Sort by variance descending
    reconciliation.sort(key=lambda x: abs(x["variance"]), reverse=True)
    
    return {"data": reconciliation, "total": len(reconciliation)}

@api_router.get("/reports/stock-summary")
async def get_stock_summary_report(
    category: Optional[str] = None,
    material_code: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if category:
        query["category"] = category
    if material_code:
        query["material_code"] = {"$regex": material_code, "$options": "i"}
    
    materials = await db.materials.find(query, {"_id": 0}).to_list(1000)
    return {"data": materials, "total": len(materials)}

@api_router.get("/reports/bin-utilization")
async def get_bin_utilization_report(
    zone: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if zone:
        query["zone"] = zone
    
    bins = await db.bins.find(query, {"_id": 0}).to_list(1000)
    
    # Calculate utilization
    for bin_doc in bins:
        bin_doc["utilization_percent"] = round((bin_doc.get("current_stock", 0) / bin_doc.get("capacity", 1)) * 100, 2)
    
    return {"data": bins, "total": len(bins)}

# Export endpoints
@api_router.get("/reports/export/excel")
async def export_excel(
    report_type: str = Query(..., description="Report type"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    material_code: Optional[str] = None,
    batch_number: Optional[str] = None,
    bin_code: Optional[str] = None,
    zone: Optional[str] = None,
    token: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Export any report to Excel"""
    # If token provided via query, verify it (for direct downloads)
    if token:
        user = await get_user_from_token(token)
    
    # Get report data based on type
    data = []
    headers = []
    title = ""
    
    if report_type == "grn-stock":
        result = await get_grn_stock_report(start_date, end_date, None, material_code, user)
        data = result["data"]
        headers = ["grn_number", "vendor_name", "po_number", "invoice_number", "total_received_quantity", "total_accepted_quantity", "total_rejected_quantity", "status", "created_at"]
        title = "GRN Stock Report"
    elif report_type == "batch-stock":
        result = await get_batch_stock_report(material_code, batch_number, start_date, end_date, user)
        data = result["data"]
        headers = ["grn_number", "material_code", "material_name", "batch_number", "received_quantity", "accepted_quantity", "manufacturing_date", "expiry_date", "bin_location"]
        title = "Batch Stock Report"
    elif report_type == "bin-stock":
        result = await get_bin_stock_report(zone, bin_code, None, material_code, user)
        data = result["data"]
        headers = ["bin_code", "zone", "aisle", "rack", "level", "capacity", "current_stock", "utilization_percent", "material_code", "status"]
        title = "Bin Stock Report"
    elif report_type == "movement-history":
        result = await get_movement_history_report(start_date, end_date, None, material_code, user)
        data = result["data"]
        headers = ["movement_type", "material_code", "quantity", "from_bin", "to_bin", "reference_type", "batch_number", "created_at"]
        title = "Movement History Report"
    elif report_type == "stock-aging":
        result = await get_stock_aging_report(30, material_code, user)
        data = result["data"]
        headers = ["material_code", "material_name", "batch_number", "quantity", "receipt_date", "age_days", "aging_bucket", "expiry_date"]
        title = "Stock Aging Report"
    elif report_type == "dead-slow-stock":
        result = await get_dead_slow_stock_report(90, material_code, user)
        data = result["data"]
        headers = ["material_code", "material_name", "category", "current_stock", "last_movement_date", "days_since_movement", "status"]
        title = "Dead/Slow Stock Report"
    elif report_type == "daily-summary":
        result = await get_daily_summary_report(start_date, end_date, user)
        data = result["data"]
        headers = ["date", "inward_count", "inward_qty", "outward_count", "outward_qty", "transfer_count", "transfer_qty"]
        title = "Daily Summary Report"
    elif report_type == "putaway-pending":
        result = await get_putaway_pending_report(material_code, user)
        data = result["data"]
        headers = ["grn_number", "material_code", "quantity", "bin_code", "status", "created_at"]
        title = "Putaway Pending Report"
    elif report_type == "stock-reconciliation":
        result = await get_stock_reconciliation_report(material_code, user)
        data = result["data"]
        headers = ["material_code", "material_name", "system_stock", "bin_stock", "variance", "variance_percent", "status"]
        title = "Stock Reconciliation Report"
    elif report_type == "stock-summary":
        result = await get_stock_summary_report(None, material_code, user)
        data = result["data"]
        headers = ["material_code", "name", "category", "uom", "current_stock", "stock_method", "min_stock_level", "reorder_point"]
        title = "Stock Summary Report"
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")
    
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]  # Excel sheet name limit
    
    # Add title
    ws.append([title])
    ws.append([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
    ws.append([])
    
    # Add headers
    ws.append([h.replace("_", " ").title() for h in headers])
    
    # Add data
    for row in data:
        ws.append([str(row.get(h, "")) for h in headers])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={report_type}-{datetime.now().strftime('%Y%m%d')}.xlsx"}
    )

@api_router.get("/reports/export/pdf")
async def export_pdf(
    report_type: str = Query(..., description="Report type"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    material_code: Optional[str] = None,
    batch_number: Optional[str] = None,
    bin_code: Optional[str] = None,
    zone: Optional[str] = None,
    token: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Export any report to PDF"""
    # If token provided via query, verify it (for direct downloads)
    if token:
        user = await get_user_from_token(token)
    
    # Get report data based on type
    data = []
    headers = []
    title = ""
    
    if report_type == "grn-stock":
        result = await get_grn_stock_report(start_date, end_date, None, material_code, user)
        data = result["data"][:100]  # Limit for PDF
        headers = ["GRN #", "Vendor", "Received", "Accepted", "Rejected", "Status"]
        title = "GRN Stock Report"
        def row_mapper(r):
            return [r.get("grn_number", "")[:15], r.get("vendor_name", "")[:20], str(r.get("total_received_quantity", 0)), str(r.get("total_accepted_quantity", 0)), str(r.get("total_rejected_quantity", 0)), r.get("status", "")]
    elif report_type == "batch-stock":
        result = await get_batch_stock_report(material_code, batch_number, start_date, end_date, user)
        data = result["data"][:100]
        headers = ["Material", "Batch", "Qty", "Mfg Date", "Expiry", "Bin"]
        title = "Batch Stock Report"
        def row_mapper(r):
            return [r.get("material_code", ""), r.get("batch_number", "")[:15], str(r.get("accepted_quantity", 0)), r.get("manufacturing_date", "")[:10] if r.get("manufacturing_date") else "-", r.get("expiry_date", "")[:10] if r.get("expiry_date") else "-", r.get("bin_location", "-")]
    elif report_type == "bin-stock":
        result = await get_bin_stock_report(zone, bin_code, None, material_code, user)
        data = result["data"][:100]
        headers = ["Bin Code", "Zone", "Capacity", "Stock", "Util%", "Status"]
        title = "Bin Stock Report"
        def row_mapper(r):
            return [r.get("bin_code", ""), r.get("zone", ""), str(r.get("capacity", 0)), str(r.get("current_stock", 0)), str(r.get("utilization_percent", 0)), r.get("status", "")]
    elif report_type == "stock-summary":
        result = await get_stock_summary_report(None, material_code, user)
        data = result["data"][:100]
        headers = ["Code", "Name", "Category", "UOM", "Stock", "Method"]
        title = "Stock Summary Report"
        def row_mapper(r):
            return [r.get("material_code", ""), r.get("name", "")[:25], r.get("category", ""), r.get("uom", ""), str(r.get("current_stock", 0)), r.get("stock_method", "")]
    elif report_type == "movement-history":
        result = await get_movement_history_report(start_date, end_date, None, material_code, user)
        data = result["data"][:100]
        headers = ["Type", "Material", "Qty", "From", "To", "Date"]
        title = "Movement History Report"
        def row_mapper(r):
            return [r.get("movement_type", ""), r.get("material_code", ""), str(r.get("quantity", 0)), r.get("from_bin", "-"), r.get("to_bin", "-"), r.get("created_at", "")[:10]]
    elif report_type == "stock-aging":
        result = await get_stock_aging_report(30, material_code, user)
        data = result["data"][:100]
        headers = ["Material", "Batch", "Qty", "Age Days", "Bucket", "Expiry"]
        title = "Stock Aging Report"
        def row_mapper(r):
            return [r.get("material_code", ""), r.get("batch_number", "")[:12], str(r.get("quantity", 0)), str(r.get("age_days", 0)), r.get("aging_bucket", ""), r.get("expiry_date", "")[:10] if r.get("expiry_date") else "-"]
    elif report_type == "dead-slow-stock":
        result = await get_dead_slow_stock_report(90, material_code, user)
        data = result["data"][:100]
        headers = ["Material", "Name", "Stock", "Days Idle", "Status"]
        title = "Dead/Slow Stock Report"
        def row_mapper(r):
            return [r.get("material_code", ""), r.get("material_name", "")[:20], str(r.get("current_stock", 0)), str(r.get("days_since_movement", 0)), r.get("status", "")]
    elif report_type == "daily-summary":
        result = await get_daily_summary_report(start_date, end_date, user)
        data = result["data"][:100]
        headers = ["Date", "In #", "In Qty", "Out #", "Out Qty", "Xfer #"]
        title = "Daily Summary Report"
        def row_mapper(r):
            return [r.get("date", ""), str(r.get("inward_count", 0)), str(r.get("inward_qty", 0)), str(r.get("outward_count", 0)), str(r.get("outward_qty", 0)), str(r.get("transfer_count", 0))]
    elif report_type == "stock-reconciliation":
        result = await get_stock_reconciliation_report(material_code, user)
        data = result["data"][:100]
        headers = ["Material", "System", "Bin", "Variance", "Var%", "Status"]
        title = "Stock Reconciliation Report"
        def row_mapper(r):
            return [r.get("material_code", ""), str(r.get("system_stock", 0)), str(r.get("bin_stock", 0)), str(r.get("variance", 0)), str(r.get("variance_percent", 0)), r.get("status", "")]
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")
    
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, spaceAfter=20)
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    if start_date or end_date:
        elements.append(Paragraph(f"Period: {start_date or 'Start'} to {end_date or 'Now'}", styles['Normal']))
    elements.append(Spacer(1, 15))
    
    # Build table
    table_data = [headers]
    for row in data:
        table_data.append(row_mapper(row))
    
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a2744')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"Total Records: {len(data)}", styles['Normal']))
    
    doc.build(elements)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={report_type}-{datetime.now().strftime('%Y%m%d')}.pdf"}
    )

@api_router.get("/reports/types")
async def get_report_types(user: dict = Depends(get_current_user)):
    """Get available report types"""
    return {
        "reports": [
            {"id": "grn-stock", "name": "GRN-wise Stock Report", "description": "All GRNs with received quantities"},
            {"id": "batch-stock", "name": "Batch-wise Stock Report", "description": "Stock by batch/lot number"},
            {"id": "bin-stock", "name": "Bin-wise Stock Report", "description": "Bin locations with contents"},
            {"id": "movement-history", "name": "Material Movement History", "description": "All inward/outward movements"},
            {"id": "fifo-compliance", "name": "FIFO Compliance Report", "description": "FIFO material issue compliance"},
            {"id": "non-fifo-exceptions", "name": "Non-FIFO Exceptions", "description": "Cases where FIFO was bypassed"},
            {"id": "putaway-pending", "name": "Putaway Pending Report", "description": "Items awaiting putaway"},
            {"id": "stock-aging", "name": "Stock Aging Report", "description": "Stock by age category"},
            {"id": "dead-slow-stock", "name": "Dead/Slow Moving Stock", "description": "Materials with no recent movement"},
            {"id": "daily-summary", "name": "Daily Inward/Outward Summary", "description": "Daily movement totals"},
            {"id": "user-activity", "name": "User Activity Log", "description": "User actions audit trail"},
            {"id": "reprint-log", "name": "Reprint Sticker Log", "description": "Label reprint history"},
            {"id": "stock-reconciliation", "name": "Stock Reconciliation", "description": "System vs bin stock comparison"},
            {"id": "stock-summary", "name": "Stock Summary", "description": "Current stock levels"}
        ]
    }

# ===================== SEED DATA =====================

@api_router.post("/seed")
async def seed_database():
    """Seed database with initial admin user and sample data"""
    # Check if admin exists
    admin = await db.users.find_one({"email": "admin@warehouse.com"})
    if admin:
        return {"message": "Database already seeded"}
    
    # Create admin user
    admin_id = f"user_{uuid.uuid4().hex[:12]}"
    admin_doc = {
        "user_id": admin_id,
        "email": "admin@warehouse.com",
        "name": "System Admin",
        "role": "Admin",
        "password": hash_password("admin123"),
        "auth_type": "local",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(admin_doc)
    
    # Create sample materials
    materials = [
        {"material_code": "RAW-001", "name": "Steel Plates", "description": "6mm thick steel plates", "category": "Raw Materials", "uom": "KG", "stock_method": "FIFO"},
        {"material_code": "RAW-002", "name": "Aluminum Rods", "description": "10mm diameter aluminum rods", "category": "Raw Materials", "uom": "PCS", "stock_method": "FIFO"},
        {"material_code": "PKG-001", "name": "Cardboard Boxes", "description": "Standard shipping boxes", "category": "Packaging", "uom": "PCS", "stock_method": "LIFO"},
        {"material_code": "SPR-001", "name": "Lubricant Oil", "description": "Machine lubricant", "category": "Spares", "uom": "LTR", "stock_method": "FIFO"},
        {"material_code": "FIN-001", "name": "Finished Brackets", "description": "Metal brackets - finished goods", "category": "Finished Goods", "uom": "PCS", "stock_method": "FIFO"},
    ]
    
    for mat in materials:
        mat_id = f"mat_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        mat_doc = {
            "material_id": mat_id,
            **mat,
            "min_stock_level": 10,
            "max_stock_level": 1000,
            "reorder_point": 50,
            "current_stock": 0,
            "created_at": now,
            "updated_at": now,
            "created_by": admin_id
        }
        await db.materials.insert_one(mat_doc)
    
    # Create sample bins
    zones = ["A", "B", "C"]
    for zone in zones:
        for aisle in range(1, 4):
            for rack in range(1, 5):
                for level in range(1, 4):
                    bin_code = f"{zone}-{aisle:02d}-{rack:02d}-{level:02d}"
                    bin_id = f"bin_{uuid.uuid4().hex[:12]}"
                    now = datetime.now(timezone.utc).isoformat()
                    bin_doc = {
                        "bin_id": bin_id,
                        "bin_code": bin_code,
                        "zone": zone,
                        "aisle": str(aisle),
                        "rack": str(rack),
                        "level": str(level),
                        "capacity": 100,
                        "bin_type": "storage",
                        "current_stock": 0,
                        "status": "empty",
                        "material_id": None,
                        "material_code": None,
                        "created_at": now,
                        "updated_at": now
                    }
                    await db.bins.insert_one(bin_doc)
    
    return {"message": "Database seeded successfully", "admin_email": "admin@warehouse.com", "admin_password": "admin123"}

# Include the router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
