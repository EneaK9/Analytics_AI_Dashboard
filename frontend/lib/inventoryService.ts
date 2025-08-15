/**
 * Inventory Analytics Service
 * Handles API calls for comprehensive inventory analysis
 */

import api from './axios';

export interface InventoryAnalyticsResponse {
  client_id: string;
  success: boolean;
  timestamp?: string;
  data_type?: string;
  schema_type?: string;
  total_records: number;
  inventory_analytics: InventoryAnalytics;
  cached: boolean;
  processing_time: string;
  error?: string;
  message?: string;
}

export interface InventoryAnalytics {
  success: boolean;
  timestamp: string;
  data_summary: {
    total_records: number;
    total_skus: number;
    analysis_period: string;
    data_completeness: number;
  };
  sku_inventory: {
    skus: SKUData[];
    summary_stats: SKUSummaryStats;
  };
  sales_kpis: SalesKPIs;
  trend_analysis: TrendAnalysis;
  alerts_summary: AlertsSummary;
  recommendations: string[];
  message?: string;
  error?: string;
}

export interface SKUData {
  sku_code: string;
  item_name: string;
  on_hand_inventory: number;
  incoming_inventory: number;
  outgoing_inventory: number;
  current_availability: number;
  unit_price: number;
  total_value: number;
  units_sold: number;
  total_revenue: number;
  last_updated: string;
  stock_status: 'in_stock' | 'low_stock' | 'out_of_stock' | 'overstock';
}

export interface SKUSummaryStats {
  total_skus: number;
  total_inventory_value: number;
  low_stock_count: number;
  out_of_stock_count: number;
  overstock_count: number;
}

export interface SalesKPIs {
  total_sales_7_days: KPIMetric;
  total_sales_30_days: KPIMetric;
  total_sales_90_days: KPIMetric;
  inventory_turnover_rate: KPIMetric;
  days_of_stock_remaining: KPIMetric;
  average_order_value: KPIMetric;
  total_active_skus: number;
}

export interface KPIMetric {
  value: number;
  display_value: string;
  units_sold?: number;
  change_percentage?: string;
  trend?: 'up' | 'down' | 'neutral';
  description?: string;
  status?: 'healthy' | 'warning' | 'critical';
}

export interface TrendAnalysis {
  daily_sales_trends: TrendDataPoint[];
  daily_inventory_trends: TrendDataPoint[];
  weekly_sales_trends: TrendDataPoint[];
  sales_comparison: ComparisonData;
  trend_summary: {
    overall_direction: string;
    growth_rate: number;
    volatility: number;
  };
}

export interface TrendDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface ComparisonData {
  current_period: number;
  previous_period: number;
  change_percentage: number;
  period_label: string;
}

export interface AlertsSummary {
  low_stock_alerts: Alert[];
  overstock_alerts: Alert[];
  sales_spike_alerts: Alert[];
  sales_slowdown_alerts: Alert[];
  summary: {
    total_alerts: number;
    critical_alerts: number;
    high_priority_alerts: number;
    affected_skus: string[];
    total_affected_skus: number;
  };
}

export interface Alert {
  type: 'low_stock' | 'out_of_stock' | 'overstock' | 'sales_spike' | 'sales_slowdown';
  sku_code?: string;
  item_name?: string;
  current_availability?: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  recommendation: string;
  affected_skus: string[];
  current_sales?: number;
  previous_sales?: number;
}

class InventoryService {
  private baseURL = '/dashboard';

  /**
   * Get comprehensive inventory analytics
   */
  async getInventoryAnalytics(
    fastMode: boolean = true,
    forceRefresh: boolean = false
  ): Promise<InventoryAnalyticsResponse> {
    try {
      console.log('🔍 Fetching inventory analytics...');
      
      const response = await api.get<InventoryAnalyticsResponse>(
        `${this.baseURL}/inventory-analytics`,
        {
          params: {
            fast_mode: fastMode,
            force_refresh: forceRefresh,
          },
        }
      );

      console.log('✅ Inventory analytics fetched successfully:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('❌ Failed to fetch inventory analytics:', error);
      
      // Return error response structure
      return {
        client_id: 'unknown',
        success: false,
        total_records: 0,
        inventory_analytics: {
          success: false,
          timestamp: new Date().toISOString(),
          error: error.response?.data?.detail || error.message || 'Failed to fetch inventory analytics',
          data_summary: { total_records: 0, total_skus: 0, analysis_period: '', data_completeness: 0 },
          sku_inventory: { skus: [], summary_stats: { total_skus: 0, total_inventory_value: 0, low_stock_count: 0, out_of_stock_count: 0, overstock_count: 0 } },
          sales_kpis: {} as SalesKPIs,
          trend_analysis: {} as TrendAnalysis,
          alerts_summary: { summary: { total_alerts: 0, critical_alerts: 0, high_priority_alerts: 0, affected_skus: [], total_affected_skus: 0 } } as AlertsSummary,
          recommendations: []
        },
        cached: false,
        processing_time: '0ms',
        error: error.response?.data?.detail || error.message || 'Failed to fetch inventory analytics'
      };
    }
  }

  /**
   * Get only SKU inventory data
   */
  async getSKUInventory(): Promise<SKUData[]> {
    try {
      const response = await this.getInventoryAnalytics();
      return response.inventory_analytics.sku_inventory.skus;
    } catch (error) {
      console.error('❌ Failed to fetch SKU inventory:', error);
      return [];
    }
  }

  /**
   * Get only sales KPIs
   */
  async getSalesKPIs(): Promise<SalesKPIs | null> {
    try {
      const response = await this.getInventoryAnalytics();
      return response.inventory_analytics.sales_kpis;
    } catch (error) {
      console.error('❌ Failed to fetch sales KPIs:', error);
      return null;
    }
  }

  /**
   * Get only trend analysis data
   */
  async getTrendAnalysis(): Promise<TrendAnalysis | null> {
    try {
      const response = await this.getInventoryAnalytics();
      return response.inventory_analytics.trend_analysis;
    } catch (error) {
      console.error('❌ Failed to fetch trend analysis:', error);
      return null;
    }
  }

  /**
   * Get only alerts summary
   */
  async getAlertsSummary(): Promise<AlertsSummary | null> {
    try {
      const response = await this.getInventoryAnalytics();
      return response.inventory_analytics.alerts_summary;
    } catch (error) {
      console.error('❌ Failed to fetch alerts summary:', error);
      return null;
    }
  }

  /**
   * Check if inventory analytics are available
   */
  async isInventoryAnalyticsAvailable(): Promise<boolean> {
    try {
      const response = await this.getInventoryAnalytics();
      return response.success && response.inventory_analytics.data_summary.total_records > 0;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get inventory analytics summary stats
   */
  async getInventorySummary(): Promise<{
    totalSKUs: number;
    totalValue: number;
    alertsCount: number;
    stockHealthScore: number;
  }> {
    try {
      const response = await this.getInventoryAnalytics();
      const analytics = response.inventory_analytics;
      
      const totalSKUs = analytics.sku_inventory.summary_stats.total_skus;
      const totalValue = analytics.sku_inventory.summary_stats.total_inventory_value;
      const alertsCount = analytics.alerts_summary.summary.total_alerts;
      
      // Calculate stock health score (0-100)
      const lowStockCount = analytics.sku_inventory.summary_stats.low_stock_count;
      const outOfStockCount = analytics.sku_inventory.summary_stats.out_of_stock_count;
      const healthyStock = totalSKUs - lowStockCount - outOfStockCount;
      const stockHealthScore = totalSKUs > 0 ? Math.round((healthyStock / totalSKUs) * 100) : 100;
      
      return {
        totalSKUs,
        totalValue,
        alertsCount,
        stockHealthScore
      };
    } catch (error) {
      console.error('❌ Failed to fetch inventory summary:', error);
      return {
        totalSKUs: 0,
        totalValue: 0,
        alertsCount: 0,
        stockHealthScore: 0
      };
    }
  }
}

// Export singleton instance
export const inventoryService = new InventoryService();
export default inventoryService;
