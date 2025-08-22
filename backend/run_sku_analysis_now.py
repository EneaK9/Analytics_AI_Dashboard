#!/usr/bin/env python3
"""
Manual SKU Analysis Runner
Run this script to manually trigger SKU analysis (for testing)
"""

import asyncio
import logging
from sku_analysis_cron import SKUAnalysisCronJob

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Run SKU analysis manually"""
    print("🚀 Running SKU Analysis manually...")
    
    cron_job = SKUAnalysisCronJob()
    results = await cron_job.run_full_analysis()
    
    print(f"\n📊 Analysis Results:")
    print(f"📋 Total jobs: {results.get('total_jobs', 0)}")
    print(f"✅ Successful: {results.get('successful_jobs', 0)}")
    print(f"⚠️ Failed: {results.get('failed_jobs', 0)}")
    print(f"⏱️ Duration: {results.get('duration_seconds', 0):.2f} seconds")
    
    if results.get('total_jobs', 0) == 0:
        print(f"\nℹ️ Note: {results.get('message', 'No clients found')}")
        print("   This is normal if you haven't uploaded any e-commerce data yet.")
    
    if results.get('client_results'):
        print(f"\n📋 Client Results:")
        for client_id, client_result in results['client_results'].items():
            print(f"  Client {client_id}:")
            for platform, platform_result in client_result.items():
                status = "✅" if platform_result.get('success') else "❌"
                skus = platform_result.get('skus_cached', 0)
                print(f"    {platform}: {status} {skus} SKUs cached")

if __name__ == "__main__":
    asyncio.run(main())
