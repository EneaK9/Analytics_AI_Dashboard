#!/usr/bin/env python3
"""
Simple API Scope Test - Tests what we can access with real credentials
"""
import asyncio
import aiohttp
import json

async def test_shopify_scope_simple():
    """Simple test to see what Shopify endpoints we can access"""
    print("️ SIMPLE SHOPIFY API SCOPE TEST")
    print("=" * 40)
    
    # Your actual working credentials that successfully fetched 1002 orders + 55 products
    shop_domain = "20ebc4-9c.myshopify.com"
    access_token = "shpat_0ce95407e357a3c4c9689c6922f52f2"
    
    base_url = f"https://{shop_domain}/admin/api/2024-01"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    
    print(f" Testing shop: {shop_domain}")
    print(f" Using token: {access_token[:20]}...")
    
    # Test different endpoints to see what we can access
    test_endpoints = [
        ("/shop.json", "Shop Info", "Basic shop information"),
        ("/orders.json?limit=1", "Orders", "Access to order data"),
        ("/products.json?limit=1", "Products", "Access to product catalog"),
        ("/customers.json?limit=1", "Customers", "Access to customer data"),
        ("/inventory_items.json?limit=1", "Inventory", "Access to inventory"),
        ("/locations.json", "Locations", "Store locations"),
        ("/webhooks.json", "Webhooks", "Webhook management"),
        ("/themes.json", "Themes", "Theme access"),
        ("/reports.json", "Reports", "Built-in reports"),
        ("/analytics/reports/orders.json", "Analytics", "Analytics data"),
        ("/draft_orders.json?limit=1", "Draft Orders", "Draft orders"),
        ("/price_rules.json?limit=1", "Price Rules", "Discount rules"),
        ("/gift_cards.json?limit=1", "Gift Cards", "Gift card data"),
        ("/collects.json?limit=1", "Collections", "Product collections"),
    ]
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        print("\n TESTING API ENDPOINTS:")
        print("-" * 40)
        
        for endpoint, name, description in test_endpoints:
            try:
                url = f"{base_url}{endpoint}"
                async with session.get(url, headers=headers) as response:
                    status = response.status
                    
                    if status == 200:
                        try:
                            data = await response.json()
                            # Count items if it's a list endpoint
                            if isinstance(data, dict):
                                # Look for common list keys
                                data_key = None
                                for key in [name.lower(), name.lower().replace(' ', '_'), 'data']:
                                    if key in data:
                                        data_key = key
                                        break
                                
                                if data_key and isinstance(data[data_key], list):
                                    count = len(data[data_key])
                                    results[name] = f" GRANTED ({count} items)"
                                    print(f"   {name:15}  GRANTED - Found {count} items")
                                elif name == "Shop Info":
                                    shop_name = data.get('shop', {}).get('name', 'Unknown')
                                    results[name] = f" GRANTED (Shop: {shop_name})"
                                    print(f"   {name:15}  GRANTED - Shop: {shop_name}")
                                else:
                                    results[name] = " GRANTED"
                                    print(f"   {name:15}  GRANTED - {description}")
                            else:
                                results[name] = " GRANTED"
                                print(f"   {name:15}  GRANTED - {description}")
                        except:
                            results[name] = " GRANTED (No JSON)"
                            print(f"   {name:15}  GRANTED - {description}")
                    
                    elif status == 403:
                        results[name] = " FORBIDDEN"
                        print(f"   {name:15}  FORBIDDEN - No access granted")
                    
                    elif status == 401:
                        results[name] = " UNAUTHORIZED"
                        print(f"   {name:15}  UNAUTHORIZED - Invalid token")
                    
                    elif status == 404:
                        results[name] = " NOT FOUND"
                        print(f"   {name:15}  NOT FOUND - Endpoint doesn't exist")
                    
                    else:
                        results[name] = f" HTTP {status}"
                        print(f"   {name:15}  HTTP {status}")
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                results[name] = f" ERROR: {str(e)[:30]}"
                print(f"   {name:15}  ERROR: {str(e)[:30]}")
    
    # Summary
    print("\n PERMISSION SUMMARY:")
    print("-" * 40)
    
    granted = [name for name, status in results.items() if status.startswith("")]
    forbidden = [name for name, status in results.items() if status.startswith("")]
    
    print(f" GRANTED ACCESS ({len(granted)}):")
    for name in granted:
        print(f"   • {name}")
    
    if forbidden:
        print(f"\n NO ACCESS ({len(forbidden)}):")
        for name in forbidden:
            print(f"   • {name}")
    
    print(f"\n WHAT THIS MEANS:")
    print("   • We can only access the data marked as 'GRANTED'")
    print("   • This is determined by the API scopes you configured")
    print("   • We cannot access any data marked as 'FORBIDDEN'")
    print("   • All data access follows Shopify's rate limits")
    
    return results

async def analyze_data_we_can_collect():
    """Analyze what business insights we can provide"""
    print("\n\n DATA COLLECTION ANALYSIS")
    print("=" * 40)
    
    # Run the scope test
    permissions = await test_shopify_scope_simple()
    
    print("\n BUSINESS INSIGHTS WE CAN PROVIDE:")
    print("-" * 40)
    
    if permissions.get("Orders", "").startswith(""):
        print(" SALES & REVENUE ANALYTICS:")
        print("   • Total sales and revenue trends")
        print("   • Daily/weekly/monthly sales patterns")
        print("   • Average order value analysis")
        print("   • Payment method breakdown")
        print("   • Order status tracking")
        print("   • Geographic sales distribution")
        print("   • Seasonal trends and forecasting")
    
    if permissions.get("Products", "").startswith(""):
        print("\n️ PRODUCT PERFORMANCE:")
        print("   • Best-selling products")
        print("   • Product variant analysis")
        print("   • Inventory level tracking")
        print("   • Product category performance")
        print("   • Pricing strategy insights")
    
    if permissions.get("Customers", "").startswith(""):
        print("\n CUSTOMER ANALYTICS:")
        print("   • Customer lifetime value")
        print("   • Repeat purchase behavior")
        print("   • Customer segmentation")
        print("   • Acquisition vs retention metrics")
    else:
        print("\n CUSTOMER ANALYTICS:  NOT AVAILABLE")
        print("   • Customer data access not granted in API scopes")
    
    if permissions.get("Analytics", "").startswith(""):
        print("\n ADVANCED ANALYTICS:")
        print("   • Built-in Shopify analytics integration")
        print("   • Enhanced reporting capabilities")
        print("   • Cross-platform data correlation")
    
    print(f"\n PRIVACY & SECURITY:")
    print("   • We only access data explicitly granted through API scopes")
    print("   • No unauthorized data collection")
    print("   • All data encrypted in transit and storage")
    print("   • Data used solely for dashboard generation")

async def main():
    """Run the complete API scope test"""
    print(" SHOPIFY API SCOPE & PERMISSIONS TEST")
    print("=" * 50)
    print(" Testing what data we can access with your API credentials")
    print(" This shows exactly what permissions you've granted us")
    
    try:
        await analyze_data_we_can_collect()
        
        print("\n" + "=" * 50)
        print(" API SCOPE TEST COMPLETED")
        print("\n SUMMARY:")
        print("   • This test shows your exact API permissions")
        print("   • We can only access data you've explicitly allowed")
        print("   • No hidden or unauthorized data collection")
        print("   • Full transparency in data access")
        
    except Exception as e:
        print(f"\n Test failed: {e}")
        print("   Check your internet connection and API credentials")

if __name__ == "__main__":
    print(" Starting Shopify API Scope Test...")
    print("  This will make real API calls to test permissions")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test stopped by user")
    except Exception as e:
        print(f"\n Test error: {e}")
