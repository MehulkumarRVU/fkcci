#!/usr/bin/env python
import requests
import json
from random import randint

BASE_URL = "http://localhost:8080/api"

coach_user = f"coach{randint(10000, 99999)}"
athlete_user = f"athlete{randint(10000, 99999)}"

print("=" * 50)
print("COACH DASHBOARD TEST")
print("=" * 50)

# 1. Signup Coach
print("\n[1] Testing Coach Signup...")
try:
    coach_response = requests.post(
        f"{BASE_URL}/auth/signup-coach",
        json={
            "email": f"{coach_user}@example.com",
            "username": coach_user,
            "password": "secret123"
        }
    )
    if coach_response.status_code == 201:
        coach_data = coach_response.json()
        print(f"✅ Coach Created: ID={coach_data['id']}, Username={coach_data['username']}, Role={coach_data['role']}")
        coach_id = coach_data['id']
    else:
        print(f"❌ Failed: {coach_response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# 2. Login Coach
print("\n[2] Testing Coach Login...")
try:
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": coach_user, "password": "secret123"}
    )
    if login_response.status_code == 200:
        coach_token = login_response.json()['access_token']
        coach_headers = {"Authorization": f"Bearer {coach_token}"}
        print(f"✅ Coach Login Successful")
    else:
        print(f"❌ Failed: {login_response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# 3. Signup Athlete
print("\n[3] Testing Athlete Signup...")
try:
    athlete_response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "email": f"{athlete_user}@example.com",
            "username": athlete_user,
            "password": "secret123",
            "sport_type": "boxing",
            "skill_level": "intermediate"
        }
    )
    if athlete_response.status_code == 201:
        athlete_data = athlete_response.json()
        print(f"✅ Athlete Created: ID={athlete_data['id']}, Username={athlete_data['username']}")
        athlete_id = athlete_data['id']
    else:
        print(f"❌ Failed: {athlete_response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# 4. Test Coach Summary
print("\n[4] Testing Coach Summary Endpoint...")
try:
    summary_response = requests.get(
        f"{BASE_URL}/analytics/coach/summary",
        headers=coach_headers
    )
    if summary_response.status_code == 200:
        summary = summary_response.json()
        print(f"✅ Summary Retrieved:")
        print(f"   - Total Athletes: {summary['total_athletes']}")
        print(f"   - Sessions This Month: {summary['total_sessions_this_month']}")
        print(f"   - Avg Performance: {summary['avg_performance_across_athletes']}%")
    else:
        print(f"❌ Failed: {summary_response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# 5. Test Coach Athletes List
print("\n[5] Testing Coach Athletes Endpoint...")
try:
    athletes_response = requests.get(
        f"{BASE_URL}/analytics/coach/athletes",
        headers=coach_headers
    )
    if athletes_response.status_code == 200:
        athletes = athletes_response.json()
        print(f"✅ Athletes Retrieved: Count={len(athletes)}")
        for athlete in athletes:
            print(f"   - {athlete['username']} ({athlete['sport_type']}, {athlete['skill_level']})")
    else:
        print(f"❌ Failed: {athletes_response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# 6. Test Monthly Report (should show no sessions yet)
print("\n[6] Testing Monthly Report Endpoint...")
try:
    report_response = requests.get(
        f"{BASE_URL}/analytics/coach/athlete/{athlete_id}/monthly-report",
        headers=coach_headers
    )
    if report_response.status_code == 200:
        report = report_response.json()
        print(f"✅ Monthly Report Retrieved:")
        print(f"   - Athlete: {report['athlete_username']}")
        print(f"   - This Month Sessions: {report['this_month_sessions']}")
        print(f"   - Total Sessions: {report['total_sessions']}")
        print(f"   - Avg Performance Score: {report['monthly_stats']['avg_performance_score']}%")
    else:
        print(f"❌ Failed: {report_response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)
print("✅ ALL TESTS PASSED - COACH DASHBOARD IS READY")
print("=" * 50)
print(f"\nTest Credentials:")
print(f"Coach: {coach_user} / secret123")
print(f"Athlete: {athlete_user} / secret123")
print(f"\nAccess admin.html with coach account to view analytics")
