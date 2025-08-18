/**
 * Smart Inventory Dashboard
 * Uses single API call to power multiple analytics components
 */

"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { TrendingUp, TrendingDown, Package, AlertTriangle, DollarSign, BarChart3, ShoppingCart, Package2 } from "lucide-react";
import useInventoryData from "../../hooks/useInventoryData";
import InventorySKUList from "./InventorySKUList";
import { formatCurrency } from "../../lib/utils";

interface SmartInventoryDashboardProps {
  clientData?: any[];
  refreshInterval?: number;
}

export default function SmartInventoryDashboard({
  clientData,
  refreshInterval = 300000, // 5 minutes
}: SmartInventoryDashboardProps) {
  
  // Platform state management
  const [selectedPlatform, setSelectedPlatform] = useState<"shopify" | "amazon">("shopify");
  
  // Single API call for ALL inventory data - no more multiple requests!
  const {
    loading,
    error,
    skuData,
    summaryStats,
    salesKPIs,
    trendAnalysis,
    alertsSummary,
    cached,
    lastUpdated,
    refresh,
  } = useInventoryData({
    refreshInterval,
    fastMode: true,
    platform: selectedPlatform,
  });

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="h-32">
              <CardContent className="p-6">
                <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-300 rounded w-1/2"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <CardContent className="p-6">
          <div className="flex items-center space-x-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            <span>Failed to load inventory data: {error}</span>
          </div>
          <button
            onClick={() => refresh(true)}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with platform toggle and refresh info */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Inventory Analytics</h2>
          <p className="text-sm text-gray-600">
            {lastUpdated && `Last updated: ${lastUpdated.toLocaleTimeString()}`}
            {cached && (
              <Badge variant="outline" className="ml-2">
                Cached
              </Badge>
            )}
            <Badge variant="secondary" className="ml-2">
              {selectedPlatform === "shopify" ? "Shopify" : "Amazon"} Data
            </Badge>
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Platform Toggle */}
          <div className="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
                      <button
            onClick={() => {
              setSelectedPlatform("shopify");
              refresh(true); // Force refresh when platform changes
            }}
            className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedPlatform === "shopify"
                ? "bg-white text-green-700 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <ShoppingCart className="h-4 w-4" />
            <span>Shopify</span>
          </button>
          <button
            onClick={() => {
              setSelectedPlatform("amazon");
              refresh(true); // Force refresh when platform changes
            }}
            className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedPlatform === "amazon"
                ? "bg-white text-orange-700 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <Package2 className="h-4 w-4" />
            <span>Amazon</span>
          </button>
          </div>
          
          <button
            onClick={() => refresh(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Refresh Data
          </button>
        </div>
      </div>

      {/* KPI Summary Cards - All from one API call */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total SKUs */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total SKUs</p>
                <p className="text-2xl font-bold">{summaryStats?.total_skus || 0}</p>
              </div>
              <Package className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        {/* Total Inventory Value */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Inventory Value</p>
                <p className="text-2xl font-bold">
                  {formatCurrency(summaryStats?.total_inventory_value || 0)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        {/* Low Stock Alerts */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Low Stock</p>
                <p className="text-2xl font-bold text-orange-600">
                  {summaryStats?.low_stock_count || 0}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>

        {/* Out of Stock */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Out of Stock</p>
                <p className="text-2xl font-bold text-red-600">
                  {summaryStats?.out_of_stock_count || 0}
                </p>
              </div>
              <BarChart3 className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sales KPIs - Also from same API call */}
      {salesKPIs && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Sales (7 Days)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold">
                  {salesKPIs.total_sales_7_days?.display_value || "N/A"}
                </span>
                {salesKPIs.total_sales_7_days?.trend === "up" ? (
                  <TrendingUp className="h-5 w-5 text-green-600" />
                ) : salesKPIs.total_sales_7_days?.trend === "down" ? (
                  <TrendingDown className="h-5 w-5 text-red-600" />
                ) : null}
              </div>
              {salesKPIs.total_sales_7_days?.change_percentage && (
                <p className="text-sm text-gray-600 mt-1">
                  {salesKPIs.total_sales_7_days.change_percentage} vs last period
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Sales (30 Days)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold">
                  {salesKPIs.total_sales_30_days?.display_value || "N/A"}
                </span>
                {salesKPIs.total_sales_30_days?.trend === "up" ? (
                  <TrendingUp className="h-5 w-5 text-green-600" />
                ) : salesKPIs.total_sales_30_days?.trend === "down" ? (
                  <TrendingDown className="h-5 w-5 text-red-600" />
                ) : null}
              </div>
              {salesKPIs.total_sales_30_days?.change_percentage && (
                <p className="text-sm text-gray-600 mt-1">
                  {salesKPIs.total_sales_30_days.change_percentage} vs last period
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Average Order Value
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold">
                  {salesKPIs.average_order_value?.display_value || "N/A"}
                </span>
                {salesKPIs.average_order_value?.trend === "up" ? (
                  <TrendingUp className="h-5 w-5 text-green-600" />
                ) : salesKPIs.average_order_value?.trend === "down" ? (
                  <TrendingDown className="h-5 w-5 text-red-600" />
                ) : null}
              </div>
              {salesKPIs.average_order_value?.change_percentage && (
                <p className="text-sm text-gray-600 mt-1">
                  {salesKPIs.average_order_value.change_percentage} vs last period
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Active Alerts */}
      {alertsSummary && alertsSummary.summary.total_alerts > 0 && (
        <Card className="border-orange-200">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              <span>Active Alerts ({alertsSummary.summary.total_alerts})</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alertsSummary.low_stock_alerts.slice(0, 3).map((alert, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-orange-50 rounded">
                  <span className="text-sm">{alert.message}</span>
                  <Badge variant="secondary">{alert.severity}</Badge>
                </div>
              ))}
              {alertsSummary.summary.total_alerts > 3 && (
                <p className="text-sm text-gray-600">
                  +{alertsSummary.summary.total_alerts - 3} more alerts
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* SKU Data Table - Same data, no additional API call */}
      <Card>
        <CardHeader>
          <CardTitle>SKU Inventory Details</CardTitle>
          <p className="text-sm text-gray-600">
            Showing {skuData.length} SKUs from the same API call
          </p>
        </CardHeader>
        <CardContent>
          {/* Pass the fetched data directly to avoid duplicate API calls */}
          <InventorySKUList 
            clientData={clientData} 
            refreshInterval={0} // Disable separate refresh since we handle it here
            platform={selectedPlatform}
            skuData={skuData}
            summaryStats={summaryStats}
            loading={loading}
            error={error}
          />
        </CardContent>
      </Card>
    </div>
  );
}
