"""
Enhanced Data Organizer with Proper Variant Handling

This version separates product variants into their own table for better analytics
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from data_organizer import DataOrganizer

logger = logging.getLogger(__name__)

class VariantEnhancedOrganizer(DataOrganizer):
    """Enhanced organizer that properly handles product variants in separate tables"""
    
    def categorize_data(self, raw_data: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Enhanced categorization that also extracts variants"""
        try:
            categorized = {
                'shopify_orders': [],
                'shopify_products': [],
                'shopify_variants': [],
                'amazon_orders': [],
                'amazon_products': [],
                'amazon_variants': []
            }
            
            for record in raw_data:
                try:
                    # Handle different data formats
                    if isinstance(record, str):
                        data = json.loads(record)
                    elif isinstance(record, dict):
                        data = record
                    else:
                        logger.warning(f" Unexpected data format: {type(record)}")
                        continue
                    
                    # Determine platform and type
                    platform = data.get('platform', '').lower()
                    
                    if platform == 'shopify':
                        if 'order_id' in data or 'order_number' in data:
                            categorized['shopify_orders'].append(data)
                        elif 'title' in data and ('handle' in data or 'variants' in data):
                            categorized['shopify_products'].append(data)
                            
                            # Extract variants separately
                            variants = data.get('variants', [])
                            if variants and isinstance(variants, list):
                                for variant in variants:
                                    # Add product context to variant
                                    variant_with_context = variant.copy()
                                    variant_with_context['parent_product_id'] = data.get('id')
                                    variant_with_context['parent_title'] = data.get('title')
                                    variant_with_context['parent_handle'] = data.get('handle')
                                    categorized['shopify_variants'].append(variant_with_context)
                    
                    elif platform == 'amazon':
                        if 'order_id' in data and 'order_status' in data:
                            categorized['amazon_orders'].append(data)
                        elif 'asin' in data or ('sku' in data and 'price' in data):
                            categorized['amazon_products'].append(data)
                            # Amazon variants would be handled differently
                            # For now, treat each ASIN as a variant if there's variation info
                    
                    # Handle data without explicit platform but with recognizable structure
                    elif not platform:
                        # Try to infer from structure
                        if 'marketplace_id' in data or 'sales_channel' in data:
                            categorized['amazon_orders'].append(data)
                        elif 'handle' in data and 'variants' in data:
                            categorized['shopify_products'].append(data)
                            # Extract variants
                            variants = data.get('variants', [])
                            if variants and isinstance(variants, list):
                                for variant in variants:
                                    variant_with_context = variant.copy()
                                    variant_with_context['parent_product_id'] = data.get('id')
                                    variant_with_context['parent_title'] = data.get('title')
                                    variant_with_context['parent_handle'] = data.get('handle')
                                    categorized['shopify_variants'].append(variant_with_context)
                        elif 'customer_email' in data and 'financial_status' in data:
                            categorized['shopify_orders'].append(data)
                        else:
                            logger.warning(f" Could not categorize record: {data}")
                
                except Exception as e:
                    logger.warning(f" Error processing record: {e}")
                    continue
            
            # Log categorization results
            for category, items in categorized.items():
                if items:
                    logger.info(f" {category}: {len(items)} records")
            
            return categorized
            
        except Exception as e:
            logger.error(f" Failed to categorize data: {e}")
            return {}
    
    def transform_shopify_product(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Transform Shopify product data WITHOUT variants (variants handled separately)"""
        try:
            return {
                'client_id': client_id,
                'product_id': data.get('id'),
                'title': data.get('title'),
                'handle': data.get('handle'),
                'vendor': data.get('vendor'),
                'platform': 'shopify',
                'status': data.get('status'),
                'tags': data.get('tags', ''),
                'variants': json.dumps([]),  # Empty - variants in separate table
                'options': json.dumps(data.get('options', [])),
                'images': json.dumps(data.get('images', [])),
                'raw_data': json.dumps(data)
            }
        except Exception as e:
            logger.warning(f" Error transforming Shopify product: {e}")
            return None
    
    def transform_shopify_variant(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Transform Shopify variant data into separate record"""
        try:
            # Parse title to extract options (e.g., "Black / L" -> option1="Black", option2="L")
            title = data.get('title', '')
            option1, option2, option3 = None, None, None
            
            if ' / ' in title:
                options = title.split(' / ')
                option1 = options[0] if len(options) > 0 else None
                option2 = options[1] if len(options) > 1 else None
                option3 = options[2] if len(options) > 2 else None
            else:
                option1 = title
            
            return {
                'client_id': client_id,
                'product_id': data.get('parent_product_id'),
                'variant_id': data.get('variant_id'),
                'sku': data.get('sku'),
                'title': title,
                'price': self._safe_decimal(data.get('price')),
                'weight': self._safe_decimal(data.get('weight')),
                'inventory_quantity': data.get('inventory_quantity'),
                'requires_shipping': data.get('requires_shipping', True),
                'position': data.get('position'),
                'option1': option1,
                'option2': option2,
                'option3': option3,
                'barcode': data.get('barcode'),
                'compare_at_price': self._safe_decimal(data.get('compare_at_price')),
                'fulfillment_service': data.get('fulfillment_service'),
                'inventory_management': data.get('inventory_management'),
                'inventory_policy': data.get('inventory_policy'),
                'created_at': self._safe_datetime(data.get('created_at')),
                'updated_at': self._safe_datetime(data.get('updated_at'))
            }
        except Exception as e:
            logger.warning(f" Error transforming Shopify variant: {e}")
            return None
    
    async def insert_organized_data(self, client_id: str, categorized_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """Insert organized data including variants into separate tables"""
        try:
            results = {}
            
            # Transform and insert each category into its actual table
            for data_type, records in categorized_data.items():
                if not records:
                    results[data_type] = 0
                    continue
                
                logger.info(f" Processing {len(records)} {data_type} records into separate table")
                
                # Transform records based on type
                transformed_records = []
                for record in records:
                    try:
                        if data_type == 'shopify_orders':
                            transformed = self.transform_shopify_order(record, client_id)
                        elif data_type == 'shopify_products':
                            transformed = self.transform_shopify_product(record, client_id)
                        elif data_type == 'shopify_variants':
                            transformed = self.transform_shopify_variant(record, client_id)
                        elif data_type == 'amazon_orders':
                            transformed = self.transform_amazon_order(record, client_id)
                        elif data_type == 'amazon_products':
                            transformed = self.transform_amazon_product(record, client_id)
                        else:
                            continue
                        
                        if transformed:
                            transformed_records.append(transformed)
                    
                    except Exception as e:
                        logger.warning(f" Error transforming {data_type} record: {e}")
                        continue
                
                if not transformed_records:
                    results[data_type] = 0
                    continue
                
                # Insert into actual separate table
                table_name = f"{client_id.replace('-', '_')}_{data_type}"
                
                try:
                    # Insert directly into the separate table
                    response = self.admin_client.table(table_name).insert(transformed_records).execute()
                    results[data_type] = len(response.data) if response.data else 0
                    logger.info(f" Inserted {results[data_type]} records into {table_name}")
                
                except Exception as e:
                    logger.error(f" Failed to insert into {table_name}: {e}")
                    logger.info(f" Make sure the table {table_name} exists in Supabase")
                    results[data_type] = 0
            
            return results
            
        except Exception as e:
            logger.error(f" Failed to insert organized data: {e}")
            return {}

async def main():
    """Test the variant-enhanced organizer"""
    client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
    
    try:
        logger.info(" Testing Variant-Enhanced Data Organizer")
        
        organizer = VariantEnhancedOrganizer()
        result = await organizer.organize_client_data(client_id)
        
        if result.get('success'):
            print(" Variant-enhanced data organization successful!")
            print(f" Results:")
            print(f"   - Processing time: {result.get('processing_time_seconds'):.2f}s")
            print(f"   - Total raw records: {result.get('total_raw_records')}")
            print(f"   - Total organized: {result.get('total_organized')}")
            print(f"   - Breakdown:")
            for data_type, count in result.get('organized_records', {}).items():
                if count > 0:
                    print(f"     * {data_type}: {count} records")
        else:
            print(f" Variant-enhanced organization failed: {result.get('error')}")
    
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
