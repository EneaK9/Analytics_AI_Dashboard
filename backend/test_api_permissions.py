#!/usr/bin/env python3
"""
API Permissions & Data Access Test

This script tests what data we can actually access with the provided API credentials.
It will show you exactly what the client has given us permission to access.
"""
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_shopify_permissions():
    """Test what data we can access from Shopify with current credentials"""
    print("\n️ SHOPIFY API PERMISSIONS TEST")
    print("=" * 50)
    
    # Using the actual working credentials from your successful integration
    test_credentials = {
        "shop_domain": "20ebc4-9c.myshopify.com",  # Your shop domain
        "access_token": "shpat_0ce95407e357a3c4c9689c6922f52f2"  # Your working access token
    }
    
    print(f" Shop Domain: {test_credentials['shop_domain']}")
    print(f" Access Token: {test_credentials['access_token'][:20]}...")
    
    try:
        from api_connectors import ShopifyConnector
        from models import ShopifyCredentials
        
        # Create credentials object
        creds = ShopifyCredentials(**test_credentials)
        connector = ShopifyConnector(creds)
        
        # Test 1: Basic Connection & Shop Info
        print("\n1️⃣ Testing Basic Connection...")
        success, message = await connector.test_connection()
        print(f"   Connection Status: {' SUCCESS' if success else ' FAILED'}")
        print(f"   Message: {message}")
        
        if not success:
            print("    Cannot continue without valid connection")
            return
        
        # Test 2: Check Available Scopes/Permissions
        print("\n2️⃣ Testing API Permissions...")
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Test different endpoints to see what we can access
            endpoints_to_test = [
                ("/shop.json", "Shop Information"),
                ("/orders.json?limit=1", "Orders Access"),
                ("/products.json?limit=1", "Products Access"),
                ("/customers.json?limit=1", "Customers Access"),
                ("/inventory_items.json?limit=1", "Inventory Access"),
                ("/locations.json", "Locations Access"),
                ("/reports.json", "Reports Access"),
                ("/analytics/reports/orders.json", "Analytics Access"),
            ]
            
            permissions = {}
            
            for endpoint, description in endpoints_to_test:
                try:
                    url = f"{connector.base_url}{endpoint}"
                    async with session.get(url, headers=connector.headers) as response:
                        if response.status == 200:
                            permissions[description] = " GRANTED"
                            print(f"   {description}:  GRANTED")
                        elif response.status == 403:
                            permissions[description] = " FORBIDDEN"
                            print(f"   {description}:  FORBIDDEN")
                        elif response.status == 401:
                            permissions[description] = " UNAUTHORIZED"
                            print(f"   {description}:  UNAUTHORIZED")
                        else:
                            permissions[description] = f" HTTP {response.status}"
                            print(f"   {description}:  HTTP {response.status}")
                except Exception as e:
                    permissions[description] = f" ERROR: {str(e)[:50]}"
                    print(f"   {description}:  ERROR: {str(e)[:50]}")
        
        # Test 3: Sample Data Retrieval
        print("\n3️⃣ Testing Data Retrieval...")
        
        if permissions.get("Orders Access") == " GRANTED":
            print("    Testing Orders Data...")
            try:
                # Fetch just a few orders for testing
                orders = await connector.fetch_orders(days_back=7)  # Last 7 days
                print(f"    Successfully retrieved {len(orders)} orders from last 7 days")
                
                if orders:
                    sample_order = orders[0]
                    print(f"    Sample Order Fields Available:")
                    for key, value in sample_order.items():
                        value_preview = str(value)[:30] + "..." if len(str(value)) > 30 else str(value)
                        print(f"      • {key}: {value_preview}")
                else:
                    print("    No orders found in the last 7 days")
                    
            except Exception as e:
                print(f"    Orders retrieval failed: {str(e)[:100]}")
        
        if permissions.get("Products Access") == " GRANTED":
            print("   ️ Testing Products Data...")
            try:
                # Fetch just a few products for testing
                products = await connector.fetch_products()
                print(f"    Successfully retrieved {len(products)} products")
                
                if products:
                    sample_product = products[0]
                    print(f"    Sample Product Fields Available:")
                    for key, value in sample_product.items():
                        if key == 'variants' and isinstance(value, list) and value:
                            print(f"      • {key}: [{len(value)} variants] - {list(value[0].keys()) if value else 'empty'}")
                        else:
                            value_preview = str(value)[:30] + "..." if len(str(value)) > 30 else str(value)
                            print(f"      • {key}: {value_preview}")
                else:
                    print("    No products found")
                    
            except Exception as e:
                print(f"    Products retrieval failed: {str(e)[:100]}")
        
        # Test 4: Rate Limits
        print("\n4️⃣ Testing Rate Limits...")
        print(f"   Current Rate Limit: {connector.rate_limit_remaining} requests/second")
        print("    Note: Shopify allows 40 requests per second (burst)")
        
        return permissions
        
    except ImportError as e:
        print(f" Cannot import required modules: {e}")
        print("   This test needs to run in the backend environment with dependencies installed")
        return None
    except Exception as e:
        print(f" Unexpected error: {e}")
        return None

async def test_amazon_permissions():
    """Test what data we can access from Amazon with current credentials"""
    print("\n AMAZON SP-API PERMISSIONS TEST")
    print("=" * 50)
    
    print(" Amazon SP-API requires specific setup:")
    print("   • SP-API access approval from Amazon")
    print("   • AWS IAM user with proper permissions")
    print("   • LWA (Login with Amazon) refresh token")
    print("   • Marketplace IDs for regions you want to access")
    
    # Note: Amazon credentials would be more complex
    print("\n Required Amazon Credentials:")
    print("   • Seller ID")
    print("   • Marketplace IDs (e.g., ATVPDKIKX0DER for US)")
    print("   • AWS Access Key ID")
    print("   • AWS Secret Access Key")
    print("   • LWA Refresh Token")
    print("   • AWS Region")
    
    print("\n Amazon API Endpoints We Would Test:")
    print("   • /sellers/v1/marketplaceParticipations (Connection test)")
    print("   • /orders/v0/orders (Orders data)")
    print("   • /catalog/v0/items (Product catalog)")
    print("   • /reports/2021-06-30/reports (Reports access)")
    print("   • /finances/v0/financialEvents (Financial data)")
    
    print("\n Note: Amazon SP-API has strict rate limits:")
    print("   • Different limits per endpoint")
    print("   • Usually 0.0167 to 1 request per second")
    print("   • Burst capacity available for some endpoints")
    
    return None

async def test_data_scope_analysis():
    """Analyze what kind of business insights we can provide with the available data"""
    print("\n DATA SCOPE & BUSINESS INSIGHTS ANALYSIS")
    print("=" * 50)
    
    # Test with actual Shopify permissions
    shopify_permissions = await test_shopify_permissions()
    amazon_permissions = await test_amazon_permissions()
    
    print("\n BUSINESS INSIGHTS WE CAN PROVIDE:")
    print("-" * 40)
    
    if shopify_permissions:
        if shopify_permissions.get("Orders Access") == " GRANTED":
            print(" SALES ANALYTICS:")
            print("   • Total revenue and sales trends")
            print("   • Order volume patterns")
            print("   • Average order value")
            print("   • Customer purchase behavior")
            print("   • Payment method preferences")
            print("   • Geographic sales distribution")
            print("   • Seasonal trends and patterns")
        
        if shopify_permissions.get("Products Access") == " GRANTED":
            print("\n️ PRODUCT ANALYTICS:")
            print("   • Product performance metrics")
            print("   • Inventory levels and trends")
            print("   • Variant analysis")
            print("   • Category performance")
            print("   • Pricing optimization insights")
        
        if shopify_permissions.get("Customers Access") == " GRANTED":
            print("\n CUSTOMER ANALYTICS:")
            print("   • Customer lifetime value")
            print("   • Retention rates")
            print("   • Customer segmentation")
            print("   • Purchase frequency analysis")
        else:
            print("\n CUSTOMER ANALYTICS:  NOT AVAILABLE")
            print("   • Customer data access not granted")
    
    print("\n PRIVACY & SECURITY NOTES:")
    print("   • We only access data explicitly granted by API scopes")
    print("   • All data is encrypted in transit and at rest")
    print("   • No personal customer information is stored unnecessarily")
    print("   • Data is used only for dashboard generation")

async def main():
    """Run comprehensive API permissions test"""
    print(" API PERMISSIONS & DATA ACCESS TEST")
    print("=" * 60)
    print(f" Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n PURPOSE:")
    print("   This test shows exactly what data we can access with your API credentials.")
    print("   It helps ensure transparency about data permissions and access scope.")
    
    await test_data_scope_analysis()
    
    print("\n" + "=" * 60)
    print(" API PERMISSIONS TEST COMPLETED")
    print("\n KEY TAKEAWAYS:")
    print("   • We only access data you've explicitly granted permission for")
    print("   • API scopes determine what data types are available")
    print("   • All data access follows platform rate limits and best practices")
    print("   • You maintain full control over data access permissions")

if __name__ == "__main__":
    print(" Running API Permissions Test...")
    print("  Note: This test requires the backend environment with all dependencies")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n Test failed: {e}")
        print("   Make sure you're running this in the backend directory with dependencies installed")
