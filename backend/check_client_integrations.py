#!/usr/bin/env python3
"""
Quick script to check client API integrations
"""

import asyncio
import sys

async def check_client_integrations(client_id: str = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"):
    """Check what API integrations exist for a client"""
    
    try:
        # Import database module properly
        import os
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from database import get_admin_client
        
        db_client = get_admin_client()
        if not db_client:
            print("❌ Could not connect to database")
            return
        
        print(f"🔍 Checking API integrations for client: {client_id}")
        print("=" * 80)
        
        # Get all API integrations for this client
        response = db_client.table("client_api_credentials").select(
            "credential_id, client_id, platform_type, connection_name, status, "
            "last_sync_at, next_sync_at, sync_frequency_hours, created_at"
        ).eq("client_id", client_id).order("platform_type").execute()
        
        if not response.data:
            print(f"❌ NO API integrations found for client {client_id}")
            print("💡 You need to add API integrations via the admin panel")
            return
        
        print(f"✅ Found {len(response.data)} API integration(s):")
        print("")
        
        platforms = {}
        for integration in response.data:
            platform = integration['platform_type']
            platforms[platform] = integration
            
            print(f"📱 Platform: {platform.upper()}")
            print(f"   Connection: {integration['connection_name']}")
            print(f"   Status: {integration['status']}")
            print(f"   Last Sync: {integration.get('last_sync_at', 'Never')}")
            print(f"   Next Sync: {integration.get('next_sync_at', 'Not scheduled')}")
            print(f"   Frequency: {integration['sync_frequency_hours']} hours")
            print(f"   Created: {integration['created_at']}")
            print("")
        
        print("=" * 80)
        print("📊 SUMMARY:")
        print(f"   Total integrations: {len(response.data)}")
        print(f"   Platforms: {', '.join(platforms.keys())}")
        
        # Check for expected platforms
        expected = ['shopify', 'amazon']
        missing = [p for p in expected if p not in platforms]
        
        if missing:
            print(f"   ❌ Missing: {', '.join(missing)}")
            print("")
            print("💡 TO ADD MISSING INTEGRATIONS:")
            print("   1. Go to your admin panel")
            print("   2. Navigate to API Integrations") 
            print(f"   3. Add {', '.join(missing)} integration(s)")
            print(f"   4. Use client ID: {client_id}")
        else:
            print("   ✅ All expected platforms found!")
            
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    client_id = sys.argv[1] if len(sys.argv) > 1 else "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
    asyncio.run(check_client_integrations(client_id))
