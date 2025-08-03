#!/usr/bin/env python3
"""
LLM Cache Manager - Efficient caching for LLM responses
Stores responses in database and only regenerates when client data changes
"""

import hashlib
import json
import logging
import asyncio
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
        Get cached LLM response if data hasn't changed (updated for time-based storage)
        
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
            
            # NEW: Get most recent cache entry for this client and dashboard type
            response = self.db_client.table("llm_response_cache").select("*").eq("client_id", client_id).eq("data_type", dashboard_type).order("created_at", desc=True).limit(1).execute()
            
            if response.data:
                cached_record = response.data[0]
                cached_hash = cached_record.get("data_hash")
                cached_llm_response = cached_record.get("llm_response")
                created_at = cached_record.get("created_at")
                
                # Check if data hash matches (data hasn't changed)
                logger.info(f"🔍 Hash comparison for client {client_id} ({dashboard_type}): cached={cached_hash[:12] if cached_hash else 'None'}... vs current={current_hash[:12]}...")
                
                if cached_hash == current_hash and cached_llm_response:
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
                            # Return the LLM analysis from the cached response
                            if isinstance(cached_llm_response, dict):
                                return cached_llm_response.get("llm_analysis", cached_llm_response)
                            elif isinstance(cached_llm_response, str):
                                try:
                                    parsed_response = json.loads(cached_llm_response)
                                    return parsed_response.get("llm_analysis", parsed_response)
                                except:
                                    return None
                        else:
                            logger.info(f"⚠️ Cache expired for client {client_id} ({dashboard_type}) (age: {cache_age.days} days)")
                            return None
                    except Exception as time_error:
                        logger.warning(f"⚠️ Failed to parse cache timestamp for client {client_id} ({dashboard_type}): {time_error}")
                        # If we can't parse the timestamp, assume cache is valid
                        if isinstance(cached_llm_response, dict):
                            return cached_llm_response.get("llm_analysis", cached_llm_response)
                        return None
                else:
                    logger.info(f"🔄 Cache MISS for client {client_id} ({dashboard_type}) - data changed (hash mismatch)")
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
        Store LLM response in cache with time-based versioning
        ALWAYS creates new entries for proper historical tracking
        
        Args:
            client_id: Client identifier
            client_data: Client data used for analysis
            llm_response: LLM analysis response
            dashboard_type: Type of dashboard (metrics, business, performance)
            data_snapshot_date: When this data snapshot was current
        
        Returns:
            - True if stored successfully
            - False if storage failed
        """
        try:
            # Calculate data hash
            data_hash = self._calculate_data_hash(client_data)
            
            # ALWAYS insert new record for time-based tracking (no more updates)
            # Store the response in the exact format specified by user
            cache_record = {
                "client_id": client_id,
                "data_hash": data_hash,
                "llm_response": {
                    "client_id": client_id,
                    "data_type": dashboard_type,
                    "schema_type": "dashboard_analysis",
                    "total_records": client_data.get("total_records", len(client_data.get("data", []))),
                    "llm_analysis": llm_response,
                    "cached": True,
                    "fast_mode": True
                },
                "data_type": dashboard_type,  # Store dashboard type for filtering
                "total_records": client_data.get("total_records", len(client_data.get("data", []))),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.db_client.table("llm_response_cache").insert(cache_record).execute()
            
            if response.data:
                logger.info(f"✅ Cached LLM response for client {client_id} ({dashboard_type}) (hash: {data_hash[:8]}...) at {cache_record['created_at']}")
                return True
            else:
                logger.error(f"❌ Failed to cache LLM response for client {client_id} ({dashboard_type})")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error storing cache for client {client_id} ({dashboard_type}): {e}")
            return False
    
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
    
    async def intelligent_cache_cleanup(self, client_id: str, preserve_policy: str = "balanced") -> Dict[str, int]:
        """
        Intelligent cache cleanup that preserves important historical data
        
        Args:
            client_id: Client identifier
            preserve_policy: Cleanup policy - "aggressive", "balanced", or "conservative"
        
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            stats = {
                "total_entries_before": 0,
                "total_entries_after": 0,
                "deleted_count": 0,
                "preserved_count": 0,
                "preserved_reasons": []
            }
            
            # Get all cache entries for this client, ordered by date
            response = self.db_client.table("llm_response_cache").select("*").eq("client_id", client_id).order("created_at", desc=True).execute()
            
            if not response.data:
                logger.info(f"🧹 No cache entries found for client {client_id}")
                return stats
            
            stats["total_entries_before"] = len(response.data)
            
            # Define preservation rules based on policy
            if preserve_policy == "aggressive":
                # Keep only last 5 entries, one per week for last month
                keep_recent = 5
                keep_weekly_days = 30
            elif preserve_policy == "conservative":
                # Keep last 20 entries, one per day for last 2 months  
                keep_recent = 20
                keep_weekly_days = 60
            else:  # balanced
                # Keep last 10 entries, one per week for last 6 weeks
                keep_recent = 10
                keep_weekly_days = 42
            
            entries_to_preserve = []
            entries_to_delete = []
            
            # Always preserve the most recent entries
            entries_to_preserve.extend(response.data[:keep_recent])
            stats["preserved_reasons"].append(f"Recent entries: {min(keep_recent, len(response.data))}")
            
            # For older entries, keep one per week within the specified period
            from datetime import timezone
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=keep_weekly_days)
            weekly_preserved = {}
            
            for entry in response.data[keep_recent:]:
                try:
                    created_at_str = entry.get("created_at", "")
                    if created_at_str.endswith('Z'):
                        created_at_str = created_at_str.replace('Z', '+00:00')
                    
                    entry_date = datetime.fromisoformat(created_at_str)
                    if entry_date.tzinfo is None:
                        entry_date = entry_date.replace(tzinfo=timezone.utc)
                    
                    # If entry is within preservation window
                    if entry_date >= cutoff_date:
                        # Get week identifier (year-week)
                        week_key = entry_date.strftime("%Y-W%U")
                        
                        # Preserve one entry per week (the most recent in that week)
                        if week_key not in weekly_preserved:
                            weekly_preserved[week_key] = entry
                            entries_to_preserve.append(entry)
                    else:
                        # Entry is too old, mark for deletion
                        entries_to_delete.append(entry)
                        
                except Exception as date_error:
                    logger.warning(f"⚠️ Could not parse date for cache entry: {date_error}")
                    # If we can't parse the date, preserve it to be safe
                    entries_to_preserve.append(entry)
            
            stats["preserved_reasons"].append(f"Weekly samples: {len(weekly_preserved)}")
            
            # Special preservation rules
            special_preserved = 0
            
            # Preserve entries with unique data hashes (significant data changes)
            seen_hashes = set()
            for entry in response.data:
                data_hash = entry.get("data_hash", "")
                if data_hash and data_hash not in seen_hashes:
                    seen_hashes.add(data_hash)
                    if entry not in entries_to_preserve:
                        entries_to_preserve.append(entry)
                        special_preserved += 1
            
            if special_preserved > 0:
                stats["preserved_reasons"].append(f"Unique data states: {special_preserved}")
            
            # Remove duplicates from preserve list
            preserve_ids = {entry.get("id") for entry in entries_to_preserve}
            final_delete_list = [entry for entry in response.data if entry.get("id") not in preserve_ids]
            
            # Perform deletions
            deleted_count = 0
            for entry in final_delete_list:
                try:
                    delete_response = self.db_client.table("llm_response_cache").delete().eq("id", entry.get("id")).execute()
                    if delete_response:
                        deleted_count += 1
                except Exception as delete_error:
                    logger.warning(f"⚠️ Failed to delete cache entry {entry.get('id')}: {delete_error}")
            
            stats["deleted_count"] = deleted_count
            stats["preserved_count"] = len(entries_to_preserve)
            stats["total_entries_after"] = stats["total_entries_before"] - deleted_count
            
            logger.info(f"🧹 Intelligent cleanup for client {client_id} ({preserve_policy}): {deleted_count} deleted, {len(entries_to_preserve)} preserved")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error in intelligent cache cleanup: {e}")
            return stats
    
    async def auto_cleanup_all_clients(self, preserve_policy: str = "balanced") -> Dict[str, Any]:
        """
        Perform intelligent cleanup for all clients with cache entries
        
        Args:
            preserve_policy: Cleanup policy for all clients
        
        Returns:
            Overall cleanup statistics
        """
        try:
            # Get all unique client IDs with cache entries
            response = self.db_client.table("llm_response_cache").select("client_id").execute()
            
            if not response.data:
                logger.info("🧹 No cache entries found for any client")
                return {"message": "No cache entries to clean up"}
            
            unique_clients = list(set(entry["client_id"] for entry in response.data))
            
            overall_stats = {
                "clients_processed": 0,
                "total_deleted": 0,
                "total_preserved": 0,
                "clients_stats": {}
            }
            
            for client_id in unique_clients:
                try:
                    client_stats = await self.intelligent_cache_cleanup(client_id, preserve_policy)
                    overall_stats["clients_processed"] += 1
                    overall_stats["total_deleted"] += client_stats["deleted_count"]
                    overall_stats["total_preserved"] += client_stats["preserved_count"]
                    overall_stats["clients_stats"][client_id] = client_stats
                    
                    # Small delay to prevent database overload
                    await asyncio.sleep(0.1)
                    
                except Exception as client_error:
                    logger.error(f"❌ Failed to cleanup cache for client {client_id}: {client_error}")
                    continue
            
            logger.info(f"🧹 Auto-cleanup completed: {overall_stats['clients_processed']} clients, {overall_stats['total_deleted']} entries deleted")
            return overall_stats
            
        except Exception as e:
            logger.error(f"❌ Error in auto cleanup for all clients: {e}")
            return {"error": str(e)}
    
    async def get_cached_responses_by_date_range(self, client_id: str, start_date: str, end_date: str, dashboard_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get cached responses within a specific date range for calendar filtering
        
        Args:
            client_id: Client identifier
            start_date: Start date in ISO format (e.g., "2024-01-01")
            end_date: End date in ISO format (e.g., "2024-01-31")
            dashboard_type: Optional filter by dashboard type
        
        Returns:
            List of cached responses with metadata
        """
        try:
            # Convert dates to ISO format for comparison
            start_dt = datetime.fromisoformat(start_date).isoformat()
            end_dt = datetime.fromisoformat(end_date).isoformat()
            
            # Query cache entries within date range
            query = self.db_client.table("llm_response_cache").select("*").eq("client_id", client_id)
            
            # Add date range filter
            query = query.gte("created_at", start_dt).lte("created_at", end_dt)
            
            # Add dashboard type filter if specified
            if dashboard_type:
                query = query.eq("data_type", dashboard_type)
            
            # Order by creation date (newest first)
            response = query.order("created_at", desc=True).execute()
            
            results = []
            for entry in response.data:
                llm_response = entry.get("llm_response")
                if llm_response:
                    # Parse the response if it's stored as JSON string
                    if isinstance(llm_response, str):
                        try:
                            llm_response = json.loads(llm_response)
                        except Exception:
                            continue
                    
                    result_entry = {
                        "id": entry.get("id"),
                        "created_at": entry.get("created_at"),
                        "data_type": entry.get("data_type"),
                        "data_hash": entry.get("data_hash"),
                        "total_records": entry.get("total_records"),
                        "llm_response": llm_response
                    }
                    results.append(result_entry)
            
            logger.info(f"📅 Retrieved {len(results)} cached responses for client {client_id} between {start_date} and {end_date}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error retrieving cached responses by date range: {e}")
            return []
    
    async def get_cached_response_by_date(self, client_id: str, target_date: str, dashboard_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached response closest to a specific date for calendar selection
        
        Args:
            client_id: Client identifier
            target_date: Target date in ISO format (e.g., "2024-01-15")
            dashboard_type: Optional filter by dashboard type
        
        Returns:
            Closest cached response or None if not found
        """
        try:
            target_dt = datetime.fromisoformat(target_date).date()
            
            # Get all cache entries for this client
            query = self.db_client.table("llm_response_cache").select("*").eq("client_id", client_id)
            
            # Add dashboard type filter if specified
            if dashboard_type:
                query = query.eq("data_type", dashboard_type)
            
            response = query.order("created_at").execute()
            
            # Find the entry closest to the target date
            best_match = None
            best_diff = float('inf')
            
            for entry in response.data:
                created_at = entry.get('created_at')
                llm_response = entry.get('llm_response')
                
                if created_at and llm_response:
                    try:
                        # Parse the date (handle different formats)
                        if created_at.endswith('Z'):
                            entry_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                        elif '+' in created_at:
                            entry_date = datetime.fromisoformat(created_at).date()
                        else:
                            entry_date = datetime.fromisoformat(created_at + '+00:00').date()
                        
                        diff = abs((entry_date - target_dt).days)
                        
                        if diff < best_diff:
                            best_diff = diff
                            best_match = entry
                    except Exception as e:
                        logger.warning(f"Could not parse date {created_at}: {e}")
                        continue
            
            if best_match:
                llm_response = best_match.get('llm_response')
                if isinstance(llm_response, str):
                    try:
                        llm_response = json.loads(llm_response)
                    except Exception:
                        return None
                
                return {
                    "id": best_match.get("id"),
                    "created_at": best_match.get("created_at"),
                    "target_date": target_date,
                    "days_difference": best_diff,
                    "data_type": best_match.get("data_type"),
                    "data_hash": best_match.get("data_hash"),
                    "total_records": best_match.get("total_records"),
                    "llm_response": llm_response
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error retrieving cached response by date: {e}")
            return None
    
    async def get_available_cache_dates(self, client_id: str, dashboard_type: Optional[str] = None) -> List[str]:
        """
        Get list of available cache dates for calendar display
        
        Args:
            client_id: Client identifier
            dashboard_type: Optional filter by dashboard type
        
        Returns:
            List of dates (YYYY-MM-DD format) when cache entries exist
        """
        try:
            query = self.db_client.table("llm_response_cache").select("created_at, data_type").eq("client_id", client_id)
            
            # Add dashboard type filter if specified
            if dashboard_type:
                query = query.eq("data_type", dashboard_type)
            
            response = query.order("created_at", desc=True).execute()
            
            dates = []
            for entry in response.data:
                created_at = entry.get('created_at')
                if created_at:
                    try:
                        # Parse and extract date part
                        if created_at.endswith('Z'):
                            date_part = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                        elif '+' in created_at:
                            date_part = datetime.fromisoformat(created_at).date()
                        else:
                            date_part = datetime.fromisoformat(created_at + '+00:00').date()
                        
                        date_str = date_part.isoformat()
                        if date_str not in dates:
                            dates.append(date_str)
                    except Exception as e:
                        logger.warning(f"Could not parse date {created_at}: {e}")
                        continue
            
            logger.info(f"📅 Found {len(dates)} available cache dates for client {client_id}")
            return dates
            
        except Exception as e:
            logger.error(f"❌ Error retrieving available cache dates: {e}")
            return []

# Global instance
llm_cache_manager = LLMCacheManager() 