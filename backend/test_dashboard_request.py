#!/usr/bin/env python3
"""
Test dashboard request to debug 403 errors
Simulates the exact request the frontend is making
"""
import sys
import os
import asyncio
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_dashboard_request():
    try:
        from app import get_inventory_analytics, create_access_token, security
        from fastapi.security import HTTPAuthorizationCredentials
        
        print("🔑 Testing dashboard request simulation...")
        
        # Test data - using the actual user from the application
        test_email = "peelz@gmail.com"
        test_client_id = "150bec71-e0bb-4f99-b4e4-4e8e35d4b6a9"  # Actual client ID
        
        # Create a test token
        test_data = {
            "email": test_email,
            "client_id": test_client_id
        }
        
        print(f"📝 Creating token for: {test_email} (client: {test_client_id})")
        token = create_access_token(test_data)
        print(f"✅ Token created: {token[:50]}...")
        
        # Create mock HTTPAuthorizationCredentials
        class MockHTTPAuthorizationCredentials:
            def __init__(self, token):
                self.scheme = "Bearer"
                self.credentials = token
        
        mock_token = MockHTTPAuthorizationCredentials(token)
        
        # Test the dashboard endpoint that's failing
        print(f"🔍 Testing /api/dashboard/inventory-analytics...")
        print(f"   Parameters: platform=all, fast_mode=True, force_refresh=False")
        
        try:
            # Call the exact endpoint that's failing
            result = await get_inventory_analytics(
                token=mock_token,
                fast_mode=True,
                force_refresh=False,
                platform="all",
                start_date=None,
                end_date=None
            )
            print(f"✅ Dashboard request SUCCESS!")
            print(f"   - Response type: {type(result)}")
            if isinstance(result, dict):
                print(f"   - Response keys: {list(result.keys())}")
            
        except Exception as e:
            print(f"❌ Dashboard request FAILED: {e}")
            print(f"   - Error type: {type(e).__name__}")
            
            # Check if it's an HTTPException
            if hasattr(e, 'status_code'):
                print(f"   - Status code: {e.status_code}")
                print(f"   - Detail: {e.detail}")
            
            traceback.print_exc()
        
        # Also test another endpoint
        print(f"\n🔍 Testing /api/dashboard/sku-inventory...")
        try:
            from app import get_paginated_sku_inventory
            from fastapi import BackgroundTasks
            
            background_tasks = BackgroundTasks()
            result = await get_paginated_sku_inventory(
                token=mock_token,
                page=1,
                page_size=2000,
                use_cache=True,
                force_refresh=False,
                platform="shopify",
                background_tasks=background_tasks
            )
            print(f"✅ SKU inventory request SUCCESS!")
            
        except Exception as e:
            print(f"❌ SKU inventory request FAILED: {e}")
            if hasattr(e, 'status_code'):
                print(f"   - Status code: {e.status_code}")
                print(f"   - Detail: {e.detail}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Test setup error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dashboard_request())
