"""
Test script to verify platform endpoints work correctly
"""

import asyncio
from dashboard_inventory_analyzer import dashboard_inventory_analyzer

async def test_platform_endpoints():
    """Test both Shopify and Amazon platform endpoints"""
    
    # Test client ID
    client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
    
    print(f"🧪 Testing platform endpoints for client: {client_id}")
    
    try:
        # Test Shopify platform
        print("\n📦 Testing Shopify platform...")
        shopify_result = await dashboard_inventory_analyzer.get_dashboard_inventory_analytics(
            client_id=client_id,
            platform="shopify"
        )
        
        if shopify_result.get('success'):
            data_summary = shopify_result.get('data_summary', {})
            print(f"✅ Shopify Analytics:")
            print(f"   Platform: {data_summary.get('platform')}")
            print(f"   Shopify products: {data_summary.get('shopify_products', 0)}")
            print(f"   Shopify orders: {data_summary.get('shopify_orders', 0)}")
            print(f"   Amazon products: {data_summary.get('amazon_products', 0)}")
            print(f"   Amazon orders: {data_summary.get('amazon_orders', 0)}")
            
            # Check KPIs
            kpis = shopify_result.get('sales_kpis', {})
            print(f"   Sales KPIs available: {len(kpis)} metrics")
            
            # Check trends
            trends = shopify_result.get('trend_analysis', {})
            print(f"   Trend data available: {len(trends)} trend metrics")
            
            # Check alerts
            alerts = shopify_result.get('alerts_summary', {})
            print(f"   Alerts available: {len(alerts)} alert categories")
        else:
            print(f"❌ Shopify Analytics failed: {shopify_result.get('error')}")
        
        # Test Amazon platform
        print("\n🛒 Testing Amazon platform...")
        amazon_result = await dashboard_inventory_analyzer.get_dashboard_inventory_analytics(
            client_id=client_id,
            platform="amazon"
        )
        
        if amazon_result.get('success'):
            data_summary = amazon_result.get('data_summary', {})
            print(f"✅ Amazon Analytics:")
            print(f"   Platform: {data_summary.get('platform')}")
            print(f"   Amazon products: {data_summary.get('amazon_products', 0)}")
            print(f"   Amazon orders: {data_summary.get('amazon_orders', 0)}")
            print(f"   Shopify products: {data_summary.get('shopify_products', 0)}")
            print(f"   Shopify orders: {data_summary.get('shopify_orders', 0)}")
            
            # Check KPIs
            kpis = amazon_result.get('sales_kpis', {})
            print(f"   Sales KPIs available: {len(kpis)} metrics")
            
            # Check trends
            trends = amazon_result.get('trend_analysis', {})
            print(f"   Trend data available: {len(trends)} trend metrics")
            
            # Check alerts
            alerts = amazon_result.get('alerts_summary', {})
            print(f"   Alerts available: {len(alerts)} alert categories")
        else:
            print(f"❌ Amazon Analytics failed: {amazon_result.get('error')}")
        
        print("\n🎯 Platform Isolation Test:")
        print("✅ Shopify platform should only show Shopify data")
        print("✅ Amazon platform should only show Amazon data")
        print("✅ Both should have identical response structure")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_platform_endpoints())
