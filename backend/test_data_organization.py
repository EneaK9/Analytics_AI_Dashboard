"""
Test script for data organization functionality

This script tests the data organization for client ID: 3b619a14-3cd8-49fa-9c24-d8df5e54c452
"""

import asyncio
import logging
from data_organizer import DataOrganizer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_data_organization():
    """Test data organization for the specified client"""
    client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
    
    try:
        logger.info(f" Testing data organization for client: {client_id}")
        
        # Initialize organizer
        organizer = DataOrganizer()
        
        # Test 1: Check raw data availability
        logger.info(" Step 1: Checking raw data availability...")
        raw_data = await organizer.fetch_client_data(client_id)
        logger.info(f" Found {len(raw_data)} raw records")
        
        if not raw_data:
            logger.warning(" No raw data found. Cannot proceed with organization test.")
            return
        
        # Test 2: Categorize data
        logger.info(" Step 2: Categorizing data...")
        categorized = organizer.categorize_data(raw_data)
        logger.info(" Categorization results:")
        for category, items in categorized.items():
            logger.info(f"   - {category}: {len(items)} records")
        
        # Test 3: Full organization process
        logger.info(" Step 3: Running full data organization...")
        result = await organizer.organize_client_data(client_id)
        
        if result.get('success'):
            logger.info(" Data organization test PASSED!")
            logger.info(f" Results:")
            logger.info(f"   - Processing time: {result.get('processing_time_seconds'):.2f}s")
            logger.info(f"   - Total raw records: {result.get('total_raw_records')}")
            logger.info(f"   - Total organized: {result.get('total_organized')}")
            logger.info(f"   - Breakdown:")
            for data_type, count in result.get('organized_records', {}).items():
                if count > 0:
                    logger.info(f"     * {data_type}: {count} records")
        else:
            logger.error(f" Data organization test FAILED: {result.get('error')}")
    
    except Exception as e:
        logger.error(f" Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_data_organization())
