#!/usr/bin/env python3
"""
Test script to check what cache entries exist and test the new date filtering endpoints
"""

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
CLIENT_ID = "0c965b09-f8bd-42f9-ae30-1015c4ec1ea2"

# You'll need to provide a valid token
TOKEN = "your_valid_token_here"  # Replace with actual token

def test_cache_endpoints():
    """Test the new cache date filtering endpoints"""
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print("🔍 Testing Cache Date Filtering Endpoints")
    print("=" * 50)
    
    # 1. Check available cache dates
    print("\n1. 📅 Getting available cache dates...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/cache/available-dates/{CLIENT_ID}",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Available dates: {data}")
            available_dates = data.get('available_dates', [])
            
            if available_dates:
                print(f"📊 Found {len(available_dates)} cached dates:")
                for date in available_dates:
                    print(f"   - {date}")
            else:
                print("📭 No cached dates found")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error getting available dates: {e}")
    
    # 2. Check if there's cached data for 2024-01-15
    print("\n2. 🎯 Checking cache for specific date (2024-01-15)...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/cache/by-date/{CLIENT_ID}",
            params={"date": "2024-01-15", "dashboard_type": "metrics"},
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Found cached data for 2024-01-15:")
                print(f"   - Cached date: {data.get('cached_date')}")
                print(f"   - Days difference: {data.get('days_difference')}")
                print(f"   - Has data: {bool(data.get('data'))}")
            else:
                print(f"📭 No cached data found for 2024-01-15: {data.get('error')}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error checking specific date: {e}")
    
    # 3. List all cache entries for debugging
    print("\n3. 🔍 Listing all cache entries for debugging...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/list-cache",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cache entries: {data}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error listing cache: {e}")
    
    # 4. Test the main metrics endpoint with date
    print("\n4. 🚀 Testing main metrics endpoint with date...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/dashboard/metrics",
            params={
                "fast_mode": "true",
                "start_date": "2024-01-15",
                "end_date": "2024-01-15"
            },
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Metrics response:")
            print(f"   - Client ID: {data.get('client_id')}")
            print(f"   - Cached: {data.get('cached')}")
            print(f"   - Target date: {data.get('target_date')}")
            print(f"   - Cached date: {data.get('cached_date')}")
            print(f"   - Days difference: {data.get('days_difference')}")
            print(f"   - Has LLM analysis: {bool(data.get('llm_analysis'))}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error testing metrics endpoint: {e}")

def direct_db_check():
    """Direct database check to see what's in the cache table"""
    print("\n5. 💾 Direct Database Check")
    print("=" * 30)
    print("To check what's actually in your database, run this SQL query:")
    print("""
    SELECT 
        client_id,
        data_type,
        created_at,
        data_hash,
        total_records,
        CASE 
            WHEN llm_response IS NOT NULL THEN 'Has Data'
            ELSE 'No Data'
        END as has_response
    FROM llm_response_cache 
    WHERE client_id = '0c965b09-f8bd-42f9-ae30-1015c4ec1ea2'
    ORDER BY created_at DESC;
    """)

if __name__ == "__main__":
    print("🧪 Cache Date Filtering Test")
    print("=" * 40)
    print(f"Base URL: {BASE_URL}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Target Date: 2024-01-15")
    
    if TOKEN == "your_valid_token_here":
        print("\n⚠️  Please update the TOKEN variable with your actual auth token")
        print("You can get it from your browser's Network tab when calling the API")
    else:
        test_cache_endpoints()
    
    direct_db_check()
    
    print("\n💡 Next Steps:")
    print("1. Check if there are any cache entries in the database")
    print("2. If no entries exist, call the metrics endpoint without dates to generate some")
    print("3. Then try calling with dates to test the filtering")