/**
 * Global Data Store using Zustand
 * Centralized state management for dashboard data with API call deduplication
 */

import React from 'react';
import { create } from 'zustand';
import api from '../lib/axios';

// Cache duration (5 minutes)
const CACHE_DURATION = 5 * 60 * 1000;

// Helper to check if data is stale
const isDataStale = (lastFetched: number | null): boolean => {
  if (!lastFetched) return true;
  return Date.now() - lastFetched > CACHE_DURATION;
};

interface GlobalDataState {
  // Main data from the two endpoints we actually use
  inventoryData: any | null;
  skuData: any[]; // Always an array, never null
  dashboardAnalytics: any | null;
  
  // Loading states
  loading: {
    inventoryData: boolean;
    skuData: boolean;
    dashboardAnalytics: boolean;
  };
  
  // Error states
  errors: {
    inventoryData: string | null;
    skuData: string | null;
    dashboardAnalytics: string | null;
  };
  
  // Cache metadata
  lastFetched: {
    inventoryData: number | null;
    skuData: number | null;
    dashboardAnalytics: number | null;
  };
  
  // Request tracking to prevent duplicate calls
  activeRequests: Set<string>;
  
  // Filters
  filters: {
    platform: 'shopify' | 'amazon' | 'combined';
    dateRange: '7d' | '30d' | '90d' | 'custom';
    startDate?: string;
    endDate?: string;
  };
  
  // Actions
  setFilters: (filters: Partial<GlobalDataState['filters']>) => void;
  fetchInventoryData: (forceRefresh?: boolean) => Promise<void>;
  fetchSKUData: (page?: number, forceRefresh?: boolean) => Promise<void>;
  fetchDashboardAnalytics: (forceRefresh?: boolean) => Promise<void>;
  fetchAllData: (forceRefresh?: boolean) => Promise<void>;
  clearError: (dataType: keyof GlobalDataState['errors']) => void;
}

export const useGlobalDataStore = create<GlobalDataState>()((set, get) => ({
    // Initial state
    inventoryData: null,
    skuData: [], // Initialize as empty array instead of null
    dashboardAnalytics: null,
    
    loading: {
      inventoryData: false,
      skuData: false,
      dashboardAnalytics: false,
    },
    
    errors: {
      inventoryData: null,
      skuData: null,
      dashboardAnalytics: null,
    },
    
    lastFetched: {
      inventoryData: null,
      skuData: null,
      dashboardAnalytics: null,
    },
    
    activeRequests: new Set(),
    
    filters: {
      platform: 'shopify',
      dateRange: '7d',
    },
    
    // Actions
    setFilters: (newFilters) => {
      set((state) => ({
        filters: { ...state.filters, ...newFilters },
      }));
    },
    
    fetchInventoryData: async (forceRefresh = false) => {
      const state = get();
      const requestKey = 'inventoryData';
      
      // Check if already loading or cached data is fresh
      if (state.activeRequests.has(requestKey)) return;
      if (!forceRefresh && !isDataStale(state.lastFetched.inventoryData)) return;
      
      set((state) => ({
        activeRequests: new Set(state.activeRequests).add(requestKey),
        loading: { ...state.loading, inventoryData: true },
        errors: { ...state.errors, inventoryData: null },
      }));
      
      try {
        const { platform } = state.filters;
        const params = {
          platform: platform === 'combined' ? undefined : platform,
          fast_mode: true,
          force_refresh: forceRefresh,
        };
        
        const response = await api.get('/dashboard/inventory-analytics', { params });
        
        set((state) => ({
          inventoryData: response.data,
          lastFetched: { ...state.lastFetched, inventoryData: Date.now() },
          loading: { ...state.loading, inventoryData: false },
        }));
      } catch (error: any) {
        set((state) => ({
          errors: { ...state.errors, inventoryData: error.message || 'Failed to fetch inventory data' },
          loading: { ...state.loading, inventoryData: false },
        }));
      } finally {
        set((state) => {
          const newActiveRequests = new Set(state.activeRequests);
          newActiveRequests.delete(requestKey);
          return { activeRequests: newActiveRequests };
        });
      }
    },
    
    fetchSKUData: async (page = 1, forceRefresh = false) => {
      const state = get();
      const requestKey = `skuData-${page}`;
      
      if (state.activeRequests.has(requestKey)) return;
      if (!forceRefresh && !isDataStale(state.lastFetched.skuData)) return;
      
      set((state) => ({
        activeRequests: new Set(state.activeRequests).add(requestKey),
        loading: { ...state.loading, skuData: true },
        errors: { ...state.errors, skuData: null },
      }));
      
      try {
        const { platform } = state.filters;
        const params = {
          platform: platform === 'combined' ? undefined : platform,
          page,
          page_size: 20,
          use_cache: !forceRefresh,
          force_refresh: forceRefresh,
        };
        
        const response = await api.get('/dashboard/sku-inventory', { params });
        
        // Extract SKU array from response - handle different response structures
        let skuArray = [];
        if (response.data?.success) {
          skuArray = response.data.skus || response.data.sku_inventory?.skus || [];
        } else if (Array.isArray(response.data)) {
          skuArray = response.data;
        } else if (response.data?.data && Array.isArray(response.data.data)) {
          skuArray = response.data.data;
        }
        
        set((state) => ({
          skuData: skuArray, // Ensure it's always an array
          lastFetched: { ...state.lastFetched, skuData: Date.now() },
          loading: { ...state.loading, skuData: false },
        }));
      } catch (error: any) {
        set((state) => ({
          errors: { ...state.errors, skuData: error.message || 'Failed to fetch SKU data' },
          loading: { ...state.loading, skuData: false },
          skuData: [], // Reset to empty array on error
        }));
      } finally {
        set((state) => {
          const newActiveRequests = new Set(state.activeRequests);
          newActiveRequests.delete(requestKey);
          return { activeRequests: newActiveRequests };
        });
      }
    },
    
    fetchDashboardAnalytics: async (forceRefresh = false) => {
      const state = get();
      const requestKey = 'dashboardAnalytics';
      
      if (state.activeRequests.has(requestKey)) return;
      if (!forceRefresh && !isDataStale(state.lastFetched.dashboardAnalytics)) return;
      
      set((state) => ({
        activeRequests: new Set(state.activeRequests).add(requestKey),
        loading: { ...state.loading, dashboardAnalytics: true },
        errors: { ...state.errors, dashboardAnalytics: null },
      }));
      
      try {
        const response = await api.get('/dashboard/metrics?fast_mode=true');
        
        set((state) => ({
          dashboardAnalytics: response.data?.llm_analysis || null,
          lastFetched: { ...state.lastFetched, dashboardAnalytics: Date.now() },
          loading: { ...state.loading, dashboardAnalytics: false },
        }));
      } catch (error: any) {
        set((state) => ({
          errors: { ...state.errors, dashboardAnalytics: error.message || 'Failed to fetch dashboard analytics' },
          loading: { ...state.loading, dashboardAnalytics: false },
        }));
      } finally {
        set((state) => {
          const newActiveRequests = new Set(state.activeRequests);
          newActiveRequests.delete(requestKey);
          return { activeRequests: newActiveRequests };
        });
      }
    },
    
    fetchAllData: async (forceRefresh = false) => {
      // Fetch all data concurrently - SIMPLE AND SAFE
      const promises = [
        get().fetchInventoryData(forceRefresh),
        get().fetchSKUData(1, forceRefresh),
        get().fetchDashboardAnalytics(forceRefresh),
      ];
      
      await Promise.allSettled(promises);
    },
    
    clearError: (dataType) => {
      set((state) => ({
        errors: { ...state.errors, [dataType]: null },
      }));
    },
  }));

// Stable selectors using individual properties to prevent re-renders
export const useInventoryData = () => {
  const data = useGlobalDataStore((state) => state.inventoryData);
  const loading = useGlobalDataStore((state) => state.loading.inventoryData);
  const error = useGlobalDataStore((state) => state.errors.inventoryData);
  const fetch = useGlobalDataStore((state) => state.fetchInventoryData);
  
  return { data, loading, error, fetch };
};

export const useSKUData = () => {
  const data = useGlobalDataStore((state) => state.skuData);
  const loading = useGlobalDataStore((state) => state.loading.skuData);
  const error = useGlobalDataStore((state) => state.errors.skuData);
  const fetch = useGlobalDataStore((state) => state.fetchSKUData);
  
  return { data, loading, error, fetch };
};

export const useDashboardAnalytics = () => {
  const data = useGlobalDataStore((state) => state.dashboardAnalytics);
  const loading = useGlobalDataStore((state) => state.loading.dashboardAnalytics);
  const error = useGlobalDataStore((state) => state.errors.dashboardAnalytics);
  const fetch = useGlobalDataStore((state) => state.fetchDashboardAnalytics);
  
  return { data, loading, error, fetch };
};

export const useFilters = () => {
  const filters = useGlobalDataStore((state) => state.filters);
  const setFilters = useGlobalDataStore((state) => state.setFilters);
  
  return { filters, setFilters };
};

export const useGlobalLoading = () => {
  const loadingStates = useGlobalDataStore((state) => state.loading);
  // Use useMemo to prevent recalculation on every render
  const isLoading = React.useMemo(() => 
    Object.values(loadingStates).some(Boolean), 
    [loadingStates]
  );
  
  return { isLoading, loadingStates };
};