#!/usr/bin/env python3
"""
Debug script to understand why units sold extraction is returning 0.
This will help us see what data actually exists in the database.
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from component_data_functions import ComponentDataManager
from database_config import get_admin_client

async def debug_units_extraction():
    """Debug the units extraction process step by step"""
    print("🔍 Debugging Units Extraction Process")
    print("=" * 60)
    
    client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
    platform = "shopify"
    start_date = "2025-08-22"
    end_date = "2025-08-29"
    
    print(f"📊 Testing Parameters:")
    print(f"   Client ID: {client_id}")
    print(f"   Platform: {platform}")
    print(f"   Date Range: {start_date} to {end_date}")
    print()
    
    manager = ComponentDataManager()
    db_client = get_admin_client()
    
    try:
        # Step 1: Check table names
        print("1️⃣ Checking Table Names:")
        table_names = manager._get_table_names(client_id)
        print(f"   Table Names: {table_names}")
        print()
        
        # Step 2: Check if Shopify orders exist
        print("2️⃣ Checking Shopify Orders Table:")
        orders_table = table_names['shopify_orders']
        print(f"   Querying table: {orders_table}")
        
        # Query all orders for this client (no date filter first)
        all_orders_query = db_client.table(orders_table).select("*").eq('client_id', client_id).limit(5)
        all_orders_response = all_orders_query.execute()
        all_orders = all_orders_response.data or []
        
        print(f"   Total orders found (sample): {len(all_orders)}")
        
        if all_orders:
            print("   Sample order data:")
            for i, order in enumerate(all_orders[:2]):
                print(f"     Order {i+1}:")
                print(f"       order_id: {order.get('order_id')}")
                print(f"       created_at_shopify: {order.get('created_at_shopify')}")
                print(f"       financial_status: {order.get('financial_status')}")
                print(f"       fulfillment_status: {order.get('fulfillment_status')}")
                print(f"       total_price: {order.get('total_price')}")
                print(f"       Available fields: {list(order.keys())}")
                print()
        else:
            print("   ❌ No orders found in shopify_orders table!")
            return
        
        # Step 3: Check orders in date range
        print("3️⃣ Checking Orders in Date Range:")
        start_dt = manager._parse_date(start_date)
        end_dt = manager._parse_date(end_date)
        
        date_filtered_query = db_client.table(orders_table).select(
            "order_id, created_at_shopify, financial_status, fulfillment_status"
        ).eq('client_id', client_id)
        
        if start_dt:
            date_filtered_query = date_filtered_query.gte("created_at_shopify", start_dt.isoformat())
        if end_dt:
            date_filtered_query = date_filtered_query.lte("created_at_shopify", end_dt.isoformat())
            
        date_orders_response = date_filtered_query.execute()
        date_orders = date_orders_response.data or []
        
        print(f"   Orders in date range: {len(date_orders)}")
        
        if date_orders:
            print("   Orders in range:")
            for order in date_orders:
                print(f"     {order.get('order_id')}: {order.get('created_at_shopify')} - Financial: {order.get('financial_status')}, Fulfillment: {order.get('fulfillment_status')}")
        else:
            print("   ❌ No orders found in the specified date range!")
            print(f"   Date range: {start_dt.isoformat()} to {end_dt.isoformat()}")
            
            # Check what dates we actually have
            print("   Checking actual order dates...")
            actual_dates_query = db_client.table(orders_table).select("created_at_shopify").eq('client_id', client_id).limit(10)
            actual_dates_response = actual_dates_query.execute()
            actual_dates = actual_dates_response.data or []
            
            print("   Sample actual order dates:")
            for order in actual_dates[:5]:
                print(f"     {order.get('created_at_shopify')}")
            return
        
        # Step 4: Check fulfilled orders
        print("4️⃣ Checking Fulfilled Orders:")
        fulfilled_orders = []
        for order in date_orders:
            financial_status = (order.get('financial_status', '') or '').lower()
            fulfillment_status = (order.get('fulfillment_status', '') or '').lower()
            
            print(f"   Order {order.get('order_id')}: financial='{financial_status}', fulfillment='{fulfillment_status}'")
            
            if financial_status == 'paid' and fulfillment_status == 'fulfilled':
                fulfilled_orders.append(order)
                print(f"     ✅ FULFILLED!")
            else:
                print(f"     ❌ Not fulfilled")
        
        print(f"   Fulfilled orders: {len(fulfilled_orders)}")
        
        if not fulfilled_orders:
            print("   ❌ No fulfilled orders found!")
            return
        
        # Step 5: Check order items
        print("5️⃣ Checking Order Items:")
        order_items_table = table_names['shopify_order_items']
        fulfilled_order_ids = [order['order_id'] for order in fulfilled_orders]
        
        print(f"   Querying table: {order_items_table}")
        print(f"   For order IDs: {fulfilled_order_ids}")
        
        items_query = db_client.table(order_items_table).select(
            "order_id, quantity, sku, product_id"
        ).eq('client_id', client_id).in_('order_id', fulfilled_order_ids)
        
        items_response = items_query.execute()
        items = items_response.data or []
        
        print(f"   Order items found: {len(items)}")
        
        if items:
            total_quantity = 0
            for item in items:
                quantity = item.get('quantity', 0)
                total_quantity += int(quantity) if quantity else 0
                print(f"     Order {item.get('order_id')}: quantity={quantity}, sku={item.get('sku')}")
            
            print(f"   🎯 TOTAL UNITS SOLD: {total_quantity}")
        else:
            print("   ❌ No order items found!")
            
            # Check if order items table has any data at all
            print("   Checking if order items table has any data...")
            any_items_query = db_client.table(order_items_table).select("*").eq('client_id', client_id).limit(5)
            any_items_response = any_items_query.execute()
            any_items = any_items_response.data or []
            
            if any_items:
                print(f"   Order items table has {len(any_items)} items (sample):")
                for item in any_items[:2]:
                    print(f"     {item}")
            else:
                print("   ❌ Order items table is empty for this client!")
        
        # Step 6: Test the actual method
        print("6️⃣ Testing Actual Method:")
        units_sold = await manager._get_units_sold_in_period(client_id, platform, start_date, end_date)
        print(f"   _get_units_sold_in_period returned: {units_sold}")
        
    except Exception as e:
        print(f"❌ Error during debugging: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Run the debug process"""
    await debug_units_extraction()

if __name__ == "__main__":
    asyncio.run(main())
