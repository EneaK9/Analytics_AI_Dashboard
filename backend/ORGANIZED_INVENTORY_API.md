# Organized Inventory Analytics API

This document describes the new inventory analytics endpoints that work with organized client tables.

## 🚀 **New Endpoints**

### **1. Organized Inventory Analytics**
```
GET /api/dashboard/organized-inventory-analytics/{client_id}
```

**Description**: Get comprehensive inventory analytics from organized client tables

**Parameters**:
- `client_id` (path): The client UUID to analyze
- `Authorization: Bearer {token}` (header): Client authentication token

**Response Structure**:
```json
{
  "success": true,
  "client_id": "3b619a14-3cd8-49fa-9c24-d8df5e54c452",
  "timestamp": "2025-01-15T10:30:00Z",
  "analytics": {
    "data_sources": {
      "shopify_products": 120,
      "amazon_orders": 85,
      "amazon_products": 45
    },
    "inventory_kpis": {
      "total_inventory_units": 2450,
      "total_inventory_value": 45680.50,
      "total_unique_skus": 95,
      "low_stock_count": 12,
      "shopify": {
        "total_units": 1800,
        "total_value": 32400.00,
        "unique_skus": 60,
        "low_stock": 8,
        "avg_price": 39.50,
        "total_variants": 120
      },
      "amazon": {
        "total_units": 650,
        "total_value": 13280.50,
        "unique_skus": 35,
        "low_stock": 4,
        "avg_price": 295.12,
        "total_products": 45
      }
    },
    "sales_kpis": {
      "total_orders": 85,
      "total_revenue": 12450.75,
      "avg_order_value": 146.48,
      "orders_by_status": {
        "Shipped": 70,
        "Pending": 12,
        "Cancelled": 3
      },
      "premium_orders_ratio": 45.2,
      "recent_30_days": {
        "orders": 25,
        "revenue": 3680.25
      }
    },
    "trend_analysis": {
      "monthly_trends": [
        {
          "month": "2025-01",
          "orders": 25,
          "revenue": 3680.25,
          "growth_rate": 12.5
        }
      ]
    },
    "alerts": [
      {
        "type": "low_stock",
        "platform": "shopify",
        "severity": "high",
        "title": "Low Stock: Ray Scrub Top",
        "message": "SKU ray-blk-s has only 2 units left",
        "sku": "ray-blk-s",
        "current_stock": 2
      }
    ],
    "top_products": {
      "shopify_top_by_value": [
        {
          "title": "Premium Scrub Set",
          "sku": "premium-set-001",
          "price": 89.99,
          "inventory": 50,
          "total_value": 4499.50,
          "option1": "Navy",
          "option2": "Large"
        }
      ],
      "amazon_top_by_price": [
        {
          "title": "High-End Medical Device",
          "asin": "B08XYZ123",
          "sku": "med-device-001",
          "price": 1299.99,
          "quantity": 5,
          "brand": "MedBrand"
        }
      ]
    },
    "low_stock_alerts": [
      {
        "platform": "shopify",
        "title": "Ray Scrub Top",
        "sku": "ray-blk-s",
        "current_stock": 2,
        "price": 39.50,
        "variant": "Black S",
        "urgency": "high"
      }
    ]
  }
}
```

### **2. Client Data Health Check**
```
GET /api/dashboard/client-data-health/{client_id}
```

**Description**: Check the health status of organized client tables

**Parameters**:
- `client_id` (path): The client UUID to check
- `Authorization: Bearer {token}` (header): Client authentication token

**Response Structure**:
```json
{
  "success": true,
  "client_id": "3b619a14-3cd8-49fa-9c24-d8df5e54c452",
  "timestamp": "2025-01-15T10:30:00Z",
  "summary": {
    "existing_tables": 3,
    "total_tables": 3,
    "total_records": 250,
    "is_organized": true
  },
  "tables": {
    "shopify_products": {
      "exists": true,
      "count": 120,
      "table_name": "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products"
    },
    "amazon_orders": {
      "exists": true,
      "count": 85,
      "table_name": "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_orders"
    },
    "amazon_products": {
      "exists": true,
      "count": 45,
      "table_name": "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_products"
    }
  }
}
```

## 🎯 **Usage Examples**

### **JavaScript/TypeScript Frontend**
```javascript
// Get inventory analytics for a specific client
const getInventoryAnalytics = async (clientId, token) => {
  try {
    const response = await fetch(
      `/api/dashboard/organized-inventory-analytics/${clientId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      return data.analytics;
    } else {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  } catch (error) {
    console.error('Error fetching inventory analytics:', error);
    throw error;
  }
};

// Check if client data is organized
const checkDataHealth = async (clientId, token) => {
  try {
    const response = await fetch(
      `/api/dashboard/client-data-health/${clientId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      return data.summary.is_organized;
    }
    return false;
  } catch (error) {
    console.error('Error checking data health:', error);
    return false;
  }
};

// Usage in React component
const InventoryDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const clientId = "3b619a14-3cd8-49fa-9c24-d8df5e54c452";
  const token = localStorage.getItem('authToken');
  
  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        const isOrganized = await checkDataHealth(clientId, token);
        
        if (isOrganized) {
          const analyticsData = await getInventoryAnalytics(clientId, token);
          setAnalytics(analyticsData);
        } else {
          console.warn('Client data is not organized yet');
        }
      } catch (error) {
        console.error('Failed to load analytics:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadAnalytics();
  }, [clientId, token]);
  
  if (loading) return <div>Loading analytics...</div>;
  
  return (
    <div>
      <h1>Inventory Analytics</h1>
      {analytics && (
        <div>
          <div>Total Inventory Value: ${analytics.inventory_kpis.total_inventory_value}</div>
          <div>Low Stock Items: {analytics.inventory_kpis.low_stock_count}</div>
          <div>Total Orders: {analytics.sales_kpis.total_orders}</div>
        </div>
      )}
    </div>
  );
};
```

### **Python Client**
```python
import aiohttp
import asyncio

async def get_inventory_analytics(client_id: str, token: str):
    """Get inventory analytics for a client"""
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"http://localhost:8000/api/dashboard/organized-inventory-analytics/{client_id}"
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data["analytics"]
            else:
                raise Exception(f"HTTP {response.status}: {await response.text()}")

# Usage
async def main():
    client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
    token = "your_auth_token_here"
    
    try:
        analytics = await get_inventory_analytics(client_id, token)
        
        print(f"Total Inventory Value: ${analytics['inventory_kpis']['total_inventory_value']:,.2f}")
        print(f"Low Stock Items: {analytics['inventory_kpis']['low_stock_count']}")
        print(f"Total Orders: {analytics['sales_kpis']['total_orders']}")
        
        # Show alerts
        for alert in analytics['alerts']:
            print(f"ALERT: {alert['title']} - {alert['message']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📊 **Data Requirements**

For the endpoints to work properly, clients must have organized tables:

### **Required Tables**:
1. `{client_id}_shopify_products` - Shopify products with variants as rows
2. `{client_id}_amazon_orders` - Amazon orders data  
3. `{client_id}_amazon_products` - Amazon products data

### **Table Creation**:
Use the provided SQL scripts and population scripts:
1. Run table creation SQL in Supabase
2. Run data population scripts to organize raw JSON data
3. Verify with health check endpoint

## 🔍 **Key Differences from Legacy Endpoint**

### **Legacy**: `/api/dashboard/inventory-analytics`
- Uses JSON data from `client_data` table
- Requires JSON parsing for each request
- Slower performance
- Limited query capabilities

### **New**: `/api/dashboard/organized-inventory-analytics/{client_id}`
- Uses structured SQL tables
- Direct database queries
- Faster performance  
- Rich query capabilities
- Client ID in URL for multi-client support

## 🎯 **Perfect for Dashboard Use**

The organized inventory analytics provide:

✅ **Fast KPIs**: Instant inventory values, stock levels, sales metrics  
✅ **Real-time Alerts**: Low stock, high value inventory warnings  
✅ **Trend Analysis**: Monthly sales growth, order patterns  
✅ **Platform Separation**: Clear Shopify vs Amazon metrics  
✅ **Detailed Breakdowns**: Product performance, customer insights  
✅ **Multi-client Support**: Handle multiple clients with URL parameter  

## 🚀 **Testing**

Use the provided test script:
```bash
cd Analytics_AI_Dashboard/backend
python test_organized_inventory_api.py
```

Choose option 2 for direct database testing (no auth required).
