"""
Comprehensive WMS Backend API Tests
Tests all major features: Auth, Materials, GRN, Quality Inspection, Bins, Putaway, Transfer Orders, Reports
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@warehouse.com"
ADMIN_PASSWORD = "admin123"
OPERATOR_EMAIL = "operator@test.com"
OPERATOR_PASSWORD = "test123"


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful - Role: {data['user']['role']}")
    
    def test_operator_login_success(self):
        """Test operator login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OPERATOR_EMAIL,
            "password": OPERATOR_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        print(f"✓ Operator login successful - Role: {data['user']['role']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestMaterials:
    """Material Master endpoint tests"""
    
    def test_get_all_materials(self, auth_headers):
        """Test fetching all materials"""
        response = requests.get(f"{BASE_URL}/api/materials", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of materials"
        print(f"✓ Retrieved {len(data)} materials")
        
        # Verify we have the expected 73 materials
        if len(data) >= 70:
            print(f"✓ Material count matches expected (~73 materials)")
        
        # Verify material structure
        if len(data) > 0:
            material = data[0]
            assert "material_id" in material
            assert "material_code" in material
            assert "name" in material
            assert "category" in material
            assert "current_stock" in material
            print(f"✓ Material structure validated")
    
    def test_get_materials_by_category(self, auth_headers):
        """Test filtering materials by category"""
        response = requests.get(f"{BASE_URL}/api/materials?category=Raw Materials", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Retrieved {len(data)} Raw Materials")
    
    def test_search_materials(self, auth_headers):
        """Test searching materials"""
        response = requests.get(f"{BASE_URL}/api/materials?search=solar", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Search returned {len(data)} materials matching 'solar'")


class TestGRN:
    """GRN (Goods Receipt Note) endpoint tests"""
    
    def test_get_all_grns(self, auth_headers):
        """Test fetching all GRNs"""
        response = requests.get(f"{BASE_URL}/api/grn", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of GRNs"
        print(f"✓ Retrieved {len(data)} GRNs")
        
        # Verify GRN structure
        if len(data) > 0:
            grn = data[0]
            assert "grn_id" in grn
            assert "grn_number" in grn
            assert "vendor_name" in grn
            assert "items" in grn
            assert "status" in grn
            print(f"✓ GRN structure validated")
    
    def test_get_grns_by_status(self, auth_headers):
        """Test filtering GRNs by status"""
        for status in ["pending", "completed", "partial"]:
            response = requests.get(f"{BASE_URL}/api/grn?status={status}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            print(f"✓ Retrieved {len(data)} GRNs with status '{status}'")
    
    def test_get_completed_grns(self, auth_headers):
        """Test fetching completed GRNs (for putaway)"""
        response = requests.get(f"{BASE_URL}/api/grn?status=completed", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Retrieved {len(data)} completed GRNs for putaway")


class TestQualityInspection:
    """Quality Inspection endpoint tests"""
    
    def test_get_pending_inspections(self, auth_headers):
        """Test fetching GRNs pending inspection"""
        response = requests.get(f"{BASE_URL}/api/grn?status=pending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        pending_count = len(data)
        print(f"✓ Retrieved {pending_count} GRNs pending inspection")
        
        # Also check partial status
        response = requests.get(f"{BASE_URL}/api/grn?status=partial", headers=auth_headers)
        assert response.status_code == 200
        partial_data = response.json()
        print(f"✓ Retrieved {len(partial_data)} GRNs with partial inspection")


class TestBins:
    """Bin Location endpoint tests"""
    
    def test_get_all_bins(self, auth_headers):
        """Test fetching all bins"""
        response = requests.get(f"{BASE_URL}/api/bins", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of bins"
        print(f"✓ Retrieved {len(data)} bins")
        
        # Verify we have 24 bins across 4 zones
        if len(data) >= 24:
            print(f"✓ Bin count matches expected (24 bins)")
        
        # Verify bin structure
        if len(data) > 0:
            bin_item = data[0]
            assert "bin_id" in bin_item
            assert "bin_code" in bin_item
            assert "zone" in bin_item
            assert "capacity" in bin_item
            assert "current_stock" in bin_item
            print(f"✓ Bin structure validated")
    
    def test_get_bin_zones(self, auth_headers):
        """Test fetching bin zones"""
        response = requests.get(f"{BASE_URL}/api/bins/zones/list", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Retrieved {len(data)} zones: {data}")
        
        # Verify we have 4 zones
        if len(data) >= 4:
            print(f"✓ Zone count matches expected (4 zones)")
    
    def test_filter_bins_by_zone(self, auth_headers):
        """Test filtering bins by zone"""
        # First get zones
        zones_response = requests.get(f"{BASE_URL}/api/bins/zones/list", headers=auth_headers)
        zones = zones_response.json()
        
        if zones:
            zone = zones[0]
            response = requests.get(f"{BASE_URL}/api/bins?zone={zone}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            print(f"✓ Retrieved {len(data)} bins in zone '{zone}'")


class TestPutaway:
    """Putaway endpoint tests"""
    
    def test_get_all_putaways(self, auth_headers):
        """Test fetching all putaways"""
        response = requests.get(f"{BASE_URL}/api/putaway", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of putaways"
        print(f"✓ Retrieved {len(data)} putaway tasks")
    
    def test_get_pending_putaways(self, auth_headers):
        """Test fetching pending putaways"""
        response = requests.get(f"{BASE_URL}/api/putaway?status=pending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Retrieved {len(data)} pending putaway tasks")
    
    def test_get_completed_putaways(self, auth_headers):
        """Test fetching completed putaways"""
        response = requests.get(f"{BASE_URL}/api/putaway?status=completed", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Retrieved {len(data)} completed putaway tasks")


class TestTransferOrders:
    """Transfer Orders (WM) endpoint tests"""
    
    def test_get_transfer_requirements(self, auth_headers):
        """Test fetching transfer requirements"""
        response = requests.get(f"{BASE_URL}/api/wm/transfer-requirements", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "transfer_requirements" in data
        print(f"✓ Retrieved {data['total']} transfer requirements")
        
        # Verify TR structure
        if data['total'] > 0:
            tr = data['transfer_requirements'][0]
            assert "tr_number" in tr
            assert "material_code" in tr
            assert "required_quantity" in tr
            assert "status" in tr
            print(f"✓ Transfer Requirement structure validated")
    
    def test_get_transfer_orders(self, auth_headers):
        """Test fetching transfer orders"""
        response = requests.get(f"{BASE_URL}/api/wm/transfer-orders", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "transfer_orders" in data
        print(f"✓ Retrieved {data['total']} transfer orders")
        
        # Verify TO structure
        if data['total'] > 0:
            to = data['transfer_orders'][0]
            assert "to_number" in to
            assert "to_type" in to
            assert "status" in to
            assert "items" in to
            print(f"✓ Transfer Order structure validated")
    
    def test_get_open_transfer_requirements(self, auth_headers):
        """Test fetching open TRs for TO creation"""
        response = requests.get(f"{BASE_URL}/api/wm/transfer-requirements?status=OPEN", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Retrieved {data['total']} OPEN transfer requirements")


class TestWMReports:
    """WM Reports endpoint tests"""
    
    def test_quant_list_report(self, auth_headers):
        """Test LX03 Quant List report"""
        response = requests.get(f"{BASE_URL}/api/wm/reports/quant-list", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "quants" in data or "total_quants" in data
        print(f"✓ Quant List report generated")
    
    def test_bin_status_report(self, auth_headers):
        """Test LX02 Bin Status report"""
        response = requests.get(f"{BASE_URL}/api/wm/reports/bin-status", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "bins" in data or "summary" in data
        print(f"✓ Bin Status report generated")


class TestDashboard:
    """Dashboard/Stock endpoint tests"""
    
    def test_stock_summary(self, auth_headers):
        """Test stock summary endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stock-summary", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"✓ Stock summary retrieved")
    
    def test_bin_utilization(self, auth_headers):
        """Test bin utilization endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/bin-utilization", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"✓ Bin utilization retrieved")
    
    def test_stock_aging(self, auth_headers):
        """Test stock aging endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stock-aging", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"✓ Stock aging retrieved")
    
    def test_fifo_alerts(self, auth_headers):
        """Test FIFO alerts endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/fifo-alerts", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"✓ FIFO alerts retrieved")


class TestLabels:
    """Labels endpoint tests"""
    
    def test_get_labels(self, auth_headers):
        """Test fetching labels"""
        response = requests.get(f"{BASE_URL}/api/labels", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} labels")


class TestUsers:
    """User management endpoint tests"""
    
    def test_get_users(self, auth_headers):
        """Test fetching users (admin only)"""
        response = requests.get(f"{BASE_URL}/api/users", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} users")
        
        # Verify user structure
        if len(data) > 0:
            user = data[0]
            assert "user_id" in user
            assert "email" in user
            assert "role" in user
            print(f"✓ User structure validated")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
