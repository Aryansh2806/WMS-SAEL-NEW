#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class ReportsAPITester:
    def __init__(self, base_url="https://emergent-advanced.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if 'data' in response_data:
                        print(f"   📊 Data count: {len(response_data.get('data', []))}")
                    if 'total' in response_data:
                        print(f"   📈 Total records: {response_data.get('total', 0)}")
                except:
                    pass
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'No error details')
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text[:200]}")
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'endpoint': endpoint
                })

            return success, response.json() if success else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                'name': name,
                'error': str(e),
                'endpoint': endpoint
            })
            return False, {}

    def test_login(self):
        """Test login with admin credentials"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@warehouse.com", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   🔑 Token obtained for user: {response.get('user', {}).get('name', 'Unknown')}")
            return True
        return False

    def test_grn_stock_report(self):
        """Test GRN-wise stock report"""
        success, response = self.run_test(
            "GRN Stock Report",
            "GET",
            "reports/grn-stock",
            200
        )
        return success

    def test_batch_stock_report(self):
        """Test Batch-wise stock report"""
        success, response = self.run_test(
            "Batch Stock Report",
            "GET",
            "reports/batch-stock",
            200
        )
        return success

    def test_bin_stock_report(self):
        """Test Bin-wise stock report"""
        success, response = self.run_test(
            "Bin Stock Report",
            "GET",
            "reports/bin-stock",
            200
        )
        return success

    def test_movement_history_report(self):
        """Test Movement history report"""
        success, response = self.run_test(
            "Movement History Report",
            "GET",
            "reports/movement-history",
            200
        )
        return success

    def test_fifo_compliance_report(self):
        """Test FIFO compliance report"""
        success, response = self.run_test(
            "FIFO Compliance Report",
            "GET",
            "reports/fifo-compliance",
            200
        )
        return success

    def test_non_fifo_exceptions_report(self):
        """Test Non-FIFO exceptions report"""
        success, response = self.run_test(
            "Non-FIFO Exceptions Report",
            "GET",
            "reports/non-fifo-exceptions",
            200
        )
        return success

    def test_putaway_pending_report(self):
        """Test Putaway pending report"""
        success, response = self.run_test(
            "Putaway Pending Report",
            "GET",
            "reports/putaway-pending",
            200
        )
        return success

    def test_stock_aging_report(self):
        """Test Stock aging report"""
        success, response = self.run_test(
            "Stock Aging Report",
            "GET",
            "reports/stock-aging",
            200
        )
        return success

    def test_dead_slow_stock_report(self):
        """Test Dead/slow stock report"""
        success, response = self.run_test(
            "Dead/Slow Stock Report",
            "GET",
            "reports/dead-slow-stock",
            200
        )
        return success

    def test_daily_summary_report(self):
        """Test Daily summary report"""
        success, response = self.run_test(
            "Daily Summary Report",
            "GET",
            "reports/daily-summary",
            200
        )
        return success

    def test_user_activity_report(self):
        """Test User activity report (Admin only)"""
        success, response = self.run_test(
            "User Activity Report",
            "GET",
            "reports/user-activity",
            200
        )
        return success

    def test_reprint_log_report(self):
        """Test Reprint log report (Admin only)"""
        success, response = self.run_test(
            "Reprint Log Report",
            "GET",
            "reports/reprint-log",
            200
        )
        return success

    def test_stock_reconciliation_report(self):
        """Test Stock reconciliation report"""
        success, response = self.run_test(
            "Stock Reconciliation Report",
            "GET",
            "reports/stock-reconciliation",
            200
        )
        return success

    def test_stock_summary_report(self):
        """Test Stock summary report"""
        success, response = self.run_test(
            "Stock Summary Report",
            "GET",
            "reports/stock-summary",
            200
        )
        return success

    def test_bin_utilization_report(self):
        """Test Bin utilization report"""
        success, response = self.run_test(
            "Bin Utilization Report",
            "GET",
            "reports/bin-utilization",
            200
        )
        return success

    def test_reports_with_filters(self):
        """Test reports with various filters"""
        print("\n🔍 Testing Reports with Filters...")
        
        # Test date filters
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        filters = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        success, response = self.run_test(
            "GRN Stock Report with Date Filter",
            "GET",
            "reports/grn-stock",
            200,
            params=filters
        )
        
        # Test material filter
        material_filters = {
            'material_code': 'MAT001'
        }
        
        success2, response2 = self.run_test(
            "Batch Stock Report with Material Filter",
            "GET",
            "reports/batch-stock",
            200,
            params=material_filters
        )
        
        return success and success2

    def test_export_endpoints(self):
        """Test export endpoints (should return URLs or files)"""
        print("\n🔍 Testing Export Endpoints...")
        
        # Test Excel export
        success1, response1 = self.run_test(
            "Excel Export Endpoint",
            "GET",
            "reports/export/excel",
            200,
            params={'report_type': 'grn-stock'}
        )
        
        # Test PDF export
        success2, response2 = self.run_test(
            "PDF Export Endpoint",
            "GET",
            "reports/export/pdf",
            200,
            params={'report_type': 'grn-stock'}
        )
        
        return success1 and success2

    def test_report_types_endpoint(self):
        """Test report types endpoint"""
        success, response = self.run_test(
            "Report Types Endpoint",
            "GET",
            "reports/types",
            200
        )
        return success

def main():
    print("🚀 Starting Reports Module API Testing...")
    print("=" * 60)
    
    tester = ReportsAPITester()
    
    # Login first
    if not tester.test_login():
        print("❌ Login failed, stopping tests")
        return 1

    print("\n📊 Testing Individual Report Endpoints...")
    print("-" * 40)
    
    # Test all report endpoints
    report_tests = [
        tester.test_grn_stock_report,
        tester.test_batch_stock_report,
        tester.test_bin_stock_report,
        tester.test_movement_history_report,
        tester.test_fifo_compliance_report,
        tester.test_non_fifo_exceptions_report,
        tester.test_putaway_pending_report,
        tester.test_stock_aging_report,
        tester.test_dead_slow_stock_report,
        tester.test_daily_summary_report,
        tester.test_user_activity_report,
        tester.test_reprint_log_report,
        tester.test_stock_reconciliation_report,
        tester.test_stock_summary_report,
        tester.test_bin_utilization_report
    ]
    
    for test in report_tests:
        test()

    # Test additional functionality
    print("\n🔧 Testing Additional Features...")
    print("-" * 40)
    
    tester.test_reports_with_filters()
    tester.test_export_endpoints()
    tester.test_report_types_endpoint()

    # Print results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print("=" * 60)
    print(f"✅ Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"❌ Tests failed: {len(tester.failed_tests)}")
    
    if tester.failed_tests:
        print("\n❌ Failed Tests:")
        for test in tester.failed_tests:
            error_msg = test.get('error', f"Expected {test.get('expected')}, got {test.get('actual')}")
            print(f"   • {test['name']}: {error_msg}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 Reports module backend testing completed successfully!")
        return 0
    else:
        print("⚠️  Reports module has significant issues that need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())