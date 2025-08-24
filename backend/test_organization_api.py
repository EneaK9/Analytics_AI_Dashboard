"""
Test script for data organization API endpoints

This script tests the API endpoints for data organization
"""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_BASE_URL = "http://localhost:8000"
CLIENT_ID = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"

# You'll need to get an actual superadmin token by logging in first
SUPERADMIN_TOKEN = None  # Will be obtained from login

async def get_superadmin_token():
    """Get superadmin token by logging in"""
    async with aiohttp.ClientSession() as session:
        login_data = {
            "username": os.getenv("SUPERADMIN_USERNAME", "admin"),
            "password": os.getenv("SUPERADMIN_PASSWORD", "admin123")
        }
        
        async with session.post(f"{API_BASE_URL}/api/superadmin/login", json=login_data) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("access_token")
            else:
                print(f" Login failed: {response.status}")
                text = await response.text()
                print(f"Error: {text}")
                return None

async def test_client_data_summary(token: str):
    """Test getting client data summary"""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}/api/superadmin/client-data-summary/{CLIENT_ID}"
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                print(" Client data summary retrieved successfully!")
                print(json.dumps(result, indent=2))
                return result
            else:
                print(f" Failed to get client data summary: {response.status}")
                text = await response.text()
                print(f"Error: {text}")
                return None

async def test_organize_data(token: str):
    """Test organizing client data"""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}/api/superadmin/organize-data/{CLIENT_ID}"
        
        print(f" Starting data organization for client {CLIENT_ID}...")
        async with session.post(url, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                print(" Data organization completed successfully!")
                print(json.dumps(result, indent=2))
                return result
            else:
                print(f" Data organization failed: {response.status}")
                text = await response.text()
                print(f"Error: {text}")
                return None

async def main():
    """Main test function"""
    print(" Testing Data Organization API")
    print("=" * 50)
    
    # Step 1: Get superadmin token
    print("1. Getting superadmin token...")
    token = await get_superadmin_token()
    if not token:
        print(" Cannot proceed without valid token")
        return
    print(" Token obtained successfully")
    
    # Step 2: Test client data summary
    print("\n2. Testing client data summary...")
    summary = await test_client_data_summary(token)
    
    if summary and summary.get('organization_recommended'):
        print("\n Organization is recommended for this client")
        
        # Step 3: Test data organization
        print("\n3. Testing data organization...")
        result = await test_organize_data(token)
        
        if result and result.get('success'):
            print("\n4. Verifying organization results...")
            # Get summary again to see the changes
            updated_summary = await test_client_data_summary(token)
            if updated_summary:
                print(" Updated summary after organization:")
                print(f"   - Organized tables: {len(updated_summary.get('organized_tables', []))}")
                print(f"   - Is organized: {updated_summary.get('is_organized')}")
    else:
        print("ℹ️ Client data may already be organized or no data available")

if __name__ == "__main__":
    asyncio.run(main())
