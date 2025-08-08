import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

def test_login_and_refresh():
    # Step 1: Login
    login_data = {
        "email": "your_email@example.com",  # Replace with actual email
        "password": "your_password"         # Replace with actual password
    }
    
    print("1. Testing Login...")
    login_response = requests.post(f"{BASE_URL}/api/login/", json=login_data)
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        print("✅ Login successful!")
        print(f"Access Token: {login_result['access_token'][:50]}...")
        print(f"Refresh Token: {login_result['refresh_token'][:50]}...")
        
        # Step 2: Test refresh token
        refresh_data = {
            "refresh": login_result['refresh_token']
        }
        
        print("\n2. Testing Token Refresh...")
        refresh_response = requests.post(f"{BASE_URL}/api/token/refresh/", json=refresh_data)
        
        if refresh_response.status_code == 200:
            refresh_result = refresh_response.json()
            print("✅ Token refresh successful!")
            print(f"New Access Token: {refresh_result['access'][:50]}...")
        else:
            print(f"❌ Token refresh failed: {refresh_response.status_code}")
            print(f"Response: {refresh_response.text}")
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")

if __name__ == "__main__":
    test_login_and_refresh()

