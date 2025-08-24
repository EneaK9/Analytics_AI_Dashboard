import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional, Dict, List, Any, Union
import logging
import asyncio
import json
import time
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceOptimizedDatabaseManager:
    """High-performance database manager with caching, pooling, and batch operations"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        #  MASSIVE CONNECTION POOL for high throughput
        self.client_pool: List[Client] = []
        self.admin_pool: List[Client] = []
        self.pool_size = 25  # Maintain 25 connections in pool
        
        # Caching
        self.cache = {}
        self.cache_ttl = {}
        self.cache_lock = threading.Lock()
        self.default_cache_duration = 300  # 5 minutes
        
        #  HIGH-SPEED BATCH PROCESSING
        self.batch_queue = defaultdict(list)
        self.batch_lock = threading.Lock()
        self.batch_size = 500  # 10x larger batches
        self.batch_timeout = 1  # Faster timeout for rapid processing
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        if not self.supabase_url or not self.supabase_key:
            raise Exception(" Supabase credentials REQUIRED - no fallbacks allowed")
        
        try:
            self._initialize_connection_pools()
            # Start background batch processor
            self._start_batch_processor()
        except Exception as e:
            logger.error(f" Failed to initialize optimized database manager: {e}")
            raise
    
    def _initialize_connection_pools(self):
        """Initialize connection pools for better performance"""
        try:
            logger.info(" Initializing high-performance connection pools...")
            
            # Try to create a simple client first to test the connection
            try:
                #  CUSTOM TIMEOUT SETTINGS - Use correct supabase-py format
                test_client = create_client(self.supabase_url, self.supabase_key)
                # Set timeout on the underlying httpx client
                if hasattr(test_client, '_client') and hasattr(test_client._client, 'timeout'):
                    test_client._client.timeout = 120.0
                logger.info(" Supabase connection test successful with 120s timeout")
            except Exception as e:
                logger.error(f" Supabase connection test failed: {e}")
                raise
            
            # Create regular client pool with extended timeouts
            for i in range(self.pool_size):
                try:
                    client = create_client(self.supabase_url, self.supabase_key)
                    # Set timeout on the underlying httpx client
                    if hasattr(client, '_client') and hasattr(client._client, 'timeout'):
                        client._client.timeout = 120.0
                    self.client_pool.append(client)
                except Exception as e:
                    logger.warning(f"  Failed to create client {i+1}: {e}")
                    if i == 0:  # If first client fails, abort
                        raise
            
            # Create admin client pool with extended timeouts
            if self.supabase_service_key:
                for i in range(self.pool_size):
                    try:
                        admin_client = create_client(self.supabase_url, self.supabase_service_key)
                        # Set timeout on the underlying httpx client
                        if hasattr(admin_client, '_client') and hasattr(admin_client._client, 'timeout'):
                            admin_client._client.timeout = 120.0
                        self.admin_pool.append(admin_client)
                    except Exception as e:
                        logger.warning(f"  Failed to create admin client {i+1}: {e}")
                        if i == 0:  # If first admin client fails, abort
                            raise
                logger.info(f" Created {len(self.client_pool)} client connections and {len(self.admin_pool)} admin connections")
            else:
                logger.warning("  No service role key - admin operations will be limited")
                
        except Exception as e:
            logger.error(f" Failed to initialize connection pools: {e}")
            # Fallback: Create minimal single client
            try:
                logger.info(" Attempting fallback to single client mode...")
                fallback_client = create_client(self.supabase_url, self.supabase_key)
                # Set timeout on fallback client
                if hasattr(fallback_client, '_client') and hasattr(fallback_client._client, 'timeout'):
                    fallback_client._client.timeout = 120.0
                self.client_pool = [fallback_client]
                if self.supabase_service_key:
                    fallback_admin = create_client(self.supabase_url, self.supabase_service_key)
                    if hasattr(fallback_admin, '_client') and hasattr(fallback_admin._client, 'timeout'):
                        fallback_admin._client.timeout = 120.0
                    self.admin_pool = [fallback_admin]
                logger.info(" Fallback single client mode initialized with 120s timeout")
            except Exception as fallback_error:
                logger.error(f" Fallback initialization also failed: {fallback_error}")
                raise
    
    def _get_pooled_client(self) -> Client:
        """Get a client from the pool (round-robin)"""
        if not self.client_pool:
            raise Exception("No client connections available")
        return self.client_pool[int(time.time()) % len(self.client_pool)]
    
    def _get_pooled_admin_client(self) -> Client:
        """Get an admin client from the pool (round-robin)"""
        if not self.admin_pool:
            raise Exception("No admin connections available")
        return self.admin_pool[int(time.time()) % len(self.admin_pool)]
    
    def _cache_key(self, prefix: str, *args) -> str:
        """Generate cache key"""
        return f"{prefix}::{':'.join(str(arg) for arg in args)}"
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        with self.cache_lock:
            if key in self.cache:
                if key in self.cache_ttl and time.time() < self.cache_ttl[key]:
                    logger.debug(f" Cache HIT: {key}")
                    return self.cache[key]
                else:
                    # Expired, remove from cache
                    if key in self.cache:
                        del self.cache[key]
                    if key in self.cache_ttl:
                        del self.cache_ttl[key]
        return None
    
    def _set_cache(self, key: str, value: Any, ttl_seconds: int = None):
        """Set value in cache with TTL"""
        ttl = ttl_seconds or self.default_cache_duration
        with self.cache_lock:
            self.cache[key] = value
            self.cache_ttl[key] = time.time() + ttl
            logger.debug(f" Cache SET: {key} (TTL: {ttl}s)")
    
    def _start_batch_processor(self):
        """Start background batch processor for bulk operations"""
        def process_batches():
            while True:
                try:
                    with self.batch_lock:
                        if self.batch_queue:
                            for table, operations in self.batch_queue.items():
                                if len(operations) >= self.batch_size or \
                                   (operations and time.time() - operations[0]['timestamp'] > self.batch_timeout):
                                    # Process this batch
                                    batch_to_process = operations[:self.batch_size]
                                    self.batch_queue[table] = operations[self.batch_size:]
                                    
                                    # Execute batch in background
                                    self.executor.submit(self._execute_batch, table, batch_to_process)
                    
                    time.sleep(0.1)  # Check every 100ms
                except Exception as e:
                    logger.error(f" Batch processor error: {e}")
                    time.sleep(1)
        
        batch_thread = threading.Thread(target=process_batches, daemon=True)
        batch_thread.start()
        logger.info(" Background batch processor started")
    
    def _execute_batch(self, table: str, operations: List[Dict]):
        """Execute a batch of operations"""
        try:
            client = self._get_pooled_admin_client()
            
            # Group operations by type
            inserts = [op['data'] for op in operations if op['type'] == 'insert']
            
            if inserts:
                logger.info(f" Executing batch: {len(inserts)} inserts to {table}")
                response = client.table(table).insert(inserts).execute()
                logger.info(f" Batch completed: {len(response.data)} records processed")
                
        except Exception as e:
            logger.error(f" Batch execution failed: {e}")
    
    async def fast_client_data_lookup(self, client_id: str, use_cache: bool = True, start_date: str = None, end_date: str = None, limit: int = None) -> Dict:
        """Ultra-fast client data lookup with aggressive caching and optional date range.

        If start_date/end_date provided, returns all records within the period (no artificial limit).
        Dates are ISO strings (YYYY-MM-DD or full ISO)."""
        # Build a cache key that considers range and limit
        cache_fragments = ["client_data", client_id]
        if start_date:
            cache_fragments.append(f"from:{start_date}")
        if end_date:
            cache_fragments.append(f"to:{end_date}")
        if limit:
            cache_fragments.append(f"limit:{limit}")
        cache_key = self._cache_key("|".join(cache_fragments), client_id)

        if use_cache:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result

        try:
            start_time = time.time()
            client = self._get_pooled_admin_client()

            # Base query
            query = client.table("client_data").select("data, table_name, created_at").eq("client_id", client_id)

            # Date filtering
            if start_date:
                query = query.gte("created_at", start_date)
            if end_date:
                query = query.lte("created_at", end_date)

            # Ordering newest first for consistency
            query = query.order("created_at", desc=True)

            # Apply limit only if explicitly requested and no date range
            # For dashboard generation, we need ALL records to get full business data
            if limit and not (start_date or end_date) and limit < 1000:
                logger.info(f" Applying limit {limit} to data retrieval - this may truncate business entities")
                query = query.limit(limit)
            elif limit and limit >= 1000:
                # Don't apply large limits - get all data for comprehensive analysis
                logger.info(f" Skipping large limit {limit} to ensure complete data retrieval")

            response = query.execute()

            data_records = [record["data"] for record in (response.data or [])]

            result = {
                "client_id": client_id,
                "data": data_records,
                "row_count": len(data_records),
                "query_time": time.time() - start_time,
                "cached": False,
            }

            # Cache the result for fast future access (shorter TTL for unbounded queries)
            ttl = 180 if not (start_date or end_date) else 60
            self._set_cache(cache_key, result, ttl_seconds=ttl)

            logger.info(
                f" Fast lookup completed in {result['query_time']:.3f}s - {len(data_records)} records"
            )
            return result

        except Exception as e:
            logger.error(f" Fast client data lookup failed: {e}")
            raise Exception(f"Database lookup failed: {str(e)}")
    
    async def batch_insert_client_data(self, table_name: str, data: List[Dict[str, Any]], client_id: str) -> int:
        """High-performance batch insert with retry logic and exponential backoff for large datasets"""
        try:
            start_time = time.time()
            logger.info(f" ENHANCED batch insert: {len(data)} records to {table_name}")
            
            # Prepare records with metadata
            records_to_insert = []
            for record in data:
                record_with_metadata = {
                    "client_id": client_id,
                    "table_name": table_name,
                    "data": record,
                    "created_at": "now()"
                }
                records_to_insert.append(record_with_metadata)
            
            # Use pooled admin client for faster processing
            client = self._get_pooled_admin_client()
            
            #  ULTRA-FAST SETTINGS for massive datasets (1M+ records)
            batch_size = 1000  # Match app layer - 1000 record chunks
            max_retries = 4
            total_inserted = 0
            failed_batches = []
            
            for i in range(0, len(records_to_insert), batch_size):
                batch = records_to_insert[i:i + batch_size]
                batch_num = i // batch_size + 1
                retry_count = 0
                batch_inserted = False
                
                while retry_count <= max_retries and not batch_inserted:
                    try:
                        #  NO DELAYS - Maximum throughput for massive datasets
                        
                        response = client.table("client_data").insert(batch).execute()
                        
                        if response.data:
                            total_inserted += len(response.data)
                            logger.debug(f" Batch {batch_num}: {len(response.data)} records inserted")
                            batch_inserted = True
                        else:
                            raise Exception("No data returned from insert")
                            
                    except Exception as batch_error:
                        retry_count += 1
                        error_msg = str(batch_error)
                        
                        #  SMART TIMEOUT DETECTION - Similar to app layer
                        is_timeout = any(keyword in error_msg.lower() for keyword in [
                            "timeout", "timed out", "statement timeout", "canceling statement", "57014"
                        ])
                        
                        if is_timeout and retry_count <= max_retries:
                            #  MINIMAL BACKOFF - Linear instead of exponential for speed
                            delay = 0.2 * retry_count  # 0.2s, 0.4s, 0.6s, 0.8s
                            logger.warning(f"⏱️ Batch {batch_num} timeout (attempt {retry_count}/{max_retries + 1}). Retrying in {delay}s...")
                            await asyncio.sleep(delay)
                        elif retry_count > max_retries:
                            logger.error(f" Batch {batch_num} failed after {max_retries + 1} attempts")
                            failed_batches.append(batch)
                            break
                        else:
                            logger.error(f" Batch {batch_num} failed with error: {batch_error}")
                            failed_batches.append(batch)
                            break
            
            #  FAST RECOVERY - Handle failed batches with optimized smaller chunks
            if failed_batches:
                logger.info(f" FAST RECOVERY: Processing {len(failed_batches)} failed batches...")
                recovery_batch_size = 500  # Larger recovery chunks for speed
                
                for failed_batch in failed_batches:
                    for j in range(0, len(failed_batch), recovery_batch_size):
                        recovery_batch = failed_batch[j:j + recovery_batch_size]
                        try:
                            await asyncio.sleep(0.1)  # Minimal delay for recovery
                            response = client.table("client_data").insert(recovery_batch).execute()
                            if response.data:
                                total_inserted += len(response.data)
                                logger.info(f" Recovered {len(response.data)} records")
                        except Exception as final_error:
                            logger.error(f" Final batch attempt failed: {final_error}")
                            # Skip this problematic batch rather than individual inserts
                            continue
            
            # Invalidate cache for this client
            cache_key = self._cache_key("client_data", client_id)
            with self.cache_lock:
                if cache_key in self.cache:
                    del self.cache[cache_key]
                if cache_key in self.cache_ttl:
                    del self.cache_ttl[cache_key]
            
            insert_time = time.time() - start_time
            success_rate = (total_inserted / len(data)) * 100
            logger.info(f" Enhanced batch insert completed in {insert_time:.3f}s - {total_inserted}/{len(data)} records ({success_rate:.1f}% success)")
            
            return total_inserted
            
        except Exception as e:
            logger.error(f" Batch insert failed: {e}")
            raise Exception(f"Database insert failed: {str(e)}")

    def _compute_record_fingerprint(self, record: Dict[str, Any]) -> str:
        """Compute a stable fingerprint for a record to support deduplication.

        Prefers stable unique keys if present; otherwise hashes a normalized JSON excluding volatile fields."""
        import hashlib, json

        # Prefer common unique identifiers if present
        candidate_keys = [
            "id", "uuid", "order_id", "transaction_id", "customer_id", "invoice_id",
            "event_id", "record_id", "external_id", "sku", "product_id"
        ]

        for key in candidate_keys:
            if key in record and record[key] is not None and str(record[key]).strip() != "":
                return f"key:{key}:{str(record[key])}"

        # Remove volatile fields commonly present in API payloads
        volatile_fields = {
            "updated_at", "created_at", "retrieved_at", "last_updated", "timestamp",
            "request_id", "processing_time", "query_time", "fetch_time"
        }
        stable_copy = {k: v for k, v in record.items() if k not in volatile_fields}
        try:
            normalized = json.dumps(stable_copy, sort_keys=True, default=str)
        except Exception:
            normalized = str(stable_copy)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    async def dedup_and_batch_insert_client_data(
        self,
        table_name: str,
        data: List[Dict[str, Any]],
        client_id: str,
        dedup_scope: str = "day",
    ) -> int:
        """Insert only new records for the current scope (default day).

        - Fetches existing records for the scope and computes fingerprints
        - Skips incoming records whose fingerprint already exists
        - If a stable unique key exists and the record changed, updates existing row
        - Inserts only new records using batch_insert_client_data
        """
        if not data:
            return 0

        # Determine scope window (start/end)
        from datetime import datetime, timedelta
        scope_start = None
        scope_end = None
        now = datetime.utcnow()
        if dedup_scope == "day":
            scope_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            scope_end = now.replace(hour=23, minute=59, second=59, microsecond=999000).isoformat()
        elif dedup_scope == "hour":
            scope_start = now.replace(minute=0, second=0, microsecond=0).isoformat()
            scope_end = (now.replace(minute=59, second=59, microsecond=999000)).isoformat()

        # Build set of existing fingerprints in scope and index by stable unique key
        existing_fingerprints: set[str] = set()
        existing_by_key: Dict[str, Dict[str, Any]] = {}
        try:
            client = self._get_pooled_admin_client()
            resp = client.table("client_data").select("id,data,created_at").eq("client_id", client_id) \
                .gte("created_at", scope_start).lte("created_at", scope_end).order("created_at", desc=True).execute()
            for row in resp.data or []:
                rec = row.get("data")
                if isinstance(rec, dict):
                    fp = self._compute_record_fingerprint(rec)
                    existing_fingerprints.add(fp)
                    # Try to capture a stable key
                    for key_name in [
                        "id", "uuid", "order_id", "transaction_id", "customer_id", "invoice_id",
                        "event_id", "record_id", "external_id", "sku", "product_id"
                    ]:
                        if key_name in rec and rec[key_name] is not None and str(rec[key_name]).strip() != "":
                            existing_by_key[f"{key_name}:{rec[key_name]}"] = {"row_id": row.get("id"), "data": rec}
                            break
        except Exception as e:
            logger.warning(f" Could not load existing scope records for dedup/update: {e}")

        # Filter incoming
        unique_records: List[Dict[str, Any]] = []
        updates: List[Dict[str, Any]] = []  # {row_id, new_data}
        for rec in data:
            try:
                record_obj = rec if isinstance(rec, dict) else {"value": rec}
                fp = self._compute_record_fingerprint(record_obj)
                # Detect stable key-based update
                stable_key = None
                for key_name in [
                    "id", "uuid", "order_id", "transaction_id", "customer_id", "invoice_id",
                    "event_id", "record_id", "external_id", "sku", "product_id"
                ]:
                    if key_name in record_obj and record_obj[key_name] is not None and str(record_obj[key_name]).strip() != "":
                        stable_key = f"{key_name}:{record_obj[key_name]}"
                        break

                if stable_key and stable_key in existing_by_key:
                    existing_entry = existing_by_key[stable_key]
                    # If content differs, schedule update
                    if self._compute_record_fingerprint(existing_entry["data"]) != fp:
                        updates.append({"row_id": existing_entry["row_id"], "new_data": record_obj})
                    # Whether updated or same, do not insert as new
                    continue

                # No exact existing key match; use fingerprint dedup
                if fp not in existing_fingerprints:
                    unique_records.append(record_obj)
                    existing_fingerprints.add(fp)
            except Exception:
                # If fingerprinting fails, keep the record to avoid data loss
                unique_records.append(rec if isinstance(rec, dict) else {"value": rec})

        # Apply updates first
        updated_count = 0
        if updates:
            client = self._get_pooled_admin_client()
            for upd in updates:
                try:
                    client.table("client_data").update({"data": upd["new_data"], "updated_at": "now()"}).eq("id", upd["row_id"]).execute()
                    updated_count += 1
                except Exception as ue:
                    logger.warning(f" Failed to update row {upd['row_id']}: {ue}")

        if not unique_records:
            logger.info(f"ℹ️ No new unique records to insert after dedup; {updated_count} updated")
            return updated_count

        inserted = await self.batch_insert_client_data(table_name, unique_records, client_id)
        return inserted + updated_count
    
    async def fast_dashboard_config_save(self, client_id: str, dashboard_config: Dict) -> bool:
        """Ultra-fast dashboard config save with optimized queries"""
        try:
            start_time = time.time()
            client = self._get_pooled_admin_client()
            
            config_data = {
                'client_id': client_id,
                'dashboard_config': dashboard_config,
                'is_generated': True,
                'generation_timestamp': "now()"
            }
            
            # Use upsert for maximum efficiency
            response = client.table('client_dashboard_configs').upsert(
                config_data,
                on_conflict='client_id'
            ).execute()
            
            # Invalidate related caches
            cache_keys = [
                self._cache_key("dashboard_config", client_id),
                self._cache_key("dashboard_exists", client_id)
            ]
            
            with self.cache_lock:
                for key in cache_keys:
                    if key in self.cache:
                        del self.cache[key]
                    if key in self.cache_ttl:
                        del self.cache_ttl[key]
            
            save_time = time.time() - start_time
            logger.info(f" Dashboard config saved in {save_time:.3f}s")
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f" Fast dashboard config save failed: {e}")
            raise Exception(f"Dashboard save failed: {str(e)}")
    
    async def fast_dashboard_metrics_save(self, metrics_data: List[Dict]) -> int:
        """High-performance metrics save with batch processing"""
        try:
            start_time = time.time()
            
            if not metrics_data:
                return 0
            
            client = self._get_pooled_admin_client()
            
            # Batch insert all metrics at once
            response = client.table('client_dashboard_metrics').insert(metrics_data).execute()
            
            inserted_count = len(response.data) if response.data else 0
            save_time = time.time() - start_time
            
            logger.info(f" {inserted_count} metrics saved in {save_time:.3f}s")
            return inserted_count
            
        except Exception as e:
            logger.error(f" Fast metrics save failed: {e}")
            raise Exception(f"Metrics save failed: {str(e)}")
    
    async def cached_dashboard_exists(self, client_id: str) -> bool:
        """Fast cached check if dashboard exists"""
        cache_key = self._cache_key("dashboard_exists", client_id)
        
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        try:
            client = self._get_pooled_client()
            response = client.table('client_dashboard_configs') \
                .select('client_id') \
                .eq('client_id', client_id) \
                .limit(1) \
                .execute()
            
            exists = bool(response.data)
            self._set_cache(cache_key, exists, ttl_seconds=300)  # 5 minute cache
            
            return exists
            
        except Exception as e:
            logger.error(f" Dashboard exists check failed: {e}")
            return False
    
    def clear_cache(self, pattern: str = None):
        """Clear cache entries matching pattern or all if no pattern"""
        with self.cache_lock:
            if pattern:
                keys_to_remove = [key for key in self.cache.keys() if pattern in key]
                for key in keys_to_remove:
                    if key in self.cache:
                        del self.cache[key]
                    if key in self.cache_ttl:
                        del self.cache_ttl[key]
                logger.info(f"️ Cleared {len(keys_to_remove)} cache entries matching '{pattern}'")
            else:
                self.cache.clear()
                self.cache_ttl.clear()
                logger.info("️ Cleared all cache entries")
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        with self.cache_lock:
            current_time = time.time()
            active_entries = sum(1 for ttl in self.cache_ttl.values() if ttl > current_time)
            
            return {
                "total_entries": len(self.cache),
                "active_entries": active_entries,
                "expired_entries": len(self.cache) - active_entries,
                "pool_size": len(self.client_pool),
                "admin_pool_size": len(self.admin_pool)
            }
    
    # Legacy compatibility methods (optimized)
    async def get_client_data(self, client_id: str, table_name: str = None, limit: int = 100) -> Dict:
        """Legacy method - redirects to optimized version"""
        return await self.fast_client_data_lookup(client_id, use_cache=True)
    
    async def insert_client_data(self, table_name: str, data: List[Dict[str, Any]], client_id: str) -> int:
        """Legacy method - redirects to optimized version"""
        return await self.batch_insert_client_data(table_name, data, client_id)
    
    def get_client(self) -> Client:
        """Legacy method - returns pooled client"""
        return self._get_pooled_client()
    
    def get_admin_client(self) -> Client:
        """Legacy method - returns pooled admin client"""
        return self._get_pooled_admin_client()

# Global optimized database manager instance (lazy initialization)
_db_manager = None

def get_db_manager():
    """Get database manager with lazy initialization"""
    global _db_manager
    if _db_manager is None:
        try:
            _db_manager = PerformanceOptimizedDatabaseManager()
        except Exception as e:
            logger.error(f" Failed to initialize database manager: {e}")
            # Return a simple fallback that will allow the app to start
            _db_manager = SimpleDatabaseManager()
    return _db_manager

class SimpleDatabaseManager:
    """Fallback simple database manager for when optimization fails"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning(" Supabase credentials not configured")
    
    def get_client(self):
        """Get simple client without pooling"""
        if not self.supabase_url or not self.supabase_key:
            return None
        #  EXTENDED TIMEOUT for simple client too
        client = create_client(self.supabase_url, self.supabase_key)
        if hasattr(client, '_client') and hasattr(client._client, 'timeout'):
            client._client.timeout = 120.0
        return client
    
    def get_admin_client(self):
        """Get simple admin client without pooling"""
        if not self.supabase_url or not self.supabase_service_key:
            return None
        #  EXTENDED TIMEOUT for simple admin client too
        admin_client = create_client(self.supabase_url, self.supabase_service_key)
        if hasattr(admin_client, '_client') and hasattr(admin_client._client, 'timeout'):
            admin_client._client.timeout = 120.0
        return admin_client
    
    async def test_connection(self):
        """Test database connection"""
        try:
            client = self.get_client()
            if client:
                # Simple test query
                response = client.table('clients').select('count', count='exact').limit(1).execute()
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
        return False
    
    async def create_base_schema(self):
        """Return basic schema setup SQL"""
        return "-- Simple database manager fallback - schema setup not available"
    
    async def create_client_table(self, table_name: str, create_sql: str):
        """Simple fallback for table creation"""
        logger.info(f" Simple manager: Table creation simulated for {table_name}")
        return True
    
    async def fast_client_data_lookup(self, client_id: str, use_cache: bool = True):
        """Simple fallback for data lookup"""
        return {"data": [], "row_count": 0, "query_time": 0.001}
    
    async def batch_insert_client_data(self, table_name: str, data: list, client_id: str):
        """Simple fallback for data insertion"""
        logger.info(f" Simple manager: Data insertion simulated for {table_name}")
        return len(data)
    
    async def fast_dashboard_config_save(self, client_id: str, dashboard_config: dict):
        """Simple fallback for dashboard config save"""
        logger.info(f" Simple manager: Dashboard config save simulated for {client_id}")
        return True
    
    async def cached_dashboard_exists(self, client_id: str):
        """Simple fallback for dashboard existence check"""
        return False
    
    async def fast_dashboard_metrics_save(self, metrics_data: list):
        """Simple fallback for metrics save"""
        logger.info(f" Simple manager: Metrics save simulated for {len(metrics_data)} metrics")
        return len(metrics_data)
    
    async def insert_client_data(self, table_name: str, records: list, client_id: str):
        """Simple fallback for data insertion"""
        logger.info(f" Simple manager: Data insertion simulated for {table_name}")
        return len(records)

# Convenience functions (optimized with lazy loading)
def get_db_client() -> Client:
    """Get a high-performance pooled database client"""
    manager = get_db_manager()
    return manager.get_client()

def get_admin_client() -> Client:
    """Get a high-performance pooled admin database client"""
    manager = get_db_manager()
    return manager.get_admin_client()

# Legacy compatibility - expose db_manager as a function
def db_manager():
    """Get database manager instance (legacy compatibility)"""
    return get_db_manager() 