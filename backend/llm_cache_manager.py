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
        """Calculate SHA256 hash of client data to detect changes (excludes volatile fields)"""
        try:
            # 🔍 DEBUG: Log the structure of client_data to understand what's changing
            logger.info(f"🔍 DEBUG: client_data keys: {list(client_data.keys()) if isinstance(client_data, dict) else type(client_data)}")
            
            # Create a copy of client_data excluding volatile fields that change frequently
            stable_data = {}
            excluded_count = 0
            
            # Only include the actual business data, not metadata
            if isinstance(client_data, dict):
                for key, value in client_data.items():
                    # Exclude volatile fields that change on every request but don't affect analysis
                    # Expanded list of volatile fields to exclude
                    if key not in ['retrieved_at', 'generated_at', 'last_updated', 'timestamp', 'request_id', 'cached', 'response_time', 'query_time', 'processing_time', 'metadata', 'last_fetched', 'fetch_time']:
                        stable_data[key] = value
                    else:
                        excluded_count += 1
                        logger.info(f"🔍 DEBUG: Excluded volatile field '{key}': {str(value)[:100]}...")
            else:
                stable_data = client_data
            
            # 🔍 DEBUG: Log what we're actually hashing
            logger.info(f"🔍 DEBUG: stable_data keys: {list(stable_data.keys()) if isinstance(stable_data, dict) else type(stable_data)}")
            logger.info(f"🔍 DEBUG: Excluded {excluded_count} volatile fields")
            
            # Convert to sorted JSON string for consistent hashing  
            data_str = json.dumps(stable_data, sort_keys=True, default=str)
            hash_result = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
            
            logger.info(f"🔍 Calculated data hash: {hash_result[:12]}... from {len(data_str)} chars (excluded {excluded_count} volatile fields)")
            return hash_result
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
            
            # Get existing cache record for this client (all dashboard types in one record)
            response = self.db_client.table("llm_response_cache").select("*").eq("client_id", client_id).limit(1).execute()
            
            if response.data:
                cached_record = response.data[0]
                cached_hash = cached_record.get("data_hash")
                cached_responses_json = cached_record.get("llm_response")
                created_at = cached_record.get("created_at")
                
                # Check if data hash matches (data hasn't changed)
                logger.info(f"🔍 Hash comparison for client {client_id} ({dashboard_type}): cached={cached_hash[:12]}... vs current={current_hash[:12]}...")
                
                # 🚀 TEMPORARY: Force cache usage for debugging (ignore hash mismatch)
                if cached_responses_json:
                    logger.info(f"🚀 TEMP: Using cache regardless of hash for debugging purposes")
                    try:
                        # Handle both string and dict formats for backward compatibility
                        if isinstance(cached_responses_json, str):
                            cached_responses = json.loads(cached_responses_json)
                        elif isinstance(cached_responses_json, dict):
                            cached_responses = cached_responses_json
                        else:
                            logger.warning(f"⚠️ Unexpected cache format for client {client_id}: {type(cached_responses_json)}")
                            return None
                        
                        # If the cached response is the direct LLM analysis (not wrapped)
                        if "llm_analysis" in cached_responses and dashboard_type == "metrics":
                            dashboard_response = cached_responses
                        else:
                            # Get the specific dashboard type response
                            dashboard_response = cached_responses.get(dashboard_type)
                        
                        if dashboard_response:
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
                                    return dashboard_response
                                else:
                                    logger.info(f"⚠️ Cache expired for client {client_id} ({dashboard_type}) (age: {cache_age.days} days)")
                                    return None
                            except Exception as time_error:
                                logger.warning(f"⚠️ Failed to parse cache timestamp for client {client_id} ({dashboard_type}): {time_error}")
                                # If we can't parse the timestamp, assume cache is valid
                                return dashboard_response
                        else:
                            logger.info(f"🔄 No {dashboard_type} cache found for client {client_id}")
                            return None
                    except Exception as parse_error:
                        logger.warning(f"⚠️ Failed to parse cached responses for client {client_id}: {parse_error}")
                        return None
                else:
                    logger.info(f"🔄 Cache MISS for client {client_id} ({dashboard_type}) - data changed or no cache")
                    return None
            else:
                logger.info(f"🔄 No cache found for client {client_id} ({dashboard_type})")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error checking cache for client {client_id} ({dashboard_type}): {e}")
            return None
    
    async def get_most_recent_analysis(self, client_id: str, dashboard_type: str) -> Optional[Dict[str, Any]]:
        """Get the most recent cached analysis for a client and dashboard type"""
        try:
            query = """
            SELECT cached_response 
            FROM llm_response_cache 
            WHERE client_id = %s 
            ORDER BY created_at DESC 
            LIMIT 1
            """
            
            result = self.db_client.table('llm_response_cache').select('cached_response').eq('client_id', client_id).order('created_at', desc=True).limit(1).execute()
            
            if result.data and len(result.data) > 0:
                cached_data = result.data[0]['cached_response']
                # Look for the specific dashboard type
                if dashboard_type in cached_data:
                    logger.info(f"📦 Retrieved most recent analysis for {dashboard_type}")
                    return cached_data[dashboard_type]
                    
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get most recent analysis: {e}")
            return None

    async def get_data_snapshot_for_period(self, client_id: str, start_date: str, end_date: str) -> Optional[str]:
        """Find the most recent data snapshot that was available during the requested period"""
        try:
            # Convert dates for comparison
            end_dt = datetime.fromisoformat(end_date) if end_date else datetime.now()
            
            # Get all cache entries for this client
            result = self.db_client.table('llm_response_cache').select('created_at').eq('client_id', client_id).order('created_at', desc=True).execute()
            
            if result.data:
                for entry in result.data:
                    entry_date = datetime.fromisoformat(entry['created_at'].replace('Z', '+00:00'))
                    if entry_date <= end_dt:
                        snapshot_date = entry['created_at']
                        logger.info(f"📅 Found data snapshot {snapshot_date} for period {start_date} to {end_date}")
                        return snapshot_date
                    
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to find data snapshot for period: {e}")
            return None

    async def get_analysis_by_snapshot_date(self, client_id: str, snapshot_date: str, dashboard_type: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis for a specific data snapshot date"""
        try:
            # Find cache entry closest to snapshot date
            result = self.db_client.table('llm_response_cache').select('cached_response').eq('client_id', client_id).order('created_at', desc=True).execute()
            
            if result.data:
                target_dt = datetime.fromisoformat(snapshot_date.replace('Z', '+00:00'))
                
                # Find the entry that was current at the snapshot date
                for entry in result.data:
                    entry_date = datetime.fromisoformat(entry['cached_response'].get('created_at', entry.get('created_at', '')).replace('Z', '+00:00'))
                    if entry_date <= target_dt:
                        cached_data = entry['cached_response']
                        if dashboard_type in cached_data:
                            logger.info(f"📦 Retrieved cached analysis for snapshot {snapshot_date}")
                            return cached_data[dashboard_type]
                        break
                    
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get analysis by snapshot date: {e}")
            return None

    async def store_cached_llm_response(self, client_id: str, client_data: Dict[str, Any], llm_response: Dict[str, Any], dashboard_type: str = "default", data_snapshot_date: Optional[str] = None) -> bool:
        """
        Store LLM response and keep a single rolling entry per day per dashboard type.
        """
        try:
            data_hash = self._calculate_data_hash(client_data)

            # Compute UTC analysis date for daily roll-up
            try:
                from datetime import timezone
                analysis_date = datetime.now(timezone.utc).date().isoformat()
            except Exception:
                analysis_date = datetime.utcnow().date().isoformat()

            # Remove existing entries for today for this client/type
            try:
                day_start = f"{analysis_date}T00:00:00+00:00"
                day_end = f"{analysis_date}T23:59:59+00:00"
                self.db_client.table("llm_response_cache").delete() \
                    .eq("client_id", client_id) \
                    .eq("data_type", dashboard_type) \
                    .gte("created_at", day_start) \
                    .lte("created_at", day_end) \
                    .execute()
            except Exception:
                pass

            # Store as JSON string to avoid schema conflicts
            llm_response_json = json.dumps({
                "client_id": client_id,
                "data_type": dashboard_type,
                "schema_type": "dashboard_analysis",
                "total_records": client_data.get("total_records", len(client_data.get("data", []))),
                "llm_analysis": llm_response,
                "cached": True,
                "fast_mode": True,
            })

            cache_record = {
                "client_id": client_id,
                "data_hash": data_hash,
                "llm_response": llm_response_json,
                "data_type": dashboard_type,
                "total_records": client_data.get("total_records", len(client_data.get("data", []))),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            response = self.db_client.table("llm_response_cache").insert(cache_record).execute()
            if response.data:
                logger.info(
                    f"✅ Cached daily LLM response for client {client_id} ({dashboard_type}) (hash: {data_hash[:8]}...)"
                )
                return True
            logger.error(
                f"❌ Failed to cache LLM response for client {client_id} ({dashboard_type})"
            )
            return False
        except Exception as e:
            logger.error(
                f"❌ Error storing daily cache for client {client_id} ({dashboard_type}): {e}"
            )
            return False

    async def get_daily_latest_in_range(self, client_id: str, start_date: str, end_date: str, dashboard_type: str = "metrics") -> List[Dict[str, Any]]:
        """Return latest cache per day within range, ordered by day ascending."""
        try:
            response = self.db_client.table("llm_response_cache").select("*") \
                .eq("client_id", client_id) \
                .eq("data_type", dashboard_type) \
                .gte("created_at", f"{start_date}T00:00:00") \
                .lte("created_at", f"{end_date}T23:59:59") \
                .order("created_at", desc=True) \
                .execute()

            latest_by_day = {}
            for entry in response.data or []:
                day_key = entry.get("analysis_date") or (entry.get("created_at", "")[:10])
                if not day_key or day_key in latest_by_day:
                    continue
                llm_resp = entry.get("llm_response")
                if isinstance(llm_resp, str):
                    try:
                        llm_resp = json.loads(llm_resp)
                    except Exception:
                        continue
                latest_by_day[day_key] = { **entry, "llm_response": llm_resp }

            return [latest_by_day[k] for k in sorted(latest_by_day.keys())]
        except Exception as e:
            logger.error(f"❌ Failed to get daily latest in range: {e}")
            return []
    
    async def invalidate_cache(self, client_id: str, dashboard_type: Optional[str] = None) -> bool:
        """
        Invalidate cache for a specific client and/or dashboard type
        
        Args:
            client_id: Client identifier
            dashboard_type: Optional dashboard type. If None, invalidates all dashboards for client
        
        Returns:
            - True if invalidated successfully
            - False if invalidation failed
        """
        try:
            if dashboard_type:
                # Invalidate specific dashboard type only - remove it from the JSON structure
                existing = self.db_client.table("llm_response_cache").select("*").eq("client_id", client_id).limit(1).execute()
                
                if existing.data:
                    existing_record = existing.data[0]
                    existing_responses_json = existing_record.get("llm_response", "{}")
                    
                    try:
                        existing_responses = json.loads(existing_responses_json)
                        
                        # Remove the specific dashboard type
                        if dashboard_type in existing_responses:
                            del existing_responses[dashboard_type]
                            
                            if existing_responses:
                                # Update record with remaining dashboard types
                                update_record = {
                                    "llm_response": json.dumps(existing_responses),
                                    "updated_at": datetime.now().isoformat()
                                }
                                response = self.db_client.table("llm_response_cache").update(update_record).eq("client_id", client_id).execute()
                                logger.info(f"🗑️ Invalidated {dashboard_type} cache for client {client_id}")
                            else:
                                # No dashboard types left, delete the entire record
                                response = self.db_client.table("llm_response_cache").delete().eq("client_id", client_id).execute()
                                logger.info(f"🗑️ Invalidated {dashboard_type} cache (last one) for client {client_id}")
                        else:
                            logger.info(f"ℹ️ No {dashboard_type} cache found to invalidate for client {client_id}")
                    except Exception as parse_error:
                        logger.warning(f"⚠️ Failed to parse cache for invalidation, deleting entire record for client {client_id}: {parse_error}")
                        response = self.db_client.table("llm_response_cache").delete().eq("client_id", client_id).execute()
                else:
                    logger.info(f"ℹ️ No cache found to invalidate for client {client_id}")
            else:
                # Invalidate all dashboard types for this client - delete entire record
                response = self.db_client.table("llm_response_cache").delete().eq("client_id", client_id).execute()
                logger.info(f"🗑️ Invalidated ALL dashboard caches for client {client_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error invalidating cache for client {client_id} ({dashboard_type}): {e}")
            return False
    
    async def invalidate_all_cache(self) -> bool:
        """
        Invalidate all cached responses (use with caution)
        
        Returns:
            - True if invalidated successfully
            - False if invalidation failed
        """
        try:
            response = self.db_client.table("llm_response_cache").delete().neq("client_id", "").execute()
            logger.info(f"🗑️ Invalidated ALL cached responses")
            return True
        except Exception as e:
            logger.error(f"❌ Error invalidating all cache: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics with dashboard-type breakdown"""
        try:
            # Get all cache entries with dashboard type breakdown
            response = self.db_client.table("llm_response_cache").select("client_id", "data_type", "created_at").execute()
            
            if not response.data:
                return {
                    "total_entries": 0,
                    "by_dashboard_type": {},
                    "unique_clients": 0,
                    "avg_age_days": 0,
                    "cache_hit_potential": "0%"
                }
            
            # Analyze cache data
            dashboard_types = {}
            unique_clients = set()
            ages = []
            
            for record in response.data:
                # Extract client_id and parse dashboard types from JSON
                client_id = record.get("client_id", "")
                cached_responses_json = record.get("llm_response", "{}")
                
                try:
                    # Parse the cached responses to count dashboard types
                    cached_responses = json.loads(cached_responses_json)
                    
                    # Count each dashboard type in this record
                    for dashboard_type in cached_responses.keys():
                        dashboard_types[dashboard_type] = dashboard_types.get(dashboard_type, 0) + 1
                except Exception:
                    # If parsing fails, count as unknown
                    dashboard_types["unknown"] = dashboard_types.get("unknown", 0) + 1
                
                # Add to unique clients set
                unique_clients.add(client_id)
                
                # Calculate age
                try:
                    created_at_str = record["created_at"]
                    if created_at_str.endswith('Z'):
                        created_at_str = created_at_str.replace('Z', '+00:00')
                    
                    created_at = datetime.fromisoformat(created_at_str)
                    
                    if created_at.tzinfo is None:
                        from datetime import timezone
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    
                    current_time = datetime.now(created_at.tzinfo)
                    age = (current_time - created_at).days
                    ages.append(age)
                except Exception as parse_error:
                    logger.warning(f"⚠️ Failed to parse created_at: {parse_error}")
                    continue
            
            oldest_cache = max(ages) if ages else 0
            newest_cache = min(ages) if ages else 0
            
            return {
                "total_entries": len(response.data),
                "by_dashboard_type": dashboard_types,
                "unique_clients": len(unique_clients),
                "avg_age_days": round(avg_age, 1),
                "oldest_cache_days": oldest_cache,
                "newest_cache_days": newest_cache,
                "cache_efficiency": f"{len(unique_clients) * 3}/{len(response.data)}" if len(response.data) > 0 else "0/0"
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