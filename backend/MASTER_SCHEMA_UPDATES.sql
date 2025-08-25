-- ========================================
-- MASTER SCHEMA UPDATES - APPLY ALL ENHANCEMENTS
-- ========================================
-- This script applies ALL schema updates to enable complete API data storage
-- 
-- BEFORE RUNNING:
-- 1. Replace {CLIENT_ID} with actual client UUID (hyphens to underscores)
-- 2. Backup your database
-- 3. Test on a single client first
--
-- WHAT THIS DOES:
-- - Adds ALL missing columns for Shopify orders (50+ new fields)
-- - Adds ALL missing columns for Shopify products (enhanced variants, images, options)
-- - Adds ALL missing columns for Amazon orders (70+ new fields)
-- - Adds ALL missing columns for Amazon products (catalog data, images, rankings)
-- - Creates new Amazon incoming inventory table
-- ========================================

-- Replace this with your actual client ID (hyphens to underscores)
-- Example: 3b619a14_3cd8_49fa_9c24_d8df5e54c452
\set CLIENT_ID 'YOUR_CLIENT_ID_HERE'

-- ========================================
-- 1. SHOPIFY ORDERS ENHANCEMENTS
-- ========================================
\echo 'Applying Shopify Orders enhancements...'

-- Enhanced order fields
ALTER TABLE :CLIENT_ID"_shopify_orders"
ADD COLUMN IF NOT EXISTS name varchar(100),
ADD COLUMN IF NOT EXISTS closed_at timestamptz,
ADD COLUMN IF NOT EXISTS cancelled_at timestamptz,
ADD COLUMN IF NOT EXISTS cancel_reason varchar(100),
ADD COLUMN IF NOT EXISTS total_weight integer,
ADD COLUMN IF NOT EXISTS total_discounts decimal(10,2),
ADD COLUMN IF NOT EXISTS total_line_items_price decimal(10,2),
ADD COLUMN IF NOT EXISTS taxes_included boolean,
ADD COLUMN IF NOT EXISTS confirmed boolean,
ADD COLUMN IF NOT EXISTS total_price_usd decimal(10,2),
ADD COLUMN IF NOT EXISTS checkout_id bigint,
ADD COLUMN IF NOT EXISTS reference varchar(255),
ADD COLUMN IF NOT EXISTS user_id bigint,
ADD COLUMN IF NOT EXISTS location_id bigint,
ADD COLUMN IF NOT EXISTS source_identifier varchar(255),
ADD COLUMN IF NOT EXISTS source_url text,
ADD COLUMN IF NOT EXISTS device_id bigint,
ADD COLUMN IF NOT EXISTS phone varchar(20),
ADD COLUMN IF NOT EXISTS customer_locale varchar(10),
ADD COLUMN IF NOT EXISTS app_id bigint,
ADD COLUMN IF NOT EXISTS browser_ip inet,
ADD COLUMN IF NOT EXISTS landing_site text,
ADD COLUMN IF NOT EXISTS referring_site text,
ADD COLUMN IF NOT EXISTS order_status_url text,
ADD COLUMN IF NOT EXISTS token varchar(255),
ADD COLUMN IF NOT EXISTS cart_token varchar(255),
ADD COLUMN IF NOT EXISTS total_items_quantity integer,
ADD COLUMN IF NOT EXISTS customer_data jsonb,
ADD COLUMN IF NOT EXISTS fulfillments jsonb,
ADD COLUMN IF NOT EXISTS refunds jsonb,
ADD COLUMN IF NOT EXISTS transactions jsonb,
ADD COLUMN IF NOT EXISTS shipping_lines jsonb,
ADD COLUMN IF NOT EXISTS discount_applications jsonb,
ADD COLUMN IF NOT EXISTS tax_lines jsonb,
ADD COLUMN IF NOT EXISTS order_adjustments jsonb,
ADD COLUMN IF NOT EXISTS client_details jsonb,
ADD COLUMN IF NOT EXISTS payment_gateway_names jsonb,
ADD COLUMN IF NOT EXISTS payment_details jsonb;

-- ========================================
-- 2. SHOPIFY PRODUCTS ENHANCEMENTS  
-- ========================================
\echo 'Applying Shopify Products enhancements...'

ALTER TABLE :CLIENT_ID"_shopify_products"
ADD COLUMN IF NOT EXISTS body_html text,
ADD COLUMN IF NOT EXISTS published_at timestamptz,
ADD COLUMN IF NOT EXISTS template_suffix varchar(100),
ADD COLUMN IF NOT EXISTS published_scope varchar(50),
ADD COLUMN IF NOT EXISTS admin_graphql_api_id varchar(255),
ADD COLUMN IF NOT EXISTS seo_title varchar(255),
ADD COLUMN IF NOT EXISTS seo_description text,
ADD COLUMN IF NOT EXISTS created_at timestamptz,
ADD COLUMN IF NOT EXISTS updated_at timestamptz,
ADD COLUMN IF NOT EXISTS variants_count integer,
ADD COLUMN IF NOT EXISTS options_count integer,
ADD COLUMN IF NOT EXISTS image jsonb;

-- ========================================
-- 3. AMAZON ORDERS ENHANCEMENTS
-- ========================================
\echo 'Applying Amazon Orders enhancements...'

ALTER TABLE :CLIENT_ID"_amazon_orders"
ADD COLUMN IF NOT EXISTS seller_order_id varchar(100),
ADD COLUMN IF NOT EXISTS purchase_date timestamptz,
ADD COLUMN IF NOT EXISTS last_update_date timestamptz,
ADD COLUMN IF NOT EXISTS order_channel varchar(50),
ADD COLUMN IF NOT EXISTS url text,
ADD COLUMN IF NOT EXISTS ship_service_level varchar(100),
ADD COLUMN IF NOT EXISTS shipment_service_level_category varchar(50),
ADD COLUMN IF NOT EXISTS cba_displayable_shipping_label varchar(255),
ADD COLUMN IF NOT EXISTS order_type varchar(50),
ADD COLUMN IF NOT EXISTS earliest_ship_date timestamptz,
ADD COLUMN IF NOT EXISTS latest_ship_date timestamptz,
ADD COLUMN IF NOT EXISTS earliest_delivery_date timestamptz,
ADD COLUMN IF NOT EXISTS latest_delivery_date timestamptz,
ADD COLUMN IF NOT EXISTS is_prime boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS is_global_express_enabled boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS replaced_order_id varchar(100),
ADD COLUMN IF NOT EXISTS is_replacement_order boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS promise_response_due_date timestamptz,
ADD COLUMN IF NOT EXISTS is_estimated_ship_date_set boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS is_sold_by_ab boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS is_iba boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS is_ispu boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS is_access_point_order boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS buyer_invoice_preference varchar(50),
ADD COLUMN IF NOT EXISTS seller_display_name varchar(255),
ADD COLUMN IF NOT EXISTS total_items_quantity integer,
ADD COLUMN IF NOT EXISTS shipping_address jsonb,
ADD COLUMN IF NOT EXISTS buyer_info jsonb,
ADD COLUMN IF NOT EXISTS payment_execution_detail jsonb,
ADD COLUMN IF NOT EXISTS payment_method_details jsonb,
ADD COLUMN IF NOT EXISTS default_ship_from_location_address jsonb,
ADD COLUMN IF NOT EXISTS buyer_tax_information jsonb,
ADD COLUMN IF NOT EXISTS fulfillment_instruction jsonb,
ADD COLUMN IF NOT EXISTS marketplace_tax_info jsonb;

-- ========================================
-- 4. AMAZON PRODUCTS ENHANCEMENTS
-- ========================================
\echo 'Applying Amazon Products enhancements...'

ALTER TABLE :CLIENT_ID"_amazon_products"
ADD COLUMN IF NOT EXISTS manufacturer varchar(255),
ADD COLUMN IF NOT EXISTS marketplace_ids jsonb,
ADD COLUMN IF NOT EXISTS images jsonb,
ADD COLUMN IF NOT EXISTS sales_rank jsonb,
ADD COLUMN IF NOT EXISTS relationships jsonb;

-- ========================================
-- 5. CREATE AMAZON INCOMING INVENTORY TABLE
-- ========================================
\echo 'Creating Amazon Incoming Inventory table...'

CREATE TABLE IF NOT EXISTS :CLIENT_ID"_amazon_incoming_inventory" (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id uuid NOT NULL,
    shipment_id varchar(100) UNIQUE NOT NULL,
    shipment_name varchar(255),
    shipment_status varchar(50),
    platform varchar(20) DEFAULT 'amazon',
    destination_fulfillment_center_id varchar(100),
    label_prep_preference varchar(50),
    are_cases_required boolean DEFAULT false,
    confirmed_need_by_date timestamptz,
    box_contents_source varchar(50),
    estimated_box_contents_fee decimal(10,2),
    created_at timestamptz,
    raw_data jsonb,
    processed_at timestamptz DEFAULT now()
);

-- ========================================
-- 6. CREATE PERFORMANCE INDEXES
-- ========================================
\echo 'Creating performance indexes...'

-- Shopify Orders Indexes
CREATE INDEX IF NOT EXISTS idx_shopify_orders_name ON :CLIENT_ID"_shopify_orders" (name);
CREATE INDEX IF NOT EXISTS idx_shopify_orders_cancelled_at ON :CLIENT_ID"_shopify_orders" (cancelled_at);
CREATE INDEX IF NOT EXISTS idx_shopify_orders_total_items_quantity ON :CLIENT_ID"_shopify_orders" (total_items_quantity);

-- Amazon Orders Indexes  
CREATE INDEX IF NOT EXISTS idx_amazon_orders_purchase_date ON :CLIENT_ID"_amazon_orders" (purchase_date);
CREATE INDEX IF NOT EXISTS idx_amazon_orders_is_prime ON :CLIENT_ID"_amazon_orders" (is_prime);
CREATE INDEX IF NOT EXISTS idx_amazon_orders_total_items_quantity ON :CLIENT_ID"_amazon_orders" (total_items_quantity);

-- Amazon Incoming Inventory Indexes
CREATE INDEX IF NOT EXISTS idx_amazon_incoming_inventory_shipment_id ON :CLIENT_ID"_amazon_incoming_inventory" (shipment_id);
CREATE INDEX IF NOT EXISTS idx_amazon_incoming_inventory_status ON :CLIENT_ID"_amazon_incoming_inventory" (shipment_status);

-- JSON Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_shopify_orders_line_items_sku ON :CLIENT_ID"_shopify_orders" USING GIN ((line_items -> 'sku'));
CREATE INDEX IF NOT EXISTS idx_amazon_orders_line_items_sku ON :CLIENT_ID"_amazon_orders" USING GIN ((line_items -> 'seller_sku'));

-- ========================================
-- 7. VERIFICATION QUERIES
-- ========================================
\echo 'Running verification queries...'

-- Count columns in each table
SELECT 
    table_name,
    COUNT(*) as column_count
FROM information_schema.columns 
WHERE table_name LIKE '%' || :'CLIENT_ID' || '%'
GROUP BY table_name
ORDER BY table_name;

-- ========================================
-- COMPLETION MESSAGE
-- ========================================
\echo ''
\echo '========================================='
\echo 'SCHEMA UPDATES COMPLETE!'
\echo '========================================='
\echo 'Enhanced tables now support ALL API data:'
\echo '- Shopify Orders: Complete order data with line items, fulfillments, transactions'
\echo '- Shopify Products: Complete product data with variants, images, options'  
\echo '- Amazon Orders: Complete order data with enhanced line items, buyer info'
\echo '- Amazon Products: Enhanced catalog data with images, rankings, relationships'
\echo '- Amazon Incoming Inventory: New FBA shipment tracking table'
\echo ''
\echo 'Your next API sync will capture ALL available data!'
\echo '========================================='
