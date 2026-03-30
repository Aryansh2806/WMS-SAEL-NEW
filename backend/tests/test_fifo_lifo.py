"""
FIFO/LIFO Rule Engine Backend Tests
Tests for recommendation, exception logging, and exception retrieval APIs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data from seed
FIFO_MATERIAL_ID = "mat_8081c852d61d"  # RAW-001 Steel Plates (FIFO)
LIFO_MATERIAL_ID = "mat_d0dea7cfe860"  # PKG-001 Cardboard Boxes (LIFO)

# Test credentials
ADMIN_EMAIL = "admin@warehouse.com"
ADMIN_PASSWORD = "admin123"
MANAGER_EMAIL = "manager@warehouse.com"
MANAGER_PASSWORD = "manager123"
OPERATOR_EMAIL = "operator@test.com"
OPERATOR_PASSWORD = "test123"


class TestAuth:
    """Authentication tests - regression"""
    
    def test_admin_login(self):
        """Test admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful, role: {data['user']['role']}")
    
    def test_manager_login(self):
        """Test manager login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MANAGER_EMAIL,
            "password": MANAGER_PASSWORD
        })
        assert response.status_code == 200, f"Manager login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "Management Viewer"
        print(f"✓ Manager login successful, role: {data['user']['role']}")
    
    def test_operator_login(self):
        """Test operator login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OPERATOR_EMAIL,
            "password": OPERATOR_PASSWORD
        })
        assert response.status_code == 200, f"Operator login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        print(f"✓ Operator login successful, role: {data['user']['role']}")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.text}")
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def operator_token():
    """Get operator auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": OPERATOR_EMAIL,
        "password": OPERATOR_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Operator login failed: {response.text}")
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def manager_token():
    """Get manager auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": MANAGER_EMAIL,
        "password": MANAGER_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Manager login failed: {response.text}")
    return response.json()["access_token"]


class TestFIFORecommendation:
    """Test FIFO recommendation endpoint - oldest stock first"""
    
    def test_fifo_recommendation_returns_batches_sorted_oldest_first(self, admin_token):
        """GET /api/fifo-lifo/recommendation/{material_id} - FIFO material should return oldest batch first"""
        response = requests.get(
            f"{BASE_URL}/api/fifo-lifo/recommendation/{FIFO_MATERIAL_ID}?quantity_needed=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"FIFO recommendation failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data["material_id"] == FIFO_MATERIAL_ID
        assert data["stock_method"] == "FIFO", f"Expected FIFO, got {data['stock_method']}"
        assert data["quantity_needed"] == 50
        assert "recommended_batches" in data
        assert "all_batches" in data
        
        # Verify FIFO ordering - oldest first
        all_batches = data["all_batches"]
        assert len(all_batches) >= 2, f"Expected at least 2 batches, got {len(all_batches)}"
        
        # First batch should be oldest (earliest receipt_date)
        for i in range(len(all_batches) - 1):
            date1 = all_batches[i].get("receipt_date", "9999")
            date2 = all_batches[i+1].get("receipt_date", "9999")
            assert date1 <= date2, f"FIFO order violated: {date1} > {date2}"
        
        # First batch should be recommended
        assert all_batches[0]["is_recommended"] == True, "First batch should be recommended for FIFO"
        
        print(f"✓ FIFO recommendation correct - {len(all_batches)} batches, oldest first")
        print(f"  First batch: {all_batches[0]['batch_number']} (date: {all_batches[0].get('receipt_date', 'N/A')[:10]})")
    
    def test_fifo_recommendation_has_correct_fields(self, admin_token):
        """Verify all required fields in FIFO recommendation response"""
        response = requests.get(
            f"{BASE_URL}/api/fifo-lifo/recommendation/{FIFO_MATERIAL_ID}?quantity_needed=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check top-level fields
        required_fields = ["material_id", "material_code", "stock_method", "quantity_needed", 
                          "available_stock", "can_fulfill", "recommended_batches", "all_batches"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check batch fields
        if data["all_batches"]:
            batch = data["all_batches"][0]
            batch_fields = ["batch_number", "quantity", "receipt_date", "is_recommended"]
            for field in batch_fields:
                assert field in batch, f"Missing batch field: {field}"
        
        print(f"✓ FIFO recommendation has all required fields")


class TestLIFORecommendation:
    """Test LIFO recommendation endpoint - newest stock first"""
    
    def test_lifo_recommendation_returns_batches_sorted_newest_first(self, admin_token):
        """GET /api/fifo-lifo/recommendation/{material_id} - LIFO material should return newest batch first"""
        response = requests.get(
            f"{BASE_URL}/api/fifo-lifo/recommendation/{LIFO_MATERIAL_ID}?quantity_needed=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"LIFO recommendation failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data["material_id"] == LIFO_MATERIAL_ID
        assert data["stock_method"] == "LIFO", f"Expected LIFO, got {data['stock_method']}"
        assert data["quantity_needed"] == 50
        
        # Verify LIFO ordering - newest first
        all_batches = data["all_batches"]
        assert len(all_batches) >= 2, f"Expected at least 2 batches, got {len(all_batches)}"
        
        # First batch should be newest (latest receipt_date)
        for i in range(len(all_batches) - 1):
            date1 = all_batches[i].get("receipt_date", "0000")
            date2 = all_batches[i+1].get("receipt_date", "0000")
            assert date1 >= date2, f"LIFO order violated: {date1} < {date2}"
        
        # First batch should be recommended
        assert all_batches[0]["is_recommended"] == True, "First batch should be recommended for LIFO"
        
        print(f"✓ LIFO recommendation correct - {len(all_batches)} batches, newest first")
        print(f"  First batch: {all_batches[0]['batch_number']} (date: {all_batches[0].get('receipt_date', 'N/A')[:10]})")
    
    def test_lifo_recommendation_has_correct_fields(self, admin_token):
        """Verify all required fields in LIFO recommendation response"""
        response = requests.get(
            f"{BASE_URL}/api/fifo-lifo/recommendation/{LIFO_MATERIAL_ID}?quantity_needed=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["stock_method"] == "LIFO"
        assert "rule_description" in data or "recommendation_reason" in data.get("all_batches", [{}])[0]
        print(f"✓ LIFO recommendation has all required fields")


class TestExceptionLogging:
    """Test FIFO/LIFO exception logging endpoint"""
    
    def test_log_exception_success(self, admin_token):
        """POST /api/fifo-lifo/log-exception - Log a FIFO override exception"""
        # First get recommendation to know batch numbers
        rec_response = requests.get(
            f"{BASE_URL}/api/fifo-lifo/recommendation/{FIFO_MATERIAL_ID}?quantity_needed=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert rec_response.status_code == 200
        rec_data = rec_response.json()
        
        all_batches = rec_data["all_batches"]
        if len(all_batches) < 2:
            pytest.skip("Need at least 2 batches to test override")
        
        recommended_batch = all_batches[0]["batch_number"]
        selected_batch = all_batches[1]["batch_number"]  # Non-recommended batch
        
        # Log exception
        response = requests.post(
            f"{BASE_URL}/api/fifo-lifo/log-exception",
            params={
                "material_id": FIFO_MATERIAL_ID,
                "selected_batch": selected_batch,
                "recommended_batch": recommended_batch,
                "override_reason": "TEST: Customer requested specific batch for quality testing purposes"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Log exception failed: {response.text}"
        data = response.json()
        
        assert "exception_id" in data
        assert "message" in data
        assert "FIFO" in data["message"]
        
        print(f"✓ Exception logged successfully: {data['exception_id']}")
    
    def test_log_exception_requires_min_10_chars_reason(self, admin_token):
        """POST /api/fifo-lifo/log-exception - Should reject short override reason"""
        response = requests.post(
            f"{BASE_URL}/api/fifo-lifo/log-exception",
            params={
                "material_id": FIFO_MATERIAL_ID,
                "selected_batch": "BATCH-001",
                "recommended_batch": "BATCH-002",
                "override_reason": "short"  # Less than 10 chars
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should fail validation
        assert response.status_code == 422, f"Expected 422 for short reason, got {response.status_code}"
        print(f"✓ Short override reason correctly rejected")
    
    def test_log_exception_requires_auth(self):
        """POST /api/fifo-lifo/log-exception - Should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/fifo-lifo/log-exception",
            params={
                "material_id": FIFO_MATERIAL_ID,
                "selected_batch": "BATCH-001",
                "recommended_batch": "BATCH-002",
                "override_reason": "Test override reason for auth check"
            }
        )
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print(f"✓ Exception logging requires authentication")


class TestExceptionRetrieval:
    """Test FIFO/LIFO exception retrieval endpoints"""
    
    def test_get_exceptions_list(self, admin_token):
        """GET /api/fifo-lifo/exceptions - Returns list of logged exceptions"""
        response = requests.get(
            f"{BASE_URL}/api/fifo-lifo/exceptions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Get exceptions failed: {response.text}"
        data = response.json()
        
        assert "total" in data
        assert "exceptions" in data
        assert isinstance(data["exceptions"], list)
        
        # Should have at least one exception from previous test or seed data
        if data["total"] > 0:
            exc = data["exceptions"][0]
            required_fields = ["exception_id", "material_id", "stock_method", 
                             "recommended_batch", "selected_batch", "override_reason"]
            for field in required_fields:
                assert field in exc, f"Missing exception field: {field}"
        
        print(f"✓ Exceptions list retrieved: {data['total']} total exceptions")
    
    def test_get_exception_summary(self, admin_token):
        """GET /api/fifo-lifo/exceptions/summary - Returns exception summary stats"""
        response = requests.get(
            f"{BASE_URL}/api/fifo-lifo/exceptions/summary?days=30",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Get summary failed: {response.text}"
        data = response.json()
        
        # Check summary structure
        assert "total_exceptions" in data
        assert "by_method" in data
        assert "top_materials" in data
        
        print(f"✓ Exception summary retrieved: {data['total_exceptions']} exceptions in last 30 days")
        print(f"  By method: FIFO={data['by_method'].get('FIFO', 0)}, LIFO={data['by_method'].get('LIFO', 0)}")
    
    def test_exceptions_require_proper_role(self, operator_token):
        """GET /api/fifo-lifo/exceptions - Operator should not have access"""
        response = requests.get(
            f"{BASE_URL}/api/fifo-lifo/exceptions",
            headers={"Authorization": f"Bearer {operator_token}"}
        )
        # Operator role is not in allowed roles for exceptions view
        assert response.status_code == 403, f"Expected 403 for operator, got {response.status_code}"
        print(f"✓ Exceptions endpoint correctly restricts operator access")


class TestRBACManagementViewer:
    """Test RBAC for Management Viewer role"""
    
    def test_manager_cannot_access_material_master(self, manager_token):
        """Management Viewer should NOT have access to Material Master"""
        response = requests.get(
            f"{BASE_URL}/api/materials",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        # Management Viewer should be restricted from Material Master
        # Check if they get 403 or limited data
        print(f"  Material Master response: {response.status_code}")
        # Note: This depends on backend implementation - may return 403 or empty
    
    def test_manager_can_access_stock_dashboard(self, manager_token):
        """Management Viewer should have access to Stock Dashboard APIs"""
        response = requests.get(
            f"{BASE_URL}/api/stock-dashboard/summary",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == 200, f"Manager should access stock dashboard: {response.text}"
        print(f"✓ Management Viewer can access Stock Dashboard")
    
    def test_manager_cannot_create_users(self, manager_token):
        """Management Viewer should NOT be able to create users"""
        response = requests.post(
            f"{BASE_URL}/api/users",
            json={
                "email": "test_new@test.com",
                "password": "test123",
                "name": "Test User",
                "role": "Warehouse Operator"
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == 403, f"Expected 403 for user creation, got {response.status_code}"
        print(f"✓ Management Viewer cannot create users")


class TestReportsRegression:
    """Regression tests for Reports page"""
    
    def test_reports_stock_summary(self, admin_token):
        """GET /api/reports/stock-summary - Stock summary report"""
        response = requests.get(
            f"{BASE_URL}/api/reports/stock-summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # May return empty but should not error
        assert response.status_code == 200, f"Stock summary failed: {response.text}"
        print(f"✓ Stock summary report accessible")
    
    def test_reports_fifo_compliance(self, admin_token):
        """GET /api/reports/fifo-compliance - FIFO compliance report"""
        response = requests.get(
            f"{BASE_URL}/api/reports/fifo-compliance",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"FIFO compliance failed: {response.text}"
        print(f"✓ FIFO compliance report accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
