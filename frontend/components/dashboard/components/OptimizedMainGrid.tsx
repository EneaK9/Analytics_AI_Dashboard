/**
 * Optimized MainGrid Component
 * 
 * Features:
 * - Independent component state management  
 * - React.memo for preventing unnecessary re-renders
 * - Each component manages its own platform and date range
 * - No shared state causing cascading re-renders
 * - Prefetching for better performance
 */

import React, { memo, useCallback, useEffect } from "react";
import Grid from "@mui/material/Grid";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import Copyright from "../internals/components/Copyright";

// Import optimized components
import OptimizedSmartEcommerceMetrics from "../../analytics/OptimizedSmartEcommerceMetrics";
import OptimizedInventoryTrendCharts from "../../analytics/OptimizedInventoryTrendCharts";
import OptimizedAlertsSummary from "../../analytics/OptimizedAlertsSummary";
import InventorySKUList from "../../analytics/InventorySKUList";
import { usePrefetchDashboardData } from "../../hooks/useOptimizedDashboardData";

interface OptimizedMainGridProps {
  dashboardData?: any;
  user?: { client_id: string; company_name: string; email: string };
  dashboardType?: string;
  className?: string;
}

const OptimizedMainGrid: React.FC<OptimizedMainGridProps> = memo(({
  dashboardData,
  user,
  dashboardType = "main",
  className = "",
}) => {
  const { prefetchPlatformData } = usePrefetchDashboardData();

  // Prefetch data for both platforms on component mount for better UX
  useEffect(() => {
    const prefetchData = async () => {
      try {
        // Prefetch Shopify data for 7d and 30d presets
        await Promise.all([
          prefetchPlatformData('shopify', '7d'),
          prefetchPlatformData('shopify', '30d'),
          prefetchPlatformData('amazon', '7d'),
          prefetchPlatformData('amazon', '30d'),
        ]);
        console.log('✅ Dashboard data prefetched successfully');
      } catch (error) {
        console.log('⚠️ Prefetch failed (non-critical):', error);
      }
    };

    // Only prefetch if we have a user (avoid unnecessary calls)
    if (user?.client_id) {
      prefetchData();
    }
  }, [user?.client_id, prefetchPlatformData]);

  // Memoized error handler
  const handleComponentError = useCallback((componentName: string, error: any) => {
    console.error(`Error in ${componentName}:`, error);
  }, []);

  if (!user) {
    return (
      <Box
        className={className}
        sx={{
          width: "100%",
          maxWidth: { sm: "100%", md: "1700px" },
          px: 2,
          py: 4,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "400px",
        }}>
        <Typography variant="h6" color="text.secondary">
          Please log in to view dashboard analytics...
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      className={className}
      sx={{
        width: "100%",
        maxWidth: { sm: "100%", md: "1700px" },
        px: 2,
        py: 2,
        overflow: "hidden",
      }}>

      {/* 📊 SALES PERFORMANCE METRICS */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardHeader
              title="Sales Performance Metrics"
              subheader="Real-time sales metrics with independent platform and date controls"
            />
            <CardContent>
              <OptimizedSmartEcommerceMetrics
                initialPlatform="shopify"
                initialDatePreset="7d"
                refreshInterval={5 * 60 * 1000} // 5 minutes
                showDatePicker={true}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 🚨 ALERTS & NOTIFICATIONS */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardHeader
              title="Alerts & Notifications"
              subheader="Real-time monitoring with independent alert settings"
            />
            <CardContent sx={{ p: 0 }}>
              <OptimizedAlertsSummary
                initialPlatform="shopify"
                initialDatePreset="7d"
                refreshInterval={3 * 60 * 1000} // 3 minutes for alerts
                showDatePicker={true}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 📈 INVENTORY TRENDS */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardHeader
              title="Inventory & Sales Trends"
              subheader="Time-series analysis with independent date range controls"
            />
            <CardContent>
              <OptimizedInventoryTrendCharts
                initialPlatform="shopify"
                initialDatePreset="30d"
                refreshInterval={5 * 60 * 1000} // 5 minutes
                showDatePicker={true}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Additional Analytics Section - Each with Independent Settings */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Amazon Sales Metrics - Independent from Shopify */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Card>
            <CardHeader
              title="Amazon Sales Analytics"
              subheader="Independent Amazon platform metrics"
            />
            <CardContent>
              <OptimizedSmartEcommerceMetrics
                initialPlatform="amazon"
                initialDatePreset="7d"
                refreshInterval={5 * 60 * 1000}
                showDatePicker={true}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Combined Platform Analytics */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Card>
            <CardHeader
              title="Combined Platform Analytics" 
              subheader="Cross-platform metrics and insights"
            />
            <CardContent>
              <OptimizedSmartEcommerceMetrics
                initialPlatform="combined"
                initialDatePreset="30d"
                refreshInterval={10 * 60 * 1000} // 10 minutes for combined data
                showDatePicker={true}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Amazon Trends - Independent from Shopify Trends */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardHeader
              title="Amazon Inventory Trends"
              subheader="Independent Amazon trend analysis"
            />
            <CardContent>
              <OptimizedInventoryTrendCharts
                initialPlatform="amazon"
                initialDatePreset="30d"
                refreshInterval={5 * 60 * 1000}
                showDatePicker={true}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 📦 SKU INVENTORY MANAGEMENT - Uses existing component with platform toggle */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardHeader
              title="SKU Inventory Management"
              subheader="Comprehensive inventory tracking with platform switching"
            />
            <CardContent sx={{ p: 0 }}>
              <InventorySKUList
                clientData={[]} // This component manages its own data
                platform="shopify" // Initial platform
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance Showcase Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12 }}>
          <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
            <CardHeader
              title="🚀 Optimized Dashboard Features"
              subheader="Performance improvements implemented"
              sx={{ color: 'white', '& .MuiCardHeader-subheader': { color: 'rgba(255,255,255,0.8)' } }}
            />
            <CardContent>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr 1fr' }, gap: 3 }}>
                <Box>
                  <Typography variant="h6" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                    ⚡ Independent State
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Each component manages its own platform and date range without affecting others
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="h6" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                    💾 Smart Caching
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    React Query prevents duplicate API calls and provides instant cached responses
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="h6" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                    🎯 Optimized Rendering
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    React.memo and optimized hooks prevent unnecessary component re-renders
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Footer */}
      <Box sx={{ mt: 4, pt: 3, borderTop: '1px solid', borderColor: 'divider' }}>
        <Copyright />
      </Box>
    </Box>
  );
});

OptimizedMainGrid.displayName = 'OptimizedMainGrid';

export default OptimizedMainGrid;
