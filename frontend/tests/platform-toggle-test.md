# Platform Toggle Testing Guide

## Issue Resolution

### ✅ **Fixed: TypeError "Cannot read properties of undefined"**

**Problem**: AlertsSummary component was trying to access `alertsSummary.sales_spike_alerts[0]` when the array was undefined.

**Solution**: 
- Added proper null checks: `((alertsSummary.sales_spike_alerts || [])[0]?.message)`
- Updated component to handle both old and new data structures from backend
- Added fallback to `alertsSummary.detailed_alerts?.*_alerts` arrays

### ✅ **Fixed: Platform Toggle Not Showing**

**Problem**: Components weren't using the platform-aware useInventoryData hook.

**Solution**:
- Updated `useInventoryData` hook to support `platform` parameter
- Updated `SmartInventoryDashboard` to pass `selectedPlatform` to the hook
- Added force refresh when platform changes
- Updated `AlertsSummary` to use shared hook instead of separate API call

## Testing Steps

### 1. **Basic Platform Toggle**
```typescript
// Navigate to SmartInventoryDashboard component
// You should see:
// - Shopify/Amazon toggle buttons in header
// - Platform indicator badge showing current selection
// - Data automatically refreshes when switching platforms
```

### 2. **Data Separation Verification**
```bash
# Check network requests when switching platforms:

# Shopify selected:
GET /api/dashboard/inventory-analytics?platform=shopify
GET /api/dashboard/sku-inventory?platform=shopify

# Amazon selected:
GET /api/dashboard/inventory-analytics?platform=amazon
GET /api/dashboard/sku-inventory?platform=amazon
```

### 3. **Alert Component Testing**
```typescript
// AlertsSummary should:
// - Show platform name in header: "Alerts Summary (Shopify)" or "Alerts Summary (Amazon)"
// - Handle empty alert arrays gracefully
// - Show different data when platform changes
// - Use shared data (no separate API calls)
```

### 4. **Backend Verification**
```python
# Test backend endpoints directly:
curl "localhost:8000/api/dashboard/inventory-analytics?platform=shopify"
curl "localhost:8000/api/dashboard/inventory-analytics?platform=amazon"

# Should return different data based on platform parameter
```

## Expected Behavior

### **Shopify Mode**
- Only shows data from `{client_id}_shopify_products` and `{client_id}_shopify_orders` tables
- KPIs, trends, alerts calculated from Shopify data only
- Cache key includes platform: `{client_id}_shopify`

### **Amazon Mode**  
- Only shows data from `{client_id}_amazon_products` and `{client_id}_amazon_orders` tables
- KPIs, trends, alerts calculated from Amazon data only
- Cache key includes platform: `{client_id}_amazon`

### **UI Indicators**
- ✅ Toggle buttons show current selection with colors
- ✅ Header badge shows current platform
- ✅ Loading states during platform switches
- ✅ Alerts component shows platform-specific data

## Troubleshooting

### **If toggle still not showing:**
1. Check if `SmartInventoryDashboard` is being used in your pages
2. Verify the component import paths
3. Check browser console for any remaining JavaScript errors

### **If data not switching:**
1. Verify network requests include `platform` parameter
2. Check backend logs for platform parameter handling
3. Clear browser cache and localStorage

### **If alerts still error:**
1. Check browser console for specific error messages
2. Verify alert data structure matches expected format
3. Check if backend is returning `detailed_alerts` structure

## API Response Examples

### Shopify Response
```json
{
  "inventory_analytics": {
    "data_summary": {
      "platform": "shopify",
      "shopify_products": 150,
      "shopify_orders": 230,
      "amazon_products": 0,
      "amazon_orders": 0
    }
  }
}
```

### Amazon Response
```json
{
  "inventory_analytics": {
    "data_summary": {
      "platform": "amazon", 
      "shopify_products": 0,
      "shopify_orders": 0,
      "amazon_products": 85,
      "amazon_orders": 120
    }
  }
}
```

## Performance Notes

- Platform-specific caching prevents cross-contamination
- Force refresh on platform change ensures fresh data
- Shared useInventoryData hook prevents duplicate API calls
- Network requests are properly tagged with platform parameter
