#!/usr/bin/env python3
"""
Manual API Sync Test Script - SINGLE CLIENT VERSION
Use this to test API sync for one client immediately without waiting for cron schedule
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_single_client_sync(target_client_id: str = None):
    """Test API sync for a single client only"""
    
    print("=" * 80)
    print("TESTING SINGLE CLIENT API SYNC - FOCUSED VERSION")
    print("=" * 80)
    
    try:
        # Get target client ID
        if not target_client_id:
            target_client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"  # Default client
            print(f"Using default client ID: {target_client_id}")
        else:
            print(f"Testing specific client ID: {target_client_id}")
        
        print(f"Starting test at: {datetime.now().isoformat()}")
        print("")
        
        # Step 1: Check if this client has API integrations
        print("STEP 1: Checking client API integrations...")
        try:
            from database import get_admin_client
            db_client = get_admin_client()
            if not db_client:
                print("Could not connect to database")
                return
                
            # Get ALL API integrations for this client (regardless of status)
            response = db_client.table("client_api_credentials").select(
                "credential_id, client_id, platform_type, status, connection_name, "
                "last_sync_at, next_sync_at, sync_frequency_hours, credentials"
            ).eq("client_id", target_client_id).execute()
            
            if not response.data:
                print(f"No API integrations found for client {target_client_id}")
                print("Please set up API integrations first via the admin panel")
                return
                
            print(f"Found {len(response.data)} API integration(s) for this client:")
            platforms_found = []
            for cred in response.data:
                platform = cred['platform_type'] 
                platforms_found.append(platform)
                print(f"  Platform: {platform} ({cred['connection_name']})")
                print(f"     Status: {cred['status']}")
                print(f"     Last Sync: {cred.get('last_sync_at', 'Never')}")
                print(f"     Next Sync: {cred.get('next_sync_at', 'Not scheduled')}")
                print("")
            
            print(f"Platforms found: {', '.join(platforms_found)}")
            
            # Check for missing platforms
            missing_platforms = []
            if 'shopify' not in platforms_found:
                missing_platforms.append('Shopify')
            if 'amazon' not in platforms_found:
                missing_platforms.append('Amazon')
            
            if missing_platforms:
                print("")
                print("MISSING INTEGRATIONS:")
                for platform in missing_platforms:
                    print(f"MISSING: {platform} integration not found for this client")
                print("")
                print("SOLUTION - Use the new multi-platform API endpoint:")
                print(f"   POST /api/superadmin/clients/add-integration")
                print(f"   Body: client_id={target_client_id}")
                print(f"         platform_type=amazon")
                print(f"         connection_name=Main Amazon Store")
                print(f"         amazon_seller_id=YOUR_SELLER_ID")
                print(f"         amazon_access_key_id=YOUR_ACCESS_KEY")
                print(f"         amazon_secret_access_key=YOUR_SECRET_KEY")
                print(f"         amazon_refresh_token=YOUR_REFRESH_TOKEN")
                print("")
                print("Or ask your colleague to use the admin panel to add missing integrations.")
                print("")
            else:
                print("All expected platforms found!")
                print("MULTI-PLATFORM CLIENT CONFIRMED!")
                print("")
                
        except Exception as e:
            print(f"Error checking API credentials: {e}")
            return
        
        # Step 2: Force sync for this client only
        print("STEP 2: Forcing sync for this client...")
        current_time = datetime.now().isoformat()
        
        # Update ALL integrations for this client to sync immediately (reset any error states)
        update_response = db_client.table("client_api_credentials").update({
            "next_sync_at": current_time,
            "status": "connected"  # Reset to connected status
        }).eq("client_id", target_client_id).execute()
        
        updated_count = len(update_response.data) if update_response.data else 0
        print(f"Updated {updated_count} API integration(s) to sync immediately")
        
        if updated_count != len(response.data):
            print(f"WARNING: Found {len(response.data)} integrations but only updated {updated_count}")
        
        # Show which platforms will be synced
        platforms_to_sync = [cred['platform_type'] for cred in response.data]
        print(f"Will sync platforms: {', '.join(platforms_to_sync)}")
        
        if updated_count == 0:
            print("No connected API integrations found to sync")
            print("Make sure the client has connected API integrations")
            return
        
        # Step 3: Run sync ONLY for this specific client
        print("STEP 3: Running API sync for THIS CLIENT ONLY...")
        from api_sync_cron import api_sync_cron
        
        # Get only this client's API integrations (we just reset them all to connected)
        target_integrations = response.data  # Use all integrations since we reset their status
        
        # Update the status in our local data to reflect the database change
        for integration in target_integrations:
            integration['status'] = 'connected'
            integration['next_sync_at'] = current_time
        
        print(f"Syncing {len(target_integrations)} integration(s) for client {target_client_id}")
        expected_platforms = ['shopify', 'amazon'] 
        actual_platforms = [i['platform_type'] for i in target_integrations]
        print(f"Expected platforms: {', '.join(expected_platforms)}")
        print(f"Actual platforms: {', '.join(actual_platforms)}")
        print("")
        
        # System status check
        if len(actual_platforms) == 2 and 'shopify' in actual_platforms and 'amazon' in actual_platforms:
            print("MULTI-PLATFORM STATUS: READY FOR BOTH SHOPIFY AND AMAZON SYNC")
        elif len(actual_platforms) == 1:
            print(f"SINGLE PLATFORM STATUS: Only {actual_platforms[0].upper()} sync available")
            print("The system is now READY to handle multiple platforms when you add them!")
        print("")
        
        # Sync each integration for this client only
        total_records = 0
        successful_syncs = 0
        failed_syncs = 0
        sync_results = {}
        platform_summary = {}
        
        for integration in target_integrations:
            platform = integration['platform_type']
            try:
                print(f"Syncing {platform.upper()} integration...")
                result = await api_sync_cron.sync_client_api_data(integration)
                
                key = f"{target_client_id}_{platform}"
                sync_results[key] = result
                
                # Check if data was actually stored (success = records stored > 0)
                records_stored = result.get('total_records_stored', 0)
                if records_stored > 0:
                    successful_syncs += 1
                    total_records += records_stored
                    platform_summary[platform] = {'status': 'SUCCESS', 'records': records_stored}
                    print(f"SUCCESS: {records_stored} records stored")
                    if result.get('data_summary'):
                        for data_type, count in result['data_summary'].items():
                            print(f"   - {data_type}: {count} new records")
                    
                    # Check if calculations were updated
                    if result.get('dashboard_updated'):
                        print(f"   - SKU calculations triggered for new data")
                    else:
                        print(f"   - No calculations update needed (no new data)")
                else:
                    failed_syncs += 1
                    platform_summary[platform] = {'status': 'FAILED', 'error': result.get('error', 'No records stored')}
                    print(f"FAILED: {result.get('error', 'No records stored')}")
                    
            except Exception as e:
                failed_syncs += 1
                platform_summary[platform] = {'status': 'ERROR', 'error': str(e)}
                print(f"ERROR: {e}")
        
        print("\n" + "="*60)
        print(f"SYNC RESULTS FOR CLIENT {target_client_id}")
        print("="*60)
        for platform, result in platform_summary.items():
            if result['status'] == 'SUCCESS':
                print(f"SUCCESS - {platform.upper()}: {result['records']} records synced")
            else:
                print(f"FAILED - {platform.upper()}: {result['error']}")
        print("")
        print(f"Total successful: {successful_syncs}/{len(target_integrations)}")
        print(f"Total records synced: {total_records}")
        print(f"Integrations processed: {len(target_integrations)}")
        
        print(f"\nCheck logs at: logs/api_sync_cron.log")
        print(f"Data stored in table: client_{target_client_id.replace('-', '_')}_data")
        
        print("\n" + "=" * 80)
        print("SINGLE CLIENT TEST COMPLETED!")
        print("=" * 80)
        
    except Exception as e:
        print(f"Test Error: {e}")
        import traceback
        traceback.print_exc()

async def force_sync_specific_client(client_id: str, platform: str = None):
    """Force sync a specific client immediately"""
    
    print(f"FORCING SYNC FOR CLIENT: {client_id}")
    if platform:
        print(f"PLATFORM: {platform}")
    print("=" * 80)
    
    try:
        # Update next_sync_at to current time to force sync
        from database import get_admin_client
        from datetime import datetime
        
        db_client = get_admin_client()
        current_time = datetime.now().isoformat()
        
        # Update all credentials for this client (or specific platform)
        query = db_client.table("client_api_credentials").update({
            "next_sync_at": current_time
        }).eq("client_id", client_id)
        
        if platform:
            query = query.eq("platform_type", platform)
        
        response = query.execute()
        
        if response.data:
            print(f"Updated {len(response.data)} API credentials to sync now")
            
            # Now run the sync
            from api_sync_cron import api_sync_cron
            results = await api_sync_cron.run_full_sync()
            
            print(f"\nSYNC RESULTS:")
            print(f"Successful syncs: {results.get('successful_syncs', 0)}")
            print(f"Failed syncs: {results.get('failed_syncs', 0)}")
            print(f"Total records synced: {results.get('total_records_synced', 0)}")
            
        else:
            print(f"No API credentials found for client {client_id}")
            if platform:
                print(f"   with platform {platform}")
    
    except Exception as e:
        print(f"Error forcing sync: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
        if sys.argv[1] == "--force" and len(sys.argv) > 2:
            # Force sync with specific client and optional platform
            client_id = sys.argv[2]
            platform = sys.argv[3] if len(sys.argv) > 3 else None
            asyncio.run(force_sync_specific_client(client_id, platform))
        else:
            # Test single client sync
            asyncio.run(test_single_client_sync(client_id))
    else:
        # Test with default client
        asyncio.run(test_single_client_sync())
    
    print("\nUsage examples:")
    print("   python test_api_sync_now.py                    # Test default client")
    print("   python test_api_sync_now.py CLIENT_ID          # Test specific client")
    print("   python test_api_sync_now.py --force CLIENT_ID  # Force sync specific client")
    print("   python test_api_sync_now.py --force CLIENT_ID shopify  # Force sync specific platform")
