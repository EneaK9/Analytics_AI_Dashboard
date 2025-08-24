"""
Test Script for Component-Specific Data Functions

This script tests the new component-specific data functions to ensure
they work correctly with date range filtering and different platforms.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from component_data_functions import component_data_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_component_data_functions():
    """Test the component data functions with various scenarios"""
    
    # Mock client ID (replace with actual client ID for testing)
    test_client_id = "test_client_123"
    
    # Test date ranges
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    print(f" Testing Component Data Functions")
    print(f" Date Range: {start_date_str} to {end_date_str}")
    print(f" Client ID: {test_client_id}")
    print("=" * 60)
    
    # Test 1: Total Sales Data
    print("\n1️⃣ Testing Total Sales Data")
    print("-" * 40)
    
    try:
        # Test Shopify platform
        print("️ Testing Shopify total sales...")
        shopify_sales = await component_data_manager.get_total_sales_data(
            test_client_id, "shopify", start_date_str, end_date_str
        )
        print(f" Shopify Sales Result: {type(shopify_sales)}")
        if 'error' in shopify_sales:
            print(f" Shopify Error: {shopify_sales['error']}")
        else:
            print(f" Shopify Revenue: {shopify_sales.get('shopify', {}).get('total_sales_30_days', {}).get('revenue', 0)}")
        
        # Test Amazon platform
        print(" Testing Amazon total sales...")
        amazon_sales = await component_data_manager.get_total_sales_data(
            test_client_id, "amazon", start_date_str, end_date_str
        )
        print(f" Amazon Sales Result: {type(amazon_sales)}")
        if 'error' in amazon_sales:
            print(f" Amazon Error: {amazon_sales['error']}")
        else:
            print(f" Amazon Revenue: {amazon_sales.get('amazon', {}).get('total_sales_30_days', {}).get('revenue', 0)}")
        
        # Test Combined platform
        print(" Testing Combined total sales...")
        combined_sales = await component_data_manager.get_total_sales_data(
            test_client_id, "combined", start_date_str, end_date_str
        )
        print(f" Combined Sales Result: {type(combined_sales)}")
        if 'error' in combined_sales:
            print(f" Combined Error: {combined_sales['error']}")
        else:
            print(f" Combined Revenue: {combined_sales.get('combined', {}).get('total_revenue', 0)}")
            
    except Exception as e:
        print(f" Total Sales Test Failed: {str(e)}")
    
    # Test 2: Inventory Levels Data
    print("\n2️⃣ Testing Inventory Levels Data")
    print("-" * 40)
    
    try:
        # Test Shopify inventory levels
        print("️ Testing Shopify inventory levels...")
        shopify_inventory = await component_data_manager.get_inventory_levels_data(
            test_client_id, "shopify", start_date_str, end_date_str
        )
        print(f" Shopify Inventory Result: {type(shopify_inventory)}")
        if 'error' in shopify_inventory:
            print(f" Shopify Error: {shopify_inventory['error']}")
        else:
            timeline_data = shopify_inventory.get('shopify', {}).get('inventory_levels_chart', [])
            print(f" Shopify Timeline Points: {len(timeline_data)}")
        
        # Test Amazon inventory levels
        print(" Testing Amazon inventory levels...")
        amazon_inventory = await component_data_manager.get_inventory_levels_data(
            test_client_id, "amazon", start_date_str, end_date_str
        )
        print(f" Amazon Inventory Result: {type(amazon_inventory)}")
        if 'error' in amazon_inventory:
            print(f" Amazon Error: {amazon_inventory['error']}")
        else:
            timeline_data = amazon_inventory.get('amazon', {}).get('inventory_levels_chart', [])
            print(f" Amazon Timeline Points: {len(timeline_data)}")
        
        # Test Combined inventory levels
        print(" Testing Combined inventory levels...")
        combined_inventory = await component_data_manager.get_inventory_levels_data(
            test_client_id, "combined", start_date_str, end_date_str
        )
        print(f" Combined Inventory Result: {type(combined_inventory)}")
        if 'error' in combined_inventory:
            print(f" Combined Error: {combined_inventory['error']}")
        else:
            timeline_data = combined_inventory.get('combined', {}).get('inventory_levels_chart', [])
            print(f" Combined Timeline Points: {len(timeline_data)}")
            
    except Exception as e:
        print(f" Inventory Levels Test Failed: {str(e)}")
    
    # Test 3: Inventory Turnover Data
    print("\n3️⃣ Testing Inventory Turnover Data")
    print("-" * 40)
    
    try:
        print(" Testing Shopify inventory turnover...")
        shopify_turnover = await component_data_manager.get_inventory_turnover_data(
            test_client_id, "shopify", start_date_str, end_date_str
        )
        print(f" Shopify Turnover Result: {type(shopify_turnover)}")
        if 'error' in shopify_turnover:
            print(f" Shopify Error: {shopify_turnover['error']}")
        else:
            print(f" Shopify Turnover Ratio: {shopify_turnover.get('inventory_turnover_ratio', 0)}")
            
    except Exception as e:
        print(f" Inventory Turnover Test Failed: {str(e)}")
    
    # Test 4: Days of Stock Data
    print("\n4️⃣ Testing Days of Stock Data")
    print("-" * 40)
    
    try:
        print(" Testing Shopify days of stock...")
        shopify_days = await component_data_manager.get_days_of_stock_data(
            test_client_id, "shopify", start_date_str, end_date_str
        )
        print(f" Shopify Days Result: {type(shopify_days)}")
        if 'error' in shopify_days:
            print(f" Shopify Error: {shopify_days['error']}")
        else:
            print(f" Shopify Days of Stock: {shopify_days.get('avg_days_of_stock', 0)}")
            
    except Exception as e:
        print(f" Days of Stock Test Failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print(" Component Data Tests Completed!")
    print(" Note: Tests may show 'table not found' errors if using a mock client ID")
    print(" For full testing, use a real client ID with organized data tables")

def test_table_name_generation():
    """Test the table name generation logic"""
    print("\n Testing Table Name Generation")
    print("-" * 40)
    
    test_client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
    tables = component_data_manager._get_table_names(test_client_id)
    
    print(f"Client ID: {test_client_id}")
    print(f"Shopify Products Table: {tables['shopify_products']}")
    print(f"Shopify Orders Table: {tables['shopify_orders']}")
    print(f"Amazon Products Table: {tables['amazon_products']}")
    print(f"Amazon Orders Table: {tables['amazon_orders']}")

def test_date_parsing():
    """Test the date parsing functionality"""
    print("\n Testing Date Parsing")
    print("-" * 40)
    
    test_dates = [
        "2025-01-15",
        "2025-01-15T10:30:00Z",
        "2025-01-15T10:30:00.000Z",
        "invalid_date",
        None
    ]
    
    for date_str in test_dates:
        parsed = component_data_manager._parse_date(date_str)
        print(f"Input: {date_str} → Output: {parsed}")

if __name__ == "__main__":
    print(" Starting Component Data Function Tests")
    
    # Test utility functions
    test_table_name_generation()
    test_date_parsing()
    
    # Test main functionality
    try:
        asyncio.run(test_component_data_functions())
    except Exception as e:
        print(f" Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n All tests completed!")
