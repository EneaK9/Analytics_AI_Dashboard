-- ========================================
-- SKU SALES ANALYSIS QUERIES
-- ========================================
-- These queries show total units sold for specific SKUs
-- Replace {CLIENT_ID} with your actual client ID
-- Replace 'YOUR_SKU_HERE' with the actual SKU you want to analyze

-- ========================================
-- 1. TOTAL UNITS SOLD FOR A SPECIFIC SKU (ALL PLATFORMS)
-- ========================================
WITH shopify_sales AS (
    SELECT 
        jsonb_array_elements(line_items) ->> 'sku' as sku,
        SUM((jsonb_array_elements(line_items) ->> 'quantity')::integer) as shopify_units,
        COUNT(DISTINCT order_id) as shopify_orders,
        SUM((jsonb_array_elements(line_items) ->> 'price')::decimal * 
            (jsonb_array_elements(line_items) ->> 'quantity')::integer) as shopify_revenue
    FROM "{CLIENT_ID}_shopify_orders"
    WHERE line_items IS NOT NULL
      AND jsonb_array_elements(line_items) ->> 'sku' = 'YOUR_SKU_HERE'
    GROUP BY jsonb_array_elements(line_items) ->> 'sku'
),
amazon_sales AS (
    SELECT 
        jsonb_array_elements(line_items) ->> 'seller_sku' as sku,
        SUM((jsonb_array_elements(line_items) ->> 'quantity_ordered')::integer) as amazon_units,
        COUNT(DISTINCT order_id) as amazon_orders,
        SUM((jsonb_array_elements(line_items) -> 'item_price' ->> 'amount')::decimal) as amazon_revenue
    FROM "{CLIENT_ID}_amazon_orders"
    WHERE line_items IS NOT NULL
      AND jsonb_array_elements(line_items) ->> 'seller_sku' = 'YOUR_SKU_HERE'
    GROUP BY jsonb_array_elements(line_items) ->> 'seller_sku'
)
SELECT 
    COALESCE(s.sku, a.sku) as sku,
    COALESCE(s.shopify_units, 0) as shopify_units_sold,
    COALESCE(s.shopify_orders, 0) as shopify_orders,
    COALESCE(s.shopify_revenue, 0) as shopify_revenue,
    COALESCE(a.amazon_units, 0) as amazon_units_sold,
    COALESCE(a.amazon_orders, 0) as amazon_orders,
    COALESCE(a.amazon_revenue, 0) as amazon_revenue,
    COALESCE(s.shopify_units, 0) + COALESCE(a.amazon_units, 0) as TOTAL_UNITS_SOLD,
    COALESCE(s.shopify_revenue, 0) + COALESCE(a.amazon_revenue, 0) as TOTAL_REVENUE
FROM shopify_sales s
FULL OUTER JOIN amazon_sales a ON s.sku = a.sku;

-- ========================================
-- 2. TOTAL UNITS SOLD FOR A SPECIFIC SKU BY DATE RANGE
-- ========================================
WITH shopify_sales AS (
    SELECT 
        jsonb_array_elements(line_items) ->> 'sku' as sku,
        SUM((jsonb_array_elements(line_items) ->> 'quantity')::integer) as shopify_units
    FROM "{CLIENT_ID}_shopify_orders"
    WHERE line_items IS NOT NULL
      AND jsonb_array_elements(line_items) ->> 'sku' = 'YOUR_SKU_HERE'
      AND created_at >= '2024-01-01'  -- Replace with your start date
      AND created_at <= '2024-12-31'  -- Replace with your end date
    GROUP BY jsonb_array_elements(line_items) ->> 'sku'
),
amazon_sales AS (
    SELECT 
        jsonb_array_elements(line_items) ->> 'seller_sku' as sku,
        SUM((jsonb_array_elements(line_items) ->> 'quantity_ordered')::integer) as amazon_units
    FROM "{CLIENT_ID}_amazon_orders"
    WHERE line_items IS NOT NULL
      AND jsonb_array_elements(line_items) ->> 'seller_sku' = 'YOUR_SKU_HERE'
      AND purchase_date >= '2024-01-01'  -- Replace with your start date
      AND purchase_date <= '2024-12-31'  -- Replace with your end date
    GROUP BY jsonb_array_elements(line_items) ->> 'seller_sku'
)
SELECT 
    'YOUR_SKU_HERE' as sku,
    COALESCE(s.shopify_units, 0) + COALESCE(a.amazon_units, 0) as TOTAL_UNITS_SOLD_IN_PERIOD
FROM shopify_sales s
FULL OUTER JOIN amazon_sales a ON s.sku = a.sku;

-- ========================================
-- 3. TOTAL UNITS SOLD FOR ALL SKUs (TOP PERFORMERS)
-- ========================================
WITH shopify_sales AS (
    SELECT 
        jsonb_array_elements(line_items) ->> 'sku' as sku,
        SUM((jsonb_array_elements(line_items) ->> 'quantity')::integer) as shopify_units,
        COUNT(DISTINCT order_id) as shopify_orders
    FROM "{CLIENT_ID}_shopify_orders"
    WHERE line_items IS NOT NULL
      AND jsonb_array_elements(line_items) ->> 'sku' IS NOT NULL
      AND jsonb_array_elements(line_items) ->> 'sku' != ''
    GROUP BY jsonb_array_elements(line_items) ->> 'sku'
),
amazon_sales AS (
    SELECT 
        jsonb_array_elements(line_items) ->> 'seller_sku' as sku,
        SUM((jsonb_array_elements(line_items) ->> 'quantity_ordered')::integer) as amazon_units,
        COUNT(DISTINCT order_id) as amazon_orders
    FROM "{CLIENT_ID}_amazon_orders"
    WHERE line_items IS NOT NULL
      AND jsonb_array_elements(line_items) ->> 'seller_sku' IS NOT NULL
      AND jsonb_array_elements(line_items) ->> 'seller_sku' != ''
    GROUP BY jsonb_array_elements(line_items) ->> 'seller_sku'
)
SELECT 
    COALESCE(s.sku, a.sku) as sku,
    COALESCE(s.shopify_units, 0) as shopify_units_sold,
    COALESCE(a.amazon_units, 0) as amazon_units_sold,
    COALESCE(s.shopify_units, 0) + COALESCE(a.amazon_units, 0) as TOTAL_UNITS_SOLD,
    COALESCE(s.shopify_orders, 0) + COALESCE(a.amazon_orders, 0) as total_orders
FROM shopify_sales s
FULL OUTER JOIN amazon_sales a ON s.sku = a.sku
WHERE COALESCE(s.sku, a.sku) IS NOT NULL
ORDER BY TOTAL_UNITS_SOLD DESC
LIMIT 50;

-- ========================================
-- 4. MONTHLY UNITS SOLD FOR A SPECIFIC SKU
-- ========================================
WITH shopify_monthly AS (
    SELECT 
        DATE_TRUNC('month', created_at) as month,
        SUM((jsonb_array_elements(line_items) ->> 'quantity')::integer) as shopify_units
    FROM "{CLIENT_ID}_shopify_orders"
    WHERE line_items IS NOT NULL
      AND jsonb_array_elements(line_items) ->> 'sku' = 'YOUR_SKU_HERE'
      AND created_at >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', created_at)
),
amazon_monthly AS (
    SELECT 
        DATE_TRUNC('month', purchase_date) as month,
        SUM((jsonb_array_elements(line_items) ->> 'quantity_ordered')::integer) as amazon_units
    FROM "{CLIENT_ID}_amazon_orders"
    WHERE line_items IS NOT NULL
      AND jsonb_array_elements(line_items) ->> 'seller_sku' = 'YOUR_SKU_HERE'
      AND purchase_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', purchase_date)
)
SELECT 
    COALESCE(s.month, a.month) as month,
    COALESCE(s.shopify_units, 0) as shopify_units,
    COALESCE(a.amazon_units, 0) as amazon_units,
    COALESCE(s.shopify_units, 0) + COALESCE(a.amazon_units, 0) as total_units_sold
FROM shopify_monthly s
FULL OUTER JOIN amazon_monthly a ON s.month = a.month
ORDER BY month;

-- ========================================
-- 5. SIMPLE QUERY: JUST TOTAL UNITS FOR ONE SKU
-- ========================================
-- Use this for a quick lookup of total units sold for a specific SKU

SELECT 
    SUM(total_units) as TOTAL_UNITS_SOLD_ALL_TIME
FROM (
    -- Shopify units
    SELECT SUM((jsonb_array_elements(line_items) ->> 'quantity')::integer) as total_units
    FROM "{CLIENT_ID}_shopify_orders"
    WHERE line_items IS NOT NULL
      AND jsonb_array_elements(line_items) ->> 'sku' = 'YOUR_SKU_HERE'
    
    UNION ALL
    
    -- Amazon units  
    SELECT SUM((jsonb_array_elements(line_items) ->> 'quantity_ordered')::integer) as total_units
    FROM "{CLIENT_ID}_amazon_orders"
    WHERE line_items IS NOT NULL
      AND jsonb_array_elements(line_items) ->> 'seller_sku' = 'YOUR_SKU_HERE'
) combined;

-- ========================================
-- USAGE INSTRUCTIONS
-- ========================================
-- 1. Replace {CLIENT_ID} with your actual client ID (hyphens to underscores)
--    Example: 3b619a14_3cd8_49fa_9c24_d8df5e54c452
--
-- 2. Replace 'YOUR_SKU_HERE' with the actual SKU you want to analyze
--    Example: 'SHIRT-RED-M' or 'B08N5WRWNW'
--
-- 3. Adjust date ranges as needed for your analysis period
--
-- 4. For best performance, ensure you have the JSON indexes created:
--    CREATE INDEX idx_shopify_orders_line_items_sku ON "{CLIENT_ID}_shopify_orders" USING GIN ((line_items -> 'sku'));
--    CREATE INDEX idx_amazon_orders_line_items_sku ON "{CLIENT_ID}_amazon_orders" USING GIN ((line_items -> 'seller_sku'));
