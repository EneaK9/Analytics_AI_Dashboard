"""
Test script for organized inventory analytics API endpoints

This script tests the new organized inventory analytics endpoints
"""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_BASE_URL = "http://localhost:8000"
CLIENT_ID_SHOPIFY = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"  # Shopify client
CLIENT_ID_AMAZON = "6ee35b37-57af-4b70-bc62-1eddf1d0fd15"   # Amazon client

# You'll need to get an actual client token by logging in first
CLIENT_TOKEN = None  # Will be obtained from login

async def get_client_token():
    """Get client token by logging in"""
    async with aiohttp.ClientSession() as session:
        # You'll need actual client credentials
        login_data = {
            "email": "test@example.com",  # Replace with actual client email
            "password": "password123"     # Replace with actual client password
        }
        
        async with session.post(f"{API_BASE_URL}/api/auth/login", json=login_data) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("access_token")
            else:
                print(f" Login failed: {response.status}")
                text = await response.text()
                print(f"Error: {text}")
                return None

async def test_data_health_check(token: str, client_id: str):
    """Test data health check endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}/api/dashboard/client-data-health/{client_id}"
        
        print(f" Testing data health check for client {client_id}...")
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                print(" Data health check successful!")
                print(f" Summary:")
                summary = result.get("summary", {})
                print(f"   - Existing tables: {summary.get('existing_tables')}/{summary.get('total_tables')}")
                print(f"   - Total records: {summary.get('total_records')}")
                print(f"   - Is organized: {summary.get('is_organized')}")
                
                tables = result.get("tables", {})
                for table_name, table_info in tables.items():
                    if table_info.get("exists"):
                        print(f"   - {table_name}: {table_info.get('count')} records")
                    else:
                        print(f"   - {table_name}: NOT EXISTS")
                
                return result
            else:
                print(f" Data health check failed: {response.status}")
                text = await response.text()
                print(f"Error: {text}")
                return None

async def test_organized_inventory_analytics(token: str, client_id: str):
    """Test organized inventory analytics endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}/api/dashboard/organized-inventory-analytics/{client_id}"
        
        print(f" Testing organized inventory analytics for client {client_id}...")
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                print(" Organized inventory analytics successful!")
                
                analytics = result.get("analytics", {})
                
                # Print data sources
                data_sources = analytics.get("data_sources", {})
                print(f" Data Sources:")
                for source, count in data_sources.items():
                    print(f"   - {source}: {count} records")
                
                # Print inventory KPIs
                inventory_kpis = analytics.get("inventory_kpis", {})
                if inventory_kpis:
                    print(f" Inventory KPIs:")
                    print(f"   - Total inventory units: {inventory_kpis.get('total_inventory_units')}")
                    print(f"   - Total inventory value: ${inventory_kpis.get('total_inventory_value'):,.2f}")
                    print(f"   - Total unique SKUs: {inventory_kpis.get('total_unique_skus')}")
                    print(f"   - Low stock items: {inventory_kpis.get('low_stock_count')}")
                
                # Print sales KPIs
                sales_kpis = analytics.get("sales_kpis", {})
                if sales_kpis.get("total_orders", 0) > 0:
                    print(f" Sales KPIs:")
                    print(f"   - Total orders: {sales_kpis.get('total_orders')}")
                    print(f"   - Total revenue: ${sales_kpis.get('total_revenue'):,.2f}")
                    print(f"   - Avg order value: ${sales_kpis.get('avg_order_value'):,.2f}")
                    print(f"   - Premium orders ratio: {sales_kpis.get('premium_orders_ratio')}%")
                
                # Print alerts
                alerts = analytics.get("alerts", [])
                if alerts:
                    print(f" Alerts ({len(alerts)}):")
                    for alert in alerts[:5]:  # Show first 5 alerts
                        print(f"   - {alert.get('severity', 'info').upper()}: {alert.get('title')}")
                
                # Print trend analysis
                trends = analytics.get("trend_analysis", {})
                monthly_trends = trends.get("monthly_trends", [])
                if monthly_trends:
                    print(f" Recent Trends:")
                    for trend in monthly_trends[-3:]:  # Show last 3 months
                        print(f"   - {trend.get('month')}: {trend.get('orders')} orders, ${trend.get('revenue'):,.2f} revenue, {trend.get('growth_rate')}% growth")
                
                return result
            else:
                print(f" Organized inventory analytics failed: {response.status}")
                text = await response.text()
                print(f"Error: {text}")
                return None

async def main():
    """Main test function"""
    print(" Testing Organized Inventory Analytics API")
    print("=" * 60)
    
    # For testing, we'll use a mock token or skip auth
    # In a real scenario, you'd get a proper token from login
    print(" Note: Using mock token for testing. In production, get a real token from login.")
    
    # Create a mock token for testing (you'll need to replace this with real auth)
    mock_token = "mock_token_for_testing"
    
    # Test both clients
    test_clients = [
        ("Shopify Client", CLIENT_ID_SHOPIFY),
        ("Amazon Client", CLIENT_ID_AMAZON)
    ]
    
    for client_name, client_id in test_clients:
        print(f"\n{'='*20} {client_name} {'='*20}")
        
        # Test data health check
        print(f"\n1. Testing data health check for {client_name}...")
        health_result = await test_data_health_check(mock_token, client_id)
        
        if health_result and health_result.get("summary", {}).get("is_organized"):
            # Test organized analytics
            print(f"\n2. Testing organized inventory analytics for {client_name}...")
            analytics_result = await test_organized_inventory_analytics(mock_token, client_id)
        else:
            print(f" Skipping analytics test - {client_name} data is not organized yet")

async def test_with_direct_database():
    """Test the analyzer directly without API"""
    print("\n Testing analyzer directly (bypassing API auth)...")
    
    try:
        from organized_inventory_analyzer import organized_inventory_analyzer
        
        # Test with Shopify client
        print(f"\n Testing Shopify client: {CLIENT_ID_SHOPIFY}")
        shopify_result = await organized_inventory_analyzer.analyze_client_inventory(CLIENT_ID_SHOPIFY)
        
        if shopify_result.get('success'):
            print(" Shopify analysis successful!")
            data_sources = shopify_result.get("data_sources", {})
            print(f"   Data sources: {data_sources}")
        else:
            print(f" Shopify analysis failed: {shopify_result.get('error')}")
        
        # Test with Amazon client
        print(f"\n Testing Amazon client: {CLIENT_ID_AMAZON}")
        amazon_result = await organized_inventory_analyzer.analyze_client_inventory(CLIENT_ID_AMAZON)
        
        if amazon_result.get('success'):
            print(" Amazon analysis successful!")
            data_sources = amazon_result.get("data_sources", {})
            print(f"   Data sources: {data_sources}")
        else:
            print(f" Amazon analysis failed: {amazon_result.get('error')}")
    
    except Exception as e:
        print(f" Direct test failed: {e}")

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. API endpoints (requires auth)")
    print("2. Direct database test (no auth needed)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(main())
    elif choice == "2":
        asyncio.run(test_with_direct_database())
    else:
        print("Invalid choice. Running direct database test...")
        asyncio.run(test_with_direct_database())
