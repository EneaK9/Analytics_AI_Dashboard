"""
SKU Cache Manager
Handles caching and pagination for large SKU datasets to prevent timeouts
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from supabase import Client

logger = logging.getLogger(__name__)

class SKUCacheManager:
    def __init__(self, admin_client: Client):
        self.admin_client = admin_client
        self.cache_table = "sku_cache"
        self.cache_duration = timedelta(minutes=30)  # Cache for 30 minutes
        
    async def get_cached_skus(self, client_id: str, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get cached SKU data with pagination"""
        try:
            # Check if cache exists and is valid
            cache_response = self.admin_client.table(self.cache_table).select(
                "data, created_at, total_count"
            ).eq("client_id", client_id).eq("data_type", "sku_list").execute()
            
            if cache_response.data:
                cache_record = cache_response.data[0]
                created_at = datetime.fromisoformat(cache_record['created_at'].replace('Z', '+00:00'))
                
                # Check if cache is still valid
                if datetime.now().replace(tzinfo=created_at.tzinfo) - created_at < self.cache_duration:
                    cached_data = json.loads(cache_record['data'])
                    total_count = cache_record['total_count']
                    
                    # Apply pagination
                    start_idx = (page - 1) * page_size
                    end_idx = start_idx + page_size
                    paginated_skus = cached_data[start_idx:end_idx]
                    
                    total_pages = (total_count + page_size - 1) // page_size
                    
                    logger.info(f"✅ Cache hit for client {client_id} - page {page}/{total_pages}")
                    
                    return {
                        "success": True,
                        "cached": True,
                        "skus": paginated_skus,
                        "pagination": {
                            "current_page": page,
                            "page_size": page_size,
                            "total_count": total_count,
                            "total_pages": total_pages,
                            "has_next": page < total_pages,
                            "has_previous": page > 1
                        },
                        "cache_age_minutes": int((datetime.now().replace(tzinfo=created_at.tzinfo) - created_at).total_seconds() / 60)
                    }
            
            return {"success": False, "cached": False, "message": "No valid cache found"}
            
        except Exception as e:
            logger.error(f"❌ Error retrieving cached SKUs: {e}")
            return {"success": False, "cached": False, "error": str(e)}
    
    async def cache_skus(self, client_id: str, sku_data: List[Dict[str, Any]]) -> bool:
        """Cache SKU data for fast retrieval"""
        try:
            # First, delete any existing cache for this client
            self.admin_client.table(self.cache_table).delete().eq(
                "client_id", client_id
            ).eq("data_type", "sku_list").execute()
            
            # Cache the new data
            cache_record = {
                "client_id": client_id,
                "data_type": "sku_list",
                "data": json.dumps(sku_data),
                "total_count": len(sku_data),
                "created_at": datetime.now().isoformat()
            }
            
            self.admin_client.table(self.cache_table).insert(cache_record).execute()
            
            logger.info(f"✅ Cached {len(sku_data)} SKUs for client {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error caching SKUs: {e}")
            return False
    
    async def get_sku_summary_stats(self, client_id: str) -> Dict[str, Any]:
        """Get summary statistics from cached SKU data"""
        try:
            cache_response = self.admin_client.table(self.cache_table).select(
                "data, total_count"
            ).eq("client_id", client_id).eq("data_type", "sku_list").execute()
            
            if not cache_response.data:
                return {"success": False, "error": "No cached data found"}
            
            cached_data = json.loads(cache_response.data[0]['data'])
            
            # Calculate summary stats
            total_skus = len(cached_data)
            total_inventory_value = sum(item.get('total_value', 0) for item in cached_data)
            low_stock_count = sum(1 for item in cached_data if item.get('current_availability', 0) < 10)
            out_of_stock_count = sum(1 for item in cached_data if item.get('current_availability', 0) <= 0)
            overstock_count = sum(1 for item in cached_data if item.get('current_availability', 0) > 100)
            
            return {
                "success": True,
                "summary_stats": {
                    "total_skus": total_skus,
                    "total_inventory_value": total_inventory_value,
                    "low_stock_count": low_stock_count,
                    "out_of_stock_count": out_of_stock_count,
                    "overstock_count": overstock_count
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating summary stats: {e}")
            return {"success": False, "error": str(e)}
    
    async def invalidate_cache(self, client_id: str):
        """Invalidate/clear cached SKU data for a client"""
        try:
            self.admin_client.table(self.cache_table).delete().eq(
                "client_id", client_id
            ).eq("data_type", "sku_list").execute()
            
            logger.info(f"🗑️ Invalidated SKU cache for client {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error invalidating cache: {e}")
            return False

    async def setup_cache_table(self):
        """Setup the cache table if it doesn't exist"""
        try:
            # This would be run once to create the table
            # In practice, you'd use a migration script
            logger.info("🔧 Cache table setup would be handled by database migrations")
            return True
        except Exception as e:
            logger.error(f"❌ Error setting up cache table: {e}")
            return False

# Global instance
sku_cache_manager = None

def get_sku_cache_manager(admin_client: Client) -> SKUCacheManager:
    """Get or create SKU cache manager instance"""
    global sku_cache_manager
    if sku_cache_manager is None:
        sku_cache_manager = SKUCacheManager(admin_client)
    return sku_cache_manager
