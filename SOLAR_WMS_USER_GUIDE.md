# Solar Manufacturing WMS - Complete User Guide

**Complete Workflow Guide for Quality Inspection, Bin Locations, GRN Processing, Transfer Orders, and Stock Tracking**

---

## Table of Contents
1. [Create Bin Locations](#1-create-bin-locations)
2. [Process GRNs (Goods Receipt Notes)](#2-process-grns)
3. [Quality Inspection Workflow](#3-quality-inspection-workflow)
4. [Use Transfer Orders](#4-use-transfer-orders)
5. [Generate WM Reports](#5-generate-wm-reports)
6. [Monitor Stock Levels](#6-monitor-stock-levels)

---

## 1. Create Bin Locations

### Purpose
Set up physical storage locations in your warehouse for materials.

### Navigation
`Dashboard → Bin Locations`

### Steps to Create Bins

**Step 1: Access Bin Locations**
- Click "Bin Locations" in the sidebar
- Click "+ Add Bin" button (top right)

**Step 2: Enter Bin Details**
```
Bin Code: QC-01-01-01 (Format: Zone-Aisle-Rack-Level)
Zone: Quality Control
Storage Type: QUAR (Quarantine Area)
Capacity: 1000
Status: Available
```

**Step 3: Common Bin Naming Conventions**
```
QC-01-01-01   → Quality Control Zone, Aisle 01, Rack 01, Level 01
A-01-01-01    → General Storage Zone A, Aisle 01, Rack 01, Level 01
RECV-01       → Receiving Zone 01
PICK-A-01     → Picking Zone A, Slot 01
BULK-01       → Bulk Storage 01
```

**Step 4: Create Multiple Bins (Recommended Setup)**
```
Quality Control:
- QC-01-01-01, QC-01-01-02, QC-01-01-03

Receiving Area:
- RECV-01, RECV-02, RECV-03

General Storage:
- A-01-01-01 to A-05-10-04 (200 bins)
- B-01-01-01 to B-05-10-04 (200 bins)

Picking Area:
- PICK-A-01 to PICK-A-50
```

**Best Practices:**
- Use consistent naming convention
- Create dedicated QC bins for incoming materials
- Separate zones for different material categories
- Plan for future expansion

---

## 2. Process GRNs (Goods Receipt Notes)

### Purpose
Receive incoming materials into the warehouse from vendors.

### Navigation
`Dashboard → GRN / Inward`

### Complete GRN Workflow

**Step 1: Create New GRN**
```
1. Click "GRN / Inward" in sidebar
2. Click "+ Create GRN" button
3. Enter GRN Details:
   - PO Number: PO-2026-001
   - Vendor Name: Longi Solar Technology
   - Receipt Date: 2026-04-07
   - Invoice Number: INV-LON-2026-001
```

**Step 2: Add Materials to GRN**
```
Click "+ Add Item"

Material 1:
- Material Code: CELL-020 (Select from dropdown)
- Material Name: SC182X182 TOPCON 16BB E>25.3%
- Received Quantity: 20,000 PCS
- Batch Number: LONGI-M10-20260407-A
- Manufacturing Date: 2026-04-01
- Expiry Date: 2027-04-01
- Storage Condition: Ambient
- Bin Location: QC-01-01-01 (Quality Control)

Material 2:
- Material Code: GLASS-008
- Material Name: SOLAR GLASS TEMP/ARC2272X1128X2.0MM
- Received Quantity: 5,000 PCS
- Batch Number: GLASS-ARC-20260407-B
- Storage Condition: Ambient
- Bin Location: QC-01-01-02
```

**Step 3: Save GRN**
```
- Click "Save GRN"
- Status: Pending (Waiting for Quality Inspection)
- GRN Number auto-generated: GRN-20260407-XXXX
```

**Step 4: What Happens Next?**
```
✓ GRN created with status "Pending"
✓ Materials are in QINSP (Quality Inspection) stock category
✓ Items appear in "Quality Inspection" module for QC team
✓ Stock is NOT yet available for production (blocked until QC pass)
```

---

## 3. Quality Inspection Workflow

### Purpose
Inspect incoming materials and decide: PASS → UNRES (Unrestricted) or FAIL → BLOCK

### Navigation
`Dashboard → Quality Inspection`

### Complete QC Workflow

**Step 1: Access Pending Inspections**
```
1. Click "Quality Inspection" in sidebar
2. View summary cards:
   - Pending Inspection: 1
   - Passed: 0
   - Failed: 0
   - Total GRNs: 1
```

**Step 2: Open GRN for Inspection**
```
1. Click "Inspect" button next to GRN-20260407-XXXX
2. Modal opens showing all materials in the GRN
```

**Step 3: Perform Quality Inspection**

**For CELL-020 (Solar Cells):**
```
Material: SC182X182 TOPCON 16BB E>25.3%
Batch: LONGI-M10-20260407-A
Received: 20,000 PCS

Inspection Actions:
□ Visual inspection: Check for cracks, chips, discoloration
□ Electrical testing: Measure efficiency (should be >25.3%)
□ Dimensional checks: Verify 182mm x 182mm size
□ Sample testing: Test 50 random cells

Decision Options:
```

**Option A: PASS (All cells good)**
```
1. Click "✓ Pass All" button
2. Accepted Quantity: 20,000
3. Rejected Quantity: 0
4. Status: Passed
5. Bin Location: QC-01-01-01
6. Stock Category: QINSP → UNRES (Unrestricted Use)
```

**Option B: FAIL (All cells defective)**
```
1. Click "✗ Reject All" button
2. Accepted Quantity: 0
3. Rejected Quantity: 20,000
4. Status: Failed
5. Rejection Reason: "Efficiency below 25.3%, microcracks detected"
6. Stock Category: QINSP → BLOCK (Blocked stock)
```

**Option C: PARTIAL (Some cells good, some bad)**
```
1. Click "↔ Partial" button
2. Enter manually:
   - Accepted Quantity: 19,500
   - Rejected Quantity: 500
3. Status: Partial
4. Rejection Reason: "500 cells with microcracks"
5. Stock Categories:
   - 19,500 PCS → UNRES (Available for use)
   - 500 PCS → BLOCK (Return to vendor)
```

**Step 4: Complete Inspection for All Materials**
```
Repeat for GLASS-008:
- Accepted: 5,000 PCS
- Status: Passed
- Stock Category: UNRES
```

**Step 5: Submit Inspection**
```
1. Click "Submit Inspection" button
2. System updates:
   ✓ GRN status changed to "Completed" (if all items inspected)
   ✓ Stock categories updated (QINSP → UNRES/BLOCK)
   ✓ Materials now available in inventory
   ✓ Stock levels updated on dashboard
```

**Stock Category Flow:**
```
GRN Created      →  QINSP (Quality Inspection Hold)
                     ↓
QC Inspection    →  Decision
                     ↓
                ┌────┴────┐
                ↓         ↓
              PASS      FAIL
                ↓         ↓
             UNRES     BLOCK
     (Unrestricted) (Blocked)
```

---

## 4. Use Transfer Orders

### Purpose
Move materials between bin locations within the warehouse.

### Navigation
`Dashboard → Transfer Orders`

### Complete Transfer Order Workflow

**Step 1: Create Transfer Requirement (TR)**
```
Scenario: Move 10,000 cells from QC area to production picking area

1. Go to "Transfer Orders"
2. Click "Transfer Requirements" tab
3. System auto-generates TR from GRN completion OR create manually
```

**Step 2: Create Transfer Order from TR**
```
1. Click "+ Create TO from TR" button
2. Select Transfer Requirement: TR-2026-001
3. Enter TO Details:
   - TO Type: STOCK_TRANSFER
   - Source Bin: QC-01-01-01
   - Destination Bin: PICK-A-01
   - Material: CELL-020
   - Quantity: 10,000 PCS
   - Priority: High
```

**Step 3: Execute Transfer Order**
```
1. Warehouse operator receives TO: TO-2026-001
2. Physical movement:
   - Pick 10,000 cells from QC-01-01-01
   - Move to PICK-A-01
   - Scan barcode/RFID to confirm
3. Click "Confirm" button
4. Enter confirmed quantity: 10,000
```

**Step 4: System Updates**
```
✓ Stock deducted from QC-01-01-01: -10,000
✓ Stock added to PICK-A-01: +10,000
✓ Stock movement logged
✓ TO status: CONFIRMED
✓ Quant (bin-level stock) updated
```

**Transfer Order Types:**
```
- PUTAWAY: Move from receiving to storage
- PICKING: Move from storage to picking area
- STOCK_TRANSFER: General movement between bins
- REPLENISHMENT: Refill picking bins from storage
```

---

## 5. Generate WM Reports

### Purpose
Analyze warehouse stock, bin utilization, and material movements.

### Navigation
`Dashboard → WM Reports`

### Available Reports

**Report 1: LX03 - Quant List**
```
Purpose: View stock at bin level with filters

Steps:
1. Go to "WM Reports"
2. Select Report: "LX03 - Quant List"
3. Apply Filters:
   - Material Code: CELL-020 (optional)
   - Stock Category: UNRES (optional)
   - Storage Type: PICK (optional)
4. Click "Generate Report"

Output:
┌─────────────┬──────────┬──────────┬─────────────┬───────┬──────────┐
│ Material    │ Bin      │ Quantity │ Category    │ Batch │ SLED     │
├─────────────┼──────────┼──────────┼─────────────┼───────┼──────────┤
│ CELL-020    │ PICK-A-01│ 10,000   │ UNRES       │ LON-A │ 2027-04-01│
│ CELL-020    │ QC-01-01 │ 9,500    │ UNRES       │ LON-A │ 2027-04-01│
│ GLASS-008   │ QC-01-02 │ 5,000    │ UNRES       │ GLA-B │ N/A      │
└─────────────┴──────────┴──────────┴─────────────┴───────┴──────────┘

Summary:
- Total Quants: 3
- Total Quantity: 24,500
- By Category:
  * UNRES: 24,500
  * QINSP: 0
  * BLOCK: 0
```

**Report 2: LX02 - Bin Status**
```
Purpose: Analyze bin utilization

Steps:
1. Select Report: "LX02 - Bin Status"
2. Filter by Zone: Quality Control (optional)
3. Generate Report

Output:
┌───────────┬──────┬────────┬────────────┬──────────┬──────────────┐
│ Bin Code  │ Zone │ Status │ Capacity   │ Current  │ Utilization  │
├───────────┼──────┼────────┼────────────┼──────────┼──────────────┤
│ QC-01-01-01│ QC  │ Occupied│ 1000      │ 9500     │ 95%          │
│ QC-01-01-02│ QC  │ Occupied│ 1000      │ 5000     │ 50%          │
│ PICK-A-01 │ PICK│ Occupied│ 15000     │ 10000    │ 67%          │
└───────────┴──────┴────────┴────────────┴──────────┴──────────────┘
```

**Report 3: Stock by Category**
```
Shows breakdown of stock by UNRES, QINSP, BLOCK, RETRN

Output:
Unrestricted (UNRES):        24,500 units (12 materials)
Quality Inspection (QINSP):   0 units
Blocked (BLOCK):              500 units (1 material)
Returns (RETRN):              0 units
```

**Report 4: SLED Expiry Alert**
```
Shows materials expiring soon (configurable threshold)

Filter: Days Threshold: 30

Output:
Materials expiring in next 30 days: 0
```

**Report 5: LT21 - Transfer Order List**
```
Shows all TOs with status (Open, Confirmed, Cancelled)
```

**Report 6: Stock Movement History**
```
Complete audit trail of all stock movements
```

---

## 6. Monitor Stock Levels

### Purpose
Real-time tracking of all 73 materials across warehouse.

### Navigation Options

**Option 1: Dashboard View**
```
Dashboard → Summary Cards

Cards Show:
- Total Materials: 73
- Total Stock: 24,500 units
- Total Bins: 15
- Low Stock Alerts: 3 materials

Widgets:
- Low Stock Materials (below reorder point)
- Recent Movements (last 10 transactions)
- Bin Status (available/occupied/blocked)
```

**Option 2: Material Master View**
```
Material Master → View all 73 materials

Columns:
- Material Code: CELL-020
- Name: SC182X182 TOPCON 16BB
- Category: Solar Cells
- Current Stock: 19,500 PCS
- Status: In Stock / Out of Stock
- Actions: View Details, Edit, Delete
```

**Option 3: Stock Analytics Dashboard**
```
Stock Analytics → Advanced charts

Charts:
- Stock by Category (pie chart)
- Stock Aging (bar chart)
- Material Stock Levels (bar chart)
- Bin Utilization (gauge chart)
```

**Option 4: Bin-Level Stock**
```
Bin Locations → Click on any bin

View:
- All materials stored in that bin
- Quantities per material
- Stock categories
- Batches
- SLED dates
```

---

## Complete End-to-End Example

### Scenario: Receive 20,000 Solar Cells

**Day 1: Material Arrival**
```
1. Create GRN
   - Vendor: Longi Solar
   - Material: CELL-020
   - Quantity: 20,000 PCS
   - Batch: LONGI-M10-20260407-A
   - Bin: QC-01-01-01
   - Status: Pending QC
   - Stock Category: QINSP
```

**Day 2: Quality Inspection**
```
2. QC Team Actions:
   - Open Quality Inspection module
   - Inspect GRN-20260407-XXXX
   - Test 50 sample cells
   - Result: 19,500 PASS, 500 FAIL
   - Accept: 19,500 (→ UNRES)
   - Reject: 500 (→ BLOCK)
   - Reason: "500 cells with microcracks"
   - Submit Inspection
```

**Day 3: Stock Transfer**
```
3. Move to Production:
   - Create Transfer Order
   - Source: QC-01-01-01 (9,500 cells)
   - Destination: PICK-A-01
   - Quantity: 9,500
   - Confirm movement
   - Stock now split:
     * QC-01-01-01: 10,000 UNRES
     * PICK-A-01: 9,500 UNRES
     * QC-01-01-01: 500 BLOCK (for return)
```

**Day 4: Production Use**
```
4. Material Issue:
   - Production withdraws 8,000 cells from PICK-A-01
   - Remaining: 1,500 in PICK-A-01
   - System creates issue document
   - Stock deducted from inventory
```

**Day 5: Monitoring**
```
5. Generate Reports:
   - Quant List: See stock across all bins
   - Stock Movement History: Full audit trail
   - SLED Alert: Monitor expiry dates
   - Bin Utilization: Plan space optimization
```

---

## Stock Category Reference

| Category | Code | Description | Use Case |
|----------|------|-------------|----------|
| **Unrestricted** | UNRES | Available for use | Passed QC, ready for production |
| **Quality Inspection** | QINSP | Under inspection | Just received, awaiting QC |
| **Blocked** | BLOCK | Not usable | Failed QC, damaged, defective |
| **Returns** | RETRN | Return to vendor | Vendor returns, excess stock |

---

## Quick Reference Commands

### Create Sample Bins
```
QC-01-01-01, QC-01-01-02, QC-01-01-03
RECV-01, RECV-02
A-01-01-01 to A-05-10-04
PICK-A-01 to PICK-A-50
```

### GRN Status Flow
```
Created → Pending → Partial → Completed
```

### Quality Inspection Actions
```
✓ Pass All    → QINSP → UNRES
✗ Reject All  → QINSP → BLOCK
↔ Partial     → Split UNRES + BLOCK
```

### Transfer Order Flow
```
Create TR → Create TO → Execute → Confirm → Update Quants
```

---

## Best Practices

1. **Always use Quality Inspection**
   - Never skip QC for incoming materials
   - Document rejection reasons
   - Maintain batch traceability

2. **Maintain Bin Hygiene**
   - One material per bin (preferred)
   - Label bins clearly
   - Regular cycle counting

3. **Use Stock Categories Properly**
   - QINSP: Only for new receipts
   - UNRES: Production-ready stock
   - BLOCK: Segregate physically

4. **Monitor Stock Levels**
   - Set reorder points for each material
   - Generate weekly stock reports
   - Track slow-moving items

5. **Document Everything**
   - Record batch numbers
   - Track SLED dates
   - Maintain audit trail

---

## Troubleshooting

**Issue: Can't find Quality Inspection module**
```
Solution: Check user role
Required roles: Admin, Store In-Charge, Inventory Controller, Auditor
```

**Issue: GRN status stuck at "Pending"**
```
Solution: Complete Quality Inspection
All items must be inspected before GRN can be completed
```

**Issue: Stock not updating after QC**
```
Solution: Click "Submit Inspection" button
Ensure all quantities add up to received quantity
```

**Issue: Transfer Order won't confirm**
```
Solution: Check source bin has sufficient stock
Verify material exists in source bin
Check stock category (must be UNRES)
```

---

**End of User Guide**

For technical support or questions, contact your WMS administrator.
