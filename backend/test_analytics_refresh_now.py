#!/usr/bin/env python3
"""
Test Analytics Refresh Cron Job - MANUAL TESTING
Run this to test the analytics refresh cron job manually
"""

import asyncio
import sys

def print_banner():
    print("=" * 80)
    print("🧪 TESTING ANALYTICS REFRESH CRON JOB")
    print("=" * 80)

async def main():
    print_banner()
    
    try:
        # Import the cron job
        from analytics_refresh_cron import analytics_refresh_cron
        
        print("🚀 Running analytics refresh cron job manually...")
        print()
        
        # Run the full analytics refresh
        results = await analytics_refresh_cron.run_full_analytics_refresh()
        
        print("\n" + "=" * 80)
        print("📊 FINAL TEST RESULTS:")
        print("=" * 80)
        
        if results.get("success"):
            print(f"✅ Status: SUCCESS")
            print(f"📋 Total Jobs: {results.get('total_jobs', 0)}")
            print(f"✅ Successful: {results.get('successful_refreshes', 0)}")
            print(f"❌ Failed: {results.get('failed_refreshes', 0)}")
            print(f"⏱️ Duration: {results.get('duration_seconds', 0):.2f} seconds")
            
            # Show client results
            client_results = results.get('client_results', {})
            if client_results:
                print("\n📈 Client Details:")
                for client_id, platforms in client_results.items():
                    print(f"  Client: {client_id}")
                    for platform, result in platforms.items():
                        status = "✅" if result.get("success") else "❌"
                        if result.get("success"):
                            skus = result.get("skus_found", 0)
                            platforms_analyzed = result.get("platforms_analyzed", 0)
                            print(f"    {status} {platform}: {platforms_analyzed} platforms, {skus} SKUs")
                        else:
                            error = result.get("error", "Unknown error")
                            print(f"    {status} {platform}: {error}")
        else:
            print(f"❌ Status: FAILED")
            print(f"Error: {results.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
