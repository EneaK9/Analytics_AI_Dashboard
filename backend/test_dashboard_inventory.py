"""
Test script for dashboard inventory analytics

Tests the specific SKU lists, KPIs, trends, and alerts requested by the user
"""

import asyncio
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_dashboard_inventory_analytics():
    """Test the dashboard inventory analytics with specific data requirements"""
    
    # Test clients
    clients = {
        "Shopify Client": "3b619a14-3cd8-49fa-9c24-d8df5e54c452",
        "Amazon Client": "6ee35b37-57af-4b70-bc62-1eddf1d0fd15"
    }
    
    try:
        from dashboard_inventory_analyzer import dashboard_inventory_analyzer
        
        for client_name, client_id in clients.items():
            print(f"\n{'='*80}")
            print(f" Testing Dashboard Inventory Analytics for {client_name}")
            print(f"Client ID: {client_id}")
            print("="*80)
            
            # Test the dashboard analyzer
            logger.info(f" Running dashboard inventory analysis for {client_name}")
            result = await dashboard_inventory_analyzer.get_dashboard_inventory_analytics(client_id)
            
            if result.get('success'):
                print(" Dashboard inventory analytics successful!")
                
                # Test 1: SKU List
                sku_list = result.get("sku_list", [])
                print(f"\n SKU LIST ({len(sku_list)} items):")
                print("-" * 60)
                print(f"{'Item Name':<30} {'SKU':<15} {'On-Hand':<8} {'Outgoing':<8} {'Available':<8} {'Platform':<8}")
                print("-" * 60)
                
                for i, sku in enumerate(sku_list[:10]):  # Show first 10 items
                    name = sku.get('item_name', 'Unknown')[:29]
                    sku_code = sku.get('sku_code', 'N/A')[:14]
                    on_hand = sku.get('on_hand_inventory', 0)
                    outgoing = sku.get('outgoing_inventory', 0)
                    available = sku.get('current_availability', 0)
                    platform = sku.get('platform', 'N/A')
                    
                    print(f"{name:<30} {sku_code:<15} {on_hand:<8} {outgoing:<8} {available:<8} {platform:<8}")
                
                if len(sku_list) > 10:
                    print(f"... and {len(sku_list) - 10} more items")
                
                # Test 2: KPI Charts
                kpi_charts = result.get("kpi_charts", {})
                if kpi_charts and not kpi_charts.get("error"):
                    print(f"\n KPI CHARTS:")
                    print("-" * 40)
                    
                    sales_7d = kpi_charts.get('total_sales_7_days', {})
                    sales_30d = kpi_charts.get('total_sales_30_days', {})
                    sales_90d = kpi_charts.get('total_sales_90_days', {})
                    
                    print(f" Sales Performance:")
                    print(f"   • Last 7 days:  ${sales_7d.get('revenue', 0):,.2f} ({sales_7d.get('units', 0)} units, {sales_7d.get('orders', 0)} orders)")
                    print(f"   • Last 30 days: ${sales_30d.get('revenue', 0):,.2f} ({sales_30d.get('units', 0)} units, {sales_30d.get('orders', 0)} orders)")
                    print(f"   • Last 90 days: ${sales_90d.get('revenue', 0):,.2f} ({sales_90d.get('units', 0)} units, {sales_90d.get('orders', 0)} orders)")
                    
                    print(f"\n Inventory Metrics:")
                    print(f"   • Inventory Turnover Rate: {kpi_charts.get('inventory_turnover_rate', 0)}")
                    print(f"   • Days of Stock Remaining: {kpi_charts.get('days_stock_remaining', 'N/A')}")
                    print(f"   • Average Daily Sales: {kpi_charts.get('avg_daily_sales', 0)} units")
                    print(f"   • Total Inventory: {kpi_charts.get('total_inventory_units', 0)} units")
                
                # Test 3: Trend Visualizations
                trends = result.get("trend_visualizations", {})
                if trends and not trends.get("error"):
                    print(f"\n TREND VISUALIZATIONS:")
                    print("-" * 40)
                    
                    daily_data = trends.get('daily_data_90_days', [])
                    print(f" Daily Data Points: {len(daily_data)} days")
                    
                    if daily_data:
                        # Show last 7 days
                        print(f"\n Last 7 Days Sample:")
                        print(f"{'Date':<12} {'Revenue':<10} {'Units':<6} {'Orders':<6} {'Inventory':<9}")
                        print("-" * 45)
                        
                        for day in daily_data[-7:]:
                            date = day.get('date', 'N/A')
                            revenue = day.get('revenue', 0)
                            units = day.get('units_sold', 0)
                            orders = day.get('orders', 0)
                            inventory = day.get('inventory_level', 0)
                            
                            print(f"{date:<12} ${revenue:<9.2f} {units:<6} {orders:<6} {inventory:<9}")
                    
                    # Sales comparison
                    comparison = trends.get('sales_comparison', {})
                    if comparison:
                        print(f"\n Sales Comparison (Current vs Historical):")
                        print(f"   • Revenue: ${comparison.get('current_period_avg_revenue', 0):.2f} vs ${comparison.get('historical_avg_revenue', 0):.2f} ({comparison.get('revenue_change_percent', 0):+.1f}%)")
                        print(f"   • Units: {comparison.get('current_period_avg_units', 0):.1f} vs {comparison.get('historical_avg_units', 0):.1f} ({comparison.get('units_change_percent', 0):+.1f}%)")
                
                # Test 4: Alerts Summary
                alerts = result.get("alerts_summary", {})
                if alerts and not alerts.get("error"):
                    print(f"\n ALERTS SUMMARY:")
                    print("-" * 40)
                    
                    summary_counts = alerts.get('summary_counts', {})
                    print(f" Alert Counts:")
                    print(f"   • Low Stock Alerts: {summary_counts.get('low_stock_alerts', 0)}")
                    print(f"   • Overstock Alerts: {summary_counts.get('overstock_alerts', 0)}")
                    print(f"   • Sales Spike Alerts: {summary_counts.get('sales_spike_alerts', 0)}")
                    print(f"   • Sales Slowdown Alerts: {summary_counts.get('sales_slowdown_alerts', 0)}")
                    print(f"   • Total Alerts: {summary_counts.get('total_alerts', 0)}")
                    
                    # Show some detailed alerts
                    detailed_alerts = alerts.get('detailed_alerts', {})
                    low_stock = detailed_alerts.get('low_stock_alerts', [])
                    
                    if low_stock:
                        print(f"\n  Low Stock Alert Details (showing first 5):")
                        print(f"{'Item Name':<25} {'SKU':<15} {'Stock':<6} {'Severity':<8} {'Platform':<8}")
                        print("-" * 65)
                        
                        for alert in low_stock[:5]:
                            name = alert.get('item_name', 'Unknown')[:24]
                            sku = alert.get('sku', 'N/A')[:14]
                            stock = alert.get('current_stock', 0)
                            severity = alert.get('severity', 'unknown').upper()
                            platform = alert.get('platform', 'N/A').upper()
                            
                            print(f"{name:<25} {sku:<15} {stock:<6} {severity:<8} {platform:<8}")
                    
                    # Quick links
                    quick_links = alerts.get('quick_links', {})
                    if quick_links:
                        print(f"\n Quick Links:")
                        for link_name, link_url in quick_links.items():
                            print(f"   • {link_name}: {link_url}")
                
                # Data Summary
                data_summary = result.get("data_summary", {})
                print(f"\n DATA SUMMARY:")
                print("-" * 40)
                for source, count in data_summary.items():
                    print(f"   • {source}: {count} records")
                
            else:
                print(f" Dashboard inventory analytics failed for {client_name}")
                print(f"Error: {result.get('error')}")
    
    except Exception as e:
        print(f" Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

async def test_api_endpoint():
    """Test the API endpoint directly"""
    print(f"\n{'='*80}")
    print(" Testing API Endpoint Integration")
    print("="*80)
    
    try:
        # Test the endpoint by importing and calling the app function
        print("ℹ️  Note: This test simulates the API endpoint logic")
        print("ℹ️  For full API testing, use the actual HTTP endpoint with authentication")
        
        # Import the new dashboard analyzer
        from dashboard_inventory_analyzer import dashboard_inventory_analyzer
        
        client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
        
        print(f"\n Testing dashboard analyzer for client {client_id}")
        result = await dashboard_inventory_analyzer.get_dashboard_inventory_analytics(client_id)
        
        if result.get('success'):
            print(" API endpoint logic test successful!")
            
            # Simulate the API response structure
            api_response = {
                "client_id": client_id,
                "success": True,
                "message": f"Dashboard analytics from organized data",
                "timestamp": result.get('timestamp'),
                "data_type": "dashboard_inventory_analytics",
                "inventory_analytics": result
            }
            
            print(f"\n API Response Structure:")
            print(f"   • client_id: {api_response['client_id']}")
            print(f"   • success: {api_response['success']}")
            print(f"   • data_type: {api_response['data_type']}")
            print(f"   • inventory_analytics keys: {list(api_response['inventory_analytics'].keys())}")
            
        else:
            print(f" API endpoint logic test failed: {result.get('error')}")
    
    except Exception as e:
        print(f" API test failed: {e}")

async def main():
    """Main test function"""
    print(" Dashboard Inventory Analytics Test Suite")
    print("=" * 80)
    
    print("\nChoose test mode:")
    print("1. Test dashboard analytics (detailed)")
    print("2. Test API endpoint integration")
    print("3. Run both tests")
    
    try:
        choice = input("\nEnter choice (1, 2, or 3): ").strip()
        
        if choice == "1":
            await test_dashboard_inventory_analytics()
        elif choice == "2":
            await test_api_endpoint()
        elif choice == "3":
            print("\n Running full test suite...")
            await test_dashboard_inventory_analytics()
            await test_api_endpoint()
        else:
            print("Invalid choice. Running dashboard analytics test...")
            await test_dashboard_inventory_analytics()
    
    except KeyboardInterrupt:
        print("\n Test interrupted by user")
    except Exception as e:
        print(f"\n Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
