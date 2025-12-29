#!/usr/bin/env python3
"""
Test script for QueryAI authentication system
"""
import requests
import json

def test_login(username: str, password: str):
    """Test user login and return token"""
    url = "http://localhost:8000/auth/login"
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login successful for {username}")
            print(f"Token: {result['access_token'][:50]}...")
            print(f"User: {result['user']}")
            return result['access_token']
        else:
            print(f"❌ Login failed for {username}: {response.status_code}")
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def test_protected_endpoint(token: str):
    """Test accessing a protected endpoint with token"""
    url = "http://localhost:8000/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ Protected endpoint access successful")
            print(f"Current user: {user_info}")
        else:
            print(f"❌ Protected endpoint access failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

def main():
    print("🔐 Testing QueryAI Authentication System")
    print("=" * 50)
    
    # Test admin login
    print("\n1. Testing Admin Login")
    admin_token = test_login("admin", "admin123")
    
    if admin_token:
        print("\n2. Testing Protected Endpoint Access")
        test_protected_endpoint(admin_token)
    
    # Test analyst login
    print("\n3. Testing Analyst Login")
    analyst_token = test_login("analyst", "data456")
    
    # Test viewer login  
    print("\n4. Testing Viewer Login")
    viewer_token = test_login("viewer", "view789")
    
    # Test invalid credentials
    print("\n5. Testing Invalid Credentials")
    test_login("admin", "wrongpassword")

if __name__ == "__main__":
    main()