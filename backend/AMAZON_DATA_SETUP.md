# Amazon Data Organization Setup

This guide sets up Amazon orders and products tables for client `6ee35b37-57af-4b70-bc62-1eddf1d0fd15`.

## 🚀 **Step-by-Step Setup**

### **Step 1: Create Amazon Tables**
Run this SQL in your Supabase SQL Editor:

```bash
# Copy and paste create_amazon_tables_client2.sql into Supabase SQL Editor
```

This creates:
- `6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders`
- `6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products`

### **Step 2: Populate with Data**
Run the population script:

```bash
cd Analytics_AI_Dashboard/backend
python populate_amazon_data.py
```

### **Step 3: Test the Setup**
Verify everything works:

```bash
cd Analytics_AI_Dashboard/backend
python test_amazon_population.py
```

## 📊 **Table Structures**

### **Amazon Orders Table**
```sql
- order_id (varchar) - Amazon order identifier
- order_status (varchar) - Shipped, Pending, etc.
- total_price (decimal) - Order total
- currency (varchar) - USD, EUR, etc.
- marketplace_id (varchar) - ATVPDKIKX0DER, etc.
- sales_channel (varchar) - Amazon.com, etc.
- fulfillment_channel (varchar) - AFN, MFN
- is_premium_order (boolean) - Amazon Prime
- is_business_order (boolean) - Amazon Business
- number_of_items_shipped (integer)
- number_of_items_unshipped (integer)
- created_at, updated_at (timestamps)
```

### **Amazon Products Table**
```sql
- asin (varchar) - Amazon Standard Identification Number
- sku (varchar) - Stock Keeping Unit
- title (varchar) - Product name
- price (decimal) - Product price
- quantity (integer) - Available inventory
- brand (varchar) - Product brand
- category (varchar) - Product category
- marketplace_id (varchar) - Amazon marketplace
- fulfillment_channel (varchar) - AFN/MFN
- condition_type (varchar) - New, Used, etc.
```

## 🔍 **Data Detection Logic**

The script automatically identifies Amazon data by looking for:

### **Amazon Orders**
- Must have `order_id`
- Plus 2+ of these fields:
  - `marketplace_id`
  - `sales_channel`
  - `fulfillment_channel`
  - `is_premium_order`
  - `is_business_order`
  - `number_of_items_shipped`

### **Amazon Products**
- Must have `asin` OR `sku`
- Plus 1+ of these fields:
  - `marketplace_id`
  - `fulfillment_channel`

## 💡 **Example Queries After Setup**

```sql
-- Top selling products
SELECT title, SUM(quantity) as total_inventory 
FROM "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products" 
GROUP BY title ORDER BY total_inventory DESC;

-- Orders by status
SELECT order_status, COUNT(*), AVG(total_price) 
FROM "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders" 
GROUP BY order_status;

-- Revenue by marketplace
SELECT marketplace_id, SUM(total_price) as revenue 
FROM "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders" 
GROUP BY marketplace_id;

-- Low inventory alerts
SELECT title, sku, quantity 
FROM "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products" 
WHERE quantity < 10;

-- Premium vs regular orders
SELECT is_premium_order, COUNT(*), AVG(total_price) 
FROM "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders" 
GROUP BY is_premium_order;
```

## 🎯 **Benefits for Dashboard**

1. **Fast Analytics**: Direct SQL queries instead of JSON parsing
2. **Proper Data Types**: Numbers as decimals, booleans as booleans
3. **Indexed Performance**: Fast lookups on order_id, asin, sku
4. **Clean Structure**: Separate orders and products for clear analytics
5. **Amazon-Specific Fields**: Premium orders, business orders, fulfillment channels

## 📈 **Dashboard Use Cases**

- **Revenue Analysis**: Orders by marketplace, sales channels
- **Inventory Management**: Product quantities, low stock alerts
- **Customer Insights**: Premium vs regular order patterns
- **Fulfillment Analytics**: AFN vs MFN performance
- **Product Performance**: Best sellers, price analysis

## ⚠️ **Notes**

- Client ID: `6ee35b37-57af-4b70-bc62-1eddf1d0fd15`
- Data source: `client_data` table JSON records
- Tables created with proper indexes for performance
- Raw JSON data preserved in `raw_data` column for reference
