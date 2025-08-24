"""
Enhanced Data Organizer that inserts into actual separate tables

This version assumes the tables have been created manually in Supabase
"""

import asyncio
from data_organizer import DataOrganizer
import logging

logger = logging.getLogger(__name__)

class EnhancedDataOrganizer(DataOrganizer):
    """Enhanced organizer that inserts into actual separate tables"""
    
    async def insert_organized_data(self, client_id: str, categorized_data):
        """Insert organized data into actual separate tables"""
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
    """Test the enhanced organizer"""
    client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
    
    try:
        logger.info(" Testing Enhanced Data Organizer (separate tables)")
        
        organizer = EnhancedDataOrganizer()
        result = await organizer.organize_client_data(client_id)
        
        if result.get('success'):
            print(" Enhanced data organization successful!")
            print(f" Results: {result}")
        else:
            print(f" Enhanced organization failed: {result.get('error')}")
    
    except Exception as e:
        print(f" Error: {e}")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
