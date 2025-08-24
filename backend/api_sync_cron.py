#!/usr/bin/env python3
"""
API Sync Cron Job - PERFECT VERSION
Automatically syncs new data from Shopify and Amazon APIs every 24 hours
Checks client_api_credentials table and syncs based on next_sync_at timestamps
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Setup comprehensive logging with safe file handling
handlers = [logging.StreamHandler(sys.stdout)]

# Try to add file handler, but don't fail if logs directory doesn't exist
try:
    os.makedirs('logs', exist_ok=True)
    handlers.append(logging.FileHandler('logs/api_sync_cron.log', mode='a'))
except (OSError, PermissionError) as e:
    # Fall back to stdout-only logging in deployment environments
    print(f"Warning: Could not create log file, using stdout only: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)

class APISyncCronJob:
    """Perfect cron job that syncs new data from APIs every 24 hours"""
    
    def __init__(self):
        self.supported_platforms = ["shopify", "amazon", "woocommerce"]
        logger.info("API Sync Cron Job initialized - PERFECT VERSION")
    
    def map_api_data_to_table_columns(self, records: List[Dict], platform_type: str, data_type: str, client_id: str) -> List[Dict]:
        """Map API response data to actual table columns"""
        mapped_records = []
        
        for record in records:
            try:
                mapped_record = {
                    "client_id": client_id,
                    "platform": platform_type,
                    "processed_at": datetime.now().isoformat(),
                    "raw_data": json.dumps(record)  # Store original data
                }
                
                if platform_type == "shopify" and data_type == "orders":
                    # Map Shopify order fields to table columns (API already has correct field names)
                    order_id = record.get("order_id") or record.get("id")  # Try both fields
                    if not order_id:
                        continue  # Skip records without order ID
                        
                    mapped_record.update({
                        "order_id": str(order_id),
                        "order_number": str(record.get("order_number", "")),
                        "created_at": record.get("created_at"),
                        "updated_at": record.get("updated_at"),
                        "financial_status": record.get("financial_status"),
                        "fulfillment_status": record.get("fulfillment_status"),
                        "total_price": record.get("total_price"),
                        "subtotal_price": record.get("subtotal_price"),
                        "total_tax": record.get("total_tax"),
                        "currency": record.get("currency"),
                        "customer_email": record.get("customer_email"),  # API has customer_email directly
                        "customer_id": str(record.get("customer_id", "")),  # API has customer_id directly
                        "billing_address": json.dumps(record.get("billing_address", {})),
                        "shipping_address": json.dumps(record.get("shipping_address", {})),
                        "line_items_count": record.get("line_items_count", 0),  # API has this directly
                        "tags": record.get("tags", ""),
                        "source_name": record.get("source_name"),
                        "discount_codes": json.dumps(record.get("discount_codes", []))
                    })
                
                elif platform_type == "shopify" and data_type == "products":
                    # Map Shopify product fields to table columns (API already has correct field names)
                    for variant in record.get("variants", []):  # Process each variant as a separate record
                        product_id = record.get("product_id") or record.get("id")
                        variant_id = variant.get("variant_id") or variant.get("id")
                        
                        if not product_id or not variant_id:
                            continue  # Skip records without required IDs
                            
                        product_record = mapped_record.copy()
                        product_record.update({
                            "product_id": str(product_id),
                            "title": record.get("title"),
                            "handle": record.get("handle"),
                            "vendor": record.get("vendor"),
                            "tags": record.get("tags", ""),
                            "status": record.get("status"),
                            "variant_id": str(variant_id),
                            "variant_title": variant.get("title"),
                            "sku": variant.get("sku"),
                            "barcode": variant.get("barcode"),
                            "price": variant.get("price"),
                            "compare_at_price": variant.get("compare_at_price"),
                            "inventory_quantity": variant.get("inventory_quantity"),
                            "inventory_management": variant.get("inventory_management"),
                            "inventory_policy": variant.get("inventory_policy"),
                            "fulfillment_service": variant.get("fulfillment_service"),
                            "requires_shipping": variant.get("requires_shipping"),
                            "weight": variant.get("weight"),
                            "position": variant.get("position"),
                            "option1": variant.get("option1"),
                            "option2": variant.get("option2"),
                            "option3": variant.get("option3"),
                            "images": json.dumps([]),  # Images are at product level, keep empty for variants
                            "options": json.dumps([]),  # Options are at product level, keep empty for variants
                            "variants": json.dumps([])  # Don't duplicate variants array for each variant
                        })
                        mapped_records.append(product_record)
                    continue  # Skip the regular append since we handled variants individually
                
                elif platform_type == "amazon" and data_type == "orders":
                    # Map Amazon order fields to table columns  
                    mapped_record.update({
                        "order_id": str(record.get("AmazonOrderId")),
                        "order_number": str(record.get("SellerOrderId", record.get("AmazonOrderId", ""))),
                        "created_at": record.get("PurchaseDate"),
                        "updated_at": record.get("LastUpdateDate"),
                        "order_status": record.get("OrderStatus"),
                        "fulfillment_channel": record.get("FulfillmentChannel"),
                        "sales_channel": record.get("SalesChannel"),
                        "total_price": record.get("OrderTotal", {}).get("Amount"),
                        "currency": record.get("OrderTotal", {}).get("CurrencyCode"),
                        "number_of_items_shipped": record.get("NumberOfItemsShipped"),
                        "number_of_items_unshipped": record.get("NumberOfItemsUnshipped"),
                        "payment_method": record.get("PaymentMethod"),
                        "marketplace_id": record.get("MarketplaceId"),
                        "is_business_order": record.get("IsBusinessOrder"),
                        "is_premium_order": record.get("IsPremiumOrder")
                    })
                
                # Only add if we successfully mapped the record
                if mapped_record.get("order_id") or mapped_record.get("product_id"):
                    mapped_records.append(mapped_record)
                    
            except Exception as e:
                logger.warning(f"Failed to map record: {e}")
                continue
        
        logger.info(f"Mapped {len(mapped_records)} records from {len(records)} API records")
        return mapped_records
    
    async def insert_with_deduplication(self, table_name: str, mapped_records: List[Dict], platform_type: str, data_type: str) -> int:
        """Insert records with proper deduplication"""
        if not mapped_records:
            return 0
        
        db_client = self._get_admin_client()
        if not db_client:
            logger.error("Could not get database connection")
            return 0
        
        inserted_count = 0
        duplicate_count = 0
        
        # Determine deduplication key based on platform and data type
        dedup_key = self.get_dedup_key(platform_type, data_type)
        
        for record in mapped_records:
            try:
                # Check if record already exists
                existing = None
                dedup_value = record.get(dedup_key)
                
                # Skip records with invalid deduplication values
                if not dedup_key or not dedup_value or str(dedup_value).lower() in ['none', 'null', '']:
                    duplicate_count += 1
                    logger.debug(f"Skipping record with invalid {dedup_key}: {dedup_value}")
                    continue
                
                if dedup_key and dedup_value:
                    existing_response = db_client.table(table_name).select("id").eq(dedup_key, str(dedup_value)).execute()
                    existing = existing_response.data
                
                if existing:
                    duplicate_count += 1
                    logger.debug(f"Skipping duplicate record: {dedup_key}={record.get(dedup_key)}")
                else:
                    # Insert new record
                    response = db_client.table(table_name).insert(record).execute()
                    if response.data:
                        inserted_count += 1
                        
            except Exception as e:
                # Log error but continue with other records
                logger.debug(f"Failed to insert record: {e}")
                continue
        
        logger.info(f"Inserted {inserted_count} new records, skipped {duplicate_count} duplicates")
        return inserted_count
    
    def get_dedup_key(self, platform_type: str, data_type: str) -> str:
        """Get the deduplication key for a platform/data type combination"""
        if platform_type == "shopify":
            if data_type == "orders":
                return "order_id"
            elif data_type == "products":
                return "variant_id"
        elif platform_type == "amazon":
            if data_type == "orders":
                return "order_id"
            elif data_type == "products":
                return "product_id"
        
        return "order_id"  # Default fallback
    
    def _get_admin_client(self):
        """Get Supabase admin client"""
        try:
            from database import get_admin_client
            return get_admin_client()
        except Exception as e:
            logger.error(f"Failed to get admin client: {e}")
            return None
    
    async def get_clients_due_for_sync(self) -> List[Dict[str, Any]]:
        """Get all clients that are due for API sync"""
        try:
            db_client = self._get_admin_client()
            if not db_client:
                logger.error(" No database connection")
                return []
            
            current_time = datetime.now()
            current_time_iso = current_time.isoformat()
            
            logger.info(f"Checking for clients due for sync at {current_time_iso}")
            
            # Get all connected API credentials where next_sync_at <= current_time
            response = db_client.table("client_api_credentials").select(
                "credential_id, client_id, platform_type, connection_name, credentials, "
                "sync_frequency_hours, last_sync_at, next_sync_at, status"
            ).eq("status", "connected").lte("next_sync_at", current_time_iso).execute()
            
            clients_due = response.data if response.data else []
            
            logger.info(f"Found {len(clients_due)} API integrations due for sync:")
            for client in clients_due:
                logger.info(f"  - Client {client['client_id']} ({client['platform_type']}) - Last: {client.get('last_sync_at', 'Never')}")
            
            return clients_due
            
        except Exception as e:
            logger.error(f"Failed to get clients due for sync: {e}")
            return []
    
    async def sync_client_api_data(self, api_integration: Dict[str, Any]) -> Dict[str, Any]:
        """Sync data for a single client API integration"""
        start_time = datetime.now()
        client_id = api_integration["client_id"]
        credential_id = api_integration["credential_id"]
        platform_type = api_integration["platform_type"]
        connection_name = api_integration["connection_name"]
        sync_frequency_hours = api_integration["sync_frequency_hours"]
        
        logger.info(f"Starting API sync for Client {client_id} ({platform_type} - {connection_name})")
        
        try:
            # Get credentials
            credentials = api_integration["credentials"]
            if isinstance(credentials, str):
                credentials = json.loads(credentials)
            
            logger.info(f"Connecting to {platform_type} API...")
            
            # Import API data fetcher
            from api_connectors import api_data_fetcher
            
            # Test connection first
            success, message = await api_data_fetcher.test_connection(platform_type, credentials)
            if not success:
                logger.error(f"API connection failed for {platform_type}: {message}")
                await self._update_sync_error(credential_id, f"Connection failed: {message}")
                return {"success": False, "error": message}
            
            logger.info(f"API connection successful for {platform_type}")
            
            # Fetch all data from API
            logger.info(f"Fetching new data from {platform_type} API...")
            all_data = await api_data_fetcher.fetch_all_data(platform_type, credentials)
            
            total_records = 0
            data_summary = {}
            
            # Process and store data in dedicated platform tables
            for data_type, records in all_data.items():
                if not records:
                    logger.info(f"  - {data_type}: 0 records")
                    data_summary[data_type] = 0
                    continue
                
                logger.info(f"  - {data_type}: {len(records)} records fetched")
                
                # Store in dedicated platform-specific table (match existing table names)
                table_name = f"{client_id.replace('-', '_')}_{platform_type}_{data_type}"
                logger.info(f"Storing {data_type} data in dedicated table: {table_name}")
                
                try:
                    # Map API data to table columns
                    mapped_records = self.map_api_data_to_table_columns(records, platform_type, data_type, client_id)
                    
                    if not mapped_records:
                        logger.warning(f"No valid records to insert after mapping for {data_type}")
                        data_summary[data_type] = 0
                        continue
                    
                    # Insert records with deduplication
                    inserted_count = await self.insert_with_deduplication(
                        table_name, mapped_records, platform_type, data_type
                    )
                    
                    total_records += inserted_count
                    data_summary[data_type] = inserted_count
                    logger.info(f"Successfully stored {inserted_count} new {data_type} records in {table_name}")
                
                except Exception as e:
                    logger.error(f"Failed to store {data_type} data in dedicated table {table_name}: {e}")
                    data_summary[data_type] = 0
                    # Continue with other data types even if one fails
            
            # Calculate next sync time
            next_sync = datetime.now() + timedelta(hours=sync_frequency_hours)
            
            # Update sync status
            db_client = self._get_admin_client()
            db_client.table("client_api_credentials").update({
                "status": "connected",
                "last_sync_at": datetime.now().isoformat(),
                "next_sync_at": next_sync.isoformat(),
                "error_message": None
            }).eq("credential_id", credential_id).execute()
            
            # Calculate sync duration
            sync_duration = (datetime.now() - start_time).total_seconds()
            
            # Try to log sync result (but don't fail the entire sync if logging fails)
            try:
                db_client.table("client_api_sync_results").insert({
                    "client_id": client_id,
                    "credential_id": credential_id,
                    "platform_type": platform_type,
                    "connection_name": connection_name,
                    "records_fetched": sum(len(records) for records in all_data.values()),
                    "records_processed": total_records,
                    "records_stored": total_records,
                    "sync_duration_seconds": sync_duration,
                    "success": True,
                    "data_types_synced": list(all_data.keys())
                }).execute()
            except Exception as log_error:
                logger.warning(f"Failed to log sync result (but data sync was successful): {log_error}")
            
            logger.info(f"API sync completed for Client {client_id} ({platform_type})")
            logger.info(f"Summary: {total_records} new records stored in {sync_duration:.2f}s")
            logger.info(f"Next sync scheduled for: {next_sync.isoformat()}")
            
            # Trigger SKU calculations if new data was synced (NO AI/LLM)
            if total_records > 0:
                logger.info(f"New data synced - triggering SKU calculations for client {client_id}")
                try:
                    # Trigger SKU cache refresh for this client and platform
                    from sku_analysis_cron import SKUAnalysisCronJob
                    sku_job = SKUAnalysisCronJob()
                    
                    # Refresh SKU cache for this specific client and platform
                    sku_result = await sku_job.refresh_client_sku_analysis(client_id, platform_type)
                    if sku_result.get("success"):
                        logger.info(f"SKU calculations updated after sync: {sku_result.get('skus_cached', 0)} SKUs cached")
                    else:
                        logger.warning(f"SKU calculations failed after sync: {sku_result.get('error')}")
                        
                    # NO LLM/AI triggering - only calculations
                    logger.info(f"SKU calculations completed - AI analysis will run separately")
                    
                except Exception as calc_error:
                    logger.warning(f"SKU calculations failed (but sync was successful): {calc_error}")
            else:
                logger.info(f"No new data synced - skipping SKU calculations")
            
            # Return success=True because data was stored successfully (logging errors don't matter)
            return {
                "success": True,
                "client_id": client_id,
                "platform_type": platform_type,
                "total_records_stored": total_records,
                "data_summary": data_summary,
                "sync_duration_seconds": sync_duration,
                "next_sync_at": next_sync.isoformat(),
                "data_stored_successfully": True,
                "dashboard_updated": total_records > 0
            }
            
        except Exception as e:
            logger.error(f"API sync failed for Client {client_id} ({platform_type}): {e}")
            await self._update_sync_error(credential_id, str(e))
            return {"success": False, "error": str(e), "client_id": client_id, "platform_type": platform_type}
    
    async def _update_sync_error(self, credential_id: str, error_message: str):
        """Update credential status to error"""
        try:
            db_client = self._get_admin_client()
            if db_client:
                # Schedule retry in 1 hour
                next_sync = datetime.now() + timedelta(hours=1)
                
                db_client.table("client_api_credentials").update({
                    "status": "error",
                    "error_message": error_message,
                    "next_sync_at": next_sync.isoformat()
                }).eq("credential_id", credential_id).execute()
                
                logger.info(f"Scheduled retry in 1 hour for credential {credential_id}")
        except Exception as e:
            logger.error(f"Failed to update sync error: {e}")
    
    async def run_full_sync(self) -> Dict[str, Any]:
        """Run full API sync for all clients due for sync"""
        start_time = datetime.now()
        logger.info("Starting full API sync cron job - PERFECT VERSION")
        
        results = {
            "success": True,
            "timestamp": start_time.isoformat(),
            "total_integrations": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "total_records_synced": 0,
            "client_results": {},
            "duration_seconds": 0
        }
        
        try:
            # Get all clients due for sync
            clients_due = await self.get_clients_due_for_sync()
            
            if not clients_due:
                logger.info("No API integrations due for sync at this time")
                results["total_integrations"] = 0
                results["duration_seconds"] = (datetime.now() - start_time).total_seconds()
                return results
            
            results["total_integrations"] = len(clients_due)
            logger.info(f"Processing {len(clients_due)} API integrations...")
            
            # Process each client API integration
            for api_integration in clients_due:
                try:
                    sync_result = await self.sync_client_api_data(api_integration)
                    
                    client_id = api_integration["client_id"]
                    platform_type = api_integration["platform_type"]
                    key = f"{client_id}_{platform_type}"
                    
                    results["client_results"][key] = sync_result
                    
                    if sync_result.get("success"):
                        results["successful_syncs"] += 1
                        results["total_records_synced"] += sync_result.get("total_records_stored", 0)
                        logger.info(f"SUCCESS - {key}: {sync_result.get('total_records_stored', 0)} records")
                    else:
                        results["failed_syncs"] += 1
                        logger.error(f"FAILED - {key}: {sync_result.get('error')}")
                        
                except Exception as e:
                    results["failed_syncs"] += 1
                    client_key = f"{api_integration['client_id']}_{api_integration['platform_type']}"
                    results["client_results"][client_key] = {"success": False, "error": str(e)}
                    logger.error(f"Exception processing {client_key}: {e}")
            
            # Calculate final results
            duration = (datetime.now() - start_time).total_seconds()
            results["duration_seconds"] = duration
            
            logger.info(f"API sync cron job completed in {duration:.2f} seconds")
            logger.info(f"Results: {results['successful_syncs']} successful, {results['failed_syncs']} failed")
            logger.info(f"Total new records synced: {results['total_records_synced']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Fatal error in API sync cron job: {e}")
            results["success"] = False
            results["error"] = str(e)
            results["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            return results

# Global instance
api_sync_cron = APISyncCronJob()

if __name__ == "__main__":
    async def main():
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        logger.info("=" * 80)
        logger.info("STARTING API SYNC CRON JOB - PERFECT VERSION")
        logger.info("=" * 80)
        
        results = await api_sync_cron.run_full_sync()
        
        logger.info("=" * 80)
        logger.info("FINAL RESULTS:")
        logger.info(f"Successful syncs: {results.get('successful_syncs', 0)}")
        logger.info(f"Failed syncs: {results.get('failed_syncs', 0)}")
        logger.info(f"Total records synced: {results.get('total_records_synced', 0)}")
        logger.info(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")
        logger.info("=" * 80)
    
    asyncio.run(main())
