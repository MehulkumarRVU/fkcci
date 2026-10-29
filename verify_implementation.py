#!/usr/bin/env python
import sys
import requests
import json
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_URL = 'http://localhost:8080'
ROOT = Path(__file__).resolve().parent

print('=== COMPREHENSIVE VERIFICATION TEST ===\n')

# Test 1: Check if backend is running
print('[TEST 1] Backend Health Check')
try:
    response = requests.get(f'{BASE_URL}/health')
    response = requests.get(f'{BASE_URL}/api/auth/me', headers={'Authorization': 'Bearer invalid'})
    print('✅ Backend is running on port 8080\n')
except Exception as e:
    print(f'❌ Backend not responding: {e}\n')
    exit(1)

# Test 2: Create new coach account
print('[TEST 2] Coach Signup (New Account)')
timestamp = int(time.time())
coach_data = {
    'email': f'coach-verify-{timestamp}@example.com',
    'username': f'coachverify{timestamp}',
    'password': 'TestCoach123!'
}
try:
    response = requests.post(f'{BASE_URL}/api/auth/signup-coach', json=coach_data)
    print(f'Status: {response.status_code}')
    coach_response = response.json()
    if response.status_code == 200 or response.status_code == 201:
        print(f'✅ Coach signup successful')
        print(f'   - ID: {coach_response.get("id")}')
        print(f'   - Username: {coach_response.get("username")}')
        print(f'   - Role: {coach_response.get("role")}')
        if coach_response.get('role') == 'coach':
            print(f'   - ✅ Role field correctly set to: coach')
            coach_token = None
        else:
            print(f'   ❌ Role is not "coach": {coach_response.get("role")}')
    else:
        print(f'❌ Signup failed: {coach_response}')
    print()
except Exception as e:
    print(f'❌ Error: {e}\n')

# Test 3: Login with new coach account
print('[TEST 3] Coach Login Verification')
try:
    login_data = {
        'username': coach_data['username'],
        'password': coach_data['password']
    }
    response = requests.post(f'{BASE_URL}/api/auth/login', data=login_data)
    if response.status_code == 200:
        login_response = response.json()
        coach_token = login_response.get('access_token')
        print(f'✅ Login successful')
        print(f'   - Token: {coach_token[:20]}...')
        
        # Test 4: Verify /me endpoint returns coach role
        print()
        print('[TEST 4] /me Endpoint Verification')
        response = requests.get(f'{BASE_URL}/api/auth/me', headers={'Authorization': f'Bearer {coach_token}'})
        response = requests.get(
            f'{BASE_URL}/api/auth/me',
            headers={'Authorization': 'Bearer ' + coach_token},
        )
        if response.status_code == 200:
            me_data = response.json()
            print(f'✅ /me endpoint working')
            print(f'   - Role field: {me_data.get("role")}')
            if me_data.get('role') == 'coach':
                print(f'   - ✅ Role correctly persisted as: coach')
            else:
                print(f'   - ❌ Role mismatch: {me_data.get("role")}')
        else:
            print(f'❌ /me endpoint failed: {response.status_code}')
    else:
        print(f'❌ Login failed: {response.status_code}')
    print()
except Exception as e:
    print(f'❌ Error: {e}\n')

# Test 5: Check admin.html has required content
print('[TEST 5] Frontend File Verification')
try:
    with open(ROOT / 'frontend/pages/admin.html', 'r', encoding='utf-8') as f:
        admin_content = f.read()
        if ('Coach Dashboard' in admin_content or 'Coach Analytics' in admin_content) and 'summary-cards' in admin_content:
            print('✅ admin.html exists with coach dashboard content')
        else:
            print('❌ admin.html missing expected content')
except Exception as e:
    print(f'❌ admin.html not found: {e}')

# Test 6: Verify login.html has account type selector
print()
print('[TEST 6] Login Form Account Type Selector')
try:
    with open(ROOT / 'frontend/pages/login.html', 'r', encoding='utf-8') as f:
        login_content = f.read()
        if 'id="accountType"' in login_content and 'Athlete' in login_content and 'Coach' in login_content:
            print('✅ login.html has account type selector')
            if 'id="athleteFields"' in login_content:
                print('✅ Athlete fields container found')
            else:
                print('❌ athleteFields container not found')
        else:
            print('❌ Account type selector not found in login.html')
except Exception as e:
    print(f'❌ Error checking login.html: {e}')

# Test 7: Verify auth.js has coach signup logic
print()
print('[TEST 7] Auth.js Coach Signup Logic')
try:
    with open(ROOT / 'frontend/js/auth.js', 'r', encoding='utf-8') as f:
        auth_content = f.read()
        if 'signup-coach' in auth_content and 'accountType' in auth_content:
            print('✅ auth.js has coach signup endpoint logic')
            if 'athleteFields' in auth_content:
                print('✅ auth.js has account type field toggle logic')
            else:
                print('❌ Field toggle logic not found')
        else:
            print('❌ Coach signup logic not found in auth.js')
except Exception as e:
    print(f'❌ Error checking auth.js: {e}')

# Test 8: Verify admin link in dashboard
print()
print('[TEST 8] Dashboard Admin Link')
try:
    with open(ROOT / 'frontend/pages/dashboard.html', 'r', encoding='utf-8') as f:
        dashboard_content = f.read()
        if 'id="adminLink"' in dashboard_content and 'Coach Analytics' in dashboard_content:
            print('✅ dashboard.html has admin link')
            if 'DOMContentLoaded' in dashboard_content and 'athlete.role' in dashboard_content:
                print('✅ dashboard.html has admin link detection script')
            else:
                print('⚠️  Admin link script may be present but check detection logic')
        else:
            print('❌ Admin link not found in dashboard.html')
except Exception as e:
    print(f'❌ Error checking dashboard.html: {e}')

# Test 9: Check other pages have admin link and detection
print()
print('[TEST 9] Other Pages Admin Link Detection')
pages_to_check = [
    'frontend/pages/profile.html',
    'frontend/pages/session.html'
]
for page in pages_to_check:
    try:
        with open(ROOT / page, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'id="adminLink"' in content and 'DOMContentLoaded' in content:
                print(f'✅ {page.split("/")[-1]} has admin link with detection')
            else:
                print(f'⚠️  {page.split("/")[-1]} may be missing admin link or detection')
    except Exception as e:
        print(f'⚠️  Cannot check {page}: {e}')

print()
print('=== VERIFICATION COMPLETE ===')
print('\nNEXT STEPS:')
print('1. Go to http://localhost:3000/pages/login.html')
print('2. Click "Sign up"')
print('3. Select "🏋️ Coach" from Account Type dropdown')
print('4. Create account with email, username, password')
print('5. Login and look for "Coach Analytics" in navbar')
print('6. If not visible, open DevTools (F12) → Console and check:')
print('   JSON.parse(localStorage.getItem("athlete")).role')
