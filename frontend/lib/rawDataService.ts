/**
 * Raw Data Service
 * Dedicated service for fetching and managing raw data tables from the backend
 */

import api from './axios';

// Types for raw data tables (updated for pagination)
export interface RawDataResponse {
  client_id: string;
  table_key: string;
  display_name: string;
  table_name: string;
  platform: 'shopify' | 'amazon';
  data_type: 'products' | 'orders';
  columns: string[];
  data: any[];
  pagination: {
    current_page: number;
    page_size: number;
    total_records: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  search?: string;
  search_fallback?: boolean;
  message: string;
}

export interface RawDataFilters {
  platform: 'shopify' | 'amazon';
  dataType: 'products' | 'orders';
  page?: number;
  pageSize?: number;
  search?: string;
}

class RawDataService {
  /**
   * Fetch raw data tables for a specific client
   */
  async fetchRawDataTables(
    clientId: string, 
    filters: RawDataFilters
  ): Promise<RawDataResponse> {
    try {
      const params: any = {
        platform: filters.platform,
        data_type: filters.dataType,
        page: filters.page || 1,
        page_size: filters.pageSize || 50,
      };
      
      if (filters.search?.trim()) {
        params.search = filters.search.trim();
      }
      
      const response = await api.get(`/data/raw/${clientId}`, { params });
      return response.data as RawDataResponse;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || error.message || 'Failed to fetch raw data tables');
    }
  }

  /**
   * Get summary statistics for current data
   */
  getSummary(rawData: RawDataResponse | null): { 
    totalRecords: number; 
    currentPage: number; 
    totalPages: number; 
    platform: string; 
    dataType: string;
  } {
    if (!rawData) {
      return {
        totalRecords: 0,
        currentPage: 0,
        totalPages: 0,
        platform: '',
        dataType: ''
      };
    }
    
    return {
      totalRecords: rawData.pagination.total_records,
      currentPage: rawData.pagination.current_page,
      totalPages: rawData.pagination.total_pages,
      platform: rawData.platform,
      dataType: rawData.data_type
    };
  }

  /**
   * Format table data for DataTables component
   */
  formatTableForDataTables(rawData: RawDataResponse | null): {
    display_name: string;
    columns: string[];
    data: any[];
    pagination: any;
    metadata: {
      platform: string;
      data_type: string;
      table_name: string;
    };
  } | null {
    if (!rawData) return null;
    
    return {
      display_name: rawData.display_name,
      columns: rawData.columns,
      data: rawData.data,
      pagination: rawData.pagination,
      metadata: {
        platform: rawData.platform,
        data_type: rawData.data_type,
        table_name: rawData.table_name
      }
    };
  }


}

// Export singleton instance
export const rawDataService = new RawDataService();
export default rawDataService;
