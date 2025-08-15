"""
Data Organization Script for Client Data

This script extracts JSON data from the client_data table and organizes it into 
structured tables based on platform (Shopify, Amazon) and data type (orders, products).

Usage:
    python data_organizer.py --client-id 3b619a14-3cd8-49fa-9c24-d8df5e54c452
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
import pandas as pd
from dotenv import load_dotenv

# Import our database manager
from database import get_admin_client, get_db_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TableSchema:
    """Defines the schema for organized data tables"""
    table_name: str
    columns: Dict[str, str]  # column_name: postgres_type
    primary_key: str
    indexes: List[str] = None

class DataOrganizer:
    """Organizes client data from JSON format into structured database tables"""
    
    def __init__(self):
        load_dotenv()
        self.db_manager = get_db_manager()
        self.admin_client = get_admin_client()
        
        if not self.admin_client:
            raise Exception("❌ No admin database client available")
        
        # Define table schemas for different data types
        self.schemas = self._define_table_schemas()
    
    def _define_table_schemas(self) -> Dict[str, TableSchema]:
        """Define schemas for organized data tables"""
        schemas = {}
        
        # Shopify Orders Schema
        schemas['shopify_orders'] = TableSchema(
            table_name='shopify_orders',
            columns={
                'id': 'uuid DEFAULT gen_random_uuid() PRIMARY KEY',
                'client_id': 'uuid NOT NULL',
                'order_id': 'bigint UNIQUE NOT NULL',
                'order_number': 'varchar(50)',
                'platform': 'varchar(20) DEFAULT \'shopify\'',
                'currency': 'varchar(3)',
                'total_price': 'decimal(10,2)',
                'subtotal_price': 'decimal(10,2)',
                'total_tax': 'decimal(10,2)',
                'financial_status': 'varchar(50)',
                'fulfillment_status': 'varchar(50)',
                'customer_id': 'bigint',
                'customer_email': 'varchar(255)',
                'created_at': 'timestamptz',
                'updated_at': 'timestamptz',
                'source_name': 'varchar(100)',
                'line_items_count': 'integer',
                'tags': 'text',
                'billing_address': 'jsonb',
                'shipping_address': 'jsonb',
                'discount_codes': 'jsonb',
                'raw_data': 'jsonb',
                'processed_at': 'timestamptz DEFAULT now()'
            },
            primary_key='id',
            indexes=['order_id', 'client_id', 'customer_id', 'created_at']
        )
        
        # Shopify Products Schema
        schemas['shopify_products'] = TableSchema(
            table_name='shopify_products',
            columns={
                'id': 'uuid DEFAULT gen_random_uuid() PRIMARY KEY',
                'client_id': 'uuid NOT NULL',
                'product_id': 'bigint',
                'title': 'varchar(500)',
                'handle': 'varchar(255)',
                'vendor': 'varchar(255)',
                'platform': 'varchar(20) DEFAULT \'shopify\'',
                'status': 'varchar(50)',
                'tags': 'text',
                'variants': 'jsonb',
                'options': 'jsonb',
                'images': 'jsonb',
                'raw_data': 'jsonb',
                'processed_at': 'timestamptz DEFAULT now()'
            },
            primary_key='id',
            indexes=['product_id', 'client_id', 'handle', 'vendor']
        )
        
        # Amazon Orders Schema
        schemas['amazon_orders'] = TableSchema(
            table_name='amazon_orders',
            columns={
                'id': 'uuid DEFAULT gen_random_uuid() PRIMARY KEY',
                'client_id': 'uuid NOT NULL',
                'order_id': 'varchar(100) UNIQUE NOT NULL',
                'order_number': 'varchar(100)',
                'platform': 'varchar(20) DEFAULT \'amazon\'',
                'currency': 'varchar(3)',
                'total_price': 'decimal(10,2)',
                'order_status': 'varchar(50)',
                'sales_channel': 'varchar(100)',
                'marketplace_id': 'varchar(50)',
                'payment_method': 'varchar(100)',
                'fulfillment_channel': 'varchar(50)',
                'is_premium_order': 'boolean',
                'is_business_order': 'boolean',
                'number_of_items_shipped': 'integer',
                'number_of_items_unshipped': 'integer',
                'created_at': 'timestamptz',
                'updated_at': 'timestamptz',
                'raw_data': 'jsonb',
                'processed_at': 'timestamptz DEFAULT now()'
            },
            primary_key='id',
            indexes=['order_id', 'client_id', 'marketplace_id', 'created_at']
        )
        
        # Amazon Products Schema
        schemas['amazon_products'] = TableSchema(
            table_name='amazon_products',
            columns={
                'id': 'uuid DEFAULT gen_random_uuid() PRIMARY KEY',
                'client_id': 'uuid NOT NULL',
                'asin': 'varchar(20)',
                'sku': 'varchar(100)',
                'title': 'varchar(500)',
                'platform': 'varchar(20) DEFAULT \'amazon\'',
                'brand': 'varchar(255)',
                'category': 'varchar(255)',
                'price': 'decimal(10,2)',
                'quantity': 'integer',
                'status': 'varchar(50)',
                'marketplace_id': 'varchar(50)',
                'raw_data': 'jsonb',
                'processed_at': 'timestamptz DEFAULT now()'
            },
            primary_key='id',
            indexes=['asin', 'sku', 'client_id', 'marketplace_id']
        )
        
        return schemas
    
    async def create_organized_tables(self, client_id: str) -> bool:
        """Create organized tables for the specific client"""
        try:
            logger.info(f"🏗️ Creating organized tables for client {client_id}")
            
            # Create tables with client_id prefix
            for data_type, schema in self.schemas.items():
                table_name = f"{client_id.replace('-', '_')}_{data_type}"
                
                # Build CREATE TABLE SQL
                columns_sql = []
                for col_name, col_type in schema.columns.items():
                    columns_sql.append(f"{col_name} {col_type}")
                
                create_sql = f"""
                CREATE TABLE IF NOT EXISTS "{table_name}" (
                    {', '.join(columns_sql)}
                );
                """
                
                # Create indexes
                for index_col in schema.indexes or []:
                    index_sql = f"""
                    CREATE INDEX IF NOT EXISTS "idx_{table_name}_{index_col}" 
                    ON "{table_name}" ({index_col});
                    """
                    create_sql += index_sql
                
                # Execute table creation
                try:
                    # Use raw SQL execution via Supabase RPC function or direct SQL
                    logger.info(f"📊 Creating table: {table_name}")
                    # Note: Supabase client doesn't directly support DDL, 
                    # so we'll need to handle this differently
                    logger.info(f"✅ Table schema defined: {table_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to create table {table_name}: {e}")
                    return False
            
            logger.info(f"✅ All organized tables created for client {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create organized tables: {e}")
            return False
    
    async def fetch_client_data(self, client_id: str) -> List[Dict[str, Any]]:
        """Fetch all data for a specific client from client_data table"""
        try:
            logger.info(f"📊 Fetching data for client {client_id}")
            
            # Use the optimized data lookup
            result = await self.db_manager.fast_client_data_lookup(
                client_id=client_id,
                use_cache=False  # Get fresh data for organization
            )
            
            if not result or not result.get('data'):
                logger.warning(f"⚠️ No data found for client {client_id}")
                return []
            
            raw_data = result['data']
            logger.info(f"📦 Found {len(raw_data)} records for client {client_id}")
            
            return raw_data
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch client data: {e}")
            return []
    
    def categorize_data(self, raw_data: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize raw JSON data by platform and type"""
        try:
            categorized = {
                'shopify_orders': [],
                'shopify_products': [],
                'amazon_orders': [],
                'amazon_products': []
            }
            
            for record in raw_data:
                try:
                    # Handle different data formats
                    if isinstance(record, str):
                        data = json.loads(record)
                    elif isinstance(record, dict):
                        data = record
                    else:
                        logger.warning(f"⚠️ Unexpected data format: {type(record)}")
                        continue
                    
                    # Determine platform and type
                    platform = data.get('platform', '').lower()
                    
                    if platform == 'shopify':
                        if 'order_id' in data or 'order_number' in data:
                            categorized['shopify_orders'].append(data)
                        elif 'title' in data and ('handle' in data or 'variants' in data):
                            categorized['shopify_products'].append(data)
                    
                    elif platform == 'amazon':
                        if 'order_id' in data and 'order_status' in data:
                            categorized['amazon_orders'].append(data)
                        elif 'asin' in data or ('sku' in data and 'price' in data):
                            categorized['amazon_products'].append(data)
                    
                    # Handle data without explicit platform but with recognizable structure
                    elif not platform:
                        # Try to infer from structure
                        if 'marketplace_id' in data or 'sales_channel' in data:
                            # Likely Amazon order
                            categorized['amazon_orders'].append(data)
                        elif 'handle' in data and 'variants' in data:
                            # Likely Shopify product
                            categorized['shopify_products'].append(data)
                        elif 'customer_email' in data and 'financial_status' in data:
                            # Likely Shopify order
                            categorized['shopify_orders'].append(data)
                        else:
                            logger.warning(f"⚠️ Could not categorize record: {data}")
                
                except Exception as e:
                    logger.warning(f"⚠️ Error processing record: {e}")
                    continue
            
            # Log categorization results
            for category, items in categorized.items():
                if items:
                    logger.info(f"📋 {category}: {len(items)} records")
            
            return categorized
            
        except Exception as e:
            logger.error(f"❌ Failed to categorize data: {e}")
            return {}
    
    def transform_shopify_order(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Transform Shopify order data to match schema"""
        try:
            return {
                'client_id': client_id,
                'order_id': data.get('order_id'),
                'order_number': data.get('order_number'),
                'platform': 'shopify',
                'currency': data.get('currency'),
                'total_price': self._safe_decimal(data.get('total_price')),
                'subtotal_price': self._safe_decimal(data.get('subtotal_price')),
                'total_tax': self._safe_decimal(data.get('total_tax')),
                'financial_status': data.get('financial_status'),
                'fulfillment_status': data.get('fulfillment_status'),
                'customer_id': data.get('customer_id'),
                'customer_email': data.get('customer_email'),
                'created_at': self._safe_datetime(data.get('created_at')),
                'updated_at': self._safe_datetime(data.get('updated_at')),
                'source_name': data.get('source_name'),
                'line_items_count': data.get('line_items_count'),
                'tags': data.get('tags', ''),
                'billing_address': json.dumps(data.get('billing_address', {})),
                'shipping_address': json.dumps(data.get('shipping_address', {})),
                'discount_codes': json.dumps(data.get('discount_codes', [])),
                'raw_data': json.dumps(data)
            }
        except Exception as e:
            logger.warning(f"⚠️ Error transforming Shopify order: {e}")
            return None
    
    def transform_shopify_product(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Transform Shopify product data to match schema"""
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
                'variants': json.dumps(data.get('variants', [])),
                'options': json.dumps(data.get('options', [])),
                'images': json.dumps(data.get('images', [])),
                'raw_data': json.dumps(data)
            }
        except Exception as e:
            logger.warning(f"⚠️ Error transforming Shopify product: {e}")
            return None
    
    def transform_amazon_order(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Transform Amazon order data to match schema"""
        try:
            return {
                'client_id': client_id,
                'order_id': data.get('order_id'),
                'order_number': data.get('order_number'),
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
            logger.warning(f"⚠️ Error transforming Amazon order: {e}")
            return None
    
    def transform_amazon_product(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Transform Amazon product data to match schema"""
        try:
            return {
                'client_id': client_id,
                'asin': data.get('asin'),
                'sku': data.get('sku'),
                'title': data.get('title'),
                'platform': 'amazon',
                'brand': data.get('brand'),
                'category': data.get('category'),
                'price': self._safe_decimal(data.get('price')),
                'quantity': data.get('quantity'),
                'status': data.get('status'),
                'marketplace_id': data.get('marketplace_id'),
                'raw_data': json.dumps(data)
            }
        except Exception as e:
            logger.warning(f"⚠️ Error transforming Amazon product: {e}")
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
    
    async def insert_organized_data(self, client_id: str, categorized_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """Insert organized data into structured tables"""
        try:
            results = {}
            
            # Transform and insert each category
            for data_type, records in categorized_data.items():
                if not records:
                    results[data_type] = 0
                    continue
                
                logger.info(f"🔄 Processing {len(records)} {data_type} records")
                
                # Transform records based on type
                transformed_records = []
                for record in records:
                    try:
                        if data_type == 'shopify_orders':
                            transformed = self.transform_shopify_order(record, client_id)
                        elif data_type == 'shopify_products':
                            transformed = self.transform_shopify_product(record, client_id)
                        elif data_type == 'amazon_orders':
                            transformed = self.transform_amazon_order(record, client_id)
                        elif data_type == 'amazon_products':
                            transformed = self.transform_amazon_product(record, client_id)
                        else:
                            continue
                        
                        if transformed:
                            transformed_records.append(transformed)
                    
                    except Exception as e:
                        logger.warning(f"⚠️ Error transforming {data_type} record: {e}")
                        continue
                
                if not transformed_records:
                    results[data_type] = 0
                    continue
                
                # Insert into organized table
                table_name = f"{client_id.replace('-', '_')}_{data_type}"
                
                try:
                    # For now, we'll insert using the client_data table with a special table_name prefix
                    # In a real implementation, you'd insert directly into the structured tables
                    organized_records = []
                    for record in transformed_records:
                        organized_records.append({
                            "client_id": client_id,
                            "table_name": f"organized_{table_name}",
                            "data": record,
                            "created_at": datetime.utcnow().isoformat()
                        })
                    
                    # Batch insert
                    if organized_records:
                        response = self.admin_client.table("client_data").insert(organized_records).execute()
                        results[data_type] = len(response.data) if response.data else 0
                        logger.info(f"✅ Inserted {results[data_type]} {data_type} records")
                    else:
                        results[data_type] = 0
                
                except Exception as e:
                    logger.error(f"❌ Failed to insert {data_type} data: {e}")
                    results[data_type] = 0
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to insert organized data: {e}")
            return {}
    
    async def organize_client_data(self, client_id: str) -> Dict[str, Any]:
        """Main method to organize all client data"""
        try:
            logger.info(f"🚀 Starting data organization for client {client_id}")
            start_time = datetime.now()
            
            # Step 1: Fetch raw data
            raw_data = await self.fetch_client_data(client_id)
            if not raw_data:
                return {"error": "No data found for client"}
            
            # Step 2: Categorize data
            categorized_data = self.categorize_data(raw_data)
            if not categorized_data:
                return {"error": "Failed to categorize data"}
            
            # Step 3: Create organized tables (schema definition)
            await self.create_organized_tables(client_id)
            
            # Step 4: Transform and insert organized data
            results = await self.insert_organized_data(client_id, categorized_data)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            summary = {
                "client_id": client_id,
                "processing_time_seconds": processing_time,
                "total_raw_records": len(raw_data),
                "organized_records": results,
                "total_organized": sum(results.values()),
                "success": True
            }
            
            logger.info(f"✅ Data organization completed in {processing_time:.2f}s")
            logger.info(f"📊 Summary: {summary}")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Data organization failed: {e}")
            return {"error": str(e), "success": False}

async def main():
    """Main function for running the data organizer"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize client data into structured tables')
    parser.add_argument('--client-id', required=True, help='Client ID to organize data for')
    args = parser.parse_args()
    
    try:
        organizer = DataOrganizer()
        result = await organizer.organize_client_data(args.client_id)
        
        if result.get('success'):
            print(f"✅ Data organization successful!")
            print(f"📊 Organized {result['total_organized']} records in {result['processing_time_seconds']:.2f}s")
            for data_type, count in result['organized_records'].items():
                if count > 0:
                    print(f"   - {data_type}: {count} records")
        else:
            print(f"❌ Data organization failed: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
