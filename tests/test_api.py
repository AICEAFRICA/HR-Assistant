# -*- coding: utf-8 -*-
"""
Test Suite for HR Assistant FastAPI Backend
Tests all endpoints using requests library
Run with: python test_api.py
"""
import requests
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any
import time

# API Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

class APITester:
    """Test class for HR Assistant API"""
    
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {"passed": 0, "failed": 0, "tests": []}
    
    def test(self, method: str, endpoint: str, data: Dict = None, params: Dict = None, 
             expected_status: int = 200, description: str = ""):
        """Execute a test and record result"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                response = None
            
            success = response.status_code == expected_status
            
            result = {
                "test": description or f"{method} {endpoint}",
                "method": method,
                "endpoint": endpoint,
                "status": response.status_code,
                "expected": expected_status,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
            
            if success:
                self.results["passed"] += 1
                print(f"✅ {result['test']} - {response.status_code}")
            else:
                self.results["failed"] += 1
                print(f"❌ {result['test']} - Expected {expected_status}, got {response.status_code}")
                try:
                    result["response"] = response.json()
                except:
                    result["response"] = response.text
            
            self.results["tests"].append(result)
            return response
            
        except Exception as e:
            self.results["failed"] += 1
            result = {
                "test": description or f"{method} {endpoint}",
                "method": method,
                "endpoint": endpoint,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
            print(f"❌ {result['test']} - Error: {e}")
            self.results["tests"].append(result)
            return None
    
    def print_summary(self):
        """Print test summary"""
        total = self.results["passed"] + self.results["failed"]
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.results['passed']} ✅")
        print(f"Failed: {self.results['failed']} ❌")
        print(f"Success Rate: {(self.results['passed']/total*100):.1f}%" if total > 0 else "N/A")
        print("="*60 + "\n")

def test_system_endpoints(tester: APITester):
    """Test system endpoints"""
    print("\n### SYSTEM ENDPOINTS ###\n")
    
    tester.test("GET", f"{API_PREFIX}/health", description="Health Check")
    tester.test("GET", "/", description="Root Endpoint")

def test_rag_query_endpoints(tester: APITester):
    """Test RAG query endpoints"""
    print("\n### RAG QUERY ENDPOINTS ###\n")
    
    # Query 1: Leave Policy
    query_data = {
        "query": "What is the company's leave policy?",
        "is_urgent": False,
        "user_role": "Employee"
    }
    response = tester.test("POST", f"{API_PREFIX}/query", data=query_data, 
                          description="Query: Leave Policy")
    if response:
        print(f"   Response: {response.json().get('answer', 'N/A')[:100]}...")
    
    # Query 2: Data Query
    query_data = {
        "query": "What is our current headcount?",
        "is_urgent": False,
        "user_role": "HR Personnel"
    }
    response = tester.test("POST", f"{API_PREFIX}/query", data=query_data,
                          description="Query: Headcount")
    
    # Query 3: Urgent Query
    query_data = {
        "query": "Show me probation status alerts",
        "is_urgent": True,
        "user_role": "HR Personnel"
    }
    tester.test("POST", f"{API_PREFIX}/query", data=query_data,
                description="Query: Urgent Probation Status")
    
    # Router Info
    tester.test("POST", f"{API_PREFIX}/query/router-info", 
                description="Get Query Router Info")

def test_leave_management_endpoints(tester: APITester):
    """Test leave management endpoints"""
    print("\n### LEAVE MANAGEMENT ENDPOINTS ###\n")
    
    # Create leave request
    today = date.today()
    leave_data = {
        "employee_name": "John Doe",
        "employee_email": "john.doe@example.com",
        "leave_type": "Annual Leave",
        "start_date": (today + timedelta(days=7)).isoformat(),
        "end_date": (today + timedelta(days=12)).isoformat(),
        "reason": "Planned vacation",
        "emergency_contact": "+1234567890"
    }
    tester.test("POST", f"{API_PREFIX}/leave/request", data=leave_data,
                expected_status=200, description="Create Leave Request")
    
    # Get employee leave requests
    tester.test("GET", f"{API_PREFIX}/leave/employee/john.doe@example.com", 
                expected_status=200, description="Get Employee Leave Requests")
    
    # Get all leave requests
    tester.test("GET", f"{API_PREFIX}/leave/all", expected_status=200,
                description="Get All Leave Requests")
    
    # Get leave statistics
    tester.test("GET", f"{API_PREFIX}/leave/statistics", expected_status=200,
                description="Get Leave Statistics")
    
    # Test leave approval (Note: adjust request_id as needed)
    approval_data = {
        "request_id": 1,
        "status": "approved",
        "comments": "Approved as per policy",
        "hr_reviewer": "Jane Smith"
    }
    tester.test("PUT", f"{API_PREFIX}/leave/approve", data=approval_data,
                expected_status=200, description="Approve Leave Request")

def test_insurance_endpoints(tester: APITester):
    """Test insurance management endpoints"""
    print("\n### INSURANCE ENDPOINTS ###\n")
    
    # Enroll in insurance
    insurance_data = {
        "employee_email": "john.doe@example.com",
        "insurance_type": "Health",
        "coverage_amount": 50000,
        "effective_date": date.today().isoformat(),
        "beneficiary_name": "Jane Doe",
        "beneficiary_relation": "Spouse"
    }
    tester.test("POST", f"{API_PREFIX}/employee-services/insurance/enroll", 
                data=insurance_data, expected_status=200,
                description="Enroll in Insurance")
    
    # Get employee insurance
    tester.test("GET", f"{API_PREFIX}/employee-services/insurance/john.doe@example.com",
                expected_status=200, description="Get Employee Insurance Records")

def test_shares_endpoints(tester: APITester):
    """Test shares management endpoints"""
    print("\n### SHARES ENDPOINTS ###\n")
    
    # Allocate shares
    shares_data = {
        "employee_email": "john.doe@example.com",
        "shares_count": 100,
        "share_price": 10.50,
        "grant_date": date.today().isoformat(),
        "vesting_months": 48
    }
    tester.test("POST", f"{API_PREFIX}/employee-services/shares/allocate",
                data=shares_data, expected_status=200,
                description="Allocate Shares to Employee")
    
    # Get employee shares
    tester.test("GET", f"{API_PREFIX}/employee-services/shares/john.doe@example.com",
                expected_status=200, description="Get Employee Shares")

def test_compliance_endpoints(tester: APITester):
    """Test compliance management endpoints"""
    print("\n### COMPLIANCE ENDPOINTS ###\n")
    
    today = date.today()
    # Record compliance training
    compliance_data = {
        "employee_email": "john.doe@example.com",
        "training_type": "GDPR",
        "completion_date": today.isoformat(),
        "expiry_date": (today + timedelta(days=365)).isoformat(),
        "certificate_url": "https://example.com/cert/gdpr-2024.pdf"
    }
    tester.test("POST", f"{API_PREFIX}/employee-services/compliance/record",
                data=compliance_data, expected_status=200,
                description="Record Compliance Training")
    
    # Get compliance status
    tester.test("GET", f"{API_PREFIX}/employee-services/compliance/john.doe@example.com",
                expected_status=200, description="Get Compliance Status")

def test_governance_endpoints(tester: APITester):
    """Test governance management endpoints"""
    print("\n### GOVERNANCE ENDPOINTS ###\n")
    
    # Create governance role
    role_data = {
        "role_name": "Engineering Manager",
        "department": "Engineering",
        "responsibilities": [
            "Team leadership",
            "Performance reviews",
            "Technical oversight"
        ],
        "reporting_to": "VP Engineering"
    }
    tester.test("POST", f"{API_PREFIX}/employee-services/governance/role",
                data=role_data, expected_status=200,
                description="Create Governance Role")
    
    # Get organization structure
    tester.test("GET", f"{API_PREFIX}/employee-services/governance/structure",
                expected_status=200, description="Get Organization Structure")
    
    # Get organization structure with filter
    tester.test("GET", f"{API_PREFIX}/employee-services/governance/structure?department=Engineering",
                expected_status=200, description="Get Organization Structure (Filtered)")

def test_career_development_endpoints(tester: APITester):
    """Test career development endpoints"""
    print("\n### CAREER DEVELOPMENT ENDPOINTS ###\n")
    
    # Create development plan
    plan_data = {
        "employee_email": "john.doe@example.com",
        "plan_title": "Leadership Development Program",
        "goals": [
            {"description": "Complete project management certification"},
            {"description": "Lead 2 major projects"},
            {"description": "Mentor 2 junior engineers"}
        ],
        "timeline_months": 12,
        "mentor_email": "senior.mentor@example.com"
    }
    tester.test("POST", f"{API_PREFIX}/employee-services/development/plan",
                data=plan_data, expected_status=200,
                description="Create Development Plan")
    
    # Record training completion
    training_data = {
        "employee_email": "john.doe@example.com",
        "training_name": "Advanced Python Development",
        "training_date": date.today().isoformat(),
        "provider": "Coursera",
        "certificate_url": "https://example.com/cert/python-2024.pdf"
    }
    tester.test("POST", f"{API_PREFIX}/employee-services/development/training",
                data=training_data, expected_status=200,
                description="Record Training Completion")
    
    # Get development profile
    tester.test("GET", f"{API_PREFIX}/employee-services/development/john.doe@example.com",
                expected_status=200, description="Get Development Profile")

def test_document_endpoints(tester: APITester):
    """Test document generation endpoints"""
    print("\n### DOCUMENT GENERATION ENDPOINTS ###\n")
    
    # Get templates
    tester.test("GET", f"{API_PREFIX}/documents/templates",
                expected_status=200, description="List Document Templates")
    
    # Generate offer letter
    doc_data = {
        "document_type": "offer_letter",
        "template_data": {
            "employee_name": "John Doe",
            "position_title": "Senior Software Engineer",
            "department": "Engineering",
            "start_date": (date.today() + timedelta(days=30)).isoformat(),
            "salary": 120000,
            "employment_type": "Full-time",
            "response_deadline": (date.today() + timedelta(days=7)).isoformat(),
            "hr_manager_name": "Jane Smith",
            "company_name": "Adanian Labs"
        },
        "output_format": "html"
    }
    tester.test("POST", f"{API_PREFIX}/documents/generate",
                data=doc_data, expected_status=200,
                description="Generate Offer Letter")
    
    # Generate experience certificate
    doc_data = {
        "document_type": "experience_certificate",
        "template_data": {
            "employee_name": "John Doe",
            "position_title": "Software Engineer",
            "department": "Engineering",
            "start_date": "2020-01-15",
            "end_date": date.today().isoformat(),
            "hr_manager_name": "Jane Smith",
            "company_name": "Adanian Labs",
            "he_she": "He",
            "was_were": "was"
        },
        "output_format": "html"
    }
    tester.test("POST", f"{API_PREFIX}/documents/generate",
                data=doc_data, expected_status=200,
                description="Generate Experience Certificate")

def test_dashboard_endpoints(tester: APITester):
    """Test dashboard endpoints"""
    print("\n### DASHBOARD ENDPOINTS ###\n")
    
    # Get metrics
    tester.test("GET", f"{API_PREFIX}/dashboard/metrics",
                expected_status=200, description="Get Dashboard Metrics")
    
    # Get analytics
    tester.test("GET", f"{API_PREFIX}/dashboard/analytics",
                expected_status=200, description="Get Dashboard Analytics")
    
    # Get summary
    tester.test("GET", f"{API_PREFIX}/dashboard/summary",
                expected_status=200, description="Get Dashboard Summary")

def main():
    """Run all tests"""
    print("="*60)
    print("HR ASSISTANT API TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Start Time: {datetime.now().isoformat()}\n")
    
    tester = APITester(BASE_URL)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Server is running\n")
        else:
            print(f"⚠️ API Server returned status {response.status_code}\n")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API Server at {}\n".format(BASE_URL))
        print("Make sure the server is running with: uvicorn main:app --reload")
        return
    except Exception as e:
        print(f"❌ Error connecting to server: {e}\n")
        return
    
    # Run all test suites
    test_system_endpoints(tester)
    test_rag_query_endpoints(tester)
    test_leave_management_endpoints(tester)
    test_insurance_endpoints(tester)
    test_shares_endpoints(tester)
    test_compliance_endpoints(tester)
    test_governance_endpoints(tester)
    test_career_development_endpoints(tester)
    test_document_endpoints(tester)
    test_dashboard_endpoints(tester)
    
    # Print summary
    tester.print_summary()
    
    # Save results
    with open("api_test_results.json", "w") as f:
        json.dump(tester.results, f, indent=2, default=str)
    print("✅ Results saved to api_test_results.json\n")

if __name__ == "__main__":
    main()
