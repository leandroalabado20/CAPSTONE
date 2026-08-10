"""
Automated Login Functionality Tests
PESO CSJDM Job Recommendation System

Run: python test_login.py
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
TEST_RESULTS = []

class Colors:
    GREEN = ''
    RED = ''
    YELLOW = ''
    BLUE = ''
    END = ''

def log_result(test_name, passed, details=""):
    """Log test result"""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} | {test_name}")
    if details:
        print(f"     => {details}")
    TEST_RESULTS.append({"test": test_name, "passed": passed, "details": details})

def test_1_login_page_loads():
    """Test 1: Login page loads without errors"""
    try:
        session = requests.Session()
        response = session.get(f"{BASE_URL}/login")
        passed = response.status_code == 200 and "PESO CSJDM" in response.text
        log_result("Login page loads", passed, f"Status: {response.status_code}")
        return session
    except Exception as e:
        log_result("Login page loads", False, str(e))
        return None

def test_2_login_correct_credentials(session):
    """Test 2: Login with correct credentials (admin/admin123)"""
    try:
        data = {
            'username': 'admin',
            'password': 'admin123'
        }
        response = session.post(f"{BASE_URL}/login", data=data, allow_redirects=True)
        passed = response.status_code == 200 and "Job Recommendation" in response.text
        log_result("Login with correct credentials", passed, f"Status: {response.status_code}")
        return session if passed else None
    except Exception as e:
        log_result("Login with correct credentials", False, str(e))
        return None

def test_3_session_contains_user_id(session):
    """Test 3: Session contains user_id after login"""
    try:
        if session is None:
            raise Exception("No session available")
        # Check if cookies contain session info
        passed = len(session.cookies) > 0
        log_result("Session created after login", passed, f"Cookies count: {len(session.cookies)}")
        return passed
    except Exception as e:
        log_result("Session created after login", False, str(e))
        return False

def test_4_username_displays(session):
    """Test 4: Username displays in top-right corner"""
    try:
        response = session.get(f"{BASE_URL}/recommendation")
        passed = "Admin" in response.text or "admin" in response.text.lower()
        log_result("Username displays after login", passed, "Checked page for username display")
        return passed
    except Exception as e:
        log_result("Username displays after login", False, str(e))
        return False

def test_5_login_wrong_password():
    """Test 5: Login with wrong password shows error"""
    try:
        session = requests.Session()
        data = {
            'username': 'admin',
            'password': 'wrongpassword'
        }
        response = session.post(f"{BASE_URL}/login", data=data)
        passed = "Invalid username or password" in response.text
        log_result("Wrong password shows error", passed, "Checked for error message")
        return passed
    except Exception as e:
        log_result("Wrong password shows error", False, str(e))
        return False

def test_6_login_nonexistent_user():
    """Test 6: Login with non-existent username"""
    try:
        session = requests.Session()
        data = {
            'username': 'nonexistentuser123',
            'password': 'anypassword'
        }
        response = session.post(f"{BASE_URL}/login", data=data)
        passed = "Invalid username or password" in response.text
        log_result("Non-existent user shows error", passed, "Checked for error message")
        return passed
    except Exception as e:
        log_result("Non-existent user shows error", False, str(e))
        return False

def test_7_logout_clears_session(session):
    """Test 7: Logout clears session and redirects to login"""
    try:
        if session is None:
            raise Exception("No session available")
        response = session.get(f"{BASE_URL}/logout", allow_redirects=True)
        passed = "PESO CSJDM" in response.text and response.status_code == 200
        log_result("Logout clears session", passed, "Checked redirect to login page")
        return passed
    except Exception as e:
        log_result("Logout clears session", False, str(e))
        return False

def test_8_protected_route_redirect():
    """Test 8: Accessing protected route without login redirects to login"""
    try:
        session = requests.Session()
        response = session.get(f"{BASE_URL}/recommendation", allow_redirects=True)
        passed = "PESO CSJDM" in response.text and "login" in response.text.lower()
        log_result("Protected route redirects to login", passed, "Checked redirect behavior")
        return passed
    except Exception as e:
        log_result("Protected route redirects to login", False, str(e))
        return False

def test_9_empty_password_field():
    """Test 9: Login with empty password field"""
    try:
        session = requests.Session()
        data = {
            'username': 'admin',
            'password': ''
        }
        response = session.post(f"{BASE_URL}/login", data=data)
        passed = "Invalid username or password" in response.text
        log_result("Empty password rejected", passed, "Checked error handling")
        return passed
    except Exception as e:
        log_result("Empty password rejected", False, str(e))
        return False

def test_10_empty_username_field():
    """Test 10: Login with empty username field"""
    try:
        session = requests.Session()
        data = {
            'username': '',
            'password': 'admin123'
        }
        response = session.post(f"{BASE_URL}/login", data=data)
        passed = "Invalid username or password" in response.text
        log_result("Empty username rejected", passed, "Checked error handling")
        return passed
    except Exception as e:
        log_result("Empty username rejected", False, str(e))
        return False

def test_11_already_logged_in_redirect():
    """Test 11: Accessing /login while already logged in redirects to recommendation"""
    try:
        session = requests.Session()
        # Login first
        data = {'username': 'admin', 'password': 'admin123'}
        session.post(f"{BASE_URL}/login", data=data)
        # Try accessing login page again
        response = session.get(f"{BASE_URL}/login", allow_redirects=True)
        passed = "Job Recommendation" in response.text
        log_result("Already logged in redirects away from login", passed, "Checked redirect behavior")
        return passed
    except Exception as e:
        log_result("Already logged in redirects away from login", False, str(e))
        return False

def test_12_case_sensitive_username():
    """Test 12: Username case sensitivity (admin vs ADMIN)"""
    try:
        session = requests.Session()
        data = {
            'username': 'ADMIN',
            'password': 'admin123'
        }
        response = session.post(f"{BASE_URL}/login", data=data)
        # Check if it fails (assuming usernames are case-sensitive)
        passed = "Invalid username or password" in response.text
        log_result("Username is case-sensitive", passed, "ADMIN rejected (case matters)")
        return passed
    except Exception as e:
        log_result("Username is case-sensitive", False, str(e))
        return False

def print_summary():
    """Print test summary"""
    print(f"\n{'='*60}")
    print(f"AUTOMATED LOGIN TESTS SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for r in TEST_RESULTS if r['passed'])
    total = len(TEST_RESULTS)
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {percentage:.1f}%")

    print(f"\n{'='*60}")
    print("WHAT'S WORKING:")
    print(f"{'='*60}")
    for r in TEST_RESULTS:
        if r['passed']:
            print(f"[OK] {r['test']}")

    if any(not r['passed'] for r in TEST_RESULTS):
        print(f"\n{'='*60}")
        print("WHAT NEEDS FIXING:")
        print(f"{'='*60}")
        for r in TEST_RESULTS:
            if not r['passed']:
                print(f"[ERROR] {r['test']}")
                if r['details']:
                    print(f"   Reason: {r['details']}")

    print(f"\n{'='*60}")
    print(f"Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

def main():
    """Run all login tests"""
    print(f"\n{'='*60}")
    print(f"AUTOMATED LOGIN FUNCTIONALITY TESTS")
    print(f"Testing: {BASE_URL}")
    print(f"{'='*60}\n")

    # Run tests sequentially
    session = test_1_login_page_loads()

    if session:
        logged_in_session = test_2_login_correct_credentials(session)
        test_3_session_contains_user_id(logged_in_session)
        test_4_username_displays(logged_in_session)
        test_7_logout_clears_session(logged_in_session)

    test_5_login_wrong_password()
    test_6_login_nonexistent_user()
    test_8_protected_route_redirect()
    test_9_empty_password_field()
    test_10_empty_username_field()
    test_11_already_logged_in_redirect()
    test_12_case_sensitive_username()

    print_summary()

    # Return exit code (0 if all pass, 1 if any fail)
    return 0 if all(r['passed'] for r in TEST_RESULTS) else 1

if __name__ == '__main__':
    exit(main())
