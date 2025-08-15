"""
Script to properly populate Shopify products table with variants as separate rows

This script:
1. Clears existing Shopify products data
2. Fetches raw client data
3. Creates one row per variant, repeating the product name
4. Inserts into the updated shopify_products table structure
"""

import asyncio
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from database import get_admin_client, get_db_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShopifyProductRepopulator:
    """Repopulates Shopify products with proper variant structure"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.admin_client = get_admin_client()
        
        if not self.admin_client:
            raise Exception("❌ No admin database client available")
    
    async def fetch_client_data(self, client_id: str) -> List[Dict[str, Any]]:
        """Fetch all data for a specific client"""
        try:
            logger.info(f"📊 Fetching data for client {client_id}")
            
            result = await self.db_manager.fast_client_data_lookup(
                client_id=client_id,
                use_cache=False
            )
            
            if not result or not result.get('data'):
                logger.warning(f"⚠️ No data found for client {client_id}")
                return []
            
            return result['data']
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch client data: {e}")
            return []
    
    def extract_shopify_products(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        """Extract Shopify products from raw data"""
        shopify_products = []
        
        for record in raw_data:
            try:
                if isinstance(record, str):
                    data = json.loads(record)
                elif isinstance(record, dict):
                    data = record
                else:
                    continue
                
                platform = data.get('platform', '').lower()
                
                # Check if it's a Shopify product
                if (platform == 'shopify' and 'title' in data and 
                    ('handle' in data or 'variants' in data)):
                    shopify_products.append(data)
                elif (not platform and 'handle' in data and 'variants' in data):
                    # Likely Shopify product without explicit platform
                    shopify_products.append(data)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error processing record: {e}")
                continue
        
        logger.info(f"📦 Found {len(shopify_products)} Shopify products")
        return shopify_products
    
    def create_variant_rows(self, product_data: Dict[str, Any], client_id: str) -> List[Dict[str, Any]]:
        """Create separate rows for each variant of a product"""
        try:
            variants = product_data.get('variants', [])
            if not variants:
                logger.warning(f"⚠️ No variants found for product: {product_data.get('title')}")
                return []
            
            variant_rows = []
            
            for variant in variants:
                try:
                    # Parse variant title to extract options (e.g., "Black / L" -> option1="Black", option2="L")
                    variant_title = variant.get('title', '')
                    option1, option2, option3 = None, None, None
                    
                    if ' / ' in variant_title:
                        options = variant_title.split(' / ')
                        option1 = options[0] if len(options) > 0 else None
                        option2 = options[1] if len(options) > 1 else None
                        option3 = options[2] if len(options) > 2 else None
                    else:
                        option1 = variant_title
                    
                    # Create row with product info + variant info
                    row = {
                        'client_id': client_id,
                        'product_id': product_data.get('id'),
                        'title': product_data.get('title'),  # Product title repeated for each variant
                        'handle': product_data.get('handle'),
                        'vendor': product_data.get('vendor'),
                        'platform': 'shopify',
                        'status': product_data.get('status'),
                        'tags': product_data.get('tags', ''),
                        
                        # Variant-specific fields
                        'variant_id': variant.get('variant_id') or variant.get('id'),
                        'sku': variant.get('sku'),
                        'variant_title': variant_title,
                        'price': self._safe_decimal(variant.get('price')),
                        'weight': self._safe_decimal(variant.get('weight')),
                        'inventory_quantity': variant.get('inventory_quantity'),
                        'requires_shipping': variant.get('requires_shipping', True),
                        'position': variant.get('position'),
                        'option1': option1,
                        'option2': option2,
                        'option3': option3,
                        'barcode': variant.get('barcode'),
                        'compare_at_price': self._safe_decimal(variant.get('compare_at_price')),
                        'fulfillment_service': variant.get('fulfillment_service'),
                        'inventory_management': variant.get('inventory_management'),
                        'inventory_policy': variant.get('inventory_policy'),
                        
                        # Keep minimal product-level JSON data
                        'variants': json.dumps([]),  # Empty since we're expanding
                        'options': json.dumps(product_data.get('options', [])),
                        'images': json.dumps(product_data.get('images', [])),
                        'raw_data': json.dumps(product_data)
                    }
                    
                    variant_rows.append(row)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error processing variant: {e}")
                    continue
            
            logger.info(f"📋 Created {len(variant_rows)} variant rows for product: {product_data.get('title')}")
            return variant_rows
            
        except Exception as e:
            logger.error(f"❌ Failed to create variant rows: {e}")
            return []
    
    def _safe_decimal(self, value) -> float:
        """Safely convert value to decimal/float"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    async def clear_existing_data(self, client_id: str) -> bool:
        """Clear existing Shopify products data"""
        try:
            table_name = f"{client_id.replace('-', '_')}_shopify_products"
            
            logger.info(f"🗑️ Clearing existing data from {table_name}")
            
            # Delete all existing records
            response = self.admin_client.table(table_name).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            
            logger.info(f"✅ Cleared existing data from {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear existing data: {e}")
            return False
    
    async def insert_variant_rows(self, client_id: str, variant_rows: List[Dict[str, Any]]) -> int:
        """Insert variant rows into the shopify_products table"""
        try:
            if not variant_rows:
                return 0
            
            table_name = f"{client_id.replace('-', '_')}_shopify_products"
            
            logger.info(f"📥 Inserting {len(variant_rows)} variant rows into {table_name}")
            
            # Insert in batches to avoid timeouts
            batch_size = 100
            total_inserted = 0
            
            for i in range(0, len(variant_rows), batch_size):
                batch = variant_rows[i:i + batch_size]
                
                try:
                    response = self.admin_client.table(table_name).insert(batch).execute()
                    
                    if response.data:
                        batch_inserted = len(response.data)
                        total_inserted += batch_inserted
                        logger.info(f"✅ Inserted batch {i//batch_size + 1}: {batch_inserted} rows")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to insert batch {i//batch_size + 1}: {e}")
                    continue
            
            logger.info(f"🎉 Total inserted: {total_inserted} variant rows")
            return total_inserted
            
        except Exception as e:
            logger.error(f"❌ Failed to insert variant rows: {e}")
            return 0
    
    async def repopulate_shopify_products(self, client_id: str) -> Dict[str, Any]:
        """Main method to repopulate Shopify products with proper variant structure"""
        try:
            logger.info(f"🚀 Starting Shopify products repopulation for client {client_id}")
            start_time = datetime.now()
            
            # Step 1: Fetch raw data
            raw_data = await self.fetch_client_data(client_id)
            if not raw_data:
                return {"error": "No data found for client", "success": False}
            
            # Step 2: Extract Shopify products
            shopify_products = self.extract_shopify_products(raw_data)
            if not shopify_products:
                return {"error": "No Shopify products found", "success": False}
            
            # Step 3: Clear existing data
            await self.clear_existing_data(client_id)
            
            # Step 4: Create variant rows
            all_variant_rows = []
            for product in shopify_products:
                variant_rows = self.create_variant_rows(product, client_id)
                all_variant_rows.extend(variant_rows)
            
            if not all_variant_rows:
                return {"error": "No variant rows created", "success": False}
            
            # Step 5: Insert variant rows
            inserted_count = await self.insert_variant_rows(client_id, all_variant_rows)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            summary = {
                "client_id": client_id,
                "processing_time_seconds": processing_time,
                "shopify_products_found": len(shopify_products),
                "variant_rows_created": len(all_variant_rows),
                "variant_rows_inserted": inserted_count,
                "success": True
            }
            
            logger.info(f"✅ Shopify products repopulation completed in {processing_time:.2f}s")
            logger.info(f"📊 Summary: {summary}")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Shopify products repopulation failed: {e}")
            return {"error": str(e), "success": False}

async def main():
    """Main function for testing"""
    client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
    
    try:
        repopulator = ShopifyProductRepopulator()
        result = await repopulator.repopulate_shopify_products(client_id)
        
        if result.get('success'):
            print("✅ Shopify products repopulation successful!")
            print(f"📊 Results:")
            print(f"   - Processing time: {result['processing_time_seconds']:.2f}s")
            print(f"   - Products found: {result['shopify_products_found']}")
            print(f"   - Variant rows created: {result['variant_rows_created']}")
            print(f"   - Variant rows inserted: {result['variant_rows_inserted']}")
        else:
            print(f"❌ Repopulation failed: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
