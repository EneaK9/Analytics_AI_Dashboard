# Dashboard Inventory Analytics API

Complete inventory analytics endpoint providing **exactly** the SKU lists, KPIs, trends, and alerts requested for dashboard consumption.

## 🎯 **Endpoint**

```
GET /api/dashboard/inventory-analytics
Authorization: Bearer {token}
```

**Automatically detects organized tables and provides enhanced analytics, or falls back to legacy data.**

## 📊 **Complete Response Structure**

```json
{
  "client_id": "3b619a14-3cd8-49fa-9c24-d8df5e54c452",
  "success": true,
  "message": "Dashboard analytics from organized data - 120 products, 85 orders",
  "timestamp": "2025-01-15T10:30:00Z",
  "data_type": "dashboard_inventory_analytics",
  "total_records": 250,
  "data_source": "organized_tables",
  "inventory_analytics": {
    
    // 📦 SKU LIST - Complete inventory details
    "sku_list": [
      {
        "platform": "shopify",
        "item_name": "Ray Scrub Top",
        "sku_code": "ray-blk-s",
        "variant_title": "Black / S",
        "on_hand_inventory": 15,
        "incoming_inventory": 0,          // Pending receipts
        "outgoing_inventory": 3,          // Sales/Shipments
        "current_availability": 12,       // On-hand + Incoming - Outgoing
        "price": 39.50,
        "option1": "Black",
        "option2": "S"
      },
      {
        "platform": "amazon",
        "item_name": "Medical Device Pro",
        "sku_code": "B08XYZ123",
        "asin": "B08XYZ123", 
        "on_hand_inventory": 8,
        "incoming_inventory": 0,
        "outgoing_inventory": 2,
        "current_availability": 6,
        "price": 299.99,
        "brand": "MedBrand"
      }
    ],
    
    // 📈 KPI CHARTS - Specific time-based metrics
    "kpi_charts": {
      "total_sales_7_days": {
        "revenue": 2450.75,
        "units": 25,
        "orders": 18
      },
      "total_sales_30_days": {
        "revenue": 12680.50,
        "units": 145,
        "orders": 85
      },
      "total_sales_90_days": {
        "revenue": 35920.25,
        "units": 420,
        "orders": 245
      },
      "inventory_turnover_rate": 2.8,    // Units sold ÷ Average inventory
      "days_stock_remaining": 45.2,      // On-hand inventory ÷ Average daily sales
      "avg_daily_sales": 4.8,
      "total_inventory_units": 2450
    },
    
    // 📊 TREND VISUALIZATIONS - Chart-ready data
    "trend_visualizations": {
      "daily_data_90_days": [
        {
          "date": "2025-01-15",
          "revenue": 145.50,
          "units_sold": 3,
          "orders": 2,
          "inventory_level": 2450
        }
        // ... 90 days of data
      ],
      "inventory_levels_chart": [
        {
          "date": "2025-01-15",
          "inventory_level": 2450
        }
        // ... time-series data for 7/30/90-day ranges
      ],
      "units_sold_chart": [
        {
          "date": "2025-01-15", 
          "units_sold": 3
        }
        // ... units sold time-series
      ],
      "sales_comparison": {
        "current_period_avg_revenue": 422.68,    // Current 30-day average
        "historical_avg_revenue": 380.15,        // Previous 30-day average
        "revenue_change_percent": 11.2,          // vs historical
        "current_period_avg_units": 4.8,
        "historical_avg_units": 4.2,
        "units_change_percent": 14.3
      }
    },
    
    // 🚨 ALERTS SUMMARY - Actionable alerts with counts
    "alerts_summary": {
      "summary_counts": {
        "low_stock_alerts": 12,
        "overstock_alerts": 3,
        "sales_spike_alerts": 1,
        "sales_slowdown_alerts": 0,
        "total_alerts": 16
      },
      "detailed_alerts": {
        "low_stock_alerts": [
          {
            "platform": "shopify",
            "sku": "ray-blk-s",
            "item_name": "Ray Scrub Top",
            "current_stock": 2,
            "severity": "high"          // critical | high | medium
          }
        ],
        "overstock_alerts": [
          {
            "platform": "amazon",
            "sku": "B08ABC123",
            "item_name": "Bulk Medical Supplies",
            "current_stock": 150,
            "estimated_value": 4500.00
          }
        ],
        "sales_spike_alerts": [
          {
            "message": "Sales increased by 65.2% in the last 7 days",
            "recent_revenue": 2450.75,
            "historical_revenue": 1483.20,
            "change_percent": 65.2
          }
        ],
        "sales_slowdown_alerts": []
      },
      "quick_links": {
        "view_low_stock": "/dashboard/alerts/low-stock?client_id=3b619a14-3cd8-49fa-9c24-d8df5e54c452",
        "view_overstock": "/dashboard/alerts/overstock?client_id=3b619a14-3cd8-49fa-9c24-d8df5e54c452",
        "view_sales_alerts": "/dashboard/alerts/sales?client_id=3b619a14-3cd8-49fa-9c24-d8df5e54c452"
      }
    },
    
    // 📋 DATA SUMMARY
    "data_summary": {
      "shopify_products": 120,
      "shopify_orders": 85,
      "amazon_products": 45,
      "amazon_orders": 30
    }
  }
}
```

## 🎨 **Frontend Usage Examples**

### **SKU List Table**
```javascript
const analytics = response.inventory_analytics;
const skuList = analytics.sku_list;

// Render SKU table
skuList.forEach(sku => {
  console.log(`${sku.item_name} (${sku.sku_code})`);
  console.log(`On-hand: ${sku.on_hand_inventory}`);
  console.log(`Outgoing: ${sku.outgoing_inventory}`);
  console.log(`Available: ${sku.current_availability}`);
});
```

### **KPI Dashboard Cards**
```javascript
const kpis = analytics.kpi_charts;

// Sales KPI cards
const sales7Days = kpis.total_sales_7_days;
const sales30Days = kpis.total_sales_30_days;
const sales90Days = kpis.total_sales_90_days;

// Inventory KPIs
const turnoverRate = kpis.inventory_turnover_rate;
const daysRemaining = kpis.days_stock_remaining;
```

### **Trend Charts**
```javascript
const trends = analytics.trend_visualizations;

// Line chart data for inventory levels
const inventoryChart = trends.inventory_levels_chart.map(d => ({
  x: d.date,
  y: d.inventory_level
}));

// Line chart data for units sold
const salesChart = trends.units_sold_chart.map(d => ({
  x: d.date, 
  y: d.units_sold
}));

// Comparison bar chart
const comparison = trends.sales_comparison;
const comparisonData = [
  { period: 'Current', revenue: comparison.current_period_avg_revenue },
  { period: 'Historical', revenue: comparison.historical_avg_revenue }
];
```

### **Alerts Dashboard**
```javascript
const alerts = analytics.alerts_summary;

// Alert counts for badges
const alertCounts = alerts.summary_counts;
console.log(`${alertCounts.low_stock_alerts} low stock items`);
console.log(`${alertCounts.total_alerts} total alerts`);

// Detailed alerts for lists
const lowStockAlerts = alerts.detailed_alerts.low_stock_alerts;
lowStockAlerts.forEach(alert => {
  const severity = alert.severity; // critical, high, medium
  const urgencyClass = severity === 'critical' ? 'text-red-600' : 
                      severity === 'high' ? 'text-orange-600' : 'text-yellow-600';
});
```

## 📊 **Data Calculations**

### **Inventory Calculations**
- **On-hand Inventory**: Direct from product tables (`inventory_quantity`, `quantity`)
- **Incoming Inventory**: Currently 0 (can be enhanced with purchase orders)
- **Outgoing Inventory**: Calculated from recent orders (last 30 days)
- **Current Availability**: `On-hand + Incoming - Outgoing`

### **KPI Calculations**
- **Sales Periods**: Direct SQL queries with date filtering
- **Inventory Turnover**: `Units sold (30 days) ÷ Total inventory`
- **Days Stock Remaining**: `Total inventory ÷ Average daily sales`

### **Trend Data**
- **90-day Daily Data**: Complete day-by-day breakdown
- **Selectable Ranges**: Filter daily data for 7/30/90-day views
- **Sales Comparison**: Current 30 days vs previous 30 days

### **Alert Logic**
- **Low Stock**: `< 10 units` (critical: 0, high: <3, medium: <10)
- **Overstock**: `> 100 units`
- **Sales Spike**: `> 50% increase` in last 7 days vs previous 7 days
- **Sales Slowdown**: `< -30% decrease` in last 7 days vs previous 7 days

## ⚡ **Performance Benefits**

- **Direct SQL Queries**: No JSON parsing overhead
- **Indexed Tables**: Fast lookups on SKU, date, inventory levels
- **Pre-calculated Metrics**: KPIs computed once, not per request
- **Optimized Data Structure**: Dashboard-ready format

## 🧪 **Testing**

```bash
cd Analytics_AI_Dashboard/backend

# Test the dashboard analytics
python test_dashboard_inventory.py

# Choose option 1 for detailed analytics test
# Choose option 2 for API endpoint test  
# Choose option 3 for full test suite
```

## 🎯 **Perfect for Dashboard Components**

### **Inventory Management View**
- ✅ Complete SKU list with availability calculations
- ✅ Real-time inventory levels
- ✅ Incoming/outgoing tracking

### **KPI Dashboard**
- ✅ Time-based sales metrics (7/30/90 days)
- ✅ Inventory efficiency metrics
- ✅ Performance indicators

### **Analytics Charts**
- ✅ Time-series inventory levels
- ✅ Sales trend visualizations  
- ✅ Period-over-period comparisons

### **Alerts & Notifications**
- ✅ Categorized alert counts
- ✅ Detailed alert information
- ✅ Quick action links

## 🔄 **Data Sources**

All data comes from **organized database tables**:
- **`{client_id}_shopify_products`** → SKU list, inventory levels
- **`{client_id}_shopify_orders`** → Sales data, trends
- **`{client_id}_amazon_products`** → Amazon inventory
- **`{client_id}_amazon_orders`** → Amazon sales data

**Result**: Lightning-fast dashboard with real-time inventory analytics! 🚀
