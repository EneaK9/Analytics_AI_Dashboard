/**
 * Example: How to use the Optimized Dashboard Components
 * 
 * This example demonstrates the key improvements:
 * 1. Independent state management for each component
 * 2. React Query for optimized caching
 * 3. No unnecessary re-renders between components
 * 4. Each component has its own date picker and platform selector
 */

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Import optimized components
import OptimizedSmartEcommerceMetrics from '../components/analytics/OptimizedSmartEcommerceMetrics';
import OptimizedInventoryTrendCharts from '../components/analytics/OptimizedInventoryTrendCharts';
import OptimizedAlertsSummary from '../components/analytics/OptimizedAlertsSummary';
import OptimizedMainGrid from '../components/dashboard/components/OptimizedMainGrid';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000,   // 10 minutes
      refetchOnWindowFocus: false,
      refetchOnMount: false,
      refetchOnReconnect: true,
      retry: 3,
    },
  },
});

// Example 1: Individual Components with Independent State
export const IndependentComponentsExample = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="space-y-8 p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Optimized Dashboard - Independent Components
        </h1>

        {/* Each component has independent state management */}
        
        {/* Shopify Sales Metrics - 7 days */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Shopify Sales (7 Days)</h2>
          <OptimizedSmartEcommerceMetrics
            initialPlatform="shopify"
            initialDatePreset="7d"
            refreshInterval={5 * 60 * 1000}
            showDatePicker={true}
          />
        </div>

        {/* Amazon Sales Metrics - 30 days (independent from Shopify) */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Amazon Sales (30 Days)</h2>
          <OptimizedSmartEcommerceMetrics
            initialPlatform="amazon"
            initialDatePreset="30d"
            refreshInterval={5 * 60 * 1000}
            showDatePicker={true}
          />
        </div>

        {/* Combined Platform Metrics - 90 days (independent from others) */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Combined Platform Analytics (90 Days)</h2>
          <OptimizedSmartEcommerceMetrics
            initialPlatform="combined"
            initialDatePreset="90d"
            refreshInterval={10 * 60 * 1000}
            showDatePicker={true}
          />
        </div>

        {/* Inventory Trends - Independent from sales metrics */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Inventory Trends</h2>
          <OptimizedInventoryTrendCharts
            initialPlatform="shopify"
            initialDatePreset="30d"
            refreshInterval={5 * 60 * 1000}
            showDatePicker={true}
          />
        </div>

        {/* Alerts - More frequent refresh, independent state */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Real-time Alerts</h2>
          <OptimizedAlertsSummary
            initialPlatform="shopify"
            initialDatePreset="7d"
            refreshInterval={3 * 60 * 1000} // 3 minutes for alerts
            showDatePicker={true}
          />
        </div>
      </div>

      {/* React Query DevTools for debugging */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
};

// Example 2: Complete Optimized Dashboard
export const OptimizedDashboardExample = () => {
  const user = {
    client_id: 'example-client-123',
    company_name: 'Example Company',
    email: 'user@example.com',
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <h1 className="text-2xl font-bold text-gray-900">
              🚀 Optimized Analytics Dashboard
            </h1>
            <p className="text-gray-600 mt-1">
              Independent components • Smart caching • Optimized rendering
            </p>
          </div>
        </header>

        <main className="max-w-7xl mx-auto py-6">
          <OptimizedMainGrid
            user={user}
            dashboardType="optimized"
            className="w-full"
          />
        </main>
      </div>

      {/* React Query DevTools */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
};

// Example 3: Component Performance Comparison
export const PerformanceComparisonExample = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 p-6">
        {/* Old shared state approach would cause all to re-render */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-900">
            ❌ Old Approach (Shared State)
          </h2>
          <div className="text-sm text-gray-600 bg-yellow-50 p-4 rounded-lg">
            <p className="font-medium mb-2">Problems with old approach:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Changing platform in one component affects all components</li>
              <li>Changing date range triggers re-renders in unrelated components</li>
              <li>Multiple API calls for the same data</li>
              <li>No independent caching per component</li>
              <li>Poor user experience with unnecessary loading states</li>
            </ul>
          </div>
        </div>

        {/* New optimized approach */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-900">
            ✅ New Approach (Independent State)
          </h2>
          <div className="text-sm text-gray-600 bg-green-50 p-4 rounded-lg">
            <p className="font-medium mb-2">Benefits of optimized approach:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Each component manages its own platform and date range</li>
              <li>React Query prevents duplicate API calls with smart caching</li>
              <li>React.memo prevents unnecessary re-renders</li>
              <li>Independent query keys for isolated caching</li>
              <li>Background data refresh for better UX</li>
              <li>Prefetching for instant data access</li>
            </ul>
          </div>

          {/* Live example showing independence */}
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-medium mb-3">Try changing settings in each component:</h3>
            
            <div className="space-y-4">
              <div className="border rounded p-3">
                <h4 className="text-sm font-medium mb-2">Component 1 - Independent Settings</h4>
                <OptimizedSmartEcommerceMetrics
                  initialPlatform="shopify"
                  initialDatePreset="7d"
                  refreshInterval={5 * 60 * 1000}
                  showDatePicker={true}
                />
              </div>

              <div className="border rounded p-3">
                <h4 className="text-sm font-medium mb-2">Component 2 - Independent Settings</h4>
                <OptimizedSmartEcommerceMetrics
                  initialPlatform="amazon"
                  initialDatePreset="30d"
                  refreshInterval={5 * 60 * 1000}
                  showDatePicker={true}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* React Query DevTools */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
};

// Example 4: Caching Strategy Demonstration
export const CachingStrategyExample = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="p-6 space-y-8">
        <div className="bg-blue-50 p-6 rounded-lg">
          <h2 className="text-2xl font-bold text-blue-900 mb-4">
            🧠 Smart Caching Strategy
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-4 rounded shadow">
              <h3 className="font-bold text-gray-900 mb-2">Query Keys</h3>
              <div className="text-xs font-mono bg-gray-100 p-2 rounded">
                ["sales", "shopify", "7d", "2024-01-01", "2024-01-07"]<br />
                ["sales", "amazon", "30d", "2024-01-01", "2024-01-30"]<br />
                ["trends", "combined", "90d", "2024-01-01", "2024-03-31"]
              </div>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h3 className="font-bold text-gray-900 mb-2">Cache Benefits</h3>
              <ul className="text-sm space-y-1">
                <li>• No duplicate API calls</li>
                <li>• Instant data for cached queries</li>
                <li>• Background refresh</li>
                <li>• Stale-while-revalidate pattern</li>
              </ul>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h3 className="font-bold text-gray-900 mb-2">Performance</h3>
              <ul className="text-sm space-y-1">
                <li>• 5min stale time</li>
                <li>• 10min garbage collection</li>
                <li>• 3 retry attempts</li>
                <li>• Exponential backoff</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Live caching example */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold mb-4">
            Test Caching: Same settings = cached data
          </h3>
          <p className="text-gray-600 mb-4">
            Both components below use the same platform and date range. 
            The second component should load instantly from cache.
          </p>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="border rounded p-4">
              <h4 className="font-medium mb-2">Component A (loads fresh data)</h4>
              <OptimizedSmartEcommerceMetrics
                initialPlatform="shopify"
                initialDatePreset="7d"
                refreshInterval={5 * 60 * 1000}
                showDatePicker={false}
              />
            </div>
            
            <div className="border rounded p-4">
              <h4 className="font-medium mb-2">Component B (should use cached data)</h4>
              <OptimizedSmartEcommerceMetrics
                initialPlatform="shopify"
                initialDatePreset="7d"
                refreshInterval={5 * 60 * 1000}
                showDatePicker={false}
              />
            </div>
          </div>
        </div>
      </div>

      {/* React Query DevTools */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
};

export default {
  IndependentComponentsExample,
  OptimizedDashboardExample,
  PerformanceComparisonExample,
  CachingStrategyExample,
};
