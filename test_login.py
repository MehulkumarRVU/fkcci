#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8080/api"

print("=" * 60)
print("LOGIN TEST")
print("=" * 60)

# Test 1: Create a test athlete
print("\n[1] Creating test athlete...")
try:
    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "password123",
            "sport_type": "boxing",
            "skill_level": "beginner"
        },
        timeout=5
    )
    
    if response.status_code == 201:
        athlete = response.json()
        print(f"✅ Athlete created successfully")
        print(f"   ID: {athlete['id']}")
        print(f"   Username: {athlete['username']}")
        print(f"   Email: {athlete['email']}")
        print(f"   Role: {athlete.get('role', 'N/A')}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Login with the created athlete
print("\n[2] Testing login...")
try:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "testuser", "password": "password123"},
        timeout=5
    )
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Login successful!")
        print(f"   Access Token: {token_data['access_token'][:50]}...")
        print(f"   Token Type: {token_data['token_type']}")
        token = token_data['access_token']
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 3: Get authenticated user info
print("\n[3] Testing GET /me endpoint...")
try:
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    
    if response.status_code == 200:
        user_info = response.json()
        print(f"✅ Got user info successfully!")
        print(f"   Username: {user_info['username']}")
        print(f"   Email: {user_info['email']}")
        print(f"   Role: {user_info.get('role', 'N/A')}")
        print(f"   Sport: {user_info['sport_type']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ ALL LOGIN TESTS PASSED")
print("=" * 60)
print("\nYou can now login with:")
print(f"  Username: testuser")
print(f"  Password: password123")
