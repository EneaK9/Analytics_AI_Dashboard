"""
Script to populate Shopify orders table from client JSON data

This script extracts Shopify orders from client_data JSON and populates the organized shopify_orders table
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

class ShopifyOrdersPopulator:
    """Populates Shopify orders table from raw JSON client data"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.admin_client = get_admin_client()
        
        if not self.admin_client:
            raise Exception(" No admin database client available")
    
    async def fetch_client_data(self, client_id: str) -> List[Dict[str, Any]]:
        """Fetch all data for a specific client"""
        try:
            logger.info(f" Fetching data for client {client_id}")
            
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
    
    def extract_shopify_orders(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        """Extract Shopify orders from raw data"""
        shopify_orders = []
        
        for record in raw_data:
            try:
                if isinstance(record, str):
                    data = json.loads(record)
                elif isinstance(record, dict):
                    data = record
                else:
                    continue
                
                platform = data.get('platform', '').lower()
                
                # Check if it's a Shopify order
                if platform == 'shopify' and self._is_shopify_order(data):
                    shopify_orders.append(data)
                elif not platform and self._is_shopify_order(data):
                    # Likely Shopify order without explicit platform
                    shopify_orders.append(data)
                        
            except Exception as e:
                logger.warning(f" Error processing record: {e}")
                continue
        
        logger.info(f" Found {len(shopify_orders)} Shopify orders")
        return shopify_orders
    
    def _is_shopify_order(self, data: Dict[str, Any]) -> bool:
        """Check if data looks like a Shopify order"""
        shopify_order_indicators = [
            'customer_email', 'financial_status', 'fulfillment_status',
            'billing_address', 'shipping_address', 'line_items_count'
        ]
        
        # Must have order_id and at least 2 Shopify-specific fields
        has_order_id = 'order_id' in data and data.get('order_id')
        shopify_fields = sum(1 for field in shopify_order_indicators if field in data)
        
        # Also check for typical Shopify order structure
        has_shopify_structure = (
            'customer_email' in data or 
            'financial_status' in data or
            'billing_address' in data
        )
        
        return has_order_id and (shopify_fields >= 2 or has_shopify_structure)
    
    def transform_shopify_order(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Transform Shopify order data to match table schema INCLUDING LINE ITEMS"""
        try:
            # Calculate total items quantity from line items
            line_items = data.get('line_items', [])
            total_items_quantity = sum(item.get('quantity', 0) for item in line_items)
            
            return {
                'client_id': client_id,
                'order_id': data.get('order_id'),
                'order_number': data.get('order_number'),
                'name': data.get('name'),  # Order name like "#1001"
                'platform': 'shopify',
                'currency': data.get('currency'),
                'total_price': self._safe_decimal(data.get('total_price')),
                'subtotal_price': self._safe_decimal(data.get('subtotal_price')),
                'total_weight': data.get('total_weight'),
                'total_tax': self._safe_decimal(data.get('total_tax')),
                'total_discounts': self._safe_decimal(data.get('total_discounts')),
                'total_line_items_price': self._safe_decimal(data.get('total_line_items_price')),
                'taxes_included': data.get('taxes_included'),
                'financial_status': data.get('financial_status'),
                'confirmed': data.get('confirmed'),
                'total_price_usd': self._safe_decimal(data.get('total_price_usd')),
                'fulfillment_status': data.get('fulfillment_status'),
                'customer_id': data.get('customer_id'),
                'customer_email': data.get('customer_email'),
                'created_at': self._safe_datetime(data.get('created_at')),
                'updated_at': self._safe_datetime(data.get('updated_at')),
                'closed_at': self._safe_datetime(data.get('closed_at')),
                'cancelled_at': self._safe_datetime(data.get('cancelled_at')),
                'cancel_reason': data.get('cancel_reason'),
                'processed_at': self._safe_datetime(data.get('processed_at')),
                'checkout_id': data.get('checkout_id'),
                'reference': data.get('reference'),
                'user_id': data.get('user_id'),
                'location_id': data.get('location_id'),
                'source_identifier': data.get('source_identifier'),
                'source_url': data.get('source_url'),
                'source_name': data.get('source_name'),
                'device_id': data.get('device_id'),
                'phone': data.get('phone'),
                'customer_locale': data.get('customer_locale'),
                'app_id': data.get('app_id'),
                'browser_ip': data.get('browser_ip'),
                'landing_site': data.get('landing_site'),
                'referring_site': data.get('referring_site'),
                'order_status_url': data.get('order_status_url'),
                'line_items_count': data.get('line_items_count'),
                'total_items_quantity': total_items_quantity,  # ✅ Total quantity from line items
                'line_items': json.dumps(line_items),  # ✅ Enhanced line items with ALL fields
                'customer_data': json.dumps(data.get('customer_data', {})),  # ✅ Complete customer info
                'fulfillments': json.dumps(data.get('fulfillments', [])),  # ✅ All fulfillment data
                'refunds': json.dumps(data.get('refunds', [])),  # ✅ All refund data
                'transactions': json.dumps(data.get('transactions', [])),  # ✅ All transaction data
                'shipping_lines': json.dumps(data.get('shipping_lines', [])),  # ✅ Enhanced shipping data
                'tags': data.get('tags', ''),
                'billing_address': json.dumps(data.get('billing_address', {})),
                'shipping_address': json.dumps(data.get('shipping_address', {})),
                'discount_codes': json.dumps(data.get('discount_codes', [])),
                'discount_applications': json.dumps(data.get('discount_applications', [])),
                'note': data.get('note', ''),
                'note_attributes': json.dumps(data.get('note_attributes', [])),
                'processing_method': data.get('processing_method'),
                'checkout_token': data.get('checkout_token'),
                'token': data.get('token'),
                'cart_token': data.get('cart_token'),
                'tax_lines': json.dumps(data.get('tax_lines', [])),
                'order_adjustments': json.dumps(data.get('order_adjustments', [])),
                'client_details': json.dumps(data.get('client_details', {})),
                'payment_gateway_names': json.dumps(data.get('payment_gateway_names', [])),
                'payment_details': json.dumps(data.get('payment_details', {})),
                'raw_data': json.dumps(data)
            }
        except Exception as e:
            logger.warning(f" Error transforming Shopify order: {e}")
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
        """Clear existing Shopify orders for the client"""
        try:
            orders_table = f"{client_id.replace('-', '_')}_shopify_orders"
            
            logger.info(f"️ Clearing existing data from {orders_table}")
            
            try:
                self.admin_client.table(orders_table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                logger.info(f" Cleared {orders_table}")
            except Exception as e:
                logger.warning(f" Could not clear {orders_table}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f" Failed to clear existing data: {e}")
            return False
    
    async def insert_shopify_orders(self, client_id: str, orders: List[Dict[str, Any]]) -> int:
        """Insert Shopify orders into the organized table"""
        try:
            table_name = f"{client_id.replace('-', '_')}_shopify_orders"
            
            # Transform orders
            transformed_orders = []
            for order in orders:
                transformed = self.transform_shopify_order(order, client_id)
                if transformed:
                    transformed_orders.append(transformed)
            
            if not transformed_orders:
                return 0
            
            logger.info(f" Inserting {len(transformed_orders)} Shopify orders into {table_name}")
            
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
                        logger.info(f" Inserted batch {i//batch_size + 1}: {batch_inserted} orders")
                
                except Exception as e:
                    logger.error(f" Failed to insert batch {i//batch_size + 1}: {e}")
                    continue
            
            logger.info(f" Total Shopify orders inserted: {total_inserted}")
            return total_inserted
            
        except Exception as e:
            logger.error(f" Failed to insert Shopify orders: {e}")
            return 0
    
    async def populate_shopify_orders(self, client_id: str) -> Dict[str, Any]:
        """Main method to populate Shopify orders table"""
        try:
            logger.info(f" Starting Shopify orders population for client {client_id}")
            start_time = datetime.now()
            
            # Step 1: Fetch raw data
            raw_data = await self.fetch_client_data(client_id)
            if not raw_data:
                return {"error": "No data found for client", "success": False}
            
            # Step 2: Extract Shopify orders
            shopify_orders = self.extract_shopify_orders(raw_data)
            if not shopify_orders:
                return {"error": "No Shopify orders found", "success": False}
            
            # Step 3: Clear existing data
            await self.clear_existing_data(client_id)
            
            # Step 4: Insert orders
            inserted_count = await self.insert_shopify_orders(client_id, shopify_orders)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            summary = {
                "client_id": client_id,
                "processing_time_seconds": processing_time,
                "raw_records_processed": len(raw_data),
                "shopify_orders_found": len(shopify_orders),
                "orders_inserted": inserted_count,
                "success": True
            }
            
            logger.info(f" Shopify orders population completed in {processing_time:.2f}s")
            logger.info(f" Summary: {summary}")
            
            return summary
            
        except Exception as e:
            logger.error(f" Shopify orders population failed: {e}")
            return {"error": str(e), "success": False}

async def main():
    """Main function for testing"""
    # Test with both clients
    clients = [
        "3b619a14-3cd8-49fa-9c24-d8df5e54c452",  # Original Shopify client
        "6ee35b37-57af-4b70-bc62-1eddf1d0fd15"   # Amazon client (might have Shopify orders too)
    ]
    
    for client_id in clients:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing client: {client_id}")
            
            populator = ShopifyOrdersPopulator()
            result = await populator.populate_shopify_orders(client_id)
            
            if result.get('success'):
                print(f" Shopify orders population successful for {client_id}!")
                print(f" Results:")
                print(f"   - Processing time: {result['processing_time_seconds']:.2f}s")
                print(f"   - Raw records processed: {result['raw_records_processed']}")
                print(f"   - Shopify orders found: {result['shopify_orders_found']}")
                print(f"   - Orders inserted: {result['orders_inserted']}")
            else:
                print(f" Shopify orders population failed for {client_id}: {result.get('error')}")
        
        except Exception as e:
            print(f" Error processing {client_id}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
