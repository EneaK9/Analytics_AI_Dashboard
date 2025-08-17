/**
 * Platform-Specific Inventory Analytics Usage Example
 * Demonstrates how to use the new platform parameter for Shopify/Amazon separation
 */

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import PlatformToggle from "../components/ui/PlatformToggle";
import inventoryService from "../lib/inventoryService";

export function PlatformInventoryExample() {
  const [selectedPlatform, setSelectedPlatform] = useState<"shopify" | "amazon">("shopify");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);

  const fetchPlatformData = async (platform: "shopify" | "amazon") => {
    setLoading(true);
    try {
      // Fetch analytics for specific platform
      const analytics = await inventoryService.getInventoryAnalytics(true, false, platform);
      
      // Fetch SKU data for specific platform
      const skuData = await inventoryService.getPaginatedSKUInventory(1, 50, true, false, platform);
      
      setData({ analytics, skuData });
      console.log(`✅ Loaded ${platform} data:`, { analytics, skuData });
    } catch (error) {
      console.error(`❌ Failed to load ${platform} data:`, error);
    } finally {
      setLoading(false);
    }
  };

  const handlePlatformChange = (platform: "shopify" | "amazon") => {
    setSelectedPlatform(platform);
    fetchPlatformData(platform);
  };

  return (
    <div className="space-y-6 p-6">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Platform-Specific Inventory Analytics</CardTitle>
              <p className="text-sm text-gray-600 mt-1">
                Switch between Shopify and Amazon to see platform-separated data
              </p>
            </div>
            <PlatformToggle
              selectedPlatform={selectedPlatform}
              onPlatformChange={handlePlatformChange}
            />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Badge variant="secondary">
                Current Platform: {selectedPlatform === "shopify" ? "Shopify" : "Amazon"}
              </Badge>
              {loading && <Badge variant="outline">Loading...</Badge>}
            </div>

            {/* API Usage Examples */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="border-dashed">
                <CardHeader>
                  <CardTitle className="text-lg">Analytics API</CardTitle>
                </CardHeader>
                <CardContent>
                  <code className="text-sm bg-gray-100 p-2 rounded block">
                    {`GET /api/dashboard/inventory-analytics?platform=${selectedPlatform}`}
                  </code>
                  <p className="text-sm text-gray-600 mt-2">
                    Returns KPIs, trends, and alerts for {selectedPlatform} only
                  </p>
                </CardContent>
              </Card>

              <Card className="border-dashed">
                <CardHeader>
                  <CardTitle className="text-lg">SKU Inventory API</CardTitle>
                </CardHeader>
                <CardContent>
                  <code className="text-sm bg-gray-100 p-2 rounded block">
                    {`GET /api/dashboard/sku-inventory?platform=${selectedPlatform}`}
                  </code>
                  <p className="text-sm text-gray-600 mt-2">
                    Returns paginated SKU list for {selectedPlatform} only
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Data Preview */}
            {data && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Data Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-blue-600">
                        {data.analytics?.inventory_analytics?.data_summary?.total_skus || 0}
                      </p>
                      <p className="text-sm text-gray-600">Total SKUs</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-green-600">
                        {data.skuData?.pagination?.total_count || 0}
                      </p>
                      <p className="text-sm text-gray-600">SKU Records</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-orange-600">
                        {data.analytics?.inventory_analytics?.data_summary?.shopify_products + 
                         data.analytics?.inventory_analytics?.data_summary?.amazon_products || 0}
                      </p>
                      <p className="text-sm text-gray-600">Products</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-purple-600">
                        {data.analytics?.inventory_analytics?.data_summary?.shopify_orders + 
                         data.analytics?.inventory_analytics?.data_summary?.amazon_orders || 0}
                      </p>
                      <p className="text-sm text-gray-600">Orders</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Instructions */}
            <Card className="bg-blue-50">
              <CardContent className="p-4">
                <h4 className="font-semibold text-blue-900 mb-2">How It Works</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• <strong>Shopify:</strong> Shows data only from Shopify tables (products, orders)</li>
                  <li>• <strong>Amazon:</strong> Shows data only from Amazon tables (products, orders)</li>
                  <li>• <strong>Separate Calculations:</strong> KPIs, trends, and alerts calculated per platform</li>
                  <li>• <strong>Cache Separation:</strong> Platform-specific caching for optimal performance</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
