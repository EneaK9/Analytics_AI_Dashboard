"""
Test script for enhanced inventory analytics with Shopify orders included

This script tests the complete enhanced inventory analytics system
"""

import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_inventory_analytics():
    """Test the enhanced inventory analytics with all organized tables"""
    
    # Test clients
    clients = {
        "Shopify Client": "3b619a14-3cd8-49fa-9c24-d8df5e54c452",
        "Amazon Client": "6ee35b37-57af-4b70-bc62-1eddf1d0fd15"
    }
    
    try:
        from organized_inventory_analyzer import organized_inventory_analyzer
        
        for client_name, client_id in clients.items():
            print(f"\n{'='*60}")
            print(f"🧪 Testing Enhanced Analytics for {client_name}")
            print(f"Client ID: {client_id}")
            print("="*60)
            
            # Test the enhanced analyzer
            logger.info(f"🚀 Running enhanced inventory analysis for {client_name}")
            result = await organized_inventory_analyzer.analyze_client_inventory(client_id)
            
            if result.get('success'):
                print("✅ Enhanced inventory analytics successful!")
                
                # Print data sources
                data_sources = result.get("data_sources", {})
                print(f"\n📦 Data Sources:")
                for source, count in data_sources.items():
                    print(f"   - {source}: {count} records")
                
                total_records = sum(data_sources.values())
                print(f"   - TOTAL: {total_records} records")
                
                # Print inventory KPIs
                inventory_kpis = result.get("inventory_kpis", {})
                if inventory_kpis and not inventory_kpis.get("error"):
                    print(f"\n💰 Inventory KPIs:")
                    print(f"   - Total inventory units: {inventory_kpis.get('total_inventory_units'):,}")
                    print(f"   - Total inventory value: ${inventory_kpis.get('total_inventory_value'):,.2f}")
                    print(f"   - Total unique SKUs: {inventory_kpis.get('total_unique_skus')}")
                    print(f"   - Low stock items: {inventory_kpis.get('low_stock_count')}")
                    
                    # Platform breakdown
                    shopify_kpis = inventory_kpis.get('shopify', {})
                    amazon_kpis = inventory_kpis.get('amazon', {})
                    
                    if shopify_kpis:
                        print(f"   - Shopify: {shopify_kpis.get('total_units'):,} units, ${shopify_kpis.get('total_value'):,.2f} value")
                    if amazon_kpis:
                        print(f"   - Amazon: {amazon_kpis.get('total_units'):,} units, ${amazon_kpis.get('total_value'):,.2f} value")
                
                # Print sales KPIs
                sales_kpis = result.get("sales_kpis", {})
                if sales_kpis and not sales_kpis.get("error"):
                    print(f"\n📈 Sales KPIs:")
                    print(f"   - Total orders: {sales_kpis.get('total_orders'):,}")
                    print(f"   - Total revenue: ${sales_kpis.get('total_revenue'):,.2f}")
                    print(f"   - Avg order value: ${sales_kpis.get('avg_order_value'):,.2f}")
                    
                    # Platform breakdown
                    shopify_sales = sales_kpis.get('shopify', {})
                    amazon_sales = sales_kpis.get('amazon', {})
                    
                    if shopify_sales and shopify_sales.get('orders', 0) > 0:
                        print(f"   - Shopify: {shopify_sales.get('orders')} orders, ${shopify_sales.get('revenue'):,.2f} revenue")
                    if amazon_sales and amazon_sales.get('orders', 0) > 0:
                        print(f"   - Amazon: {amazon_sales.get('orders')} orders, ${amazon_sales.get('revenue'):,.2f} revenue")
                        print(f"   - Amazon Premium: {amazon_sales.get('premium_orders_ratio')}% of orders")
                    
                    # Recent performance
                    recent = sales_kpis.get('recent_30_days', {})
                    if recent:
                        print(f"   - Last 30 days: {recent.get('total_orders')} orders, ${recent.get('total_revenue'):,.2f} revenue")
                
                # Print trend analysis
                trends = result.get("trend_analysis", {})
                monthly_trends = trends.get("monthly_trends", [])
                if monthly_trends:
                    print(f"\n📊 Recent Trends:")
                    for trend in monthly_trends[-3:]:  # Show last 3 months
                        print(f"   - {trend.get('month')}: {trend.get('total_orders')} orders, ${trend.get('total_revenue'):,.2f} revenue")
                        if trend.get('shopify_orders', 0) > 0:
                            print(f"     * Shopify: {trend.get('shopify_orders')} orders, ${trend.get('shopify_revenue'):,.2f}")
                        if trend.get('amazon_orders', 0) > 0:
                            print(f"     * Amazon: {trend.get('amazon_orders')} orders, ${trend.get('amazon_revenue'):,.2f}")
                        print(f"     * Growth: {trend.get('growth_rate')}%")
                
                # Print alerts summary
                alerts = result.get("alerts", [])
                if alerts:
                    print(f"\n🚨 Alerts ({len(alerts)}):")
                    for alert in alerts[:5]:  # Show first 5 alerts
                        severity = alert.get('severity', 'info').upper()
                        platform = alert.get('platform', 'unknown').upper()
                        print(f"   - [{severity}] [{platform}] {alert.get('title')}")
                
                # Print top products summary
                top_products = result.get("top_products", {})
                shopify_top = top_products.get("shopify_top_by_value", [])
                amazon_top = top_products.get("amazon_top_by_price", [])
                
                if shopify_top:
                    print(f"\n🏆 Top Shopify Products (by inventory value):")
                    for i, product in enumerate(shopify_top[:3], 1):
                        print(f"   {i}. {product.get('title')} - ${product.get('total_value'):,.2f} ({product.get('inventory')} units)")
                
                if amazon_top:
                    print(f"\n🏆 Top Amazon Products (by price):")
                    for i, product in enumerate(amazon_top[:3], 1):
                        print(f"   {i}. {product.get('title')} - ${product.get('price'):,.2f}")
                
                # Print low stock summary
                low_stock = result.get("low_stock_alerts", [])
                if low_stock:
                    critical_items = [item for item in low_stock if item.get('urgency') == 'critical']
                    high_items = [item for item in low_stock if item.get('urgency') == 'high']
                    
                    print(f"\n⚠️  Low Stock Summary:")
                    print(f"   - Critical (0 units): {len(critical_items)} items")
                    print(f"   - High priority (<3 units): {len(high_items)} items")
                    print(f"   - Total low stock: {len(low_stock)} items")
                
            else:
                print(f"❌ Enhanced inventory analytics failed for {client_name}")
                print(f"Error: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

async def test_data_population():
    """Test populating Shopify orders data"""
    print("\n" + "="*60)
    print("🔧 Testing Shopify Orders Population")
    print("="*60)
    
    try:
        from populate_shopify_orders import ShopifyOrdersPopulator
        
        client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"  # Shopify client
        
        populator = ShopifyOrdersPopulator()
        result = await populator.populate_shopify_orders(client_id)
        
        if result.get('success'):
            print("✅ Shopify orders population successful!")
            print(f"📊 Results:")
            print(f"   - Raw records processed: {result['raw_records_processed']}")
            print(f"   - Shopify orders found: {result['shopify_orders_found']}")
            print(f"   - Orders inserted: {result['orders_inserted']}")
            print(f"   - Processing time: {result['processing_time_seconds']:.2f}s")
        else:
            print(f"❌ Shopify orders population failed: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Population test failed: {e}")

async def main():
    """Main test function"""
    print("🧪 Enhanced Inventory Analytics Test Suite")
    print("=" * 80)
    
    print("\nChoose test mode:")
    print("1. Test enhanced analytics only")
    print("2. Test Shopify orders population only") 
    print("3. Test population then analytics (full test)")
    
    try:
        choice = input("\nEnter choice (1, 2, or 3): ").strip()
        
        if choice == "1":
            await test_enhanced_inventory_analytics()
        elif choice == "2":
            await test_data_population()
        elif choice == "3":
            print("\n🔧 Running full test suite...")
            await test_data_population()
            await test_enhanced_inventory_analytics()
        else:
            print("Invalid choice. Running enhanced analytics test...")
            await test_enhanced_inventory_analytics()
    
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
