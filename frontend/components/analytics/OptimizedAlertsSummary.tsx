/**
 * Optimized AlertsSummary Component
 * 
 * Features:
 * - Independent date range and platform state
 * - React Query for optimized caching  
 * - React.memo for preventing unnecessary re-renders
 * - More frequent refresh for real-time alerts
 */

import React, { memo, useState, useCallback, useMemo } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Package,
  ExternalLink,
  RefreshCw,
  Bell,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { useAlertsData, DateRange, DashboardFilters } from '../../hooks/useOptimizedDashboardData';
import IndependentDatePicker from '../ui/IndependentDatePicker';

interface OptimizedAlertsSummaryProps {
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

const OptimizedAlertsSummary: React.FC<OptimizedAlertsSummaryProps> = memo(({
  initialPlatform = 'shopify',
  initialDatePreset = '7d',
  refreshInterval = 3 * 60 * 1000, // 3 minutes for alerts (more frequent)
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
  const { data: alertsSummary, isLoading, error, refetch, isRefetching } = useAlertsData(filters);

  // Memoized alert processing
  const alertData = useMemo(() => {
    if (!alertsSummary) {
      return {
        totalAlerts: 0,
        criticalAlerts: 0,
        lowStockAlerts: [],
        overstockAlerts: [],
        salesSpikeAlerts: [],
        salesSlowdownAlerts: [],
      };
    }

    // Calculate total alerts from summary (handle both old and new structure)
    const totalAlerts = alertsSummary.summary?.total_alerts || 0;
    const criticalAlerts = alertsSummary.summary?.critical_alerts || 0;

    // Helper function to get alerts with fallback
    const getAlerts = (type: string) => {
      return alertsSummary[type as keyof typeof alertsSummary] || [];
    };

    return {
      totalAlerts,
      criticalAlerts,
      lowStockAlerts: getAlerts('low_stock_alerts'),
      overstockAlerts: getAlerts('overstock_alerts'),
      salesSpikeAlerts: getAlerts('sales_spike_alerts'),
      salesSlowdownAlerts: getAlerts('sales_slowdown_alerts'),
    };
  }, [alertsSummary]);

  // Get severity badge styling
  const getSeverityBadge = useCallback((severity: string) => {
    const styles = {
      low: "bg-gray-100 text-gray-700 border-gray-200",
      medium: "bg-yellow-100 text-yellow-700 border-yellow-200", 
      high: "bg-orange-100 text-orange-700 border-orange-200",
      critical: "bg-red-100 text-red-700 border-red-200",
    };

    return (
      <span
        className={`px-2 py-1 text-xs font-medium rounded-full border ${
          styles[severity as keyof typeof styles] || styles.low
        }`}>
        {severity.toUpperCase()}
      </span>
    );
  }, []);

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
  if (isLoading && !alertsSummary) {
    return (
      <div className={`space-y-4 ${className}`}>
        {/* Date picker skeleton */}
        {showDatePicker && (
          <div className="h-12 bg-gray-200 rounded animate-pulse"></div>
        )}
        
        <Card>
          <CardHeader>
            <div className="h-6 bg-gray-200 rounded w-48 animate-pulse"></div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[...Array(4)].map((_, i) => (
                <div
                  key={i}
                  className="h-16 bg-gray-200 rounded animate-pulse"></div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
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

      <Card className="relative">
        {isRefetching && (
          <div className="absolute top-4 right-4 z-10">
            <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
          </div>
        )}
        
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-red-600" />
              Alerts Summary ({platform === 'combined' ? 'All Platforms' : platform.charAt(0).toUpperCase() + platform.slice(1)})
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-600">Total: {alertData.totalAlerts}</span>
              {alertData.criticalAlerts > 0 && (
                <span className="bg-red-100 text-red-700 px-2 py-1 rounded-full text-xs font-medium">
                  {alertData.criticalAlerts} Critical
                </span>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        
        <CardContent>
          {error ? (
            <div className="text-center py-8">
              <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">{error.message}</p>
              <button
                onClick={handleRefresh}
                disabled={isRefetching}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 flex items-center gap-2 mx-auto">
                <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
                Retry
              </button>
            </div>
          ) : alertData.totalAlerts === 0 ? (
            <div className="text-center py-8">
              <Bell className="h-12 w-12 text-green-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                All Clear!
              </h3>
              <p className="text-gray-600">
                No active alerts for{" "}
                {platform === 'combined' ? 'any platform' : platform} in the selected time period.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Low Stock Alerts */}
              {alertData.lowStockAlerts.length > 0 && (
                <div className="p-4 rounded-lg border border-yellow-200 bg-yellow-50">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="text-yellow-700">
                        <AlertTriangle className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-yellow-700">
                            Low Stock & Out of Stock Alerts
                          </h4>
                          {getSeverityBadge("high")}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          {alertData.lowStockAlerts.length} SKUs need immediate attention
                        </p>
                        <div className="text-xs text-gray-500">
                          <span className="font-medium">Affected SKUs: </span>
                          {alertData.lowStockAlerts
                            .slice(0, 3)
                            .map((alert: any) => alert.sku_code || alert.sku || "Unknown")
                            .join(", ")}
                          {alertData.lowStockAlerts.length > 3 && (
                            <span className="ml-1">
                              and {alertData.lowStockAlerts.length - 3} more...
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-bold text-yellow-700">
                        {alertData.lowStockAlerts.length}
                      </span>
                      <button
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                        title="View detailed alert conditions">
                        <ExternalLink className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Overstock Alerts */}
              {alertData.overstockAlerts.length > 0 && (
                <div className="p-4 rounded-lg border border-blue-200 bg-blue-50">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="text-blue-700">
                        <Package className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-blue-700">
                            Overstock Alerts
                          </h4>
                          {getSeverityBadge("medium")}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          {alertData.overstockAlerts.length} SKUs have excess inventory
                        </p>
                        <div className="text-xs text-gray-500">
                          <span className="font-medium">Affected SKUs: </span>
                          {alertData.overstockAlerts
                            .slice(0, 3)
                            .map((alert: any) => alert.sku_code || alert.sku || "Unknown")
                            .join(", ")}
                          {alertData.overstockAlerts.length > 3 && (
                            <span className="ml-1">
                              and {alertData.overstockAlerts.length - 3} more...
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-bold text-blue-700">
                        {alertData.overstockAlerts.length}
                      </span>
                      <button
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                        title="View detailed alert conditions">
                        <ExternalLink className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Sales Spike Alerts */}
              {alertData.salesSpikeAlerts.length > 0 && (
                <div className="p-4 rounded-lg border border-green-200 bg-green-50">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="text-green-700">
                        <TrendingUp className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-green-700">
                            Sales Spike Alerts
                          </h4>
                          {getSeverityBadge("medium")}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          {alertData.salesSpikeAlerts[0]?.message ||
                            "Unusual sales increases detected"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-bold text-green-700">
                        {alertData.salesSpikeAlerts.length}
                      </span>
                      <button
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                        title="View detailed alert conditions">
                        <ExternalLink className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Sales Slowdown Alerts */}
              {alertData.salesSlowdownAlerts.length > 0 && (
                <div className="p-4 rounded-lg border border-orange-200 bg-orange-50">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="text-orange-700">
                        <TrendingDown className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-orange-700">
                            Sales Slowdown Alerts
                          </h4>
                          {getSeverityBadge("medium")}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          {alertData.salesSlowdownAlerts[0]?.message ||
                            "Sales declines detected"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-bold text-orange-700">
                        {alertData.salesSlowdownAlerts.length}
                      </span>
                      <button
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                        title="View detailed alert conditions">
                        <ExternalLink className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="mt-6 pt-4 border-t border-gray-200 text-center">
            <p className="text-xs text-gray-500">
              <RefreshCw className="inline h-3 w-3 mr-1" />
              Platform: {platform === 'combined' ? 'All Platforms' : platform.charAt(0).toUpperCase() + platform.slice(1)} • 
              Date range: {dateRange.startDate} to {dateRange.endDate} • 
              Real-time alert monitoring active
              {isRefetching && (
                <span className="ml-2 inline-flex items-center gap-1">
                  <RefreshCw className="h-3 w-3 animate-spin" />
                  Refreshing alerts...
                </span>
              )}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
});

OptimizedAlertsSummary.displayName = 'OptimizedAlertsSummary';

export default OptimizedAlertsSummary;
