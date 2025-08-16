/**
 * EXAMPLE: How to optimize multiple analytics components with single API call
 * 
 * BEFORE: Multiple components each making separate API calls
 * - InventorySKUList: calls inventoryService.getInventoryAnalytics()
 * - EcommerceMetrics: calls inventoryService.getSalesKPIs()
 * - AlertsSummary: calls inventoryService.getAlertsSummary()
 * - TrendCharts: calls inventoryService.getTrendAnalysis()
 * 
 * Result: 4+ API calls for the same data
 * 
 * AFTER: Single hook provides all data from one API call
 */

import React from 'react';
import useInventoryData from '../hooks/useInventoryData';

// ===== OPTIMIZED APPROACH =====

/**
 * Main Dashboard Component - Makes ONE API call
 */
export function OptimizedInventoryDashboard() {
  // Single API call gets ALL the data these components need
  const inventoryData = useInventoryData({
    refreshInterval: 300000, // 5 minutes
    fastMode: true
  });

  return (
    <div className="space-y-6">
      {/* Pass shared data to all components - NO additional API calls */}
      <OptimizedMetricsCard {...inventoryData} />
      <OptimizedSKUTable {...inventoryData} />
      <OptimizedAlertsPanel {...inventoryData} />
      <OptimizedTrendsChart {...inventoryData} />
    </div>
  );
}

/**
 * Metrics Component - Uses shared data, no API call
 */
function OptimizedMetricsCard({ 
  loading, 
  error, 
  summaryStats, 
  salesKPIs 
}: ReturnType<typeof useInventoryData>) {
  if (loading) return <div>Loading metrics...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="grid grid-cols-4 gap-4">
      <div className="p-4 border rounded">
        <h3>Total SKUs</h3>
        <p className="text-2xl font-bold">{summaryStats?.total_skus || 0}</p>
      </div>
      <div className="p-4 border rounded">
        <h3>Inventory Value</h3>
        <p className="text-2xl font-bold">${summaryStats?.total_inventory_value || 0}</p>
      </div>
      <div className="p-4 border rounded">
        <h3>7-Day Sales</h3>
        <p className="text-2xl font-bold">{salesKPIs?.total_sales_7_days?.display_value || 'N/A'}</p>
      </div>
      <div className="p-4 border rounded">
        <h3>Low Stock</h3>
        <p className="text-2xl font-bold text-orange-600">{summaryStats?.low_stock_count || 0}</p>
      </div>
    </div>
  );
}

/**
 * SKU Table - Uses shared data, no API call
 */
function OptimizedSKUTable({ 
  loading, 
  error, 
  skuData 
}: ReturnType<typeof useInventoryData>) {
  if (loading) return <div>Loading SKU data...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="border rounded">
      <h3 className="p-4 border-b font-semibold">SKU Inventory ({skuData.length} items)</h3>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="p-2 text-left">SKU Code</th>
              <th className="p-2 text-left">Item Name</th>
              <th className="p-2 text-right">On Hand</th>
              <th className="p-2 text-right">Value</th>
            </tr>
          </thead>
          <tbody>
            {skuData.slice(0, 10).map((sku, index) => (
              <tr key={index} className="border-b hover:bg-gray-50">
                <td className="p-2 font-mono text-sm">{sku.sku_code}</td>
                <td className="p-2">{sku.item_name}</td>
                <td className="p-2 text-right">{sku.on_hand_inventory}</td>
                <td className="p-2 text-right">${sku.total_value?.toFixed(2) || '0.00'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Alerts Panel - Uses shared data, no API call
 */
function OptimizedAlertsPanel({ 
  loading, 
  error, 
  alertsSummary 
}: ReturnType<typeof useInventoryData>) {
  if (loading) return <div>Loading alerts...</div>;
  if (error) return <div>Error: {error}</div>;

  const totalAlerts = alertsSummary?.summary.total_alerts || 0;

  return (
    <div className="border rounded">
      <h3 className="p-4 border-b font-semibold">Active Alerts ({totalAlerts})</h3>
      <div className="p-4">
        {totalAlerts === 0 ? (
          <p className="text-green-600">✅ No active alerts</p>
        ) : (
          <div className="space-y-2">
            {alertsSummary?.low_stock_alerts.slice(0, 5).map((alert, index) => (
              <div key={index} className="p-2 bg-orange-50 border border-orange-200 rounded">
                <p className="text-sm">{alert.message}</p>
                <p className="text-xs text-gray-600">Severity: {alert.severity}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Trends Chart - Uses shared data, no API call
 */
function OptimizedTrendsChart({ 
  loading, 
  error, 
  trendAnalysis 
}: ReturnType<typeof useInventoryData>) {
  if (loading) return <div>Loading trends...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="border rounded">
      <h3 className="p-4 border-b font-semibold">Sales Trends</h3>
      <div className="p-4">
        {trendAnalysis?.trend_summary ? (
          <div>
            <p>Overall Direction: <strong>{trendAnalysis.trend_summary.overall_direction}</strong></p>
            <p>Growth Rate: <strong>{trendAnalysis.trend_summary.growth_rate}%</strong></p>
            <p>Data Points: {trendAnalysis.daily_sales_trends?.length || 0} days</p>
          </div>
        ) : (
          <p>No trend data available</p>
        )}
      </div>
    </div>
  );
}

// ===== COMPARISON: OLD vs NEW APPROACH =====

/**
 * OLD APPROACH ❌ - Multiple API calls
 */
export function UnoptimizedDashboard() {
  return (
    <div className="space-y-6">
      {/* Each component makes its own API call - INEFFICIENT! */}
      <UnoptimizedMetricsCard />    {/* API call #1 */}
      <UnoptimizedSKUTable />       {/* API call #2 */}
      <UnoptimizedAlertsPanel />    {/* API call #3 */}
      <UnoptimizedTrendsChart />    {/* API call #4 */}
    </div>
  );
}

// Each component below would have its own useEffect + API call
// Result: 4+ network requests for the same data!

function UnoptimizedMetricsCard() {
  // ❌ Makes its own API call
  // useEffect(() => {
  //   inventoryService.getInventoryAnalytics().then(...)
  // }, []);
  
  return <div>Metrics component making its own API call...</div>;
}

function UnoptimizedSKUTable() {
  // ❌ Makes its own API call
  // useEffect(() => {
  //   inventoryService.getSKUInventory().then(...)
  // }, []);
  
  return <div>SKU table making its own API call...</div>;
}

function UnoptimizedAlertsPanel() {
  // ❌ Makes its own API call
  // useEffect(() => {
  //   inventoryService.getAlertsSummary().then(...)
  // }, []);
  
  return <div>Alerts panel making its own API call...</div>;
}

function UnoptimizedTrendsChart() {
  // ❌ Makes its own API call
  // useEffect(() => {
  //   inventoryService.getTrendAnalysis().then(...)
  // }, []);
  
  return <div>Trends chart making its own API call...</div>;
}

// ===== PERFORMANCE COMPARISON =====
/*
OLD APPROACH:
- 4+ API requests per page load
- 4+ network roundtrips
- Higher server load
- Inconsistent loading states
- Race conditions possible
- Cache misses between components

NEW APPROACH:
- 1 API request per page load
- 1 network roundtrip
- Lower server load
- Consistent loading states
- No race conditions
- Shared cache across components
- Better user experience
*/

// ===== MIGRATION GUIDE =====
/*
1. Replace individual useEffect + API calls with useInventoryData hook
2. Pass shared data down to child components as props
3. Remove duplicate API calls from child components
4. Use loading/error states from the hook
5. Enable pagination only where needed

BEFORE:
```tsx
function MyComponent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    inventoryService.getInventoryAnalytics().then(setData);
  }, []);
  
  // ...
}
```

AFTER:
```tsx
function MyComponent() {
  const { data, loading } = useInventoryData({
    refreshInterval: 300000
  });
  
  // ...
}
```
*/
