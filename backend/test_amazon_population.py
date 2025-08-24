"""
Test script for Amazon data population

This script tests the Amazon data population for client: 6ee35b37-57af-4b70-bc62-1eddf1d0fd15
"""

import asyncio
import logging
from populate_amazon_data import AmazonDataPopulator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_amazon_population():
    """Test Amazon data population for the specified client"""
    client_id = "6ee35b37-57af-4b70-bc62-1eddf1d0fd15"
    
    try:
        logger.info(f" Testing Amazon data population for client: {client_id}")
        
        # Initialize populator
        populator = AmazonDataPopulator()
        
        # Test 1: Check raw data availability
        logger.info(" Step 1: Checking raw data availability...")
        raw_data = await populator.fetch_client_data(client_id)
        logger.info(f" Found {len(raw_data)} raw records")
        
        if not raw_data:
            logger.warning(" No raw data found. Cannot proceed with population test.")
            return
        
        # Test 2: Extract Amazon data
        logger.info(" Step 2: Extracting Amazon data...")
        amazon_data = populator.extract_amazon_data(raw_data)
        logger.info(" Amazon data extraction results:")
        logger.info(f"   - Orders found: {len(amazon_data['orders'])}")
        logger.info(f"   - Products found: {len(amazon_data['products'])}")
        
        # Test 3: Full population process
        logger.info(" Step 3: Running full Amazon data population...")
        result = await populator.populate_amazon_data(client_id)
        
        if result.get('success'):
            logger.info(" Amazon data population test PASSED!")
            logger.info(f" Results:")
            logger.info(f"   - Processing time: {result.get('processing_time_seconds'):.2f}s")
            logger.info(f"   - Raw records processed: {result.get('raw_records_processed')}")
            logger.info(f"   - Amazon orders found: {result.get('amazon_orders_found')}")
            logger.info(f"   - Amazon products found: {result.get('amazon_products_found')}")
            logger.info(f"   - Orders inserted: {result.get('orders_inserted')}")
            logger.info(f"   - Products inserted: {result.get('products_inserted')}")
            logger.info(f"   - Total inserted: {result.get('total_inserted')}")
        else:
            logger.error(f" Amazon data population test FAILED: {result.get('error')}")
    
    except Exception as e:
        logger.error(f" Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_amazon_population())
