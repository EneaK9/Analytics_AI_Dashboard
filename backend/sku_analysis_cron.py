#!/usr/bin/env python3
"""
SKU Analysis Cron Job - FIXED VERSION
Uses the EXACT same logic as old working app.py system
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SKUAnalysisCronJob:
    """Cron job to refresh SKU analysis cache every 8 hours - FIXED VERSION"""
    
    def __init__(self):
        self.platforms = ["shopify", "amazon"]
        logger.info("🕐 SKU Analysis Cron Job initialized - USING OLD WORKING LOGIC")
    
    async def get_specific_client(self, target_client_id: str = None) -> List[str]:
        """Get specific client ID or default to main client"""
        if target_client_id:
            logger.info(f"🎯 Targeting specific client: {target_client_id}")
            return [target_client_id]
        
        # Default to the main active client (the one with most data)
        main_client = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"  # Your current client
        logger.info(f"🎯 Using main client: {main_client}")
        return [main_client]
    
    async def refresh_client_sku_analysis(self, client_id: str, platform: str) -> Dict[str, Any]:
        """Refresh SKU analysis for a specific client and platform - OLD WORKING SYSTEM"""
        try:
            logger.info(f"🔄 Starting SKU analysis for client {client_id} (platform: {platform}) - OLD WORKING SYSTEM")
            
            # USE THE EXACT SAME dashboard_inventory_analyzer as the old working system
            from dashboard_inventory_analyzer import dashboard_inventory_analyzer
            import json
            
            # PLATFORM-SPECIFIC ANALYSIS - USE CORRECT APPROACH FOR EACH
            if platform.lower() == "shopify":
                # SHOPIFY: Use dashboard analyzer (organized product data)
                logger.info(f"🛍️ Using dashboard analyzer for Shopify (organized product data)")
                sku_result = await dashboard_inventory_analyzer.get_sku_list(client_id, 1, 10000, use_cache=False, platform=platform)
                
                if not sku_result.get("success"):
                    return {"success": False, "error": f"Shopify dashboard analyzer failed: {sku_result.get('error', 'Unknown error')}"}
                
                skus = sku_result.get("skus", [])
                logger.info(f"✅ Dashboard analyzer returned {len(skus)} Shopify SKUs")
                
            elif platform.lower() == "amazon":
                # AMAZON: Use legacy inventory analyzer (generates SKUs from 10000 orders like old working system)
                logger.info(f"📦 Using legacy inventory analyzer for Amazon (SKU generation from 10000 orders like old system)")
                
                from database import get_admin_client
                from inventory_analyzer import inventory_analyzer
                
                admin_client = get_admin_client()
                
                # Get raw client data (same approach as old working system that generated 100+ SKUs)
                response = admin_client.table("client_data").select("*").eq("client_id", client_id).order("created_at", desc=True).execute()
                
                if not response.data:
                    return {"success": False, "error": "No client data found for Amazon analysis"}
                
                # Prepare data for legacy analysis (same as old working system)
                client_data_for_analysis = {
                    "client_id": client_id,
                    "data": []
                }
                
                for record in response.data:
                    if record.get('data'):
                        try:
                            if isinstance(record['data'], dict):
                                parsed_data = record['data']
                            elif isinstance(record['data'], str):
                                parsed_data = json.loads(record['data'])
                            else:
                                continue
                            client_data_for_analysis["data"].append(parsed_data)
                        except:
                            continue
                
                if not client_data_for_analysis["data"]:
                    return {"success": False, "error": "No valid data for Amazon analysis"}
                
                # Run legacy analysis (same as old working system that generated AMZ-ORDER-xxxxx)
                logger.info(f"🔄 Running legacy inventory analysis on {len(client_data_for_analysis['data'])} records")
                analytics = inventory_analyzer.analyze_inventory_data(client_data_for_analysis)
                skus = analytics.get("sku_inventory", {}).get("skus", [])
                
                logger.info(f"✅ Legacy analyzer returned {len(skus)} Amazon SKUs (same as old working system)")
                
            else:
                return {"success": False, "error": f"Unsupported platform: {platform}"}
            
            # Cache the results using the same simple format as working system
            try:
                # Use existing admin_client for Amazon, or get one for Shopify
                if platform.lower() == "amazon":
                    # admin_client already established above for Amazon
                    pass
                else:
                    admin_client = dashboard_inventory_analyzer._ensure_client()
                    
                cache_key = f"{client_id}_{platform}"
                
                # Clear old cache
                admin_client.table("sku_cache").delete().eq("client_id", cache_key).eq("data_type", "sku_list").execute()
                
                # Insert new cache
                cache_record = {
                    "client_id": cache_key,
                    "data_type": "sku_list", 
                    "data": json.dumps(skus),
                    "total_count": len(skus),
                    "created_at": datetime.now().isoformat()
                }
                admin_client.table("sku_cache").insert(cache_record).execute()
                
                logger.info(f"✅ Successfully cached {len(skus)} SKUs for client {client_id} ({platform}) - OLD WORKING SYSTEM")
                
                return {
                    "success": True,
                    "skus_cached": len(skus),
                    "client_id": client_id,
                    "platform": platform,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"❌ Error caching SKU data: {e}")
                return {"success": False, "error": f"Failed to cache data: {str(e)}"}
                
        except Exception as e:
            logger.error(f"❌ Error in SKU analysis: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_full_analysis(self) -> Dict[str, Any]:
        """Run SKU analysis for all clients and platforms"""
        start_time = datetime.now()
        logger.info("🚀 Starting full SKU analysis cron job - OLD WORKING SYSTEM")
        
        results = {
            "success": True,
            "timestamp": start_time.isoformat(),
            "total_jobs": 0,
            "successful_jobs": 0,
            "failed_jobs": 0,
            "client_results": {}
        }
        
        # Get all active clients
        active_clients = await self.get_specific_client()
        
        if not active_clients:
            logger.warning("⚠️ No active clients found for SKU analysis")
            return {
                "success": True,  # Not really an error if no clients exist yet
                "message": "No active clients found",
                "timestamp": start_time.isoformat(),
                "total_clients": 0,
                "total_jobs": 0,
                "successful_jobs": 0,
                "failed_jobs": 0
            }
        
        logger.info(f"📋 Processing {len(active_clients)} clients with {len(self.platforms)} platforms each")
        results["total_jobs"] = len(active_clients) * len(self.platforms)
        
        # Process each client with proper platform separation
        for client_id in active_clients:
            client_results = {}
            
            for platform in self.platforms:
                try:
                    result = await self.refresh_client_sku_analysis(client_id, platform)
                    client_results[platform] = result
                    
                    if result.get("success"):
                        results["successful_jobs"] += 1
                        logger.info(f"✅ SUCCESS - Client {client_id} ({platform}): {result.get('skus_cached', 0)} SKUs cached")
                    else:
                        results["failed_jobs"] += 1
                        logger.warning(f"⚠️ FAILED - Client {client_id} ({platform}): {result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to process client {client_id} ({platform}): {e}")
                    client_results[platform] = {"success": False, "error": str(e)}
                    results["failed_jobs"] += 1
            
            results["client_results"][client_id] = client_results
        
        # Calculate final results
        duration = (datetime.now() - start_time).total_seconds()
        results["duration_seconds"] = duration
        
        logger.info(f"🏁 SKU analysis cron job completed in {duration:.2f} seconds")
        
        if results['successful_jobs'] > 0:
            logger.info(f"✅ Results: {results['successful_jobs']} successful, {results['failed_jobs']} failed out of {results['total_jobs']} total jobs")
        else:
            logger.info(f"ℹ️ Results: No SKUs cached - this may indicate organized data tables don't exist yet")
        
        return results

# Global instance for easy import
sku_cron_job = SKUAnalysisCronJob()

if __name__ == "__main__":
    async def main():
        results = await sku_cron_job.run_full_analysis()
        print(f"\n🎯 Cron Job Results:")
        print(f"✅ Successful: {results.get('successful_jobs', 0)}")
        print(f"❌ Failed: {results.get('failed_jobs', 0)}")
        print(f"⏱️ Duration: {results.get('duration_seconds', 0):.2f} seconds")
    
    asyncio.run(main())
