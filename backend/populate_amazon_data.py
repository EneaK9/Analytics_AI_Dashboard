"""
Script to populate Amazon orders and products tables from client JSON data

This script:
1. Fetches raw client data for Amazon client
2. Extracts Amazon orders and products from JSON
3. Transforms data to proper table structure
4. Inserts into Amazon orders and products tables
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from database import get_admin_client, get_db_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmazonDataPopulator:
    """Populates Amazon data tables from raw JSON client data"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.admin_client = get_admin_client()
        
        if not self.admin_client:
            raise Exception(" No admin database client available")
    
    async def fetch_client_data(self, client_id: str) -> List[Dict[str, Any]]:
        """Fetch all data for a specific client"""
        try:
            logger.info(f" Fetching data for Amazon client {client_id}")
            
            result = await self.db_manager.fast_client_data_lookup(
                client_id=client_id,
                use_cache=False
            )
            
            if not result or not result.get('data'):
                logger.warning(f" No data found for client {client_id}")
                return []
            
            logger.info(f" Found {len(result['data'])} records for client {client_id}")
            return result['data']
            
        except Exception as e:
            logger.error(f" Failed to fetch client data: {e}")
            return []
    
    def extract_amazon_data(self, raw_data: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Extract Amazon orders and products from raw data"""
        amazon_data = {
            'orders': [],
            'products': []
        }
        
        for record in raw_data:
            try:
                if isinstance(record, str):
                    data = json.loads(record)
                elif isinstance(record, dict):
                    data = record
                else:
                    continue
                
                platform = data.get('platform', '').lower()
                
                # Check if it's Amazon data
                if platform == 'amazon':
                    if self._is_amazon_order(data):
                        amazon_data['orders'].append(data)
                    elif self._is_amazon_product(data):
                        amazon_data['products'].append(data)
                elif not platform:
                    # Try to infer Amazon data from structure
                    if self._is_amazon_order(data):
                        amazon_data['orders'].append(data)
                    elif self._is_amazon_product(data):
                        amazon_data['products'].append(data)
                        
            except Exception as e:
                logger.warning(f" Error processing record: {e}")
                continue
        
        logger.info(f" Found {len(amazon_data['orders'])} Amazon orders")
        logger.info(f" Found {len(amazon_data['products'])} Amazon products")
        
        return amazon_data
    
    def _is_amazon_order(self, data: Dict[str, Any]) -> bool:
        """Check if data looks like an Amazon order"""
        amazon_order_indicators = [
            'marketplace_id', 'sales_channel', 'fulfillment_channel',
            'is_premium_order', 'is_business_order', 'number_of_items_shipped'
        ]
        
        # Must have order_id and at least 2 Amazon-specific fields
        has_order_id = 'order_id' in data and data.get('order_id')
        amazon_fields = sum(1 for field in amazon_order_indicators if field in data)
        
        return has_order_id and amazon_fields >= 2
    
    def _is_amazon_product(self, data: Dict[str, Any]) -> bool:
        """Check if data looks like an Amazon product"""
        amazon_product_indicators = [
            'asin', 'marketplace_id', 'fulfillment_channel'
        ]
        
        # Must have ASIN or SKU with Amazon indicators
        has_asin = 'asin' in data and data.get('asin')
        has_sku = 'sku' in data and data.get('sku')
        amazon_fields = sum(1 for field in amazon_product_indicators if field in data)
        
        return (has_asin or has_sku) and amazon_fields >= 1
    
    def transform_amazon_order(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Transform Amazon order data to match table schema"""
        try:
            return {
                'client_id': client_id,
                'order_id': data.get('order_id'),
                'order_number': data.get('order_number') or data.get('order_id'),
                'platform': 'amazon',
                'currency': data.get('currency'),
                'total_price': self._safe_decimal(data.get('total_price')),
                'order_status': data.get('order_status'),
                'sales_channel': data.get('sales_channel'),
                'marketplace_id': data.get('marketplace_id'),
                'payment_method': data.get('payment_method'),
                'fulfillment_channel': data.get('fulfillment_channel'),
                'is_premium_order': data.get('is_premium_order', False),
                'is_business_order': data.get('is_business_order', False),
                'number_of_items_shipped': data.get('number_of_items_shipped'),
                'number_of_items_unshipped': data.get('number_of_items_unshipped'),
                'created_at': self._safe_datetime(data.get('created_at')),
                'updated_at': self._safe_datetime(data.get('updated_at')),
                'raw_data': json.dumps(data)
            }
        except Exception as e:
            logger.warning(f" Error transforming Amazon order: {e}")
            return None
    
    def transform_amazon_product(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Transform Amazon product data to match table schema"""
        try:
            return {
                'client_id': client_id,
                'asin': data.get('asin'),
                'sku': data.get('sku'),
                'title': data.get('title') or data.get('name'),
                'platform': 'amazon',
                'brand': data.get('brand'),
                'category': data.get('category'),
                'price': self._safe_decimal(data.get('price')),
                'quantity': data.get('quantity') or data.get('inventory_quantity'),
                'status': data.get('status'),
                'marketplace_id': data.get('marketplace_id'),
                'product_type': data.get('product_type'),
                'fulfillment_channel': data.get('fulfillment_channel'),
                'condition_type': data.get('condition_type') or data.get('condition'),
                'raw_data': json.dumps(data)
            }
        except Exception as e:
            logger.warning(f" Error transforming Amazon product: {e}")
            return None
    
    def _safe_decimal(self, value) -> Optional[float]:
        """Safely convert value to decimal/float"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_datetime(self, value) -> Optional[str]:
        """Safely convert value to ISO datetime string"""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                # Try to parse and reformat to ensure consistency
                parsed = pd.to_datetime(value)
                return parsed.isoformat()
            return str(value)
        except Exception:
            return None
    
    async def clear_existing_data(self, client_id: str) -> bool:
        """Clear existing Amazon data for the client"""
        try:
            orders_table = f"{client_id.replace('-', '_')}_amazon_orders"
            products_table = f"{client_id.replace('-', '_')}_amazon_products"
            
            logger.info(f"️ Clearing existing data from Amazon tables")
            
            # Clear orders
            try:
                self.admin_client.table(orders_table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                logger.info(f" Cleared {orders_table}")
            except Exception as e:
                logger.warning(f" Could not clear {orders_table}: {e}")
            
            # Clear products
            try:
                self.admin_client.table(products_table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                logger.info(f" Cleared {products_table}")
            except Exception as e:
                logger.warning(f" Could not clear {products_table}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f" Failed to clear existing data: {e}")
            return False
    
    async def insert_amazon_data(self, client_id: str, amazon_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """Insert Amazon orders and products into their respective tables"""
        results = {}
        
        # Insert orders
        if amazon_data['orders']:
            results['orders'] = await self._insert_orders(client_id, amazon_data['orders'])
        else:
            results['orders'] = 0
        
        # Insert products
        if amazon_data['products']:
            results['products'] = await self._insert_products(client_id, amazon_data['products'])
        else:
            results['products'] = 0
        
        return results
    
    async def _insert_orders(self, client_id: str, orders: List[Dict[str, Any]]) -> int:
        """Insert Amazon orders"""
        try:
            table_name = f"{client_id.replace('-', '_')}_amazon_orders"
            
            # Transform orders
            transformed_orders = []
            for order in orders:
                transformed = self.transform_amazon_order(order, client_id)
                if transformed:
                    transformed_orders.append(transformed)
            
            if not transformed_orders:
                return 0
            
            logger.info(f" Inserting {len(transformed_orders)} Amazon orders into {table_name}")
            
            # Insert in batches
            batch_size = 100
            total_inserted = 0
            
            for i in range(0, len(transformed_orders), batch_size):
                batch = transformed_orders[i:i + batch_size]
                
                try:
                    response = self.admin_client.table(table_name).insert(batch).execute()
                    
                    if response.data:
                        batch_inserted = len(response.data)
                        total_inserted += batch_inserted
                        logger.info(f" Inserted orders batch {i//batch_size + 1}: {batch_inserted} rows")
                
                except Exception as e:
                    logger.error(f" Failed to insert orders batch {i//batch_size + 1}: {e}")
                    continue
            
            logger.info(f" Total Amazon orders inserted: {total_inserted}")
            return total_inserted
            
        except Exception as e:
            logger.error(f" Failed to insert Amazon orders: {e}")
            return 0
    
    async def _insert_products(self, client_id: str, products: List[Dict[str, Any]]) -> int:
        """Insert Amazon products"""
        try:
            table_name = f"{client_id.replace('-', '_')}_amazon_products"
            
            # Transform products
            transformed_products = []
            for product in products:
                transformed = self.transform_amazon_product(product, client_id)
                if transformed:
                    transformed_products.append(transformed)
            
            if not transformed_products:
                return 0
            
            logger.info(f" Inserting {len(transformed_products)} Amazon products into {table_name}")
            
            # Insert in batches
            batch_size = 100
            total_inserted = 0
            
            for i in range(0, len(transformed_products), batch_size):
                batch = transformed_products[i:i + batch_size]
                
                try:
                    response = self.admin_client.table(table_name).insert(batch).execute()
                    
                    if response.data:
                        batch_inserted = len(response.data)
                        total_inserted += batch_inserted
                        logger.info(f" Inserted products batch {i//batch_size + 1}: {batch_inserted} rows")
                
                except Exception as e:
                    logger.error(f" Failed to insert products batch {i//batch_size + 1}: {e}")
                    continue
            
            logger.info(f" Total Amazon products inserted: {total_inserted}")
            return total_inserted
            
        except Exception as e:
            logger.error(f" Failed to insert Amazon products: {e}")
            return 0
    
    async def populate_amazon_data(self, client_id: str) -> Dict[str, Any]:
        """Main method to populate Amazon data tables"""
        try:
            logger.info(f" Starting Amazon data population for client {client_id}")
            start_time = datetime.now()
            
            # Step 1: Fetch raw data
            raw_data = await self.fetch_client_data(client_id)
            if not raw_data:
                return {"error": "No data found for client", "success": False}
            
            # Step 2: Extract Amazon data
            amazon_data = self.extract_amazon_data(raw_data)
            if not amazon_data['orders'] and not amazon_data['products']:
                return {"error": "No Amazon data found", "success": False}
            
            # Step 3: Clear existing data
            await self.clear_existing_data(client_id)
            
            # Step 4: Insert Amazon data
            insert_results = await self.insert_amazon_data(client_id, amazon_data)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            summary = {
                "client_id": client_id,
                "processing_time_seconds": processing_time,
                "raw_records_processed": len(raw_data),
                "amazon_orders_found": len(amazon_data['orders']),
                "amazon_products_found": len(amazon_data['products']),
                "orders_inserted": insert_results.get('orders', 0),
                "products_inserted": insert_results.get('products', 0),
                "total_inserted": insert_results.get('orders', 0) + insert_results.get('products', 0),
                "success": True
            }
            
            logger.info(f" Amazon data population completed in {processing_time:.2f}s")
            logger.info(f" Summary: {summary}")
            
            return summary
            
        except Exception as e:
            logger.error(f" Amazon data population failed: {e}")
            return {"error": str(e), "success": False}

async def main():
    """Main function for testing"""
    client_id = "6ee35b37-57af-4b70-bc62-1eddf1d0fd15"
    
    try:
        populator = AmazonDataPopulator()
        result = await populator.populate_amazon_data(client_id)
        
        if result.get('success'):
            print(" Amazon data population successful!")
            print(f" Results:")
            print(f"   - Processing time: {result['processing_time_seconds']:.2f}s")
            print(f"   - Raw records processed: {result['raw_records_processed']}")
            print(f"   - Amazon orders found: {result['amazon_orders_found']}")
            print(f"   - Amazon products found: {result['amazon_products_found']}")
            print(f"   - Orders inserted: {result['orders_inserted']}")
            print(f"   - Products inserted: {result['products_inserted']}")
            print(f"   - Total inserted: {result['total_inserted']}")
        else:
            print(f" Amazon data population failed: {result.get('error')}")
    
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
