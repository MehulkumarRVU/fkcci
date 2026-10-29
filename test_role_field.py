#!/usr/bin/env python3
import sys
import requests
import json

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8080/api"

print("=" * 60)
print("VERIFY ROLE FIELD TEST")
print("=" * 60)

# Test 1: Create a coach
print("\n[1] Creating coach account...")
try:
    response = requests.post(
        f"{BASE_URL}/auth/signup-coach",
        json={
            "email": "testcoach@example.com",
            "username": "testcoach",
            "password": "secret123"
        },
        timeout=5
    )
    
    if response.status_code == 201:
        coach = response.json()
        print(f"✅ Coach response:")
        print(f"   Role: {coach.get('role', 'MISSING!')}")
        print(f"   Full response: {json.dumps(coach, indent=2)}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Create an athlete
print("\n[2] Creating athlete account...")
try:
    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "email": "testathlete@example.com",
            "username": "testathlete",
            "password": "secret123",
            "sport_type": "boxing"
        },
        timeout=5
    )
    
    if response.status_code == 201:
        athlete = response.json()
        print(f"✅ Athlete response:")
        print(f"   Role: {athlete.get('role', 'MISSING!')}")
        print(f"   Full response: {json.dumps(athlete, indent=2)}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Login as coach and check /me endpoint
print("\n[3] Login as coach and check /me...")
try:
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "testcoach", "password": "secret123"},
        timeout=5
    )
    
    if login_response.status_code == 200:
        token = login_response.json()['access_token']
        
        me_response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if me_response.status_code == 200:
            me_data = me_response.json()
            print(f"✅ Coach /me response:")
            print(f"   Role: {me_data.get('role', 'MISSING!')}")
            print(f"   Full response: {json.dumps(me_data, indent=2)}")
        else:
            print(f"❌ /me failed: {me_response.text}")
    else:
        print(f"❌ Login failed: {login_response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Login as athlete and check /me endpoint
print("\n[4] Login as athlete and check /me...")
try:
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "testathlete", "password": "secret123"},
        timeout=5
    )
    
    if login_response.status_code == 200:
        token = login_response.json()['access_token']
        
        me_response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if me_response.status_code == 200:
            me_data = me_response.json()
            print(f"✅ Athlete /me response:")
            print(f"   Role: {me_data.get('role', 'MISSING!')}")
            print(f"   Full response: {json.dumps(me_data, indent=2)}")
        else:
            print(f"❌ /me failed: {me_response.text}")
    else:
        print(f"❌ Login failed: {login_response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
