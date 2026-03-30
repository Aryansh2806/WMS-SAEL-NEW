# WMS Pro - Product Requirements Document

## Original Problem Statement
Build a Warehouse Management System (WMS Pro) with:
1. GRN (Goods Receipt Note) module with comprehensive fields
2. Role-based access control with 6 roles
3. Audit trail for all changes
4. User management with CRUD operations
5. Comprehensive reports module with Excel/PDF export

## Architecture
- **Frontend**: React.js with Tailwind CSS, Radix UI components
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: JWT-based local authentication

## User Personas
1. **Admin** - Full system access, master data management, user management
2. **Warehouse Operator** - GRN, putaway, material issue operations
3. **Store In-Charge** - All operations + approvals (no master data)
4. **Inventory Controller** - Stock inquiry, reports (read-only)
5. **Auditor** - Read-only access to all data including audit trail
6. **Management Viewer** - Dashboard and reports only

## Core Requirements (Static)
- User authentication and authorization
- Material master management
- GRN/Inward processing
- Label/sticker generation
- Bin location management
- Putaway operations
- Material issue/outward
- Stock movements tracking
- Reports and analytics

## What's Been Implemented

### Phase 1 - Initial Setup (Complete)
- Basic WMS structure with all modules
- Material Master with FIFO/LIFO support
- GRN creation and processing
- Label generation with QR codes
- Bin location management
- Putaway workflow
- Material issue workflow
- Stock movements tracking
- Basic dashboard

### Phase 2 - RBAC & Audit Trail (2026-03-29)
- Role-based access control with 6 roles:
  - Admin (full access)
  - Warehouse Operator (GRN, putaway, issue)
  - Store In-Charge (all operations + approvals)
  - Inventory Controller (stock inquiry, reports)
  - Auditor (read-only access)
  - Management Viewer (dashboard only)
- Master data restrictions (Admin only can create/edit/delete materials and bins)
- Comprehensive audit trail:
  - User actions (create, update, delete)
  - Role changes
  - Status changes
  - Entity history viewing
- User Management Page:
  - Create new users
  - Edit user details
  - Change user roles
  - Activate/deactivate users
  - Delete users
  - View user audit history

### Phase 3 - Reports Module (2026-03-29)
- 14 comprehensive reports in 5 categories:
  
  **Inventory Reports:**
  - GRN-wise Stock Report
  - Batch-wise Stock Report
  - Bin-wise Stock Report
  - Stock Summary
  - Stock Reconciliation
  
  **Movement Reports:**
  - Material Movement History
  - Daily Inward/Outward Summary
  - Putaway Pending Report
  
  **Compliance Reports:**
  - FIFO Compliance Report
  - Non-FIFO Exception Report
  
  **Stock Analysis:**
  - Stock Aging Report (0-30, 31-60, 61-90, 90+ days)
  - Dead/Slow Moving Stock Report
  
  **Audit & Activity:**
  - User Activity Log
  - Reprint Sticker Log

- Report Features:
  - Date range filters (start/end date)
  - Material code search
  - Batch number search
  - Bin code search
  - Zone filter dropdown
  - Excel export for all reports
  - PDF export for all reports
  - Record counts
  - Visual utilization bars
  - Status badges

### Phase 4 - Stock Dashboard (2026-03-30)
- Real-time Stock Dashboard with auto-refresh (30 seconds)
- Summary Cards:
  - Total Stock, Available, Blocked, Quality Hold
  - Overstock count, Understock count
- Interactive Charts (Recharts):
  - Stock by Status (pie chart)
  - Bin Utilization (donut with progress bar)
  - Stock by Category (pie chart)
  - Stock Aging Analysis (bar chart)
- Tabbed Detail Views:
  - Alerts: Understock, Overstock, Slow/Non-moving items
  - Bin Zones: Zone-wise utilization table
  - Top Materials: Top 10 by stock level
  - FIFO Status: FIFO materials with pending stock
- Expiring Soon Alert Section
- Management Viewer Homepage: Stock Dashboard displays automatically
- Refresh button for manual updates

## Prioritized Backlog

### P0 - Critical (Next)
- None currently

### P1 - High Priority
- Purchase Order integration
- Stock transfer between warehouses
- Inventory counting/cycle count
- Barcode scanner integration

### P2 - Medium Priority
- Email notifications for low stock
- Advanced analytics dashboard
- Multi-warehouse support
- API documentation

### P3 - Future Enhancements
- Mobile app for warehouse operations
- Integration with ERP systems
- AI-powered demand forecasting
- Voice-guided picking

## Test Credentials
- Admin: admin@warehouse.com / admin123
- Warehouse Operator: operator@test.com / test123

## Technical Notes
- All API endpoints are prefixed with `/api`
- JWT tokens expire after 24 hours
- MongoDB collections: users, materials, grn, bins, putaway, issues, stock_movements, labels, print_logs, audit_logs
- Frontend runs on port 3000, Backend on port 8001
