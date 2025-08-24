#!/usr/bin/env python3
"""
Manual Cache Refresh - DEVELOPMENT TESTING
Simple script to refresh analytics cache manually without cron job complexity
Run this whenever you want to test cache refresh functionality
"""

import requests
import json
import os
from datetime import datetime

def manual_cache_refresh():
    """Manually refresh analytics cache for testing"""
    
    print("🚀 Manual Analytics Cache Refresh - DEV TESTING")
    print("=" * 60)
    
    # Configuration
    base_url = "http://localhost:8000"
    
    # Test if server is running
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Server is running at {base_url}")
    except Exception as e:
        print(f"❌ Server not running at {base_url}")
        print(f"   Error: {e}")
        print(f"   👉 Make sure your backend server is running!")
        return
    
    # Get client token (you'll need to replace this with actual token)
    # For now, let's just call the endpoint directly from browser/postman
    
    endpoints_to_test = [
        f"{base_url}/api/dashboard/inventory-analytics?platform=shopify&force_refresh=true&fast_mode=true",
        f"{base_url}/api/dashboard/inventory-analytics?platform=amazon&force_refresh=true&fast_mode=true", 
        f"{base_url}/api/dashboard/inventory-analytics?platform=all&force_refresh=true&fast_mode=true"
    ]
    
    print(f"\n📡 Testing {len(endpoints_to_test)} analytics endpoints:")
    
    for i, url in enumerate(endpoints_to_test, 1):
        platform = url.split("platform=")[1].split("&")[0]
        print(f"\n{i}. Testing {platform} analytics...")
        print(f"   URL: {url}")
        print(f"   👉 Open this URL in your browser with your auth token")
        print(f"   Or use Postman/curl with Authorization header")
    
    print(f"\n💡 Manual Testing Instructions:")
    print(f"1. Start your backend server: python app.py")  
    print(f"2. Login to get your auth token")
    print(f"3. Call the URLs above with your token")
    print(f"4. Check your database - cache should be updated!")
    
    print(f"\n📋 What to check:")
    print(f"- Database cache table: [client_id]_cached_responses")
    print(f"- Look for endpoint_url: /api/dashboard/inventory-analytics") 
    print(f"- Check created_at timestamp - should be recent")
    print(f"- Response_data should contain fresh analytics")
    
    print(f"\n🎯 This is much simpler than fighting with cron job setup!")

if __name__ == "__main__":
    manual_cache_refresh()
