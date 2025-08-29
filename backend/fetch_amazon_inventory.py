#!/usr/bin/env python3
"""
Simple Amazon AWD Inventory Fetcher
==================================
Fetches AWD inventory from Amazon AWD API
and updates amazon_products table awd_inventory column per SKU.

Usage: python fetch_amazon_inventory.py --client-id <CLIENT_ID>
"""

import asyncio
import aiohttp
import json
import os
import logging
import sys
from typing import Dict, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AmazonInventoryFetcher:
    def __init__(self, client_id: str):
        self.client_id = client_id.replace('-', '_')
        self.table_name = f"{self.client_id}_amazon_products"
        self.credentials = self.load_credentials()
        self.supabase = self.init_supabase()
        
    def load_credentials(self) -> Dict:
        """Load Amazon credentials"""
        # Try credentials file first
        if os.path.exists('amazon_credentials.json'):
            with open('amazon_credentials.json', 'r') as f:
                return json.load(f)
        
        # Try environment variables
        return {
          
        }
    
    def init_supabase(self) -> Client:
        """Initialize Supabase client"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        logger.info(f"SUPABASE_URL loaded: {'✅' if supabase_url else '❌'}")
        logger.info(f"SUPABASE_KEY loaded: {'✅' if supabase_key else '❌'}")
        
        if not supabase_url or not supabase_key:
            logger.error("❌ Missing Supabase credentials!")
            logger.error("Make sure SUPABASE_URL and SUPABASE_ANON_KEY are set in your .env file")
            raise Exception("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        
        try:
            logger.info(f"Connecting to Supabase: {supabase_url[:50]}...")
            client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            raise
    
    async def get_access_token(self) -> str:
        """Get Amazon SP-API access token"""
        token_url = "https://api.amazon.com/auth/o2/token"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.credentials['refresh_token'],
            'client_id': self.credentials['access_key_id'],
            'client_secret': self.credentials['secret_access_key']
        }
        
        logger.info(f"Requesting access token with client_id: {self.credentials['access_key_id'][:20]}...")
        logger.info(f"Refresh token length: {len(self.credentials['refresh_token'])}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Successfully got access token")
                    return result['access_token']
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Token request failed: {response.status}")
                    logger.error(f"Error response: {error_text}")
                    
                    if response.status == 400:
                        if "invalid_grant" in error_text:
                            logger.error("🔑 REFRESH TOKEN IS EXPIRED OR INVALID!")
                            logger.error("="*60)
                            logger.error("💡 HOW TO FIX:")
                            logger.error("1. Go to Amazon Seller Central")
                            logger.error("2. Navigate to Apps & Services > Develop Apps")
                            logger.error("3. Find your SP-API app")
                            logger.error("4. Click 'Generate refresh token'")
                            logger.error("5. Update your credentials with the new refresh token")
                            logger.error("="*60)
                        elif "invalid_client" in error_text:
                            logger.error("🔑 Client ID or secret is invalid!")
                            logger.error("Check your access_key_id and secret_access_key")
                    
                    raise Exception(f"Failed to get access token: {response.status} - {error_text}")
    
    async def fetch_awd_inventory(self, access_token: str) -> Dict[str, int]:
        """Fetch AWD inventory from Amazon AWD API"""
        logger.info("Fetching AWD inventory...")
        
        url = "https://sellingpartnerapi-na.amazon.com/awd/2024-05-09/inventory"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'x-amz-access-token': access_token,
            'Content-Type': 'application/json'
        }
        
        params = {
            'marketplaceIds': ','.join(self.credentials['marketplace_ids'])
        }
        
        awd_inventory = {}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    for item in data.get('inventory', []):
                        sku = item.get('sku')
                        if sku:
                            # Get total onhand quantity from AWD inventory
                            total_onhand = item.get('totalOnhandQuantity', 0)
                            if total_onhand > 0:
                                awd_inventory[sku] = total_onhand
                                logger.info(f"SKU {sku}: AWD inventory = {total_onhand}")
                else:
                    logger.error(f"AWD inventory fetch failed: {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error details: {error_text}")
        
        logger.info(f"Fetched AWD inventory for {len(awd_inventory)} SKUs")
        return awd_inventory
    

    
    def test_db_connection(self):
        """Test database connection and table access"""
        try:
            logger.info(f"Testing connection to table: {self.table_name}")
            # Try to get count of records
            response = self.supabase.table(self.table_name).select('*', count='exact').limit(1).execute()
            count = response.count if hasattr(response, 'count') else len(response.data)
            logger.info(f"✅ Database connection successful. Table has {count} records")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            logger.error(f"Table: {self.table_name}")
            return False
    
    def get_skus_from_db(self) -> list:
        """Get all SKUs from amazon_products table"""
        try:
            response = self.supabase.table(self.table_name).select('sku').not_.is_('sku', 'null').execute()
            if response.data:
                skus = [row['sku'] for row in response.data if row['sku']]
                logger.info(f"Found {len(skus)} SKUs in database")
                return skus
            else:
                logger.warning("No SKUs found in database")
                return []
        except Exception as e:
            logger.error(f"Error fetching SKUs from database: {e}")
            logger.error(f"Table name: {self.table_name}")
            return []
    
    def update_inventory_columns(self, awd_inventory: Dict[str, int]):
        """Update awd_inventory column per SKU"""
        logger.info("Updating AWD inventory column...")
        
        if not awd_inventory:
            logger.warning("No AWD inventory data to update")
            return
        
        try:
            # Note: Make sure the 'awd_inventory' column exists in your Supabase table
            # You can add it manually in the Supabase dashboard or via SQL:
            # ALTER TABLE your_table_name ADD COLUMN awd_inventory integer;
            
            # Update AWD inventory per SKU
            updated_count = 0
            for sku, qty in awd_inventory.items():
                try:
                    response = self.supabase.table(self.table_name).update({'awd_inventory': qty}).eq('sku', sku).execute()
                    if response.data:
                        updated_count += 1
                        logger.info(f"Updated SKU {sku}: awd_inventory = {qty}")
                    else:
                        logger.warning(f"No rows updated for SKU: {sku}")
                except Exception as e:
                    logger.error(f"Failed to update SKU {sku}: {e}")
                    continue
            
            logger.info(f"✅ Successfully updated AWD inventory for {updated_count}/{len(awd_inventory)} SKUs")
            
        except Exception as e:
            logger.error(f"Error updating inventory columns: {e}")
            raise
    
    async def run(self):
        """Main execution function"""
        try:
            # Test database connection first
            if not self.test_db_connection():
                logger.error("❌ Database connection failed. Exiting.")
                return
            
            # Get access token
            access_token = await self.get_access_token()
            logger.info("Got Amazon access token")
            
            # Get SKUs from database
            skus = self.get_skus_from_db()
            
            if not skus:
                logger.error("❌ No SKUs found in database. Exiting.")
                return
            
            # Fetch AWD inventory
            awd_inventory = await self.fetch_awd_inventory(access_token)
            
            # Update database
            self.update_inventory_columns(awd_inventory)
            
            logger.info("✅ Inventory fetch and update completed!")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")

async def main():
    import sys
    
    if len(sys.argv) != 3 or sys.argv[1] != '--client-id':
        print("Usage: python fetch_amazon_inventory.py --client-id <CLIENT_ID>")
        sys.exit(1)
    
    client_id = sys.argv[2]
    fetcher = AmazonInventoryFetcher(client_id)
    await fetcher.run()

if __name__ == "__main__":
    asyncio.run(main())
