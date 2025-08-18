/**
 * Comprehensive Inventory Data Hook
 * Handles all inventory-related API calls in a single, optimized request
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import api from '../lib/axios';
import { 
  InventoryAnalyticsResponse, 
  SKUData, 
  SKUSummaryStats,
  SalesKPIs,
  TrendAnalysis,
  AlertsSummary 
} from '../lib/inventoryService';

interface UseInventoryDataOptions {
  refreshInterval?: number; // Auto-refresh interval in ms (0 to disable)
  fastMode?: boolean;       // Use fast mode for analytics
  pageSize?: number;        // Page size for SKU data (always paginated)
  platform?: string;       // Platform selection: "shopify" or "amazon"
}

interface InventoryDataState {
  // Loading states
  loading: boolean;
  error: string | null;
  
  // Core data
  inventoryAnalytics: InventoryAnalyticsResponse | null;
  skuData: SKUData[];
  summaryStats: SKUSummaryStats | null;
  salesKPIs: SalesKPIs | null;
  trendAnalysis: TrendAnalysis | null;
  alertsSummary: AlertsSummary | null;
  
  // Pagination (for SKU data)
  pagination: {
    current_page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  } | null;
  
  // Cache info
  cached: boolean;
  lastUpdated: Date | null;
  
  // Methods
  refresh: (forceRefresh?: boolean) => Promise<void>;
  loadPage: (page: number) => Promise<void>;
  clearCache: () => Promise<void>;
}

export const useInventoryData = (options: UseInventoryDataOptions = {}): InventoryDataState => {
  const {
    refreshInterval = 0,
    fastMode = true,
    pageSize = 50,
    platform = "shopify"
  } = options;

  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inventoryAnalytics, setInventoryAnalytics] = useState<InventoryAnalyticsResponse | null>(null);
  const [skuData, setSKUData] = useState<SKUData[]>([]);
  const [summaryStats, setSummaryStats] = useState<SKUSummaryStats | null>(null);
  const [salesKPIs, setSalesKPIs] = useState<SalesKPIs | null>(null);
  const [trendAnalysis, setTrendAnalysis] = useState<TrendAnalysis | null>(null);
  const [alertsSummary, setAlertsSummary] = useState<AlertsSummary | null>(null);
  const [pagination, setPagination] = useState<InventoryDataState['pagination']>(null);
  const [cached, setCached] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  // Refs for cleanup and request management
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isRequestInProgressRef = useRef<boolean>(false);

  /**
   * Comprehensive data fetcher - gets all inventory data in optimized calls
   */
  const fetchInventoryData = useCallback(async (
    page: number = 1, 
    forceRefresh: boolean = false
  ): Promise<void> => {
    // Prevent multiple simultaneous requests unless forced
    if (isRequestInProgressRef.current && !forceRefresh) {
      console.log('⏳ Request already in progress, skipping...');
      return;
    }

    try {
      isRequestInProgressRef.current = true;
      setLoading(true);
      setError(null);

      // Only abort if there's a genuine conflict (forced refresh)
      if (forceRefresh && abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      console.log(`🔍 Fetching inventory data (platform: ${platform}, page: ${page})...`);
      
      const [skuResponse, analyticsResponse] = await Promise.all([
        api.get('/dashboard/sku-inventory', {
          params: {
            page,
            page_size: pageSize,
            use_cache: !forceRefresh,
            force_refresh: forceRefresh,
            platform: platform,
          },
          signal: abortControllerRef.current.signal,
        }),
        api.get('/dashboard/inventory-analytics', {
          params: {
            fast_mode: fastMode,
            force_refresh: forceRefresh,
            platform: platform,
          },
          signal: abortControllerRef.current.signal,
        })
      ]);

      // Process SKU data - handle both old and new response structures
      if (skuResponse.data?.success) {
        // Handle new response structure where SKUs are directly under data.skus
        // OR old structure where SKUs are under data.sku_inventory.skus
        const skuData = skuResponse.data.skus || skuResponse.data.sku_inventory?.skus || [];
        let summaryStats = skuResponse.data.summary_stats || skuResponse.data.sku_inventory?.summary_stats || null;
        
        // Generate summary stats from SKU data if not provided by API
        if (!summaryStats && skuData.length > 0) {
          summaryStats = {
            total_skus: skuData.length,
            total_inventory_value: skuData.reduce((sum: number, sku: any) => sum + (sku.total_value || 0), 0),
            low_stock_count: skuData.filter((sku: any) => sku.current_availability > 0 && sku.current_availability < 10).length,
            out_of_stock_count: skuData.filter((sku: any) => sku.current_availability <= 0).length,
          };
        }
        
        setSKUData(skuData);
        setPagination(skuResponse.data.pagination || null);
        setSummaryStats(summaryStats);
        setCached(skuResponse.data.cached || false);
        
        console.log(`✅ SKU Data loaded: ${skuData.length} SKUs found`);
      } else {
        console.log("🚨 SKU Response failed:", skuResponse.data?.message || "Unknown error");
        setSKUData([]);
        setSummaryStats(null);
      }

      // Process analytics data
      if (analyticsResponse.data?.success) {
        setInventoryAnalytics(analyticsResponse.data);
        setSalesKPIs(analyticsResponse.data.inventory_analytics.sales_kpis || null);
        setTrendAnalysis(analyticsResponse.data.inventory_analytics.trend_analysis || null);
        setAlertsSummary(analyticsResponse.data.inventory_analytics.alerts_summary || null);
      }

      setCurrentPage(page);
      setLastUpdated(new Date());
      setError(null);
      
      console.log('✅ Inventory data fetched successfully');

    } catch (err: any) {
      // Handle request cancellation (both native AbortError and axios CanceledError)
      if (err.name === 'AbortError' || err.name === 'CanceledError' || err.code === 'ERR_CANCELED') {
        console.log('🚫 Request aborted');
        return;
      }

      console.error('❌ Failed to fetch inventory data:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to fetch inventory data');
      
      // Reset data on error
      setSKUData([]);
      setSummaryStats(null);
      setSalesKPIs(null);
      setTrendAnalysis(null);
      setAlertsSummary(null);
      setPagination(null);
      setInventoryAnalytics(null);
    } finally {
      isRequestInProgressRef.current = false;
      setLoading(false);
    }
  }, [pageSize, fastMode]);

  /**
   * Refresh data with optional force refresh
   */
  const refresh = useCallback(async (forceRefresh: boolean = false): Promise<void> => {
    await fetchInventoryData(currentPage, forceRefresh);
  }, [fetchInventoryData, currentPage]);

  /**
   * Load specific page (for pagination)
   */
  const loadPage = useCallback(async (page: number): Promise<void> => {
    if (page >= 1 && pagination && page <= pagination.total_pages) {
      await fetchInventoryData(page, false);
    }
  }, [fetchInventoryData, pagination]);

  /**
   * Clear cache and refresh
   */
  const clearCache = useCallback(async (): Promise<void> => {
    try {
      await api.delete('/dashboard/sku-cache');
      await refresh(true);
    } catch (err: any) {
      // Handle request cancellation silently
      if (err.name === 'AbortError' || err.name === 'CanceledError' || err.code === 'ERR_CANCELED') {
        console.log('🚫 Cache clear request aborted');
        return;
      }
      
      console.error('❌ Failed to clear cache:', err);
      // Still refresh even if cache clear fails
      await refresh(true);
    }
  }, [refresh]);

  // Initial data load and platform change handling
  useEffect(() => {
    fetchInventoryData(1, false);
  }, [fetchInventoryData, platform]); // Include platform to trigger reload on platform change

  // Auto-refresh setup
  useEffect(() => {
    if (refreshInterval > 0) {
      intervalRef.current = setInterval(() => {
        refresh(false);
      }, refreshInterval);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [refresh, refreshInterval]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Clear any intervals
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      
      // Reset request progress flag
      isRequestInProgressRef.current = false;
      
      // Abort any ongoing requests
      if (abortControllerRef.current) {
        try {
          abortControllerRef.current.abort();
        } catch (error) {
          // Ignore cleanup errors
          console.log('Cleanup: Request already aborted or completed');
        }
      }
    };
  }, []);

  return {
    // Loading states
    loading,
    error,
    
    // Core data
    inventoryAnalytics,
    skuData,
    summaryStats,
    salesKPIs,
    trendAnalysis,
    alertsSummary,
    
    // Pagination
    pagination,
    
    // Cache info
    cached,
    lastUpdated,
    
    // Methods
    refresh,
    loadPage,
    clearCache,
  };
};

export default useInventoryData;
