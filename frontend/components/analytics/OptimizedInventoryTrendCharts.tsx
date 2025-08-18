/**
 * Optimized InventoryTrendCharts Component
 * 
 * Features:
 * - Independent date range and platform state
 * - React Query for optimized caching
 * - React.memo for preventing unnecessary re-renders
 * - Efficient chart data processing with useMemo
 */

import React, { memo, useState, useCallback, useMemo } from 'react';
import { Calendar, TrendingUp, BarChart3, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import * as Charts from '../charts';
import { useTrendAnalysis, DateRange, DashboardFilters } from '../../hooks/useOptimizedDashboardData';
import IndependentDatePicker from '../ui/IndependentDatePicker';

interface OptimizedInventoryTrendChartsProps {
  initialPlatform?: 'shopify' | 'amazon' | 'combined';
  initialDatePreset?: '7d' | '30d' | '90d';
  refreshInterval?: number;
  className?: string;
  showDatePicker?: boolean;
}

// Helper function to format date range
const getDateRangeFromPreset = (preset: '7d' | '30d' | '90d'): DateRange => {
  const endDate = new Date();
  const startDate = new Date();
  
  switch (preset) {
    case '7d':
      startDate.setDate(endDate.getDate() - 7);
      break;
    case '30d':
      startDate.setDate(endDate.getDate() - 30);
      break;
    case '90d':
      startDate.setDate(endDate.getDate() - 90);
      break;
  }
  
  return {
    startDate: startDate.toISOString().split('T')[0],
    endDate: endDate.toISOString().split('T')[0],
    preset,
  };
};

const OptimizedInventoryTrendCharts: React.FC<OptimizedInventoryTrendChartsProps> = memo(({
  initialPlatform = 'shopify',
  initialDatePreset = '30d',
  refreshInterval = 5 * 60 * 1000, // 5 minutes
  className = '',
  showDatePicker = true,
}) => {
  // Independent state - changes here don't affect other components
  const [platform, setPlatform] = useState<'shopify' | 'amazon' | 'combined'>(initialPlatform);
  const [dateRange, setDateRange] = useState<DateRange>(() => getDateRangeFromPreset(initialDatePreset));

  // Memoized filters to prevent unnecessary re-renders
  const filters = useMemo<DashboardFilters>(() => ({
    platform,
    dateRange,
    refreshInterval,
  }), [platform, dateRange, refreshInterval]);

  // React Query hook with independent caching
  const { data: trendAnalysis, isLoading, error, refetch, isRefetching } = useTrendAnalysis(filters);

  // Memoized chart data processing - only recalculates when trendAnalysis or dateRange changes
  const chartData = useMemo(() => {
    if (!trendAnalysis) {
      return {
        inventoryTrends: [],
        salesTrends: [],
        salesComparison: [],
      };
    }

    // Process inventory levels from API trend data
    const processInventoryTrends = () => {
      if (!trendAnalysis.inventory_levels_chart) return [];

      const now = new Date(dateRange.endDate);
      const startDate = new Date(dateRange.startDate);

      return trendAnalysis.inventory_levels_chart
        .filter((item) => {
          const itemDate = new Date(item.date);
          return itemDate >= startDate && itemDate <= now;
        })
        .map((item) => ({
          date: new Date(item.date).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          }),
          inventory: item.inventory_level,
          value: item.inventory_level,
        }))
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    };

    // Process sales trends from API trend data
    const processSalesTrends = () => {
      if (!trendAnalysis.units_sold_chart) return [];

      const now = new Date(dateRange.endDate);
      const startDate = new Date(dateRange.startDate);

      return trendAnalysis.units_sold_chart
        .filter((item) => {
          const itemDate = new Date(item.date);
          return itemDate >= startDate && itemDate <= now;
        })
        .map((item) => ({
          date: new Date(item.date).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          }),
          units: item.units_sold,
          revenue: 0, // We don't have daily revenue in units_sold_chart
          value: item.units_sold,
        }))
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    };

    // Process sales comparison from API trend data
    const processSalesComparison = () => {
      if (!trendAnalysis.sales_comparison) return [];

      const comparison = trendAnalysis.sales_comparison;

      return [
        {
          name: "Historical Average",
          value: comparison.historical_avg_revenue,
          revenue: comparison.historical_avg_revenue,
        },
        {
          name: "Current Period",
          value: comparison.current_period_avg_revenue,
          revenue: comparison.current_period_avg_revenue,
        },
      ];
    };

    return {
      inventoryTrends: processInventoryTrends(),
      salesTrends: processSalesTrends(),
      salesComparison: processSalesComparison(),
    };
  }, [trendAnalysis, dateRange.startDate, dateRange.endDate]);

  // Callbacks to prevent child re-renders
  const handleDateRangeChange = useCallback((newDateRange: DateRange) => {
    setDateRange(newDateRange);
  }, []);

  const handlePlatformChange = useCallback((newPlatform: 'shopify' | 'amazon' | 'combined') => {
    setPlatform(newPlatform);
  }, []);

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  // Only show loading if we have NO data at all - show data immediately if available
  if (isLoading && !trendAnalysis) {
    return (
      <div className={`space-y-6 ${className}`}>
        {/* Date picker skeleton */}
        {showDatePicker && (
          <div className="h-12 bg-gray-200 rounded animate-pulse"></div>
        )}
        
        {/* Loading skeletons */}
        {[...Array(3)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <div className="h-6 bg-gray-200 rounded w-48 animate-pulse"></div>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-gray-200 rounded animate-pulse"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="p-8 text-center">
          <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <TrendingUp className="h-8 w-8 text-red-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Trend Analysis Error
          </h3>
          <p className="text-gray-600 mb-4">{error.message}</p>
          <button
            onClick={handleRefresh}
            disabled={isRefetching}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 flex items-center gap-2 mx-auto">
            <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
            Retry
          </button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Independent Date & Platform Picker */}
      {showDatePicker && (
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <IndependentDatePicker
            dateRange={dateRange}
            onDateRangeChange={handleDateRangeChange}
            platform={platform}
            disabled={isLoading}
          />
          
          {/* Platform selector */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Platform:</span>
            <select
              value={platform}
              onChange={(e) => handlePlatformChange(e.target.value as 'shopify' | 'amazon' | 'combined')}
              disabled={isLoading}
              className="px-3 py-1 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="shopify">Shopify</option>
              <option value="amazon">Amazon</option>
              <option value="combined">Combined</option>
            </select>
          </div>
        </div>
      )}

      {/* Inventory Levels Time Series */}
      <Card className="relative">
        {isRefetching && (
          <div className="absolute top-4 right-4 z-10">
            <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
          </div>
        )}
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            Inventory Levels Over Time ({dateRange.preset || 'custom'})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {chartData.inventoryTrends.length > 0 ? (
            <Charts.LineChartOne
              data={chartData.inventoryTrends}
              title="Inventory Trends"
              description={`Inventory levels from ${dateRange.startDate} to ${dateRange.endDate}`}
              minimal={true}
            />
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No inventory trend data available for the selected period
            </div>
          )}
        </CardContent>
      </Card>

      {/* Units Sold Time Series */}
      <Card className="relative">
        {isRefetching && (
          <div className="absolute top-4 right-4 z-10">
            <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
          </div>
        )}
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-green-600" />
            Units Sold Over Time ({dateRange.preset || 'custom'})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {chartData.salesTrends.length > 0 ? (
            <Charts.LineChartOne
              data={chartData.salesTrends}
              title="Sales Trends"
              description={`Units sold from ${dateRange.startDate} to ${dateRange.endDate}`}
              minimal={true}
            />
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No sales trend data available for the selected period
            </div>
          )}
        </CardContent>
      </Card>

      {/* Sales Comparison Bar Chart */}
      <Card className="relative">
        {isRefetching && (
          <div className="absolute top-4 right-4 z-10">
            <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
          </div>
        )}
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-purple-600" />
            Sales Comparison: Current vs Historical Average
          </CardTitle>
        </CardHeader>
        <CardContent>
          {chartData.salesComparison.length > 0 ? (
            <Charts.BarChartOne
              data={chartData.salesComparison}
              title="Sales Comparison"
              description={`Current period vs historical average for ${platform}`}
              minimal={true}
            />
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No comparison data available for the selected period
            </div>
          )}
        </CardContent>
      </Card>

      {/* Data Info Footer */}
      <div className="text-center text-sm text-gray-500">
        <RefreshCw className="inline h-4 w-4 mr-1" />
        Platform: {platform === 'combined' ? 'All Platforms' : platform.charAt(0).toUpperCase() + platform.slice(1)} • 
        Date range: {dateRange.startDate} to {dateRange.endDate} • 
        Showing {chartData.inventoryTrends.length} inventory data points, {chartData.salesTrends.length} sales data points
        {isRefetching && (
          <span className="ml-2 inline-flex items-center gap-1">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Refreshing data...
          </span>
        )}
      </div>
    </div>
  );
});

OptimizedInventoryTrendCharts.displayName = 'OptimizedInventoryTrendCharts';

export default OptimizedInventoryTrendCharts;
