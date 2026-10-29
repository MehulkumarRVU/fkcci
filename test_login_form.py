#!/usr/bin/env python
import sys
import requests
from time import time

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

base_url = 'http://localhost:8080/api'
username = f'formtest{int(time())}'
password = 'TestCoach123!'

signup_response = requests.post(
    f'{base_url}/auth/signup-coach',
    json={
        'email': f'{username}@example.com',
        'username': username,
        'password': password,
    },
    timeout=5,
)
signup_response.raise_for_status()

# Test login with form data (like OAuth2PasswordRequestForm expects)
login_data = {
    'username': username,
    'password': password,
}

response = requests.post(f'{base_url}/auth/login', data=login_data, timeout=5)
print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print(f'Access Token: {data.get("access_token")[:30]}...')
    print(f'Token Type: {data.get("token_type")}')
    print('✅ Login successful with form data!')
    
    # Now test getting athlete info
    token = data.get('access_token')
    me_headers = {'Authorization': 'Bearer ' + token}
    me_response = requests.get(f'{base_url}/auth/me',
        headers={'Authorization': f'Bearer {token}'})
    me_response = requests.get(f'{base_url}/auth/me', headers=me_headers, timeout=5)
    if me_response.status_code == 200:
        athlete = me_response.json()
        print(f'\n✅ /me endpoint working')
        print(f'   Role: {athlete.get("role")}')
        print(f'   Is Coach: {athlete.get("role") == "coach"}')
    else:
        print(f'❌ /me failed: {me_response.status_code}')
else:
    print(f'Response: {response.text}')
