#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class WarehouseAPITester:
    def __init__(self, base_url: str = "https://emergent-advanced.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data storage
        self.created_material_id = None
        self.created_grn_id = None
        self.created_bin_id = None
        self.created_putaway_id = None
        self.created_issue_id = None
        self.created_label_id = None

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, expected_status: int = 200) -> tuple[bool, Dict]:
        """Make API request with error handling"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"raw_response": response.text}
                
            if not success:
                response_data["status_code"] = response.status_code
                
            return success, response_data

        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_seed_database(self):
        """Test database seeding"""
        success, response = self.make_request('POST', 'seed', expected_status=200)
        self.log_test("Database Seeding", success, 
                     response.get('error', '') if not success else "")
        return success

    def test_login(self):
        """Test admin login"""
        login_data = {
            "email": "admin@warehouse.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user', {}).get('user_id')
            self.log_test("Admin Login", True)
            return True
        else:
            self.log_test("Admin Login", False, 
                         response.get('error', response.get('detail', 'Login failed')))
            return False

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, response = self.make_request('GET', 'dashboard/stats')
        
        if success:
            required_fields = ['total_materials', 'total_bins', 'pending_grns', 'pending_issues']
            has_all_fields = all(field in response for field in required_fields)
            self.log_test("Dashboard Stats", has_all_fields, 
                         "Missing required fields" if not has_all_fields else "")
            return has_all_fields
        else:
            self.log_test("Dashboard Stats", False, response.get('error', ''))
            return False

    def test_material_crud(self):
        """Test Material Master CRUD operations"""
        # Create Material
        material_data = {
            "material_code": f"TEST-{datetime.now().strftime('%H%M%S')}",
            "name": "Test Material",
            "description": "Test material for API testing",
            "category": "Raw Materials",
            "uom": "PCS",
            "stock_method": "FIFO",
            "min_stock_level": 10,
            "max_stock_level": 1000,
            "reorder_point": 50
        }
        
        success, response = self.make_request('POST', 'materials', material_data, 200)
        if success and 'material_id' in response:
            self.created_material_id = response['material_id']
            self.log_test("Create Material", True)
        else:
            self.log_test("Create Material", False, response.get('error', response.get('detail', '')))
            return False

        # Get Materials List
        success, response = self.make_request('GET', 'materials')
        self.log_test("Get Materials List", success and isinstance(response, list))

        # Get Single Material
        if self.created_material_id:
            success, response = self.make_request('GET', f'materials/{self.created_material_id}')
            self.log_test("Get Single Material", success and response.get('material_id') == self.created_material_id)

        # Update Material
        if self.created_material_id:
            update_data = material_data.copy()
            update_data['name'] = "Updated Test Material"
            success, response = self.make_request('PUT', f'materials/{self.created_material_id}', update_data)
            self.log_test("Update Material", success)

        return True

    def test_grn_operations(self):
        """Test Enhanced GRN operations with full tracking fields"""
        if not self.created_material_id:
            self.log_test("GRN Operations", False, "No material available for testing")
            return False

        # Create Enhanced GRN with all new fields
        grn_data = {
            "vendor_name": "Test Vendor Corp",
            "po_number": f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "invoice_number": f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "receipt_date": datetime.now().isoformat(),
            "items": [{
                "material_id": self.created_material_id,
                "received_quantity": 100,
                "accepted_quantity": 0,
                "rejected_quantity": 0,
                "batch_number": f"BTH-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "manufacturing_date": "2024-01-15",
                "expiry_date": "2025-01-15",
                "quality_inspection_status": "pending",
                "storage_condition": "ambient",
                "bin_location": "",
                "rejection_reason": ""
            }],
            "remarks": "Test Enhanced GRN with full tracking"
        }
        
        success, response = self.make_request('POST', 'grn', grn_data, 200)
        if success and 'grn_id' in response:
            self.created_grn_id = response['grn_id']
            # Verify enhanced fields in response
            has_grn_number = 'grn_number' in response
            has_vendor_name = response.get('vendor_name') == grn_data['vendor_name']
            has_enhanced_fields = has_grn_number and has_vendor_name
            self.log_test("Create Enhanced GRN", has_enhanced_fields, 
                         "Missing enhanced fields" if not has_enhanced_fields else "")
        else:
            self.log_test("Create Enhanced GRN", False, response.get('error', response.get('detail', '')))
            return False

        # Test multiple GRN entries for same material (different batch)
        grn_data2 = grn_data.copy()
        grn_data2['items'][0]['batch_number'] = f"BTH2-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        grn_data2['items'][0]['received_quantity'] = 50
        grn_data2['vendor_name'] = "Another Test Vendor"
        
        success, response = self.make_request('POST', 'grn', grn_data2, 200)
        self.log_test("Create Multiple GRN for Same Material", success, 
                     response.get('error', response.get('detail', '')) if not success else "")

        # Get GRNs List
        success, response = self.make_request('GET', 'grn')
        if success and isinstance(response, list):
            # Check if list contains our created GRNs
            grn_found = any(grn.get('grn_id') == self.created_grn_id for grn in response)
            self.log_test("Get GRNs List", grn_found, "Created GRN not found in list" if not grn_found else "")
        else:
            self.log_test("Get GRNs List", False, "Invalid response format")

        # Test Quality Inspection Update
        if self.created_grn_id:
            # Get the GRN to find item IDs
            success, grn_response = self.make_request('GET', f'grn/{self.created_grn_id}')
            if success and 'items' in grn_response:
                item_id = grn_response['items'][0].get('item_id')
                if item_id:
                    inspection_data = [{
                        "item_id": item_id,
                        "accepted_quantity": 80,
                        "rejected_quantity": 20,
                        "quality_inspection_status": "partial",
                        "rejection_reason": "Minor defects found",
                        "bin_location": "A-01-01-01"
                    }]
                    
                    success, response = self.make_request('PUT', f'grn/{self.created_grn_id}/inspect', inspection_data)
                    self.log_test("Quality Inspection Update", success, 
                                 response.get('error', response.get('detail', '')) if not success else "")
                else:
                    self.log_test("Quality Inspection Update", False, "No item_id found in GRN")
            else:
                self.log_test("Quality Inspection Update", False, "Could not retrieve GRN details")

        # Test GRN Completion (should update stock only for accepted quantities)
        if self.created_grn_id:
            success, response = self.make_request('PUT', f'grn/{self.created_grn_id}/complete')
            if success:
                # Verify response contains accepted/rejected quantities
                has_quantities = 'accepted_quantity' in response and 'rejected_quantity' in response
                self.log_test("Complete GRN with Stock Update", has_quantities,
                             "Missing quantity info in response" if not has_quantities else "")
            else:
                self.log_test("Complete GRN", False, response.get('error', response.get('detail', '')))

        # Test GRN filtering by status
        success, response = self.make_request('GET', 'grn?status=completed')
        self.log_test("Filter GRNs by Status", success and isinstance(response, list))

        # Test GRN filtering by vendor
        success, response = self.make_request('GET', 'grn?vendor_name=Test')
        self.log_test("Filter GRNs by Vendor", success and isinstance(response, list))

        # Test get GRNs by material
        success, response = self.make_request('GET', f'grn/by-material/{self.created_material_id}')
        self.log_test("Get GRNs by Material", success and isinstance(response, list))

        # Test get vendor list
        success, response = self.make_request('GET', 'grn/vendors/list')
        self.log_test("Get Vendor List", success and isinstance(response, list))

        return True

    def test_bin_management(self):
        """Test Bin Location Management"""
        # Create Bin
        bin_data = {
            "bin_code": f"TEST-{datetime.now().strftime('%H%M%S')}",
            "zone": "TEST",
            "aisle": "01",
            "rack": "01",
            "level": "01",
            "capacity": 100,
            "bin_type": "storage"
        }
        
        success, response = self.make_request('POST', 'bins', bin_data, 200)
        if success and 'bin_id' in response:
            self.created_bin_id = response['bin_id']
            self.log_test("Create Bin", True)
        else:
            self.log_test("Create Bin", False, response.get('error', response.get('detail', '')))
            return False

        # Get Bins List
        success, response = self.make_request('GET', 'bins')
        self.log_test("Get Bins List", success and isinstance(response, list))

        # Update Bin Status
        if self.created_bin_id:
            success, response = self.make_request('PUT', f'bins/{self.created_bin_id}/status?status=available')
            self.log_test("Update Bin Status", success)

        return True

    def test_putaway_operations(self):
        """Test Putaway Management"""
        if not all([self.created_grn_id, self.created_material_id, self.created_bin_id]):
            self.log_test("Putaway Operations", False, "Missing dependencies (GRN, Material, or Bin)")
            return False

        # Create Putaway
        putaway_data = {
            "grn_id": self.created_grn_id,
            "material_id": self.created_material_id,
            "quantity": 50,
            "bin_id": self.created_bin_id
        }
        
        success, response = self.make_request('POST', 'putaway', putaway_data, 200)
        if success and 'putaway_id' in response:
            self.created_putaway_id = response['putaway_id']
            self.log_test("Create Putaway", True)
        else:
            self.log_test("Create Putaway", False, response.get('error', response.get('detail', '')))
            return False

        # Get Putaways List
        success, response = self.make_request('GET', 'putaway')
        self.log_test("Get Putaways List", success and isinstance(response, list))

        # Complete Putaway
        if self.created_putaway_id:
            success, response = self.make_request('PUT', f'putaway/{self.created_putaway_id}/complete')
            self.log_test("Complete Putaway", success)

        return True

    def test_material_issue(self):
        """Test Material Issue operations"""
        if not self.created_material_id:
            self.log_test("Material Issue", False, "No material available for testing")
            return False

        # Create Material Issue
        issue_data = {
            "department": "Production",
            "requisition_number": f"REQ-{datetime.now().strftime('%H%M%S')}",
            "items": [{
                "material_id": self.created_material_id,
                "material_code": f"TEST-{datetime.now().strftime('%H%M%S')}",
                "material_name": "Test Material",
                "quantity": 10
            }],
            "remarks": "Test issue"
        }
        
        success, response = self.make_request('POST', 'issues', issue_data, 200)
        if success and 'issue_id' in response:
            self.created_issue_id = response['issue_id']
            self.log_test("Create Material Issue", True)
        else:
            self.log_test("Create Material Issue", False, response.get('error', response.get('detail', '')))
            return False

        # Get Issues List
        success, response = self.make_request('GET', 'issues')
        self.log_test("Get Issues List", success and isinstance(response, list))

        return True

    def test_label_generation(self):
        """Test Enhanced Label Generation and Print Logging (Phase 3)"""
        if not self.created_material_id:
            self.log_test("Label Generation", False, "No material available for testing")
            return False

        # Test 1: Check if labels are auto-generated when GRN is created
        if self.created_grn_id:
            success, response = self.make_request('GET', f'labels/by-grn/{self.created_grn_id}')
            if success and isinstance(response, list) and len(response) > 0:
                auto_label = response[0]
                # Verify all required fields are present
                required_fields = [
                    'material_code', 'material_name', 'material_description', 
                    'grn_number', 'batch_number', 'quantity', 'uom', 
                    'date_of_receipt', 'qr_data', 'barcode_data'
                ]
                has_all_fields = all(field in auto_label for field in required_fields)
                self.log_test("Auto-generated Labels from GRN", has_all_fields,
                             "Missing required fields" if not has_all_fields else "")
                
                if has_all_fields:
                    self.created_label_id = auto_label['label_id']
            else:
                self.log_test("Auto-generated Labels from GRN", False, "No labels found for GRN")

        # Test 2: Create Manual Label
        label_data = {
            "material_id": self.created_material_id,
            "grn_id": self.created_grn_id,
            "batch_number": f"MANUAL-{datetime.now().strftime('%H%M%S')}",
            "quantity": 25,
            "uom": "PCS",
            "bin_location": "TEST-01-01-01",
            "manufacturing_date": "2024-01-15",
            "expiry_date": "2025-01-15",
            "storage_condition": "ambient"
        }
        
        success, response = self.make_request('POST', 'labels', label_data, 200)
        if success and 'label_id' in response:
            manual_label_id = response['label_id']
            # Check if all enhanced fields are present
            enhanced_fields = ['qr_data', 'barcode_data', 'uom', 'manufacturing_date', 'expiry_date', 'storage_condition']
            has_enhanced = all(field in response for field in enhanced_fields)
            self.log_test("Create Manual Label with Enhanced Fields", has_enhanced,
                         "Missing enhanced fields" if not has_enhanced else "")
        else:
            self.log_test("Create Manual Label", False, response.get('error', response.get('detail', '')))
            manual_label_id = None

        # Test 3: Print Logging
        if self.created_label_id:
            success, response = self.make_request('POST', f'labels/{self.created_label_id}/print?copies=1')
            if success:
                # Check if print count is updated
                success2, label_response = self.make_request('GET', f'labels/{self.created_label_id}')
                if success2:
                    print_count = label_response.get('print_count', 0)
                    has_print_info = print_count > 0 and 'last_printed_at' in label_response
                    self.log_test("Print Logging", has_print_info,
                                 "Print count not updated" if not has_print_info else "")
                else:
                    self.log_test("Print Logging", False, "Could not retrieve updated label")
            else:
                self.log_test("Print Logging", False, response.get('error', response.get('detail', '')))

        # Test 4: Reprint with Mandatory Reason
        if self.created_label_id:
            reprint_data = {
                "label_id": self.created_label_id,
                "reason": "Label damaged during handling",
                "copies": 1
            }
            success, response = self.make_request('POST', f'labels/{self.created_label_id}/reprint', reprint_data)
            self.log_test("Reprint with Reason", success,
                         response.get('error', response.get('detail', '')) if not success else "")

        # Test 5: Reprint without Reason (should fail)
        if self.created_label_id:
            reprint_data_no_reason = {
                "label_id": self.created_label_id,
                "reason": "",
                "copies": 1
            }
            success, response = self.make_request('POST', f'labels/{self.created_label_id}/reprint', reprint_data_no_reason, 400)
            self.log_test("Reprint without Reason (should fail)", success,
                         "Should have failed with 400 status" if not success else "")

        # Test 6: Bulk Print
        label_ids = []
        if self.created_label_id:
            label_ids.append(self.created_label_id)
        if manual_label_id:
            label_ids.append(manual_label_id)
            
        if label_ids:
            bulk_data = {
                "label_ids": label_ids,
                "copies": 1
            }
            success, response = self.make_request('POST', 'labels/bulk-print', bulk_data)
            self.log_test("Bulk Print", success,
                         response.get('error', response.get('detail', '')) if not success else "")

        # Test 7: Print History for Label
        if self.created_label_id:
            success, response = self.make_request('GET', f'labels/{self.created_label_id}/print-history')
            if success and isinstance(response, list):
                # Should have at least one print log entry
                has_history = len(response) > 0
                if has_history:
                    log_entry = response[0]
                    has_required_fields = all(field in log_entry for field in ['action', 'printed_at', 'printed_by_name'])
                    self.log_test("Label Print History", has_required_fields,
                                 "Missing required fields in print log" if not has_required_fields else "")
                else:
                    self.log_test("Label Print History", False, "No print history found")
            else:
                self.log_test("Label Print History", False, response.get('error', ''))

        # Test 8: All Print Logs
        success, response = self.make_request('GET', 'print-logs')
        if success and isinstance(response, list):
            # Check if our print logs are present
            has_logs = len(response) > 0
            self.log_test("All Print Logs", has_logs,
                         "No print logs found" if not has_logs else "")
        else:
            self.log_test("All Print Logs", False, response.get('error', ''))

        # Test 9: Get Labels List with Enhanced Fields
        success, response = self.make_request('GET', 'labels')
        if success and isinstance(response, list) and len(response) > 0:
            label = response[0]
            # Check for Phase 3 enhanced fields
            phase3_fields = ['uom', 'date_of_receipt', 'manufacturing_date', 'expiry_date', 'storage_condition', 'print_count']
            has_phase3_fields = any(field in label for field in phase3_fields)
            self.log_test("Labels List with Enhanced Fields", has_phase3_fields,
                         "Missing Phase 3 enhanced fields" if not has_phase3_fields else "")
        else:
            self.log_test("Labels List", False, "No labels found or invalid response")

        return True

    def test_reports_and_exports(self):
        """Test Reports and Export functionality"""
        # Test Stock Summary Report
        success, response = self.make_request('GET', 'reports/stock-summary')
        self.log_test("Stock Summary Report", success and isinstance(response, list))

        # Test Movement History Report
        success, response = self.make_request('GET', 'reports/movement-history')
        self.log_test("Movement History Report", success and isinstance(response, list))

        # Test Bin Utilization Report
        success, response = self.make_request('GET', 'reports/bin-utilization')
        self.log_test("Bin Utilization Report", success and isinstance(response, list))

        # Test CSV Export (just check if endpoint responds)
        success, response = self.make_request('GET', 'reports/export/csv?report_type=stock-summary')
        self.log_test("CSV Export Endpoint", success)

        # Test Excel Export
        success, response = self.make_request('GET', 'reports/export/excel?report_type=stock-summary')
        self.log_test("Excel Export Endpoint", success)

        # Test PDF Export
        success, response = self.make_request('GET', 'reports/export/pdf?report_type=stock-summary')
        self.log_test("PDF Export Endpoint", success)

        return True

    def test_user_management(self):
        """Test User Management (Admin only)"""
        # Get Users List
        success, response = self.make_request('GET', 'users')
        self.log_test("Get Users List", success and isinstance(response, list))

        return True

    def test_rbac_user_management(self):
        """Test RBAC User Management features"""
        # Test creating a new user
        user_data = {
            "email": f"test-{datetime.now().strftime('%H%M%S')}@test.com",
            "name": "Test User",
            "password": "test123",
            "role": "Warehouse Operator"
        }
        
        success, response = self.make_request('POST', 'users', user_data, 200)
        created_user_id = None
        if success and 'user_id' in response:
            created_user_id = response['user_id']
            self.log_test("Create User (Admin)", True)
        else:
            self.log_test("Create User (Admin)", False, response.get('error', response.get('detail', '')))

        # Test role change
        if created_user_id:
            success, response = self.make_request('PUT', f'users/{created_user_id}/role?role=Inventory Controller')
            self.log_test("Change User Role (Admin)", success, 
                         response.get('error', response.get('detail', '')) if not success else "")

        # Test user status toggle
        if created_user_id:
            success, response = self.make_request('PUT', f'users/{created_user_id}/status')
            self.log_test("Toggle User Status (Admin)", success,
                         response.get('error', response.get('detail', '')) if not success else "")

        # Test get roles and permissions
        success, response = self.make_request('GET', 'users/roles')
        if success and 'roles' in response and 'permissions' in response:
            roles = response['roles']
            permissions = response['permissions']
            expected_roles = ["Admin", "Warehouse Operator", "Store In-Charge", "Inventory Controller", "Auditor", "Management Viewer"]
            has_all_roles = all(role in roles for role in expected_roles)
            self.log_test("Get Roles and Permissions", has_all_roles,
                         "Missing expected roles" if not has_all_roles else "")
        else:
            self.log_test("Get Roles and Permissions", False, "Invalid response format")

        # Test delete user
        if created_user_id:
            success, response = self.make_request('DELETE', f'users/{created_user_id}')
            self.log_test("Delete User (Admin)", success,
                         response.get('error', response.get('detail', '')) if not success else "")

        return True

    def test_rbac_audit_trail(self):
        """Test RBAC Audit Trail functionality"""
        # Test get audit logs
        success, response = self.make_request('GET', 'audit-logs?limit=10')
        if success and 'logs' in response and 'total' in response:
            logs = response['logs']
            self.log_test("Get Audit Logs", isinstance(logs, list))
            
            # Check if logs have required fields
            if logs:
                log = logs[0]
                required_fields = ['audit_id', 'action', 'entity_type', 'performed_by', 'performed_by_name', 'timestamp']
                has_required = all(field in log for field in required_fields)
                self.log_test("Audit Log Structure", has_required,
                             "Missing required audit fields" if not has_required else "")
        else:
            self.log_test("Get Audit Logs", False, "Invalid response format")

        # Test audit summary
        success, response = self.make_request('GET', 'audit-logs/summary?days=7')
        if success and 'action_stats' in response:
            self.log_test("Get Audit Summary", True)
        else:
            self.log_test("Get Audit Summary", False, response.get('error', ''))

        return True

    def test_rbac_operator_restrictions(self):
        """Test Warehouse Operator role restrictions"""
        # First, create a warehouse operator user and login
        operator_data = {
            "email": f"operator-{datetime.now().strftime('%H%M%S')}@test.com",
            "name": "Test Operator",
            "password": "test123",
            "role": "Warehouse Operator"
        }
        
        # Create operator user as admin
        success, response = self.make_request('POST', 'users', operator_data, 200)
        if not success:
            self.log_test("Create Operator User", False, "Could not create operator for testing")
            return False

        # Store admin token
        admin_token = self.token
        
        # Login as operator
        login_data = {
            "email": operator_data["email"],
            "password": operator_data["password"]
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        if success and 'access_token' in response:
            self.token = response['access_token']  # Switch to operator token
            self.log_test("Operator Login", True)
        else:
            self.log_test("Operator Login", False, response.get('error', ''))
            self.token = admin_token  # Restore admin token
            return False

        # Test operator CANNOT create materials (master data restriction)
        material_data = {
            "material_code": f"OP-TEST-{datetime.now().strftime('%H%M%S')}",
            "name": "Operator Test Material",
            "category": "Test",
            "uom": "PCS"
        }
        
        success, response = self.make_request('POST', 'materials', material_data, 403)
        self.log_test("Operator CANNOT Create Materials", success,
                     "Should have been forbidden (403)" if not success else "")

        # Test operator CANNOT access user management
        success, response = self.make_request('GET', 'users', expected_status=403)
        self.log_test("Operator CANNOT Access User Management", success,
                     "Should have been forbidden (403)" if not success else "")

        # Test operator CAN access GRN (should work)
        success, response = self.make_request('GET', 'grn')
        self.log_test("Operator CAN Access GRN", success,
                     response.get('error', '') if not success else "")

        # Test operator CAN access putaway
        success, response = self.make_request('GET', 'putaway')
        self.log_test("Operator CAN Access Putaway", success,
                     response.get('error', '') if not success else "")

        # Test operator CAN access issues
        success, response = self.make_request('GET', 'issues')
        self.log_test("Operator CAN Access Issues", success,
                     response.get('error', '') if not success else "")

        # Restore admin token
        self.token = admin_token

        return True

    def test_stock_movements(self):
        """Test Stock Movements tracking"""
        success, response = self.make_request('GET', 'movements')
        self.log_test("Get Stock Movements", success and isinstance(response, list))

        return True

    def test_stock_dashboard_apis(self):
        """Test Stock Dashboard APIs for real-time analytics"""
        # Test Stock Summary API
        success, response = self.make_request('GET', 'dashboard/stock-summary')
        if success and isinstance(response, dict):
            # Check for required summary fields
            required_fields = ['total_stock', 'stock_status', 'bin_summary', 'stock_by_category']
            has_required = all(field in response for field in required_fields)
            
            # Check stock_status structure
            stock_status_valid = False
            if 'stock_status' in response and isinstance(response['stock_status'], dict):
                status_fields = ['available', 'blocked', 'quality_hold']
                stock_status_valid = all(field in response['stock_status'] for field in status_fields)
            
            # Check bin_summary structure
            bin_summary_valid = False
            if 'bin_summary' in response and isinstance(response['bin_summary'], dict):
                bin_fields = ['total', 'occupied', 'empty']
                bin_summary_valid = all(field in response['bin_summary'] for field in bin_fields)
            
            overall_valid = has_required and stock_status_valid and bin_summary_valid
            self.log_test("Stock Summary API", overall_valid,
                         "Missing required fields or invalid structure" if not overall_valid else "")
        else:
            self.log_test("Stock Summary API", False, response.get('error', 'Invalid response format'))

        # Test Stock Aging API
        success, response = self.make_request('GET', 'dashboard/stock-aging')
        if success and isinstance(response, dict):
            # Check for aging buckets
            aging_valid = 'aging_buckets' in response
            if aging_valid and isinstance(response['aging_buckets'], dict):
                expected_buckets = ['0-30', '31-60', '61-90', '90+']
                aging_valid = any(bucket in response['aging_buckets'] for bucket in expected_buckets)
            
            self.log_test("Stock Aging API", aging_valid,
                         "Missing or invalid aging buckets" if not aging_valid else "")
        else:
            self.log_test("Stock Aging API", False, response.get('error', 'Invalid response format'))

        # Test Slow Moving Stock API
        success, response = self.make_request('GET', 'dashboard/slow-moving?days_threshold=60')
        if success and isinstance(response, dict):
            # Check for slow moving fields
            slow_fields = ['slow_moving_count', 'non_moving_count', 'slow_moving_items', 'non_moving_items']
            slow_valid = any(field in response for field in slow_fields)
            self.log_test("Slow Moving Stock API", slow_valid,
                         "Missing slow moving data fields" if not slow_valid else "")
        else:
            self.log_test("Slow Moving Stock API", False, response.get('error', 'Invalid response format'))

        # Test Bin Utilization API
        success, response = self.make_request('GET', 'dashboard/bin-utilization')
        if success and isinstance(response, dict):
            # Check for bin utilization fields
            bin_util_fields = ['overall_utilization', 'zone_summary']
            bin_util_valid = any(field in response for field in bin_util_fields)
            self.log_test("Bin Utilization API", bin_util_valid,
                         "Missing bin utilization data" if not bin_util_valid else "")
        else:
            self.log_test("Bin Utilization API", False, response.get('error', 'Invalid response format'))

        # Test FIFO Alerts API
        success, response = self.make_request('GET', 'dashboard/fifo-alerts')
        if success and isinstance(response, dict):
            # Check for FIFO fields
            fifo_fields = ['fifo_materials_count', 'alerts']
            fifo_valid = any(field in response for field in fifo_fields)
            self.log_test("FIFO Alerts API", fifo_valid,
                         "Missing FIFO alerts data" if not fifo_valid else "")
        else:
            self.log_test("FIFO Alerts API", False, response.get('error', 'Invalid response format'))

        # Test Material Stock API
        success, response = self.make_request('GET', 'dashboard/material-stock')
        if success and isinstance(response, dict):
            # Check for material stock fields
            mat_fields = ['top_stock_materials', 'total_materials']
            mat_valid = any(field in response for field in mat_fields)
            self.log_test("Material Stock API", mat_valid,
                         "Missing material stock data" if not mat_valid else "")
        else:
            self.log_test("Material Stock API", False, response.get('error', 'Invalid response format'))

        return True

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        # Test /auth/me endpoint
        success, response = self.make_request('GET', 'auth/me')
        self.log_test("Get Current User", success and 'email' in response)

        return True

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Warehouse Inventory Management System API Tests")
        print("=" * 60)
        
        # Test sequence - order matters due to dependencies
        test_sequence = [
            ("Database Seeding", self.test_seed_database),
            ("Authentication", self.test_login),
            ("Auth Endpoints", self.test_auth_endpoints),
            ("Dashboard Stats", self.test_dashboard_stats),
            ("Material CRUD", self.test_material_crud),
            ("GRN Operations", self.test_grn_operations),
            ("Bin Management", self.test_bin_management),
            ("Putaway Operations", self.test_putaway_operations),
            ("Material Issue", self.test_material_issue),
            ("Label Generation", self.test_label_generation),
            ("Stock Dashboard APIs", self.test_stock_dashboard_apis),
            ("Reports & Exports", self.test_reports_and_exports),
            ("User Management", self.test_user_management),
            ("RBAC User Management", self.test_rbac_user_management),
            ("RBAC Audit Trail", self.test_rbac_audit_trail),
            ("RBAC Operator Restrictions", self.test_rbac_operator_restrictions),
            ("Stock Movements", self.test_stock_movements)
        ]

        for test_name, test_func in test_sequence:
            print(f"\n📋 Testing {test_name}...")
            try:
                test_func()
            except Exception as e:
                self.log_test(f"{test_name} (Exception)", False, str(e))

        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✨ Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return 1

def main():
    """Main test execution"""
    tester = WarehouseAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())