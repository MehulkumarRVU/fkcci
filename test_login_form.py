#!/usr/bin/env python
import requests

# Test login with form data (like OAuth2PasswordRequestForm expects)
login_data = {
    'username': 'coachverify1772362703',
    'password': 'TestCoach123!'
}

response = requests.post('http://localhost:8080/api/auth/login', data=login_data)
print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print(f'Access Token: {data.get("access_token")[:30]}...')
    print(f'Token Type: {data.get("token_type")}')
    print('✅ Login successful with form data!')
    
    # Now test getting athlete info
    token = data.get('access_token')
    me_response = requests.get('http://localhost:8080/api/auth/me',
        headers={'Authorization': f'Bearer {token}'})
    if me_response.status_code == 200:
        athlete = me_response.json()
        print(f'\n✅ /me endpoint working')
        print(f'   Role: {athlete.get("role")}')
        print(f'   Is Coach: {athlete.get("role") == "coach"}')
    else:
        print(f'❌ /me failed: {me_response.status_code}')
else:
    print(f'Response: {response.text}')
