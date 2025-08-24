"""
Debug script to check price field mapping issues
This script will help identify why unit_price is showing as 0
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from database import get_admin_client, get_db_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceDebugger:
    """Debug price field mapping and data issues"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.admin_client = get_admin_client()
        
        if not self.admin_client:
            raise Exception(" No admin database client available")
    
    async def check_database_price_data(self, client_id: str) -> Dict[str, Any]:
        """Check what's actually in the database price column"""
        try:
            table_name = f"{client_id.replace('-', '_')}_shopify_products"
            
            logger.info(f" Checking price data in {table_name}")
            
            # Get sample records with price focus
            response = self.admin_client.table(table_name).select(
                "sku,title,variant_title,price,inventory_quantity,variant_id"
            ).limit(10).execute()
            
            if response.data:
                logger.info(f" Found {len(response.data)} records")
                
                price_stats = {
                    "total_records": len(response.data),
                    "records_with_price": 0,
                    "records_with_zero_price": 0,
                    "records_with_null_price": 0,
                    "sample_records": []
                }
                
                for record in response.data:
                    price = record.get('price')
                    
                    if price is None:
                        price_stats["records_with_null_price"] += 1
                    elif price == 0 or price == 0.0:
                        price_stats["records_with_zero_price"] += 1
                    else:
                        price_stats["records_with_price"] += 1
                    
                    # Add to sample
                    price_stats["sample_records"].append({
                        "sku": record.get('sku'),
                        "title": record.get('title'),
                        "price": price,
                        "price_type": type(price).__name__
                    })
                
                logger.info(f" Price Statistics:")
                logger.info(f"   Records with valid price: {price_stats['records_with_price']}")
                logger.info(f"   Records with zero price: {price_stats['records_with_zero_price']}")
                logger.info(f"   Records with null price: {price_stats['records_with_null_price']}")
                
                return price_stats
            else:
                logger.warning(" No data found in database")
                return {"error": "No data found"}
                
        except Exception as e:
            logger.error(f" Error checking database: {e}")
            return {"error": str(e)}
    
    async def check_raw_data_structure(self, client_id: str) -> Dict[str, Any]:
        """Check the raw data structure to understand price field names"""
        try:
            logger.info(f" Checking raw data structure for client {client_id}")
            
            # Fetch raw client data
            result = await self.db_manager.fast_client_data_lookup(
                client_id=client_id,
                use_cache=False
            )
            
            if not result or not result.get('data'):
                return {"error": "No raw data found"}
            
            raw_data = result['data']
            logger.info(f" Found {len(raw_data)} raw records")
            
            # Look for Shopify products with variants
            shopify_samples = []
            price_field_variations = set()
            
            for record in raw_data[:20]:  # Check first 20 records
                try:
                    if isinstance(record, str):
                        data = json.loads(record)
                    elif isinstance(record, dict):
                        data = record
                    else:
                        continue
                    
                    # Check if it's Shopify product data
                    if ('variants' in data and 'title' in data) or data.get('platform', '').lower() == 'shopify':
                        variants = data.get('variants', [])
                        if variants:
                            # Check first variant for price fields
                            variant = variants[0]
                            
                            # Look for any field that might contain price
                            for key, value in variant.items():
                                if 'price' in key.lower():
                                    price_field_variations.add(key)
                            
                            sample = {
                                "product_title": data.get('title'),
                                "variant_count": len(variants),
                                "first_variant_sample": {
                                    "sku": variant.get('sku'),
                                    "title": variant.get('title'),
                                    "id": variant.get('id'),
                                    "variant_id": variant.get('variant_id'),
                                    "price_fields": {k: v for k, v in variant.items() if 'price' in k.lower()}
                                }
                            }
                            shopify_samples.append(sample)
                        
                        if len(shopify_samples) >= 5:  # Get 5 samples
                            break
                            
                except Exception as e:
                    logger.warning(f" Error processing record: {e}")
                    continue
            
            result = {
                "total_raw_records": len(raw_data),
                "shopify_samples_found": len(shopify_samples),
                "price_field_variations": list(price_field_variations),
                "sample_products": shopify_samples
            }
            
            logger.info(f" Price field variations found: {price_field_variations}")
            return result
            
        except Exception as e:
            logger.error(f" Error checking raw data: {e}")
            return {"error": str(e)}
    
    async def test_specific_sku(self, client_id: str, sku_code: str = "todd-blk-l") -> Dict[str, Any]:
        """Test the specific SKU that has price = 0"""
        try:
            logger.info(f" Testing specific SKU: {sku_code}")
            
            # Check database
            table_name = f"{client_id.replace('-', '_')}_shopify_products"
            db_response = self.admin_client.table(table_name).select("*").eq('sku', sku_code).execute()
            
            db_record = db_response.data[0] if db_response.data else None
            
            # Check raw data
            result = await self.db_manager.fast_client_data_lookup(
                client_id=client_id,
                use_cache=False
            )
            
            raw_record = None
            if result and result.get('data'):
                for record in result['data']:
                    try:
                        if isinstance(record, str):
                            data = json.loads(record)
                        elif isinstance(record, dict):
                            data = record
                        else:
                            continue
                        
                        # Look for this SKU in variants
                        variants = data.get('variants', [])
                        for variant in variants:
                            if variant.get('sku') == sku_code:
                                raw_record = {
                                    "product_title": data.get('title'),
                                    "variant_data": variant
                                }
                                break
                        
                        if raw_record:
                            break
                            
                    except Exception as e:
                        continue
            
            return {
                "sku_code": sku_code,
                "database_record": db_record,
                "raw_data_record": raw_record,
                "comparison": {
                    "db_price": db_record.get('price') if db_record else None,
                    "raw_price": raw_record['variant_data'].get('price') if raw_record else None,
                    "raw_price_fields": {k: v for k, v in raw_record['variant_data'].items() if 'price' in k.lower()} if raw_record else {}
                }
            }
            
        except Exception as e:
            logger.error(f" Error testing specific SKU: {e}")
            return {"error": str(e)}

async def main():
    """Main debugging function"""
    client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
    
    try:
        debugger = PriceDebugger()
        
        print(" DEBUGGING PRICE MAPPING ISSUES")
        print("=" * 50)
        
        # 1. Check database price data
        print("\n1️⃣ CHECKING DATABASE PRICE DATA")
        db_stats = await debugger.check_database_price_data(client_id)
        print(json.dumps(db_stats, indent=2))
        
        # 2. Check raw data structure
        print("\n2️⃣ CHECKING RAW DATA STRUCTURE")
        raw_analysis = await debugger.check_raw_data_structure(client_id)
        print(json.dumps(raw_analysis, indent=2))
        
        # 3. Test specific problematic SKU
        print("\n3️⃣ TESTING SPECIFIC SKU: todd-blk-l")
        sku_test = await debugger.test_specific_sku(client_id, "todd-blk-l")
        print(json.dumps(sku_test, indent=2))
        
        print("\n DEBUG ANALYSIS COMPLETE")
        print("\n RECOMMENDATIONS:")
        print("1. Check if price fields in raw data use different names")
        print("2. Verify if data needs to be repopulated after schema changes")  
        print("3. Check if price data is stored at product level vs variant level")
        print("4. Run repopulate_shopify_products.py if price mapping is incorrect")
    
    except Exception as e:
        print(f" Debug error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
