# Solar Manufacturing WMS - Complete User Documentation
## Enterprise Warehouse Management System for Solar Panel Manufacturing

**Version:** 1.0  
**Last Updated:** March 2026  
**System Type:** SAP WM-Compatible Enterprise WMS

---

# Table of Contents

1. [Introduction](#introduction)
2. [System Overview](#system-overview)
3. [Getting Started](#getting-started)
4. [User Roles & Permissions](#user-roles)
5. [Core Workflows](#core-workflows)
6. [Advanced Features](#advanced-features)
7. [Reports & Analytics](#reports)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

# 1. Introduction {#introduction}

## What is Solar Manufacturing WMS?

Solar Manufacturing WMS is an enterprise-grade warehouse management system specifically designed for solar panel manufacturing facilities. It provides complete traceability from raw material receipt to finished goods dispatch, with SAP WM-level capabilities.

## Key Capabilities

✅ **Quant-Level Tracking** - Track every unit in every bin  
✅ **Bill of Materials (BOM)** - Manage 23+ solar component types  
✅ **Quality Management** - 4 stock categories with QA workflows  
✅ **SLED Tracking** - Monitor shelf life and expiry dates  
✅ **Transfer Orders** - SAP-standard warehouse execution  
✅ **Physical Inventory** - Complete cycle counting workflows  
✅ **Advanced Reports** - 7 SAP WM-style reports  

## Who Should Use This System?

- **Warehouse Operators** - Daily receiving, putaway, picking operations
- **Store In-Charge** - Supervision, approvals, stock management
- **Inventory Controllers** - Stock analysis, reporting, auditing
- **Quality Team** - Material inspection and release
- **Management** - Strategic decisions based on real-time data
- **Auditors** - Complete audit trail access

---

# 2. System Overview {#system-overview}

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│           Solar Manufacturing WMS                    │
├─────────────────────────────────────────────────────┤
│                                                       │
│  Frontend (React)          Backend (FastAPI)         │
│  ┌──────────────┐         ┌──────────────┐         │
│  │ Dashboard    │◄────────┤ 37 API       │         │
│  │ Materials    │         │ Endpoints    │         │
│  │ GRN          │         │              │         │
│  │ Transfer Orders│        │ SAP WM       │         │
│  │ Reports      │         │ Features     │         │
│  │ Inventory    │         │              │         │
│  └──────────────┘         └──────┬───────┘         │
│                                   │                  │
│                                   ▼                  │
│                          ┌──────────────┐           │
│                          │  MongoDB     │           │
│                          │  Database    │           │
│                          └──────────────┘           │
└─────────────────────────────────────────────────────┘
```

## Solar Manufacturing Warehouse Zones

### Zone SC - Solar Cells (Temperature Controlled)
- **Purpose:** Storage of monocrystalline and polycrystalline solar cells
- **Environment:** Temperature-controlled, humidity-controlled
- **Bin Codes:** SC-01-01-01 to SC-02-01-01
- **Capacity:** 10,000 pieces per bin

### Zone GM - Glass & Materials
- **Purpose:** Storage of tempered glass, EVA sheets, backsheets
- **Environment:** Clean, dry environment
- **Bin Codes:** GM-01-01-01 to GM-02-01-01
- **Capacity:** 2,000 SQM per bin

### Zone FM - Frames & Mechanical
- **Purpose:** Aluminum frames, mounting hardware
- **Environment:** Standard warehouse conditions
- **Bin Codes:** FM-01-01-01 to FM-01-02-01
- **Capacity:** 1,000 MTR per bin

### Zone EC - Electrical Components
- **Purpose:** Junction boxes, connectors, diodes, ribbons
- **Environment:** ESD-protected area
- **Bin Codes:** EC-01-01-01 to EC-02-01-01
- **Capacity:** 5,000 pieces per bin

### Zone PK - Packaging
- **Purpose:** Pallets, corner guards, packaging materials
- **Bin Codes:** PK-01-01-01
- **Capacity:** 500 pieces per bin

### Zone QC - Quality Control
- **Purpose:** Materials under inspection (QINSP category)
- **Bin Codes:** QC-01-01-01
- **Capacity:** 1,000 pieces per bin

### Zone PR - Production Line Picking
- **Purpose:** Ready-to-pick materials for production lines
- **Bin Codes:** PR-01-01-01 to PR-02-01-01
- **Capacity:** 3,000 pieces per bin

## Stock Categories (SAP WM Standard)

### UNRES - Unrestricted Use
- **Color Code:** 🟢 Green
- **Meaning:** Available for production, ready to use
- **Typical Use:** All passed QA materials, normal stock

### QINSP - Quality Inspection
- **Color Code:** 🟡 Yellow
- **Meaning:** Under quality inspection, blocked for use
- **Typical Use:** Newly received materials, suspect batches

### BLOCK - Blocked Stock
- **Color Code:** 🔴 Red
- **Meaning:** Failed QA, damaged, or hold for investigation
- **Typical Use:** Rejected materials, damaged goods, recall items

### RETRN - Returns
- **Color Code:** 🟠 Orange
- **Meaning:** Customer returns, vendor returns
- **Typical Use:** RMA materials, return-to-vendor items

---

# 3. Getting Started {#getting-started}

## System Access

**URL:** https://emergent-extend.preview.emergentagent.com

### Login Credentials

**Administrator:**
- Email: admin@warehouse.com
- Password: admin123
- Access: Full system access

**Warehouse Operator:**
- Email: operator@test.com
- Password: test123
- Access: GRN, Putaway, Picking, Issues

**Store In-Charge:**
- Email: store@test.com
- Password: test123
- Access: All operations + approvals

**Inventory Controller:**
- Email: controller@test.com
- Password: test123
- Access: Read-only, reports, inquiries

## First-Time Setup Checklist

✅ **Step 1:** Log in with admin credentials  
✅ **Step 2:** Verify master data (Materials, Bins)  
✅ **Step 3:** Review user accounts  
✅ **Step 4:** Configure number ranges (if needed)  
✅ **Step 5:** Set up storage types and strategies  
✅ **Step 6:** Verify stock categories configuration  
✅ **Step 7:** Test GRN creation workflow  

---

# 4. User Roles & Permissions {#user-roles}

## Role Matrix

| Feature | Admin | Store In-Charge | Warehouse Operator | Inventory Controller | Auditor |
|---------|-------|-----------------|-------------------|---------------------|---------|
| View Materials | ✓ | ✓ | ✓ | ✓ | ✓ |
| Create/Edit Materials | ✓ | ✓ | ✗ | ✗ | ✗ |
| View Bins | ✓ | ✓ | ✓ | ✓ | ✓ |
| Block/Unblock Bins | ✓ | ✓ | ✗ | ✗ | ✗ |
| Create GRN | ✓ | ✓ | ✓ | ✗ | ✗ |
| Complete GRN | ✓ | ✓ | ✗ | ✗ | ✗ |
| Create Transfer Orders | ✓ | ✓ | ✓ | ✗ | ✗ |
| Confirm Transfer Orders | ✓ | ✓ | ✓ | ✗ | ✗ |
| Material Issues | ✓ | ✓ | ✓ | ✗ | ✗ |
| Physical Inventory | ✓ | ✓ | ✓ | ✗ | ✗ |
| Quality Inspection | ✓ | ✓ | ✗ | ✗ | ✗ |
| Stock Category Change | ✓ | ✓ | ✗ | ✗ | ✗ |
| View Reports | ✓ | ✓ | ✓ | ✓ | ✓ |
| Export Reports | ✓ | ✓ | ✗ | ✓ | ✓ |
| User Management | ✓ | ✗ | ✗ | ✗ | ✗ |
| Audit Trail | ✓ | ✓ | ✗ | ✓ | ✓ |

---

# 5. Core Workflows {#core-workflows}

## Workflow 1: Goods Receipt (Inbound Process)

### Overview
This is the complete workflow from receiving solar materials to making them available for production.

### Step-by-Step Process

#### Phase 1: Pre-Receipt Planning
**Duration:** Before truck arrival

1. **Review Purchase Order**
   - Navigate to: Dashboard → Procurement
   - Verify PO details: Vendor, Material, Quantity, Delivery date
   - Note special requirements (temperature control, ESD handling)

2. **Prepare Receiving Area**
   - Clear GR staging zone
   - Prepare inspection area if needed
   - Ready scanning equipment

#### Phase 2: Physical Receipt
**Duration:** 30-60 minutes  
**Responsible:** Warehouse Operator

1. **Create GRN (Goods Receipt Note)**
   ```
   Navigation: GRN → Create GRN
   
   Fields to Fill:
   - Vendor Name: e.g., "Longi Solar Technology"
   - PO Number: e.g., "PO-2026-001"
   - Invoice Number: e.g., "LONGI-INV-45678"
   - Receipt Date: Auto-filled (today)
   - Remarks: "Container LNGI2026001"
   ```

2. **Add Materials to GRN**
   ```
   Click: Add Item
   
   For Each Material:
   - Material Code: Select from dropdown (e.g., CELL-MONO-166)
   - Received Quantity: Count physically
   - Batch Number: From supplier label (e.g., LONGI-M10-20260327-A)
   - Manufacturing Date: From supplier document
   - Expiry Date: From supplier document (if applicable)
   - Storage Condition: Select (temperature_controlled / ambient)
   ```

3. **Example - Receiving Solar Cells:**
   ```
   Material: CELL-MONO-166 (Monocrystalline Solar Cell 166mm M10)
   Received Quantity: 20,000 PCS
   Batch Number: LONGI-M10-20260327-A
   Manufacturing Date: 2026-03-15
   Storage Condition: temperature_controlled
   Bin Location: SC-01-01-01 (auto-suggested by system)
   ```

4. **Save GRN**
   - Status: DRAFT
   - GRN Number: Auto-generated (e.g., GRN-20260330-1D13C9)

#### Phase 3: Quality Inspection
**Duration:** 2-24 hours  
**Responsible:** Quality Team

1. **System Auto-Creates:**
   - Transfer Requirement (TR) for inspection
   - Stock Category: QINSP (Quality Inspection)
   - Quants created in QC zone

2. **Quality Team Actions:**
   ```
   Navigation: Quality Inspection → Pending Items
   
   For Each Batch:
   - View Material: CELL-MONO-166
   - Batch: LONGI-M10-20260327-A
   - Quantity: 20,000 PCS
   - Location: QC-01-01-01
   
   Perform Inspection:
   - Visual inspection
   - Electrical testing (if required)
   - Dimensional checks
   - Sample testing
   
   Decision:
   [ ] PASS → Stock Category: QINSP → UNRES (Unrestricted)
   [ ] FAIL → Stock Category: QINSP → BLOCK (Blocked)
   [ ] PARTIAL → Split into UNRES + BLOCK
   ```

3. **QA Release Process:**
   ```
   API Call (Automated):
   POST /api/wm/quality-inspection/release
   
   Body:
   {
     "material_code": "CELL-MONO-166",
     "batch_number": "LONGI-M10-20260327-A",
     "inspection_result": "PASS",
     "approved_quantity": 19800,
     "rejected_quantity": 200
   }
   
   System Actions:
   - Moves 19,800 PCS to UNRES category
   - Moves 200 PCS to BLOCK category
   - Creates audit log
   - Sends notification
   ```

#### Phase 4: Putaway (Storage)
**Duration:** 1-2 hours  
**Responsible:** Warehouse Operator

1. **System Auto-Creates Transfer Order (TO)**
   ```
   Trigger: QA Release to UNRES
   
   TO Details:
   - TO Number: TO-20260330-ABC123
   - TO Type: PUTAWAY
   - Source: QC-01-01-01 (Quality area)
   - Destination: SC-01-01-01 (Solar cells storage)
   - Material: CELL-MONO-166
   - Quantity: 19,800 PCS
   - Strategy: Next Empty Bin (if SC-01-01-01 full)
   ```

2. **Execute Putaway:**
   ```
   Navigation: Transfer Orders → Open TOs
   
   Operator Actions:
   1. Select TO: TO-20260330-ABC123
   2. Scan source bin: QC-01-01-01
   3. Scan material: CELL-MONO-166
   4. Confirm quantity: 19,800 PCS
   5. Scan destination bin: SC-01-01-01
   6. Place material physically
   7. Confirm TO
   
   System Actions:
   - Creates Quant in SC-01-01-01
   - Updates bin utilization
   - Records movement
   - Updates material stock level
   ```

3. **Final Status:**
   ```
   Quant Created:
   - Quant ID: quant_abc123def456
   - Material: CELL-MONO-166
   - Bin: SC-01-01-01
   - Quantity: 19,800 PCS
   - Stock Category: UNRES
   - Batch: LONGI-M10-20260327-A
   - SLED: 2028-03-15
   - Storage Type: SC (Solar Cells)
   ```

#### Phase 5: Complete GRN
**Duration:** 5 minutes  
**Responsible:** Store In-Charge

1. **Verify All Items Inspected & Stored**
   ```
   Navigation: GRN → View GRN Details
   
   Check:
   ✓ All items inspected
   ✓ All items with putaway completed
   ✓ Labels generated
   ✓ No pending actions
   ```

2. **Complete GRN:**
   ```
   Button: Complete GRN
   
   System Actions:
   - Updates GRN status: COMPLETED
   - Finalizes stock updates
   - Generates reports
   - Archives documents
   ```

---

## Workflow 2: Production Material Issue (Outbound Process)

### Overview
Issuing materials from warehouse to solar panel assembly lines.

### Step-by-Step Process

#### Phase 1: Production Planning
**Duration:** Planning day  
**Responsible:** Production Planner

1. **Create Production Order**
   - Production Order: PO-SOLAR-001
   - Product: 72-Cell Solar Module
   - Quantity: 1,000 modules
   - BOM Required:
     ```
     Per Module (72-cell):
     - Solar Cells (CELL-MONO-166): 72 PCS
     - Glass (GLASS-ARC-3.2): 2.1 SQM
     - EVA Film (EVA-FAST-0.45): 4.5 SQM
     - Backsheet (BACK-TPT-WHT): 2.2 SQM
     - Junction Box (JBOX-IP67-3D): 1 PCS
     - Frame (FRAME-AL-35MM): 6.3 MTR
     - Connectors (CONN-MC4): 2 PCS (1 male, 1 female)
     - Ribbon (RIBBON-2.0MM): 150 MTR
     
     For 1,000 Modules:
     - Solar Cells: 72,000 PCS
     - Glass: 2,100 SQM
     - EVA Film: 4,500 SQM
     - Backsheet: 2,200 SQM
     - Junction Boxes: 1,000 PCS
     - Frame: 6,300 MTR
     - Connectors: 2,000 PCS
     - Ribbon: 150,000 MTR
     ```

2. **System Auto-Creates Transfer Requirements (TR)**
   ```
   For Each Material:
   
   TR-20260330-001:
   - Material: CELL-MONO-166
   - Required Qty: 72,000 PCS
   - Open Qty: 72,000 PCS
   - TR Type: GI (Goods Issue)
   - Reference: PO-SOLAR-001
   - Priority: 1 (Highest)
   - Status: OPEN
   
   [Similar TRs for all BOM items]
   ```

#### Phase 2: Picking Strategy Application
**Duration:** Automatic  
**System Process:** FIFO/LIFO/FEFO

1. **System Determines Picking Strategy:**
   ```
   For CELL-MONO-166 (FIFO Strategy):
   
   Available Quants (sorted by GR date):
   1. Bin: SC-01-01-01, Qty: 19,800, Batch: LONGI-M10-20260327-A, GR Date: 2026-03-27
   2. Bin: SC-01-01-02, Qty: 15,000, Batch: LONGI-M12-20260327-B, GR Date: 2026-03-28
   3. Bin: SC-01-02-01, Qty: 40,000, Batch: LONGI-M10-20260329-C, GR Date: 2026-03-29
   
   Picking Recommendation (FIFO - oldest first):
   - Pick 19,800 from SC-01-01-01 (Batch A)
   - Pick 15,000 from SC-01-01-02 (Batch B)
   - Pick 37,200 from SC-01-02-01 (Batch C)
   Total: 72,000 PCS
   ```

2. **For EVA Film (FEFO Strategy - expiry-based):**
   ```
   Available Quants (sorted by SLED):
   1. Bin: GM-01-02-01, Qty: 8,000, SLED: 2027-03-22 (expiring first)
   2. Bin: GM-01-03-01, Qty: 6,000, SLED: 2027-06-15
   
   Picking Recommendation (FEFO):
   - Pick 4,500 from GM-01-02-01 (expires soonest)
   - Remaining 3,500 in GM-01-02-01
   ```

#### Phase 3: Create Transfer Orders
**Duration:** Automatic  
**System Process:**

1. **System Creates TOs from TRs:**
   ```
   Navigation: Transfer Orders → Create from TR
   
   TO-20260330-PICK-001:
   - TO Type: PICKING
   - Material: CELL-MONO-166
   - Items:
     
     Item 1:
     - Source Bin: SC-01-01-01
     - Source Quant: quant_abc123
     - Destination: PR-01-01-01 (Production picking area)
     - Target Qty: 19,800 PCS
     - Batch: LONGI-M10-20260327-A
     
     Item 2:
     - Source Bin: SC-01-01-02
     - Source Quant: quant_def456
     - Destination: PR-01-01-01
     - Target Qty: 15,000 PCS
     - Batch: LONGI-M12-20260327-B
     
     Item 3:
     - Source Bin: SC-01-02-01
     - Source Quant: quant_ghi789
     - Destination: PR-01-01-01
     - Target Qty: 37,200 PCS
     - Batch: LONGI-M10-20260329-C
   ```

#### Phase 4: Pick Execution
**Duration:** 2-4 hours  
**Responsible:** Warehouse Operator

1. **Operator Workflow:**
   ```
   Device: Handheld scanner or tablet
   
   Step 1: View Picking List
   Navigation: Transfer Orders → My Open TOs
   
   Step 2: For Each Pick Location
   - Navigate to: SC-01-01-01
   - Scan bin barcode: SC-01-01-01
   - System displays: CELL-MONO-166, Qty: 19,800
   - Pick material physically
   - Scan material: CELL-MONO-166
   - Confirm quantity: 19,800 (or actual if different)
   - Place in staging area or cart
   
   Step 3: Move to Destination
   - Navigate to: PR-01-01-01
   - Scan destination bin: PR-01-01-01
   - Place material
   - Confirm putaway
   
   Step 4: Repeat for all items
   ```

2. **Difference Handling:**
   ```
   If Actual Quantity ≠ Target Quantity:
   
   Example:
   - Target: 19,800 PCS
   - Actual Found: 19,750 PCS
   - Difference: -50 PCS
   
   System Actions:
   - Records difference: -50 PCS
   - Flags for investigation
   - Continues with actual quantity
   - Generates variance report
   - Admin notified for > 1% variance
   ```

#### Phase 5: Confirm Transfer Order
**Duration:** 5 minutes  
**Responsible:** Warehouse Operator

1. **Confirmation Process:**
   ```
   Navigation: Transfer Orders → Confirm TO
   
   TO: TO-20260330-PICK-001
   
   Confirmed Quantities:
   - Item 1: 19,750 PCS (variance: -50)
   - Item 2: 15,000 PCS (OK)
   - Item 3: 37,200 PCS (OK)
   - Total: 71,950 PCS
   
   Button: Confirm TO
   
   System Actions:
   - Updates source quants (reduces quantity)
   - Creates destination quants
   - Records stock movements
   - Updates TR (reduces open quantity)
   - Generates pick list report
   ```

#### Phase 6: Material Issue to Production
**Duration:** Ongoing  
**Responsible:** Production Line

1. **Issue from Staging:**
   ```
   Navigation: Material Issues → Create Issue
   
   Issue Document:
   - Issue Type: Production
   - Cost Center: ASSEMBLY-LINE-1
   - Production Order: PO-SOLAR-001
   
   Materials:
   - CELL-MONO-166: 71,950 PCS
   - [All other BOM items]
   
   System Actions:
   - Reduces UNRES stock
   - Creates consumption record
   - Updates production order
   - Triggers replenishment if below reorder point
   ```

---

## Workflow 3: Physical Inventory (Cycle Count)

### Overview
Regular cycle counting to ensure system stock matches physical stock.

### Complete 10-Step Process

#### Step 1: Create Inventory Document
**Duration:** 10 minutes  
**Responsible:** Inventory Controller

```
Navigation: Physical Inventory → Create Document

Fields:
- Inventory Type: CYCLE_COUNT
- Storage Type: SC (Solar Cells)
- Bin Codes: Select specific bins or all bins in SC zone
- Planned Count Date: 2026-04-01
- Count Team: Assign counters

Example:
- Document: PI-20260330-ABC123
- Type: CYCLE_COUNT
- Scope: SC-01-01-01, SC-01-01-02, SC-01-02-01
- Total Items: 15 quants to count

System Actions:
- Creates PI document
- Generates count sheets
- Status: CREATED
```

#### Step 2: Freeze Stock
**Duration:** Instant  
**Responsible:** Store In-Charge

```
Navigation: Physical Inventory → PI-20260330-ABC123 → Freeze

Action: Click "Freeze Stock"

System Actions:
- Blocks all movements in/out of selected bins
- Status: FROZEN
- No putaway/picking allowed
- Timestamp: 2026-03-30 10:00 AM
- Expected duration: 4 hours

Notifications Sent:
- Warehouse operators: "Bins SC-01-xx frozen for count"
- Production: "Material availability affected"
```

#### Step 3: Generate Count Sheets
**Duration:** Automatic  
**System Process:**

```
Count Sheet Example:

╔═══════════════════════════════════════════════════════════╗
║        PHYSICAL INVENTORY COUNT SHEET                     ║
║        Document: PI-20260330-ABC123                       ║
║        Date: 2026-03-30          Counter: _________       ║
╠═══════════════════════════════════════════════════════════╣
║ Bin: SC-01-01-01                                          ║
╠════════════════╦══════════╦═══════════╦══════════╦════════╣
║ Material       ║ Batch    ║ Book Qty  ║ Count Qty║ Sign   ║
╠════════════════╬══════════╬═══════════╬══════════╬════════╣
║ CELL-MONO-166  ║ LONGI-A  ║ 19,800    ║          ║        ║
╠════════════════╬══════════╬═══════════╬══════════╬════════╣
║ CELL-MONO-182  ║ LONGI-B  ║ 15,000    ║          ║        ║
╠════════════════╬══════════╬═══════════╬══════════╬════════╣
║                ║          ║           ║          ║        ║
╚════════════════╩══════════╩═══════════╩══════════╩════════╝

Instructions:
1. Count all materials in bin
2. Verify batch numbers
3. Record actual quantity
4. Sign and date
5. Report immediately if >5% variance
```

#### Step 4: First Count
**Duration:** 2-4 hours  
**Responsible:** Counter (Warehouse Operator)

```
Physical Counting Process:

For Bin SC-01-01-01:

1. Locate bin physically
2. Remove all materials
3. Count each item:
   
   Material: CELL-MONO-166
   Batch: LONGI-M10-20260327-A
   Book Quantity: 19,800 PCS
   Actual Count: 19,750 PCS
   Difference: -50 PCS (-0.25%)
   Reason: Unknown
   
4. Record on count sheet
5. Return materials to bin
6. Sign count sheet

Enter Count in System:
Navigation: Physical Inventory → Count Entry

For Each Item:
- Select Count Item: CI_001
- Material: CELL-MONO-166
- Book Qty: 19,800
- Counted Qty: 19,750
- Difference: -50
- Counter: operator@test.com
- Timestamp: 2026-03-30 11:30 AM

System Actions:
- Calculates variance: -0.25%
- Status: COUNTED
- Flags for recount if variance > 2%
```

#### Step 5: Identify Differences
**Duration:** Automatic  
**System Process:**

```
Variance Analysis:

╔════════════════════════════════════════════════════════╗
║              INVENTORY VARIANCE REPORT                 ║
║              Document: PI-20260330-ABC123              ║
╠════════════════════════════════════════════════════════╣
║ Total Items Counted: 15                                ║
║ Items with Variance: 3                                 ║
║ Zero Variance: 12                                      ║
╠════════════════╦═══════╦═══════╦══════════╦═══════════╣
║ Material       ║ Book  ║ Count ║ Diff     ║ Variance% ║
╠════════════════╬═══════╬═══════╬══════════╬═══════════╣
║ CELL-MONO-166  ║19,800 ║19,750 ║ -50      ║ -0.25%    ║
╠════════════════╬═══════╬═══════╬══════════╬═══════════╣
║ EVA-FAST-0.45  ║ 8,000 ║ 8,150 ║ +150     ║ +1.88%    ║
╠════════════════╬═══════╬═══════╬══════════╬═══════════╣
║ JBOX-IP67-3D   ║ 3,000 ║ 2,920 ║ -80      ║ -2.67% ⚠️ ║
╚════════════════╩═══════╩═══════╩══════════╩═══════════╝

Recount Required:
- JBOX-IP67-3D (variance > 2%)

Auto-Approve (variance < 2%):
- CELL-MONO-166
- EVA-FAST-0.45
```

#### Step 6: Recount (for items with >2% variance)
**Duration:** 30 minutes  
**Responsible:** Different Counter

```
Recount Process:

Material: JBOX-IP67-3D
First Count: 2,920 PCS (by operator@test.com)
Book Quantity: 3,000 PCS
Variance: -80 PCS (-2.67%)

Recount By: store@test.com (different person)

Recount Steps:
1. Re-verify bin location
2. Remove all boxes
3. Count systematically:
   - Box 1: 100 PCS
   - Box 2: 100 PCS
   - ...
   - Box 29: 100 PCS
   - Box 30: 80 PCS
   
Total Recount: 2,980 PCS

Enter Recount:
- Recount Qty: 2,980 PCS
- Recounted By: store@test.com
- Final Difference: -20 PCS (-0.67%)
- Reason: "Partial box found behind pallet"

System Actions:
- Updates difference to -20
- Status: RECOUNTED
- Variance now acceptable
```

#### Step 7: Investigate Large Variances
**Duration:** Variable  
**Responsible:** Store In-Charge

```
Investigation Process:

For variances > 5% or high-value items:

Investigation Checklist:
□ Check recent movements (last 7 days)
□ Review picking/putaway logs
□ Verify batch numbers
□ Check for damaged/returned items
□ Interview counters
□ Review CCTV (if available)
□ Check for system entry errors

Investigation Report:
- Material: JBOX-IP67-3D
- Variance: -20 PCS
- Root Cause: "Partial box placed in wrong bin during last putaway"
- Corrective Action: "Retrain operators on putaway verification"
- Approval: Store In-Charge
```

#### Step 8: Approval
**Duration:** 15 minutes  
**Responsible:** Store In-Charge or Management

```
Approval Workflow:

Navigation: Physical Inventory → PI-20260330-ABC123 → Review

Review Summary:
- Total Items: 15
- Counted: 15
- Recounted: 1
- Total Variance Qty: -70 PCS
- Total Variance Value: ₹3,500

Decision Matrix:
- Variance < ₹5,000: Store In-Charge can approve
- Variance ₹5,000-₹50,000: Management approval required
- Variance > ₹50,000: Finance + Management approval

Action: Approve

System Actions:
- Status: APPROVED
- Ready for posting
- Generates final report
```

#### Step 9: Post Inventory Differences
**Duration:** 5 minutes  
**Responsible:** Store In-Charge

```
Posting Process:

Navigation: Physical Inventory → PI-20260330-ABC123 → Post

Button: Post Differences

System Actions:
For Each Variance:

1. CELL-MONO-166: -50 PCS
   - Reduces quant quantity: 19,800 → 19,750
   - Creates adjustment movement (INVENTORY_ADJUSTMENT)
   - Updates material master: current_stock -= 50
   - Records in audit log

2. EVA-FAST-0.45: +150 SQM
   - Increases quant quantity: 8,000 → 8,150
   - Creates adjustment movement (INVENTORY_ADJUSTMENT)
   - Updates material master: current_stock += 150
   - Records in audit log

3. JBOX-IP67-3D: -20 PCS
   - Reduces quant quantity: 3,000 → 2,980
   - Creates adjustment movement
   - Updates material master
   - Records in audit log

Final Status:
- PI Document: POSTED
- All quants updated
- Stock movements recorded
- Audit trail complete
- Variance report generated
```

#### Step 10: Unfreeze Stock & Close
**Duration:** Instant  
**System Process:**

```
Unfreeze Actions:

Navigation: Physical Inventory → PI-20260330-ABC123 → Complete

System Actions:
- Removes freeze on bins
- Status: COMPLETED
- Allows normal operations
- Archives PI document
- Sends notifications:
  - Warehouse: "Bins SC-01-xx available for operations"
  - Production: "Material availability restored"
  - Management: "PI completed, variance: ₹3,500"

Generate Reports:
- Inventory Variance Report
- Adjustment Summary
- Count Sheet Archive
- Performance Metrics

Next Cycle:
- Schedule next count: +30 days
- High-variance items: +15 days (more frequent)
```

---

## Workflow 4: Quality Inspection & Release

### Overview
Complete quality management workflow from inspection to stock release.

### Step-by-Step Process

#### Phase 1: Material Arrives for Inspection
**Trigger:** GRN creation with new materials

```
Automatic System Actions:

When GRN Created:
1. Creates quants with stock category: QINSP
2. Assigns to QC zone bins
3. Notifies QA team
4. Creates inspection tasks

Example:
Material: CELL-MONO-166
Batch: LONGI-M10-20260327-A
Quantity: 20,000 PCS
Location: QC-01-01-01
Stock Category: QINSP (Quality Inspection)
Age: 0 days
```

#### Phase 2: View Pending Inspections
**Responsible:** Quality Team

```
Navigation: Quality Inspection → Pending Items

Dashboard View:

╔═══════════════════════════════════════════════════════════╗
║           PENDING QUALITY INSPECTIONS                     ║
╠═══════════════════════════════════════════════════════════╣
║ Total Batches: 3                                          ║
║ Urgent (>3 days): 0                                       ║
║ Normal (<3 days): 3                                       ║
╠════════════════╦══════════╦═══════╦════════╦══════════════╣
║ Material       ║ Batch    ║ Qty   ║ Age    ║ Priority     ║
╠════════════════╬══════════╬═══════╬════════╬══════════════╣
║ CELL-MONO-166  ║ LONGI-A  ║20,000 ║ 1 day  ║ HIGH         ║
╠════════════════╬══════════╬═══════╬════════╬══════════════╣
║ EVA-FAST-0.45  ║ EVA-B    ║ 8,000 ║ 2 days ║ MEDIUM       ║
╠════════════════╬══════════╬═══════╬════════╬══════════════╣
║ JBOX-IP67-3D   ║ TE-C     ║ 3,000 ║ 0 days ║ LOW          ║
╚════════════════╩══════════╩═══════╩════════╩══════════════╝

Select: CELL-MONO-166
```

#### Phase 3: Perform Inspection
**Duration:** 2-24 hours  
**Responsible:** QA Inspector

```
Inspection Checklist for Solar Cells:

Material: CELL-MONO-166 (Monocrystalline 166mm M10)
Batch: LONGI-M10-20260327-A
Quantity: 20,000 PCS

Visual Inspection (100% inspection):
□ No chips or cracks
□ Surface clean, no scratches
□ Uniform color
□ No discoloration
□ Proper packaging

Dimensional Checks (Sample: 50 PCS):
□ Cell size: 166mm ± 0.5mm ✓
□ Thickness: 180µm ± 10µm ✓
□ Corner radius: Within spec ✓

Electrical Testing (Sample: 20 PCS):
□ Open circuit voltage: 0.68V ± 0.02V ✓
□ Short circuit current: >9A ✓
□ Efficiency: >22.5% ✓
□ Series resistance: <1Ω ✓

Results:
- Sample Pass Rate: 100%
- Defects Found: 200 PCS (minor chips)
- Decision: PARTIAL PASS
  - Accepted: 19,800 PCS
  - Rejected: 200 PCS
```

#### Phase 4: QA Decision & Release
**Responsible:** QA Manager

```
Quality Decision:

Navigation: Quality Inspection → Release Batch

Decision Form:
- Material: CELL-MONO-166
- Batch: LONGI-M10-20260327-A
- Inspection Result: [ ] PASS  [✓] PARTIAL  [ ] FAIL

Quantities:
- Received: 20,000 PCS
- Approved: 19,800 PCS → Stock Category: UNRES
- Rejected: 200 PCS → Stock Category: BLOCK

Rejection Reason:
"Minor chips on cell edges. Cosmetic defect, functional OK.
Request vendor credit for 200 PCS."

Disposition of Rejected:
[ ] Return to Vendor
[✓] Hold for Rework
[ ] Scrap

API Call Executed:
POST /api/wm/quality-inspection/release

{
  "material_code": "CELL-MONO-166",
  "batch_number": "LONGI-M10-20260327-A",
  "inspection_result": "PARTIAL",
  "approved_quantity": 19800,
  "rejected_quantity": 200,
  "rejection_reason": "Minor chips on cell edges",
  "inspector": "qa_inspector@company.com",
  "inspector_name": "John Doe",
  "inspection_date": "2026-03-30T14:30:00Z"
}

System Actions:
1. Creates 2 quants:
   
   Quant 1 (Approved):
   - Quant ID: quant_approved_001
   - Quantity: 19,800 PCS
   - Stock Category: UNRES (Unrestricted)
   - Bin: SC-01-01-01 (moved from QC to storage)
   
   Quant 2 (Rejected):
   - Quant ID: quant_rejected_001
   - Quantity: 200 PCS
   - Stock Category: BLOCK (Blocked)
   - Bin: QC-01-01-01 (remains in QC)
   - Blocked: true
   - Block Reason: "Failed QA - minor chips"

2. Creates Transfer Order for approved stock:
   - TO Type: PUTAWAY
   - Source: QC-01-01-01
   - Destination: SC-01-01-01
   - Quantity: 19,800 PCS

3. Generates documents:
   - QA Certificate
   - Rejection Report
   - COA (Certificate of Analysis)

4. Sends notifications:
   - Warehouse: "19,800 PCS released for putaway"
   - Procurement: "200 PCS rejected - vendor credit needed"
   - Production: "CELL-MONO-166 available: 19,800 PCS"

5. Audit log:
   - Action: QA_RELEASE
   - User: qa_inspector@company.com
   - Timestamp: 2026-03-30T14:30:00Z
   - Details: Full inspection report attached
```

#### Phase 5: Handle Rejected Stock
**Responsible:** Procurement/Warehouse

```
Rejected Material Process:

Option 1: Return to Vendor
Navigation: Material Issues → Create Return

Return Document:
- Return Type: Vendor Return
- Material: CELL-MONO-166
- Batch: LONGI-M10-20260327-A
- Quantity: 200 PCS
- Reason: Quality rejection
- Vendor: Longi Solar Technology
- RMA Number: RMA-2026-001
- Expected Credit: ₹10,000

Stock Category Change:
BLOCK → RETRN (Returns)

Option 2: Hold for Rework/Use
- Keep in BLOCK category
- Flag for internal use (non-critical applications)
- Discount pricing

Option 3: Scrap
- Create scrap document
- Remove from inventory
- Record loss in accounting
```

---

## Workflow 5: Bin-to-Bin Transfer

### Overview
Moving materials between bins within the same warehouse (Movement Type 999).

### When to Use
- Reorganization
- Moving from bulk to picking area
- Consolidating scattered stock
- Moving slow movers to less accessible bins

### Step-by-Step Process

#### Step 1: Identify Transfer Need
```
Scenario: Moving solar cells from bulk storage to production picking area

Current Situation:
- Material: CELL-MONO-166
- Current Location: SC-01-01-01 (Bulk storage)
- Current Quantity: 19,800 PCS
- Issue: Production line is far from SC zone

Solution:
- Move 5,000 PCS to PR-01-01-01 (Production picking area)
- Benefit: Reduce travel time for daily picking
```

#### Step 2: Create Bin-to-Bin Transfer
```
Navigation: Warehouse Operations → Bin-to-Bin Transfer

Transfer Form:
- Source Bin: SC-01-01-01
- Destination Bin: PR-01-01-01
- Material: CELL-MONO-166
- Quantity: 5,000 PCS
- Batch: LONGI-M10-20260327-A
- Stock Category: UNRES
- Reason: "Replenish production picking area for Line 1"

Validation Checks:
✓ Source bin has sufficient quantity
✓ Destination bin has capacity
✓ Material compatible with destination zone
✓ No bin blocking active
✓ User has permission

API Call:
POST /api/wm/bin-to-bin-transfer

{
  "source_bin_code": "SC-01-01-01",
  "destination_bin_code": "PR-01-01-01",
  "material_id": "mat_abc123",
  "quantity": 5000,
  "batch_number": "LONGI-M10-20260327-A",
  "stock_category": "UNRES",
  "reason": "Replenish production picking area for Line 1"
}
```

#### Step 3: Execute Transfer
```
Physical Movement:
1. Operator receives TO: TO-BIN-20260330-ABC123
2. Navigates to: SC-01-01-01
3. Scans source bin
4. Picks 5,000 PCS (verify batch)
5. Transports to PR-01-01-01
6. Scans destination bin
7. Places material
8. Confirms in system

System Updates:
Source Bin (SC-01-01-01):
- Old Quantity: 19,800 PCS
- New Quantity: 14,800 PCS
- Quant updated

Destination Bin (PR-01-01-01):
- Old Quantity: 0 PCS
- New Quantity: 5,000 PCS
- New quant created or existing updated

Movement Record:
- Movement ID: mov_bin2bin_001
- Movement Type: BIN_TO_BIN
- Movement Code: 999 (SAP standard)
- Source: SC-01-01-01
- Destination: PR-01-01-01
- Quantity: 5,000 PCS
- Timestamp: 2026-03-30T15:45:00Z
- User: operator@test.com

No Impact on:
- Material total stock (remains same)
- Stock value
- Accounting (internal movement only)
```

---

# 6. Advanced Features {#advanced-features}

## Feature 1: SLED (Shelf Life Expiry Date) Management

### Overview
Critical for materials with limited shelf life (EVA films, sealants, batteries).

### Configuration
```
Materials with SLED:
- EVA-FAST-0.45: 12 months shelf life
- EVA-STD-0.50: 12 months
- SEAL-SIL-RTV: 12 months
- CELL-MONO-166: 24 months (degradation concern)
```

### Monitoring Process
```
Navigation: Reports → SLED Expiry Alert

Alert Thresholds:
- Red Alert: Expired
- Yellow Alert: Expiring in 30 days
- Orange Alert: Expiring in 60 days

Example Alert:

╔═══════════════════════════════════════════════════════════╗
║              SLED EXPIRY ALERT REPORT                     ║
║              Generated: 2026-03-30                        ║
╠═══════════════════════════════════════════════════════════╣
║ 🔴 EXPIRED (Use Immediately or Scrap):                   ║
╠════════════════╦══════════╦═══════╦════════╦═════════════╣
║ Material       ║ Batch    ║ Qty   ║ SLED   ║ Location    ║
╠════════════════╬══════════╬═══════╬════════╬═════════════╣
║ SEAL-SIL-RTV   ║ SIL-2025 ║ 50 KG ║2026-03║ GM-01-02    ║
╠════════════════╩══════════╩═══════╩════════╩═════════════╣
║ 🟡 EXPIRING IN 30 DAYS:                                  ║
╠════════════════╦══════════╦═══════╦════════╦═════════════╣
║ EVA-FAST-0.45  ║ EVA-2026 ║8,000  ║2026-04║ GM-01-02-01 ║
╚════════════════╩══════════╩═══════╩════════╩═════════════╝

Action Required:
- Expired: Move to BLOCK, request disposal approval
- Expiring: Use FEFO picking strategy (First Expired First Out)
```

### FEFO Picking Strategy
```
Scenario: Production needs 5,000 SQM EVA film

Available Stock:
1. Batch EVA-2026-A: 8,000 SQM, SLED: 2026-04-30 (30 days)
2. Batch EVA-2026-B: 10,000 SQM, SLED: 2026-07-15 (107 days)
3. Batch EVA-2026-C: 5,000 SQM, SLED: 2026-09-01 (155 days)

FEFO Recommendation:
Pick 5,000 SQM from Batch EVA-2026-A (expires soonest)

System automatically creates TO with FEFO picks.
```

---

## Feature 2: Storage Optimization

### Overview
AI-powered recommendations for warehouse efficiency.

### Optimization Types

#### 1. Slow Mover Identification
```
Navigation: Reports → Storage Optimization

Report Output:

╔═══════════════════════════════════════════════════════════╗
║           STORAGE OPTIMIZATION RECOMMENDATIONS            ║
╠═══════════════════════════════════════════════════════════╣
║ Type: RELOCATE_SLOW_MOVER                                 ║
║ Priority: MEDIUM                                          ║
╠════════════════════════════════════════════════════════════
║ Material: PKG-CORNER-PROT                                 ║
║ Current Location: PR-01-01-01 (Production picking)       ║
║ Current Storage Type: PICK                                ║
║ Issue: No movement in 45 days                             ║
║ Recommendation: Move to BULK storage                      ║
║ Suggested Bin: PK-01-01-01                                ║
║ Benefit: Free up prime picking location                   ║
║ Estimated Savings: 15% travel time for active items       ║
╚═══════════════════════════════════════════════════════════╝

Action: Create bin-to-bin transfer based on recommendation
```

#### 2. Bin Over-Capacity Alert
```
Alert:

╔═══════════════════════════════════════════════════════════╗
║ Type: BIN_OVER_CAPACITY                                   ║
║ Priority: HIGH                                            ║
╠═══════════════════════════════════════════════════════════╣
║ Bin: SC-01-01-01                                          ║
║ Capacity: 10,000 PCS                                      ║
║ Current Stock: 12,500 PCS (125%)                          ║
║ Excess: 2,500 PCS                                         ║
║ Issue: Safety risk, access difficulty                     ║
║ Recommendation: Split stock to SC-01-01-02                ║
╚═══════════════════════════════════════════════════════════╝

Action: Transfer 2,500 PCS to another bin
```

#### 3. Consolidation Opportunity
```
Recommendation:

╔═══════════════════════════════════════════════════════════╗
║ Type: CONSOLIDATION                                       ║
║ Priority: LOW                                             ║
╠═══════════════════════════════════════════════════════════╣
║ Material: RIBBON-2.0MM                                    ║
║ Current Bins: 7 bins                                      ║
║ Bins: EC-01-01-01 (2,000m), EC-01-02-01 (1,500m),        ║
║       EC-02-01-01 (800m), EC-02-02-01 (500m)...          ║
║ Total Quantity: 6,500 MTR                                 ║
║ Issue: Scattered across multiple bins                     ║
║ Recommendation: Consolidate into 2 bins                   ║
║ Benefit: Easier picking, better space utilization         ║
╚═══════════════════════════════════════════════════════════╝

Action: Schedule consolidation during low-activity period
```

---

## Feature 3: Number Range Management

### Overview
Customize document numbering for different document types.

### Configuration
```
Navigation: Settings → Number Ranges

Available Ranges:

╔═══════════════════════════════════════════════════════════╗
║              NUMBER RANGE CONFIGURATION                   ║
╠════════════╦══════════╦══════════╦════════════╦══════════╣
║ Range ID   ║ Prefix   ║ Current  ║ Increment  ║ Example  ║
╠════════════╬══════════╬══════════╬════════════╬══════════╣
║ GRN        ║ GRN-     ║ 1500     ║ 1          ║ GRN-1500 ║
╠════════════╬══════════╬══════════╬════════════╬══════════╣
║ TR         ║ TR-      ║ 2000     ║ 1          ║ TR-2000  ║
╠════════════╬══════════╬══════════╬════════════╬══════════╣
║ TO         ║ TO-      ║ 3000     ║ 1          ║ TO-3000  ║
╠════════════╬══════════╬══════════╬════════════╬══════════╣
║ PI         ║ PI-      ║ 100      ║ 1          ║ PI-100   ║
╠════════════╬══════════╬══════════╬════════════╬══════════╣
║ SU         ║ SU-      ║ 5000     ║ 1          ║ SU-5000  ║
╠════════════╬══════════╬══════════╬════════════╬══════════╣
║ QUANT      ║ quant_   ║ 10000    ║ 1          ║ quant_10k║
╚════════════╩══════════╩══════════╩════════════╩══════════╝

Customization Options:
- Change prefix (e.g., GRN- → SOLAR-GRN-)
- Set starting number
- Define increment (1, 5, 10, etc.)
- Add year/month (e.g., GRN-2026-001)
```

---

# 7. Reports & Analytics {#reports}

## Report 1: LX03 - Quant List Report

### Purpose
Complete bin-level inventory listing with stock categories.

### How to Generate
```
Navigation: WM Reports → Select Report: LX03 - Quant List

Filters Available:
- Storage Type: SC, GM, FM, EC, PK, QC, PR
- Stock Category: UNRES, QINSP, BLOCK, RETRN
- Material Code: Enter code or partial code
- Expired Only: Yes/No

Example Filter:
- Storage Type: SC (Solar Cells)
- Stock Category: UNRES
- Expired Only: No

Click: Generate Report

Output:
╔═══════════════════════════════════════════════════════════════════════════╗
║                    QUANT LIST REPORT (LX03)                               ║
║                    Generated: 2026-03-30 16:00                            ║
╠═══════════════════════════════════════════════════════════════════════════╣
║ Storage Type: SC                                                          ║
║ Stock Category: UNRES                                                     ║
║                                                                           ║
║ Total Quants: 4                                                          ║
║ Total Quantity: 74,800 PCS                                               ║
╠════════════╦═══════════╦════════╦═════╦══════════╦═══════════╦═════════╣
║ Material   ║ Bin       ║ Qty    ║ UOM ║ Category ║ Batch     ║ SLED    ║
╠════════════╬═══════════╬════════╬═════╬══════════╬═══════════╬═════════╣
║ CELL-MO-166║SC-01-01-01║ 14,800 ║ PCS ║ UNRES    ║LONGI-A    ║2028-03  ║
╠════════════╬═══════════╬════════╬═════╬══════════╬═══════════╬═════════╣
║ CELL-MO-182║SC-01-01-02║ 15,000 ║ PCS ║ UNRES    ║LONGI-B    ║2028-03  ║
╠════════════╬═══════════╬════════╬═════╬══════════╬═══════════╬═════════╣
║ CELL-MO-166║SC-01-02-01║ 40,000 ║ PCS ║ UNRES    ║LONGI-C    ║2028-03  ║
╠════════════╬═══════════╬════════╬═════╬══════════╬═══════════╬═════════╣
║ CELL-PO-156║SC-02-01-01║  5,000 ║ PCS ║ UNRES    ║POLY-D     ║2027-12  ║
╚════════════╩═══════════╩════════╩═════╩══════════╩═══════════╩═════════╝

Actions:
- Export to CSV
- Print
- Email to stakeholders
```

---

## Report 2: LX02 - Bin Status Report

### Purpose
Analyze bin utilization and capacity management.

### How to Generate
```
Navigation: WM Reports → Select Report: LX02 - Bin Status

Filter: Zone: All (or specific zone like SC)

Click: Generate Report

Output:
╔═══════════════════════════════════════════════════════════════════════════╗
║                    BIN STATUS REPORT (LX02)                               ║
║                    Generated: 2026-03-30 16:05                            ║
╠═══════════════════════════════════════════════════════════════════════════╣
║ Summary:                                                                  ║
║ - Total Bins: 16                                                         ║
║ - Occupied Bins: 10 (62.5%)                                              ║
║ - Empty Bins: 6 (37.5%)                                                  ║
║ - Average Utilization: 68.3%                                             ║
╠═══════════╦══════╦════════╦══════════╦═══════════╦══════════╦═══════════╣
║ Bin       ║ Zone ║ Status ║ Capacity ║ Current   ║ Utiliz.  ║ Materials ║
╠═══════════╬══════╬════════╬══════════╬═══════════╬══════════╬═══════════╣
║SC-01-01-01║ SC   ║ Avail  ║  10,000  ║  14,800   ║ 148.0% ⚠️║     1     ║
╠═══════════╬══════╬════════╬══════════╬═══════════╬══════════╬═══════════╣
║SC-01-01-02║ SC   ║ Avail  ║  10,000  ║  15,000   ║ 150.0% ⚠️║     1     ║
╠═══════════╬══════╬════════╬══════════╬═══════════╬══════════╬═══════════╣
║SC-01-02-01║ SC   ║ Avail  ║  10,000  ║  40,000   ║ 400.0% 🔴║     1     ║
╠═══════════╬══════╬════════╬══════════╬═══════════╬══════════╬═══════════╣
║GM-01-01-01║ GM   ║ Avail  ║   2,000  ║   3,000   ║ 150.0% ⚠️║     1     ║
╠═══════════╬══════╬════════╬══════════╬═══════════╬══════════╬═══════════╣
║EC-01-01-01║ EC   ║ Avail  ║   5,000  ║   3,000   ║  60.0% ✓ ║     2     ║
╠═══════════╬══════╬════════╬══════════╬═══════════╬══════════╬═══════════╣
║PR-01-01-01║ PR   ║ Avail  ║   3,000  ║   5,000   ║ 166.7% ⚠️║     1     ║
╠═══════════╬══════╬════════╬══════════╬═══════════╬══════════╬═══════════╣
║QC-01-01-01║ QC   ║ Avail  ║   1,000  ║     500   ║  50.0% ✓ ║     2     ║
╠═══════════╬══════╬════════╬══════════╬═══════════╬══════════╬═══════════╣
║A-01-01-01 ║ A    ║ Empty  ║     100  ║       0   ║   0.0%   ║     0     ║
╚═══════════╩══════╩════════╩══════════╩═══════════╩══════════╩═══════════╝

Insights:
🔴 Critical: SC-01-02-01 at 400% capacity - immediate action required
⚠️ Warning: 5 bins over 100% capacity - plan redistribution
✓ Good: 2 bins within optimal range (50-90%)

Actions Recommended:
1. Split SC-01-02-01 stock across multiple bins
2. Review storage strategies
3. Consider adding bins in high-demand zones
```

---

# 8. Best Practices {#best-practices}

## Daily Operations

### Morning Checklist (Warehouse Operator)
```
Every Day - 8:00 AM:

□ Log into system
□ Check dashboard alerts
□ Review today's inbound deliveries (GRNs expected)
□ Review open Transfer Orders
□ Check material availability for production
□ Verify bin blocks (any maintenance today?)
□ Check SLED expiry alerts
□ Review yesterday's variances (if any)
□ Brief team on priorities

Priority Order:
1. Urgent production picks (TO with Priority 1-2)
2. Quality inspection releases
3. GRN receipts
4. Putaway tasks
5. Bin-to-bin transfers
6. Cycle counting
```

### Weekly Tasks (Store In-Charge)
```
Every Monday Morning:

□ Review last week's KPIs:
  - GRNs processed: Target 20/week
  - TOs confirmed: Target 100/week
  - Picking accuracy: Target >99%
  - Putaway accuracy: Target >99%
  - Cycle count variance: Target <2%

□ Plan this week:
  - Expected GRNs (from procurement)
  - Production schedule
  - Cycle count zones
  - Maintenance activities

□ Review stock health:
  - Low stock items (below reorder point)
  - Overstocked items
  - Slow-moving items (>60 days no movement)
  - SLED expiring items

□ Team management:
  - Review operator performance
  - Training needs
  - Schedule adjustments
```

### Monthly Activities (Management)
```
First Week of Month:

□ Review monthly reports:
  - Inventory accuracy (target: >98%)
  - Stock turnover ratio
  - Bin utilization
  - Dead stock value
  - Waste/scrap percentage

□ Strategic planning:
  - Capacity planning (bins, zones)
  - Process improvements
  - Technology upgrades
  - Vendor performance review

□ Compliance:
  - Audit trail review
  - Compliance checklist
  - Documentation updates
  - System backup verification
```

## Accuracy Targets

```
╔═══════════════════════════════════════════════════════════╗
║              KEY PERFORMANCE INDICATORS                   ║
╠═══════════════════════════════════════════════════════════╣
║ Metric                        Target      Current   Status║
╠═══════════════════════════════════════════════════════════╣
║ Inventory Accuracy            >98%        98.5%     ✓     ║
║ Picking Accuracy               >99%        99.2%     ✓     ║
║ Putaway Accuracy               >99%        98.8%     ⚠️    ║
║ Cycle Count Variance           <2%         1.8%      ✓     ║
║ SLED Compliance                100%        100%      ✓     ║
║ On-Time GRN Processing         >95%        96%       ✓     ║
║ Transfer Order Completion      >90%        88%       ⚠️    ║
║ Stock Availability             >98%        99%       ✓     ║
║ Bin Utilization              70-85%        68%       ⚠️    ║
╚═══════════════════════════════════════════════════════════╝

Action Items:
⚠️ Putaway Accuracy: Additional training on bin verification
⚠️ TO Completion: Investigate delays, optimize routes
⚠️ Bin Utilization: Review storage strategies
```

---

# 9. Troubleshooting {#troubleshooting}

## Common Issues & Solutions

### Issue 1: Cannot Create GRN
```
Problem: "Material not found" error when creating GRN

Possible Causes:
1. Material not in master data
2. Material code typo
3. Inactive material

Solution:
Step 1: Verify material exists
- Navigate: Materials → Search
- Search for material code
- Check status: Active/Inactive

Step 2: If not found, create material
- Navigate: Materials → Create
- Fill all required fields
- Save

Step 3: Retry GRN creation
```

### Issue 2: Transfer Order Won't Confirm
```
Problem: "Insufficient stock in source bin" error

Possible Causes:
1. Stock already picked
2. Stock category mismatch
3. Bin blocked
4. Concurrent TO on same stock

Solution:
Step 1: Check current stock
- Navigate: Bins → View Bin: [source_bin]
- Verify actual quantity
- Check stock category

Step 2: Check for conflicts
- View all open TOs for same material
- Check if bin is blocked

Step 3: If stock exists
- Cancel and recreate TO
- Or adjust TO quantity to available stock

Step 4: If stock doesn't exist
- Investigate: Check stock movements
- Review last picking/putaway
- Run quant list report
```

### Issue 3: Physical Inventory Won't Post
```
Problem: "Variance exceeds threshold" error

Possible Causes:
1. Large variance not approved
2. Recount required
3. Missing investigation report

Solution:
Step 1: Review variances
- Check variance percentage
- Identify high-variance items

Step 2: Complete investigation
- For variances >2%: Mandatory recount
- For variances >5%: Investigation report required

Step 3: Get approvals
- Store In-Charge: <₹5,000
- Management: >₹5,000

Step 4: Retry posting
```

---

## Emergency Procedures

### Power Outage During Operations
```
Immediate Actions:

1. Physical Security:
   □ Secure all materials
   □ Lock warehouse doors
   □ Note last known positions

2. When Power Returns:
   □ Log into system
   □ Check last saved transactions
   □ Verify open TOs status
   □ Compare physical vs. system

3. Recovery:
   □ Complete in-progress transactions
   □ Verify stock positions
   □ Run bin status report
   □ Reconcile any discrepancies
```

### System Downtime
```
Backup Process:

1. Manual Documentation:
   - Use paper GRN forms
   - Manual picking lists
   - Record all movements

2. During System Operation:
   - Backdate entries to actual time
   - Enter all manual documents
   - Verify stock accuracy

3. Verification:
   - Run reconciliation report
   - Check for duplicates
   - Verify totals
```

---

## Contact & Support

### Internal Support
```
Technical Support:
- Email: it.support@company.com
- Phone: +91-XXX-XXXXXXX
- Hours: 24/7

Warehouse Management:
- Store In-Charge: store@company.com
- Warehouse Manager: manager@company.com

Training & Help:
- Training Manager: training@company.com
- User Manual: System → Help → Documentation
```

### System Administration
```
Admin Access:
- Email: admin@warehouse.com
- Responsibilities:
  - User management
  - System configuration
  - Data backup
  - Report access
  - Audit trail monitoring
```

---

# Appendix

## Solar BOM Components Reference

### Complete Material List (23 items)

```
╔═══════════════════════════════════════════════════════════════════╗
║                  SOLAR PANEL BOM COMPONENTS                       ║
╠════════════════════════════════════════════════════════════════════
║ SOLAR CELLS (3 types)                                            ║
╠═══════════════╦═══════════════════════════════════════════════════╣
║ CELL-MONO-166 ║ Monocrystalline 166mm M10, 5.2-5.5W, Grade A    ║
║ CELL-MONO-182 ║ Monocrystalline 182mm M12, 6.0-6.5W, Grade A+   ║
║ CELL-POLY-156 ║ Polycrystalline 156mm, 4.8-5.0W, Grade A        ║
╠═══════════════════════════════════════════════════════════════════╣
║ GLASS & ENCAPSULATION (4 types)                                  ║
╠═══════════════╦═══════════════════════════════════════════════════╣
║ GLASS-ARC-3.2 ║ Anti-reflective coated glass, 3.2mm, low-iron   ║
║ GLASS-TEMP-4.0║ Tempered glass 4.0mm, ultra-clear, bifacial     ║
║ EVA-FAST-0.45 ║ Fast cure EVA film, 0.45mm, UV stabilized       ║
║ EVA-STD-0.50  ║ Standard EVA film, 0.50mm, high transparency    ║
╠═══════════════════════════════════════════════════════════════════╣
║ BACKSHEET (2 types)                                              ║
╠═══════════════╦═══════════════════════════════════════════════════╣
║ BACK-TPT-WHT  ║ TPT backsheet white, UV resistant               ║
║ BACK-TPE-BLK  ║ TPE backsheet black, for bifacial modules       ║
╠═══════════════════════════════════════════════════════════════════╣
║ FRAMES & MOUNTING (2 types)                                      ║
╠═══════════════╦═══════════════════════════════════════════════════╣
║ FRAME-AL-35MM ║ Aluminum frame 35mm silver, anodized            ║
║ FRAME-AL-40MM ║ Aluminum frame 40mm black, premium finish       ║
╠═══════════════════════════════════════════════════════════════════╣
║ ELECTRICAL COMPONENTS (3 types)                                  ║
╠═══════════════╦═══════════════════════════════════════════════════╣
║ JBOX-IP67-3D  ║ Junction box IP67, 3 bypass diodes              ║
║ JBOX-SMART-BT ║ Smart junction box, Bluetooth, IP68             ║
║ DIODE-BYPASS  ║ Schottky bypass diode, 15A                      ║
╠═══════════════════════════════════════════════════════════════════╣
║ INTERCONNECTS & CABLES (3 types)                                 ║
╠═══════════════╦═══════════════════════════════════════════════════╣
║ RIBBON-2.0MM  ║ Tinned copper ribbon, 2.0mm, solder coated      ║
║ BUSBAR-5BB    ║ Multi-busbar 5BB ribbon, high efficiency        ║
║ CABLE-PV-4MM  ║ PV cable 4mm², UV resistant                     ║
╠═══════════════════════════════════════════════════════════════════╣
║ CONNECTORS (2 types)                                             ║
╠═══════════════╦═══════════════════════════════════════════════════╣
║ CONN-MC4-MALE ║ MC4 male connector, IP67, TUV certified         ║
║ CONN-MC4-FEM  ║ MC4 female connector, IP67, TUV certified       ║
╠═══════════════════════════════════════════════════════════════════╣
║ SEALANTS & ADHESIVES (2 types)                                   ║
╠═══════════════╦═══════════════════════════════════════════════════╣
║ SEAL-SIL-RTV  ║ RTV silicone sealant, weatherproof              ║
║ TAPE-DBL-3M   ║ 3M VHB double-sided tape, high strength         ║
╠═══════════════════════════════════════════════════════════════════╣
║ PACKAGING (2 types)                                              ║
╠═══════════════╦═══════════════════════════════════════════════════╣
║ PKG-PALLET-EUR║ Euro pallet 1200x800mm, heat treated            ║
║ PKG-CORNER    ║ Corner protectors for shipping                   ║
╚═══════════════╩═══════════════════════════════════════════════════╝
```

---

## Glossary

**Quant:** Smallest trackable stock unit. One material + one bin + one batch + one stock category = one quant.

**TR (Transfer Requirement):** Planning document that states "need to move X quantity of material Y". Created before physical movement.

**TO (Transfer Order):** Execution document that instructs warehouse operator to move material. Created from TR.

**SLED:** Shelf Life Expiry Date. Critical for time-sensitive materials.

**Stock Category:** Classification of stock status (UNRES, QINSP, BLOCK, RETRN).

**FIFO:** First In First Out. Pick oldest stock first.

**LIFO:** Last In First Out. Pick newest stock first.

**FEFO:** First Expired First Out. Pick stock expiring soonest.

**GRN:** Goods Receipt Note. Document for receiving materials.

**PI:** Physical Inventory. Cycle counting process.

**BOM:** Bill of Materials. Recipe for solar panel assembly.

**Putaway:** Moving received goods from receiving area to storage location.

**Picking:** Removing materials from storage for production/shipping.

---

**END OF DOCUMENTATION**

*For latest updates and online help, visit the system at:*  
*https://emergent-extend.preview.emergentagent.com*

*Login: admin@warehouse.com / admin123*
