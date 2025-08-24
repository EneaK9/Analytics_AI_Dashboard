"""
Test script to verify Amazon platform switching functionality
"""

import asyncio
import json
from database import get_admin_client
from dashboard_inventory_analyzer import dashboard_inventory_analyzer

async def test_amazon_platform():
    """Test Amazon platform functionality"""
    
    # Test client ID (replace with actual client ID)
    client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
    
    print(f" Testing platform switching for client: {client_id}")
    
    # Test 1: Shopify platform
    print("\n Testing Shopify platform...")
    shopify_result = await dashboard_inventory_analyzer.get_dashboard_inventory_analytics(
        client_id=client_id,
        platform="shopify"
    )
    
    shopify_products = shopify_result.get('data_summary', {}).get('shopify_products', 0)
    shopify_orders = shopify_result.get('data_summary', {}).get('shopify_orders', 0)
    amazon_products = shopify_result.get('data_summary', {}).get('amazon_products', 0)
    amazon_orders = shopify_result.get('data_summary', {}).get('amazon_orders', 0)
    
    print(f" Shopify result: {shopify_products} products, {shopify_orders} orders")
    print(f"   Amazon data should be 0: {amazon_products} products, {amazon_orders} orders")
    
    # Test 2: Amazon platform
    print("\n Testing Amazon platform...")
    amazon_result = await dashboard_inventory_analyzer.get_dashboard_inventory_analytics(
        client_id=client_id,
        platform="amazon"
    )
    
    amazon_products = amazon_result.get('data_summary', {}).get('amazon_products', 0)
    amazon_orders = amazon_result.get('data_summary', {}).get('amazon_orders', 0)
    shopify_products = amazon_result.get('data_summary', {}).get('shopify_products', 0)
    shopify_orders = amazon_result.get('data_summary', {}).get('shopify_orders', 0)
    
    print(f" Amazon result: {amazon_products} products, {amazon_orders} orders")
    print(f"   Shopify data should be 0: {shopify_products} products, {shopify_orders} orders")
    
    # Test 3: Check Amazon tables existence
    print("\n Checking Amazon table existence...")
    admin_client = get_admin_client()
    
    amazon_products_table = f"{client_id.replace('-', '_')}_amazon_products"
    amazon_orders_table = f"{client_id.replace('-', '_')}_amazon_orders"
    
    try:
        products_check = admin_client.table(amazon_products_table).select("id").limit(1).execute()
        print(f" Amazon products table exists: {len(products_check.data)} records found")
    except Exception as e:
        print(f" Amazon products table not found: {e}")
    
    try:
        orders_check = admin_client.table(amazon_orders_table).select("id").limit(1).execute()
        print(f" Amazon orders table exists: {len(orders_check.data)} records found")
    except Exception as e:
        print(f" Amazon orders table not found: {e}")
    
    # Print KPIs comparison
    print("\n Sales KPIs Comparison:")
    print("Shopify Platform:")
    shopify_kpis = shopify_result.get('sales_kpis', {})
    print(f"  7-day sales: {shopify_kpis.get('total_sales_7_days', {})}")
    print(f"  30-day sales: {shopify_kpis.get('total_sales_30_days', {})}")
    
    print("Amazon Platform:")
    amazon_kpis = amazon_result.get('sales_kpis', {})
    print(f"  7-day sales: {amazon_kpis.get('total_sales_7_days', {})}")
    print(f"  30-day sales: {amazon_kpis.get('total_sales_30_days', {})}")

if __name__ == "__main__":
    asyncio.run(test_amazon_platform())
