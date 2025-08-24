"""
Quick test for optimized dashboard inventory analytics
"""

import asyncio
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fast_inventory():
    """Test the optimized inventory analytics for speed"""
    
    client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
    
    try:
        print(" Testing Fast Dashboard Inventory Analytics")
        print("=" * 60)
        
        start_time = time.time()
        
        from dashboard_inventory_analyzer import dashboard_inventory_analyzer
        
        print(f" Testing for client: {client_id}")
        
        result = await dashboard_inventory_analyzer.get_dashboard_inventory_analytics(client_id)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        
        if result.get('success'):
            print(" Fast analytics successful!")
            
            # Show key metrics
            data_summary = result.get('data_summary', {})
            print(f"\n Data Summary:")
            for source, count in data_summary.items():
                print(f"   • {source}: {count} records")
            
            # Show SKU count
            sku_list = result.get('sku_list', [])
            print(f"   • Total SKUs: {len(sku_list)}")
            
            # Show KPI summary
            kpi_charts = result.get('kpi_charts', {})
            if kpi_charts and not kpi_charts.get('error'):
                sales_30d = kpi_charts.get('total_sales_30_days', {})
                print(f"\n Quick KPIs:")
                print(f"   • 30-day revenue: ${sales_30d.get('revenue', 0):,.2f}")
                print(f"   • 30-day orders: {sales_30d.get('orders', 0)}")
                print(f"   • Total inventory: {kpi_charts.get('total_inventory_units', 0):,} units")
                print(f"   • Turnover rate: {kpi_charts.get('inventory_turnover_rate', 0)}")
            
            # Show alerts count
            alerts = result.get('alerts_summary', {})
            if alerts and not alerts.get('error'):
                counts = alerts.get('summary_counts', {})
                print(f"\n Alerts:")
                print(f"   • Low stock: {counts.get('low_stock_alerts', 0)}")
                print(f"   • Overstock: {counts.get('overstock_alerts', 0)}")
                print(f"   • Total alerts: {counts.get('total_alerts', 0)}")
            
            # Check if response is under 5 seconds (fast enough)
            if processing_time < 5.0:
                print(f"\n PERFORMANCE: Excellent! ({processing_time:.2f}s)")
            elif processing_time < 10.0:
                print(f"\n PERFORMANCE: Good ({processing_time:.2f}s)")
            else:
                print(f"\n  PERFORMANCE: Still slow ({processing_time:.2f}s)")
            
        else:
            print(f" Analytics failed: {result.get('error')}")
    
    except Exception as e:
        print(f" Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fast_inventory())
