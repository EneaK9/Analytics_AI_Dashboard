#!/usr/bin/env python3
"""
LLM Cache Manager - Efficient caching for LLM responses
Stores responses in database and only regenerates when client data changes
"""

import hashlib
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from database import get_admin_client
import uuid

# Set up logger
logger = logging.getLogger(__name__)

class LLMCacheManager:
    """Manages LLM response caching to avoid unnecessary regeneration"""
    
    def __init__(self):
        self.db_client = get_admin_client()
    
    def _calculate_data_hash(self, client_data: Dict[str, Any]) -> str:
        """Calculate SHA256 hash of client data to detect changes"""
        try:
            # Convert to sorted JSON string for consistent hashing
            data_str = json.dumps(client_data, sort_keys=True, default=str)
            return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"❌ Failed to calculate data hash: {e}")
            return "unknown"
    
    async def get_cached_llm_response(self, client_id: str, client_data: Dict[str, Any], dashboard_type: str = "default") -> Optional[Dict[str, Any]]:
        """
        Get cached LLM response if data hasn't changed
        
        Args:
            client_id: Client identifier
            client_data: Client data for hashing
            dashboard_type: Type of dashboard (business, performance, etc.) for separate caching
        
        Returns:
            - Cached response if data unchanged
            - None if no cache or data changed
        """
        try:
            # Calculate current data hash
            current_hash = self._calculate_data_hash(client_data)
            
            # Check for cached response using client_id only 
            # Note: Current schema allows only one cache entry per client
            response = self.db_client.table("llm_response_cache").select("*").eq("client_id", client_id).limit(1).execute()
            
            if response.data:
                cached_record = response.data[0]
                cached_hash = cached_record.get("data_hash")
                cached_response = cached_record.get("llm_response")
                created_at = cached_record.get("created_at")
                
                # Check if data hash matches (data hasn't changed)
                if cached_hash == current_hash and cached_response:
                    logger.info(f"✅ Cache HIT for client {client_id} ({dashboard_type}) - data unchanged")
                    
                                    # Check if cache is still valid (not too old)
                try:
                    # Handle timezone-aware datetime parsing
                    created_at_str = created_at
                    if created_at_str.endswith('Z'):
                        created_at_str = created_at_str.replace('Z', '+00:00')
                    
                    created_at_dt = datetime.fromisoformat(created_at_str)
                    
                    # Ensure both datetimes are timezone-aware
                    if created_at_dt.tzinfo is None:
                        # If created_at is naive, assume UTC
                        from datetime import timezone
                        created_at_dt = created_at_dt.replace(tzinfo=timezone.utc)
                    
                    current_time = datetime.now(created_at_dt.tzinfo)
                    cache_age = current_time - created_at_dt
                    
                    if cache_age.days < 7:  # Cache valid for 7 days
                        return json.loads(cached_response)
                    else:
                        logger.info(f"⚠️ Cache expired for client {client_id} ({dashboard_type}) (age: {cache_age.days} days)")
                        return None
                except Exception as time_error:
                    logger.warning(f"⚠️ Failed to parse cache timestamp for client {client_id} ({dashboard_type}): {time_error}")
                    # If we can't parse the timestamp, assume cache is valid
                    return json.loads(cached_response)
                else:
                    logger.info(f"🔄 Cache MISS for client {client_id} ({dashboard_type}) - data changed or no cache")
                    return None
            else:
                logger.info(f"🔄 No cache found for client {client_id} ({dashboard_type})")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error checking cache for client {client_id} ({dashboard_type}): {e}")
            return None
    
    async def store_cached_llm_response(self, client_id: str, client_data: Dict[str, Any], llm_response: Dict[str, Any], dashboard_type: str = "default") -> bool:
        """
        Store LLM response in cache with data hash
        
        Args:
            client_id: Client identifier
            client_data: Client data for hashing
            llm_response: LLM response to cache
            dashboard_type: Type of dashboard for separate caching
        
        Returns:
            - True if stored successfully
            - False if storage failed
        """
        try:
            # Calculate data hash
            data_hash = self._calculate_data_hash(client_data)
            
            # Prepare cache record - use actual client_id UUID, store dashboard_type in data_type
            cache_record = {
                "client_id": client_id,  # Use actual UUID, not concatenated string
                "data_hash": data_hash,
                "llm_response": json.dumps(llm_response),
                "data_type": dashboard_type,  # Store dashboard type here
                "total_records": client_data.get("total_records", 0),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Upsert cache record (update if exists, insert if not)
            # Note: Current schema has UNIQUE(client_id), so this will overwrite existing cache for the client
            response = self.db_client.table("llm_response_cache").upsert(
                cache_record, 
                on_conflict="client_id"
            ).execute()
            
            if response.data:
                logger.info(f"✅ Cached LLM response for client {client_id} ({dashboard_type}) (hash: {data_hash[:8]}...)")
                return True
            else:
                logger.error(f"❌ Failed to cache LLM response for client {client_id} ({dashboard_type})")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error storing cache for client {client_id} ({dashboard_type}): {e}")
            return False
    
    async def invalidate_cache(self, client_id: str) -> bool:
        """
        Invalidate cache for a specific client
        
        Returns:
            - True if invalidated successfully
            - False if invalidation failed
        """
        try:
            response = self.db_client.table("llm_response_cache").delete().eq("client_id", client_id).execute()
            logger.info(f"🗑️ Invalidated cache for client {client_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error invalidating cache for client {client_id}: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            # Get total cache entries
            total_response = self.db_client.table("llm_response_cache").select("client_id", count="exact").execute()
            total_entries = total_response.count if total_response.count is not None else 0
            
            # Get cache age distribution
            response = self.db_client.table("llm_response_cache").select("created_at").execute()
            
            if response.data:
                ages = []
                for record in response.data:
                    try:
                        # Handle timezone-aware datetime parsing
                        created_at_str = record["created_at"]
                        if created_at_str.endswith('Z'):
                            created_at_str = created_at_str.replace('Z', '+00:00')
                        
                        created_at = datetime.fromisoformat(created_at_str)
                        
                        # Ensure both datetimes are timezone-aware
                        if created_at.tzinfo is None:
                            # If created_at is naive, assume UTC
                            from datetime import timezone
                            created_at = created_at.replace(tzinfo=timezone.utc)
                        
                        current_time = datetime.now(created_at.tzinfo)
                        age = (current_time - created_at).days
                        ages.append(age)
                    except Exception as parse_error:
                        logger.warning(f"⚠️ Failed to parse created_at: {parse_error}")
                        continue
                
                avg_age = sum(ages) / len(ages) if ages else 0
                oldest_cache = max(ages) if ages else 0
                newest_cache = min(ages) if ages else 0
            else:
                avg_age = oldest_cache = newest_cache = 0
            
            return {
                "total_entries": total_entries,
                "average_age_days": round(avg_age, 1),
                "oldest_cache_days": oldest_cache,
                "newest_cache_days": newest_cache,
                "cache_hit_rate": "N/A"  # Would need to track hits/misses
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting cache stats: {e}")
            return {"error": str(e)}
    
    async def cleanup_expired_cache(self, max_age_days: int = 7) -> int:
        """
        Clean up expired cache entries
        
        Returns:
            - Number of entries cleaned up
        """
        try:
            # Use timezone-aware datetime for cutoff
            from datetime import timezone
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
            
            # Get expired entries
            response = self.db_client.table("llm_response_cache").select("client_id").lt("created_at", cutoff_date).execute()
            
            if response.data:
                expired_count = len(response.data)
                
                # Delete expired entries
                delete_response = self.db_client.table("llm_response_cache").delete().lt("created_at", cutoff_date).execute()
                
                logger.info(f"🧹 Cleaned up {expired_count} expired cache entries (older than {max_age_days} days)")
                return expired_count
            else:
                logger.info(f"🧹 No expired cache entries to clean up")
                return 0
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired cache: {e}")
            return 0

# Global instance
llm_cache_manager = LLMCacheManager() 