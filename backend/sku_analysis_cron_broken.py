#!/usr/bin/env python3
"""
SKU Analysis Cron Job
Runs SKU inventory analysis every 8 hours and caches results
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
    """Cron job to refresh SKU analysis cache every 8 hours"""
    
    def __init__(self):
        self.platforms = ["combined"]  # Raw data isn't platform-specific, so just do one analysis
        logger.info("🕐 SKU Analysis Cron Job initialized")
    
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
        """Refresh SKU analysis for a specific client and platform - SIMPLE VERSION"""
        try:
            logger.info(f"🔄 Starting SKU analysis for client {client_id} (platform: {platform})")
            
            # USE THE EXACT SAME LOGIC AS OLD WORKING SYSTEM - dashboard_inventory_analyzer
            from dashboard_inventory_analyzer import dashboard_inventory_analyzer
            import json
            
            logger.info(f"🚀 Using dashboard_inventory_analyzer.get_sku_list() - SAME AS OLD WORKING SYSTEM")
            
            # This uses organized data tables (shopify_products/amazon_products) like the old working system
            sku_result = await dashboard_inventory_analyzer.get_sku_list(client_id, 1, 10000, use_cache=False, platform=platform)
            
            if not sku_result.get("success"):
                return {"success": False, "error": f"Dashboard analyzer failed: {sku_result.get('error', 'Unknown error')}"}
            
            # Prepare data for analysis (same as app.py)
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
                return {"success": False, "error": "No valid data to analyze"}
            
            # SEPARATE ANALYSIS BY PLATFORM - FILTER RAW DATA BY PLATFORM FIRST
            shopify_data = {"client_id": client_id, "data": []}
            amazon_data = {"client_id": client_id, "data": []}
            
            # Filter raw data by platform - USE PLATFORM FIELD, NOT ORDER ID LENGTH
            for record in client_data_for_analysis["data"]:
                try:
                    platform = record.get('platform', '').lower()
                    if platform == 'shopify':
                        shopify_data['data'].append(record)
                    elif platform == 'amazon':
                        amazon_data['data'].append(record)
                    else:
                        # If no platform field, try to determine by other fields
                        if 'gateway' in record or 'source_name' in record:
                            shopify_data['data'].append(record)  # Likely Shopify
                        elif 'marketplace_id' in record:
                            amazon_data['data'].append(record)   # Likely Amazon
                        else:
                            shopify_data['data'].append(record)  # Default to Shopify for your data
                except Exception as e:
                    logger.warning(f"⚠️ Error processing record: {e}")
                    continue
            
            logger.info(f"📊 Platform split: Shopify={len(shopify_data['data'])}, Amazon={len(amazon_data['data'])}")
            
            # Analyze each platform separately with proper context
            shopify_skus = []
            amazon_skus = []
            
            try:
                # Analyze Shopify data with SHOPIFY context
                if shopify_data['data']:
                    # Add platform context to help analyzer
                    for record in shopify_data['data']:
                        record['_analysis_platform'] = 'shopify'
                    
                    shopify_analytics = inventory_analyzer.analyze_inventory_data(shopify_data)
                    shopify_skus = shopify_analytics.get("sku_inventory", {}).get("skus", [])
                    
                    # Fix SKU codes for Shopify - replace AMZ-ORDER with SHOPIFY-ORDER
                    for sku in shopify_skus:
                        if sku.get('sku_code', '').startswith('AMZ-ORDER-'):
                            sku['sku_code'] = sku['sku_code'].replace('AMZ-ORDER-', 'SHOPIFY-ORDER-')
                        if sku.get('item_name') == 'Amazon Order Item':
                            sku['item_name'] = 'Shopify Order Item'
                    
                    logger.info(f"✅ Shopify analysis: {len(shopify_skus)} SKUs")
                else:
                    logger.info("⚠️ No Shopify data to analyze")
                
                # Analyze Amazon data with AMAZON context
                if amazon_data['data']:
                    # Add platform context to help analyzer
                    for record in amazon_data['data']:
                        record['_analysis_platform'] = 'amazon'
                    
                    amazon_analytics = inventory_analyzer.analyze_inventory_data(amazon_data)
                    amazon_skus = amazon_analytics.get("sku_inventory", {}).get("skus", [])
                    logger.info(f"✅ Amazon analysis: {len(amazon_skus)} SKUs")
                else:
                    logger.info("⚠️ No Amazon data to analyze")
                
                # Cache Shopify results
                admin_client.table("sku_cache").delete().eq("client_id", f"{client_id}_shopify").eq("data_type", "sku_list").execute()
                if shopify_skus:
                    cache_record_shopify = {
                        "client_id": f"{client_id}_shopify",
                        "data_type": "sku_list", 
                        "data": json.dumps(shopify_skus),
                        "total_count": len(shopify_skus),
                        "created_at": datetime.now().isoformat()
                    }
                    admin_client.table("sku_cache").insert(cache_record_shopify).execute()
                
                # Cache Amazon results
                admin_client.table("sku_cache").delete().eq("client_id", f"{client_id}_amazon").eq("data_type", "sku_list").execute()
                if amazon_skus:
                    cache_record_amazon = {
                        "client_id": f"{client_id}_amazon",
                        "data_type": "sku_list", 
                        "data": json.dumps(amazon_skus),
                        "total_count": len(amazon_skus),
                        "created_at": datetime.now().isoformat()
                    }
                    admin_client.table("sku_cache").insert(cache_record_amazon).execute()
                
                logger.info(f"✅ Successfully cached Shopify={len(shopify_skus)}, Amazon={len(amazon_skus)} SKUs for client {client_id} - PLATFORM SEPARATED PROPERLY")
                
                return {
                    "success": True,
                    "skus_cached": len(shopify_skus) + len(amazon_skus),
                    "shopify_skus": len(shopify_skus),
                    "amazon_skus": len(amazon_skus),
                    "client_id": client_id,
                    "platform": platform,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as cache_error:
                logger.error(f"❌ Error caching SKUs: {cache_error}")
                return {"success": False, "error": f"Analysis worked but caching failed: {str(cache_error)}"}
                
        except Exception as e:
            logger.error(f"❌ Error in SKU analysis for client {client_id} ({platform}): {e}")
            return {"success": False, "error": str(e)}
    
    async def run_full_analysis(self) -> Dict[str, Any]:
        """Run SKU analysis for all active clients and platforms"""
        start_time = datetime.now()
        logger.info(f"🚀 Starting full SKU analysis cron job at {start_time}")
        
        # Get specific client (not all clients)
        active_clients = await self.get_specific_client()
        
        if not active_clients:
            logger.warning("⚠️ No active clients found for SKU analysis - this may be normal if organized tables haven't been set up yet")
            return {
                "success": True,  # Not really an error if no clients exist yet
                "message": "No active clients found - organized data tables may not exist yet",
                "timestamp": start_time.isoformat(),
                "total_clients": 0,
                "total_jobs": 0,
                "successful_jobs": 0,
                "failed_jobs": 0,
                "note": "This is normal if you haven't uploaded data yet"
            }
        
        results = {
            "success": True,
            "timestamp": start_time.isoformat(),
            "total_clients": len(active_clients),
            "total_jobs": len(active_clients) * len(self.platforms),
            "successful_jobs": 0,
            "failed_jobs": 0,
            "client_results": {}
        }
        
        # Process each client with proper platform separation
        for client_id in active_clients:
            client_results = {}
            
            try:
                result = await self.refresh_client_sku_analysis(client_id, "separated")
                
                # Create separate results for each platform
                shopify_result = {
                    "success": result.get("success", False),
                    "skus_cached": result.get("shopify_skus", 0)
                }
                amazon_result = {
                    "success": result.get("success", False),
                    "skus_cached": result.get("amazon_skus", 0)
                }
                
                client_results["shopify"] = shopify_result
                client_results["amazon"] = amazon_result
                    
                # Count success for each platform separately
                if shopify_result.get("success") and shopify_result.get("skus_cached", 0) > 0:
                    results["successful_jobs"] += 1
                    logger.info(f"✅ SUCCESS - Client {client_id} (Shopify): {shopify_result.get('skus_cached', 0)} SKUs cached")
                else:
                    results["failed_jobs"] += 1
                    logger.info(f"⚠️ INFO - Client {client_id} (Shopify): No data to cache")
                
                if amazon_result.get("success") and amazon_result.get("skus_cached", 0) > 0:
                    results["successful_jobs"] += 1
                    logger.info(f"✅ SUCCESS - Client {client_id} (Amazon): {amazon_result.get('skus_cached', 0)} SKUs cached")
                else:
                    results["failed_jobs"] += 1
                    logger.info(f"⚠️ INFO - Client {client_id} (Amazon): No data to cache")
                    
            except Exception as e:
                logger.error(f"❌ Failed to process client {client_id}: {e}")
                client_results["shopify"] = {"success": False, "error": str(e)}
                client_results["amazon"] = {"success": False, "error": str(e)}
                results["failed_jobs"] += 2
            
            results["client_results"][client_id] = client_results
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"🏁 SKU analysis cron job completed in {duration:.2f} seconds")
        
        if results['successful_jobs'] > 0:
            logger.info(f"✅ Results: {results['successful_jobs']} successful, {results['failed_jobs']} failed out of {results['total_jobs']} total jobs")
        else:
            logger.info(f"ℹ️ Results: No SKUs cached - this is normal if organized data tables haven't been set up yet")
        
        results["duration_seconds"] = duration
        results["completed_at"] = end_time.isoformat()
        
        return results
    
    async def cleanup_old_cache(self, days_old: int = 2):
        """Clean up old cache entries"""
        try:
            from database import get_admin_client
            admin_client = get_admin_client()
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Delete old cache entries
            response = admin_client.table("sku_cache").delete().lt("created_at", cutoff_date.isoformat()).execute()
            
            deleted_count = len(response.data) if response.data else 0
            logger.info(f"🗑️ Cleaned up {deleted_count} old cache entries (older than {days_old} days)")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up old cache: {e}")

async def main():
    """Main function to run the cron job"""
    try:
        cron_job = SKUAnalysisCronJob()
        
        # Run the full analysis
        results = await cron_job.run_full_analysis()
        
        # Clean up old cache
        await cron_job.cleanup_old_cache()
        
        # Log summary
        if results.get("success"):
            logger.info(f"✅ Cron job completed successfully: {results['successful_jobs']}/{results['total_jobs']} jobs successful")
        else:
            logger.error(f"❌ Cron job failed: {results.get('message')}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Fatal error in cron job: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
