"use client";

import React from "react";
import InventoryAnalyticsDataTable from "../components/analytics/InventoryAnalyticsDataTable";

// Example usage of the InventoryAnalyticsDataTable component
export default function InventoryAnalyticsTableUsage() {
	// Example data structure - this would typically come from your API
	const sampleAnalyticsData = {
		"cached": true,
		"message": "Dashboard analytics from organized data - 0 products, 0 orders (SKU data available via /api/dashboard/sku-inventory)",
		"success": true,
		"client_id": "3b619a14-3cd8-49fa-9c24-d8df5e54c452",
		"data_type": "dashboard_inventory_analytics",
		"timestamp": "2025-08-18T22:11:34.235229",
		"data_source": "organized_tables",
		"schema_type": "dashboard_inventory_analytics",
		"total_records": 0,
		"processing_time": "optimized",
		"inventory_analytics": {
			"message": "Multi-platform analytics with separate Shopify, Amazon, and combined data",
			"success": true,
			"platform": "all",
			"client_id": "3b619a14-3cd8-49fa-9c24-d8df5e54c452",
			"platforms": {
				"amazon": {
					"sales_kpis": {
						"avg_daily_sales": 75.1,
						"total_sales_7_days": {
							"units": 225,
							"orders": 172,
							"revenue": 6013.65
						},
						"total_sales_30_days": {
							"units": 2252,
							"orders": 1422,
							"revenue": 74578.61
						},
						"total_sales_90_days": {
							"units": 7381,
							"orders": 4644,
							"revenue": 242246.34
						},
						"days_stock_remaining": 0.0,
						"total_inventory_units": 0,
						"inventory_turnover_rate": 0
					},
					"alerts_summary": {
						"summary_counts": {
							"total_alerts": 1,
							"low_stock_alerts": 0,
							"overstock_alerts": 0,
							"sales_spike_alerts": 0,
							"sales_slowdown_alerts": 1
						}
					},
					"trend_analysis": {
						"sales_comparison": {
							"historical_avg_units": 633.2,
							"units_change_percent": -19.8,
							"historical_avg_revenue": 21411.65,
							"revenue_change_percent": -21.8,
							"current_period_avg_units": 508.0,
							"current_period_avg_revenue": 16741.79
						}
					}
				},
				"shopify": {
					"sales_kpis": {
						"avg_daily_sales": 9.2,
						"total_sales_7_days": {
							"units": 53,
							"orders": 24,
							"revenue": 1110.65
						},
						"total_sales_30_days": {
							"units": 275,
							"orders": 132,
							"revenue": 9353.02
						},
						"total_sales_90_days": {
							"units": 837,
							"orders": 397,
							"revenue": 24226.89
						},
						"days_stock_remaining": 999,
						"total_inventory_units": 40852,
						"inventory_turnover_rate": 0.01
					},
					"alerts_summary": {
						"summary_counts": {
							"total_alerts": 589,
							"low_stock_alerts": 581,
							"overstock_alerts": 7,
							"sales_spike_alerts": 0,
							"sales_slowdown_alerts": 1
						}
					},
					"trend_analysis": {
						"sales_comparison": {
							"historical_avg_units": 68.8,
							"units_change_percent": -7.3,
							"historical_avg_revenue": 1830.86,
							"revenue_change_percent": 20.7,
							"current_period_avg_units": 63.8,
							"current_period_avg_revenue": 2209.4
						}
					}
				},
				"combined": {
					"sales_kpis": {
						"avg_daily_sales": 84.2,
						"total_sales_7_days": {
							"units": 278,
							"orders": 196,
							"revenue": 7124.3
						},
						"total_sales_30_days": {
							"units": 2527,
							"orders": 1554,
							"revenue": 83931.63
						},
						"total_sales_90_days": {
							"units": 8218,
							"orders": 5041,
							"revenue": 266473.23
						},
						"days_stock_remaining": 485.0,
						"total_inventory_units": 40852,
						"inventory_turnover_rate": 0.06
					},
					"alerts_summary": {
						"summary_counts": {
							"total_alerts": 589,
							"low_stock_alerts": 581,
							"overstock_alerts": 7,
							"sales_spike_alerts": 0,
							"sales_slowdown_alerts": 1
						}
					},
					"trend_analysis": {
						"sales_comparison": {
							"historical_avg_units": 702.0,
							"units_change_percent": -18.6,
							"historical_avg_revenue": 23242.51,
							"revenue_change_percent": -18.5,
							"current_period_avg_units": 571.8,
							"current_period_avg_revenue": 18951.19
						}
					}
				}
			}
		}
	};

	return (
		<div className="space-y-6 p-6">
			<div>
				<h1 className="text-3xl font-bold text-gray-900 mb-2">
					Inventory Analytics Data Table
				</h1>
				<p className="text-gray-600 mb-6">
					Comprehensive inventory analytics data organized in an easy-to-read table format.
					This table includes sales KPIs, inventory metrics, alerts summary, and trend analysis
					across all platforms (Amazon, Shopify, Combined).
				</p>
			</div>

			{/* Basic Usage */}
			<section>
				<h2 className="text-xl font-semibold text-gray-800 mb-4">Basic Usage</h2>
				<InventoryAnalyticsDataTable analyticsData={sampleAnalyticsData} />
			</section>

			{/* Custom Title Example */}
			<section>
				<h2 className="text-xl font-semibold text-gray-800 mb-4">Custom Title Example</h2>
				<InventoryAnalyticsDataTable 
					analyticsData={sampleAnalyticsData}
					title="Multi-Platform Inventory Dashboard"
					subtitle="Real-time analytics from Amazon, Shopify, and combined data sources"
				/>
			</section>

			{/* Usage Instructions */}
			<section className="bg-gray-50 p-6 rounded-lg">
				<h2 className="text-xl font-semibold text-gray-800 mb-4">How to Use</h2>
				<div className="space-y-4">
					<div>
						<h3 className="font-medium text-gray-700 mb-2">1. Import the Component</h3>
						<pre className="bg-gray-800 text-white p-3 rounded text-sm overflow-x-auto">
							<code>{`import InventoryAnalyticsDataTable from "../components/analytics/InventoryAnalyticsDataTable";`}</code>
						</pre>
					</div>
					
					<div>
						<h3 className="font-medium text-gray-700 mb-2">2. Pass Analytics Data</h3>
						<pre className="bg-gray-800 text-white p-3 rounded text-sm overflow-x-auto">
							<code>{`<InventoryAnalyticsDataTable 
  analyticsData={yourAnalyticsData}
  title="Your Custom Title"
  subtitle="Your custom subtitle"
/>`}</code>
						</pre>
					</div>

					<div>
						<h3 className="font-medium text-gray-700 mb-2">3. Data Structure Required</h3>
						<p className="text-gray-600 mb-2">
							The component expects data in the following structure:
						</p>
						<ul className="list-disc list-inside text-gray-600 space-y-1">
							<li><code>analyticsData.inventory_analytics.platforms</code> - Platform data (amazon, shopify, combined)</li>
							<li><code>sales_kpis</code> - Sales KPIs including 7, 30, 90 day metrics</li>
							<li><code>alerts_summary</code> - Alert counts by category</li>
							<li><code>trend_analysis</code> - Historical vs current performance comparison</li>
						</ul>
					</div>

					<div>
						<h3 className="font-medium text-gray-700 mb-2">4. Features</h3>
						<ul className="list-disc list-inside text-gray-600 space-y-1">
							<li><strong>Tabbed Interface:</strong> Organize data into Sales KPIs, Inventory Metrics, Alerts Summary, and Trend Analysis</li>
							<li><strong>Search Functionality:</strong> Search across platforms</li>
							<li><strong>Pagination:</strong> Handle large datasets efficiently</li>
							<li><strong>Visual Indicators:</strong> Trend arrows, color-coded alerts, and status chips</li>
							<li><strong>Responsive Design:</strong> Works on desktop and mobile devices</li>
							<li><strong>Data Formatting:</strong> Automatic currency, number, and percentage formatting</li>
						</ul>
					</div>
				</div>
			</section>
		</div>
	);
}
