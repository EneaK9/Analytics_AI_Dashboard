-- ========================================
-- EXAMPLE QUERIES FOR ENHANCED API DATA
-- ========================================
-- These examples show how to query the enhanced data structures
-- Replace {CLIENT_ID} with your actual client ID

-- ========================================
-- SHOPIFY ENHANCED QUERIES
-- ========================================

-- 1. Get all SKUs and quantities from orders
SELECT 
    order_id,
    order_number,
    total_price,
    jsonb_array_elements(line_items) ->> 'sku' as sku,
    (jsonb_array_elements(line_items) ->> 'quantity')::integer as quantity,
    (jsonb_array_elements(line_items) ->> 'price')::decimal as item_price
FROM "{CLIENT_ID}_shopify_orders"
WHERE line_items IS NOT NULL
ORDER BY created_at DESC;

-- 2. Get customer purchase history with complete data
SELECT 
    customer_data ->> 'email' as customer_email,
    customer_data ->> 'total_spent' as lifetime_value,
    customer_data ->> 'orders_count' as total_orders,
    COUNT(*) as orders_in_period,
    SUM(total_price) as revenue_in_period
FROM "{CLIENT_ID}_shopify_orders"
WHERE customer_data IS NOT NULL
GROUP BY customer_data ->> 'email', customer_data ->> 'total_spent', customer_data ->> 'orders_count'
ORDER BY revenue_in_period DESC;

-- 3. Get fulfillment performance by carrier
SELECT 
    fulfillment ->> 'tracking_company' as carrier,
    fulfillment ->> 'status' as status,
    COUNT(*) as shipment_count,
    AVG(EXTRACT(days FROM (fulfillment ->> 'created_at')::timestamp - created_at)) as avg_days_to_ship
FROM "{CLIENT_ID}_shopify_orders",
     jsonb_array_elements(fulfillments) as fulfillment
WHERE fulfillments IS NOT NULL
GROUP BY fulfillment ->> 'tracking_company', fulfillment ->> 'status'
ORDER BY shipment_count DESC;

-- 4. Analyze refund patterns
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as total_orders,
    COUNT(CASE WHEN jsonb_array_length(refunds) > 0 THEN 1 END) as refunded_orders,
    ROUND(COUNT(CASE WHEN jsonb_array_length(refunds) > 0 THEN 1 END)::decimal / COUNT(*) * 100, 2) as refund_rate
FROM "{CLIENT_ID}_shopify_orders"
WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month;

-- ========================================
-- AMAZON ENHANCED QUERIES
-- ========================================

-- 5. Get all Amazon SKUs and quantities from orders
SELECT 
    order_id,
    purchase_date,
    is_prime,
    ship_service_level,
    jsonb_array_elements(line_items) ->> 'seller_sku' as sku,
    jsonb_array_elements(line_items) ->> 'asin' as asin,
    (jsonb_array_elements(line_items) ->> 'quantity_ordered')::integer as quantity,
    (jsonb_array_elements(line_items) -> 'item_price' ->> 'amount')::decimal as item_price
FROM "{CLIENT_ID}_amazon_orders"
WHERE line_items IS NOT NULL
ORDER BY purchase_date DESC;

-- 6. Prime vs Non-Prime order analysis
SELECT 
    is_prime,
    COUNT(*) as order_count,
    AVG(total_price) as avg_order_value,
    SUM(total_items_quantity) as total_items,
    AVG(total_items_quantity) as avg_items_per_order
FROM "{CLIENT_ID}_amazon_orders"
WHERE purchase_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY is_prime
ORDER BY avg_order_value DESC;

-- 7. Shipping performance by service level
SELECT 
    ship_service_level,
    COUNT(*) as order_count,
    AVG(EXTRACT(days FROM latest_delivery_date - earliest_delivery_date)) as avg_delivery_window_days,
    AVG(EXTRACT(days FROM latest_ship_date - earliest_ship_date)) as avg_ship_window_days
FROM "{CLIENT_ID}_amazon_orders"
WHERE ship_service_level IS NOT NULL
  AND earliest_delivery_date IS NOT NULL
  AND latest_delivery_date IS NOT NULL
GROUP BY ship_service_level
ORDER BY order_count DESC;

-- 8. Enhanced product analysis with catalog data
SELECT 
    asin,
    title,
    brand,
    manufacturer,
    jsonb_array_length(images) as image_count,
    jsonb_array_length(sales_rank) as categories_ranked,
    marketplace_ids ->> 0 as primary_marketplace
FROM "{CLIENT_ID}_amazon_products"
WHERE images IS NOT NULL
ORDER BY jsonb_array_length(sales_rank) DESC;

-- ========================================
-- CROSS-PLATFORM ANALYTICS
-- ========================================

-- 9. SKU performance across platforms
WITH shopify_skus AS (
    SELECT 
        jsonb_array_elements(line_items) ->> 'sku' as sku,
        SUM((jsonb_array_elements(line_items) ->> 'quantity')::integer) as shopify_qty,
        COUNT(DISTINCT order_id) as shopify_orders
    FROM "{CLIENT_ID}_shopify_orders"
    WHERE line_items IS NOT NULL
    GROUP BY jsonb_array_elements(line_items) ->> 'sku'
),
amazon_skus AS (
    SELECT 
        jsonb_array_elements(line_items) ->> 'seller_sku' as sku,
        SUM((jsonb_array_elements(line_items) ->> 'quantity_ordered')::integer) as amazon_qty,
        COUNT(DISTINCT order_id) as amazon_orders
    FROM "{CLIENT_ID}_amazon_orders"
    WHERE line_items IS NOT NULL
    GROUP BY jsonb_array_elements(line_items) ->> 'seller_sku'
)
SELECT 
    COALESCE(s.sku, a.sku) as sku,
    COALESCE(s.shopify_qty, 0) as shopify_quantity,
    COALESCE(s.shopify_orders, 0) as shopify_orders,
    COALESCE(a.amazon_qty, 0) as amazon_quantity,
    COALESCE(a.amazon_orders, 0) as amazon_orders,
    COALESCE(s.shopify_qty, 0) + COALESCE(a.amazon_qty, 0) as total_quantity
FROM shopify_skus s
FULL OUTER JOIN amazon_skus a ON s.sku = a.sku
WHERE COALESCE(s.sku, a.sku) IS NOT NULL
ORDER BY total_quantity DESC;

-- 10. Revenue comparison by platform and month
WITH monthly_revenue AS (
    SELECT 
        'Shopify' as platform,
        DATE_TRUNC('month', created_at) as month,
        SUM(total_price) as revenue,
        COUNT(*) as orders
    FROM "{CLIENT_ID}_shopify_orders"
    WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', created_at)
    
    UNION ALL
    
    SELECT 
        'Amazon' as platform,
        DATE_TRUNC('month', purchase_date) as month,
        SUM(total_price) as revenue,
        COUNT(*) as orders
    FROM "{CLIENT_ID}_amazon_orders"
    WHERE purchase_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', purchase_date)
)
SELECT 
    month,
    SUM(CASE WHEN platform = 'Shopify' THEN revenue ELSE 0 END) as shopify_revenue,
    SUM(CASE WHEN platform = 'Amazon' THEN revenue ELSE 0 END) as amazon_revenue,
    SUM(revenue) as total_revenue,
    SUM(CASE WHEN platform = 'Shopify' THEN orders ELSE 0 END) as shopify_orders,
    SUM(CASE WHEN platform = 'Amazon' THEN orders ELSE 0 END) as amazon_orders,
    SUM(orders) as total_orders
FROM monthly_revenue
GROUP BY month
ORDER BY month;

-- ========================================
-- NOTES
-- ========================================
-- These queries demonstrate the power of the enhanced data structure
-- JSON fields allow complex queries while maintaining performance
-- Replace {CLIENT_ID} with your actual client UUID (hyphens to underscores)
-- Use GIN indexes for optimal JSON query performance
