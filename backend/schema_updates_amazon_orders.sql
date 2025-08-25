-- ========================================
-- AMAZON ORDERS TABLE - ADD ALL MISSING COLUMNS
-- ========================================
-- This script adds ALL possible fields from the Amazon SP-API Orders
-- Run this for each client's Amazon orders table by replacing the table name

-- Replace {CLIENT_ID} with actual client ID (with hyphens replaced by underscores)
-- Example: 6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders

-- ========================================
-- ENHANCED ORDER IDENTIFICATION FIELDS
-- ========================================
ALTER TABLE "{CLIENT_ID}_amazon_orders"
ADD COLUMN IF NOT EXISTS seller_order_id varchar(100),             -- Seller-defined order ID
ADD COLUMN IF NOT EXISTS purchase_date timestamptz,                -- When order was purchased
ADD COLUMN IF NOT EXISTS last_update_date timestamptz,             -- Last update timestamp

-- ========================================
-- ENHANCED ORDER STATUS AND TYPE FIELDS
-- ========================================
ADD COLUMN IF NOT EXISTS order_channel varchar(50),                -- Order channel
ADD COLUMN IF NOT EXISTS url text,                                 -- Order URL
ADD COLUMN IF NOT EXISTS ship_service_level varchar(100),          -- Ship service level
ADD COLUMN IF NOT EXISTS shipment_service_level_category varchar(50), -- Service level category
ADD COLUMN IF NOT EXISTS cba_displayable_shipping_label varchar(255), -- CBA shipping label
ADD COLUMN IF NOT EXISTS order_type varchar(50),                   -- Order type

-- ========================================
-- SHIPPING AND DELIVERY DATES
-- ========================================
ADD COLUMN IF NOT EXISTS earliest_ship_date timestamptz,           -- Earliest ship date
ADD COLUMN IF NOT EXISTS latest_ship_date timestamptz,             -- Latest ship date
ADD COLUMN IF NOT EXISTS earliest_delivery_date timestamptz,       -- Earliest delivery
ADD COLUMN IF NOT EXISTS latest_delivery_date timestamptz,         -- Latest delivery

-- ========================================
-- ORDER CHARACTERISTICS
-- ========================================
ADD COLUMN IF NOT EXISTS is_prime boolean DEFAULT false,           -- Prime order
ADD COLUMN IF NOT EXISTS is_global_express_enabled boolean DEFAULT false, -- Global express
ADD COLUMN IF NOT EXISTS replaced_order_id varchar(100),           -- Replaced order ID
ADD COLUMN IF NOT EXISTS is_replacement_order boolean DEFAULT false, -- Replacement order
ADD COLUMN IF NOT EXISTS promise_response_due_date timestamptz,     -- Promise response due
ADD COLUMN IF NOT EXISTS is_estimated_ship_date_set boolean DEFAULT false, -- Ship date set
ADD COLUMN IF NOT EXISTS is_sold_by_ab boolean DEFAULT false,       -- Sold by AB
ADD COLUMN IF NOT EXISTS is_iba boolean DEFAULT false,             -- Is IBA
ADD COLUMN IF NOT EXISTS is_ispu boolean DEFAULT false,            -- Is ISPU
ADD COLUMN IF NOT EXISTS is_access_point_order boolean DEFAULT false, -- Access point order

-- ========================================
-- BUYER AND INVOICE PREFERENCES
-- ========================================
ADD COLUMN IF NOT EXISTS buyer_invoice_preference varchar(50),     -- Invoice preference
ADD COLUMN IF NOT EXISTS seller_display_name varchar(255),         -- Seller display name

-- ========================================
-- ENHANCED LINE ITEMS (JSON)
-- ========================================
ADD COLUMN IF NOT EXISTS total_items_quantity integer,             -- Total quantity of all items
ADD COLUMN IF NOT EXISTS line_items jsonb,                         -- Enhanced line items with ALL fields

-- ========================================
-- SHIPPING ADDRESS DATA (JSON)
-- ========================================
ADD COLUMN IF NOT EXISTS shipping_address jsonb,                   -- Complete shipping address

-- ========================================
-- BUYER INFORMATION (JSON)
-- ========================================
ADD COLUMN IF NOT EXISTS buyer_info jsonb,                         -- Complete buyer information

-- ========================================
-- PAYMENT INFORMATION (JSON)
-- ========================================
ADD COLUMN IF NOT EXISTS payment_execution_detail jsonb,           -- Payment execution details
ADD COLUMN IF NOT EXISTS payment_method_details jsonb,             -- Payment method details

-- ========================================
-- COMPLEX DATA STRUCTURES (JSON)
-- ========================================
ADD COLUMN IF NOT EXISTS default_ship_from_location_address jsonb, -- Ship from location
ADD COLUMN IF NOT EXISTS buyer_tax_information jsonb,              -- Buyer tax info
ADD COLUMN IF NOT EXISTS fulfillment_instruction jsonb,            -- Fulfillment instructions
ADD COLUMN IF NOT EXISTS marketplace_tax_info jsonb;               -- Marketplace tax info

-- ========================================
-- INDEXES FOR NEW COLUMNS
-- ========================================
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_seller_order_id" ON "{CLIENT_ID}_amazon_orders" (seller_order_id);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_purchase_date" ON "{CLIENT_ID}_amazon_orders" (purchase_date);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_last_update_date" ON "{CLIENT_ID}_amazon_orders" (last_update_date);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_order_channel" ON "{CLIENT_ID}_amazon_orders" (order_channel);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_ship_service_level" ON "{CLIENT_ID}_amazon_orders" (ship_service_level);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_order_type" ON "{CLIENT_ID}_amazon_orders" (order_type);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_earliest_ship_date" ON "{CLIENT_ID}_amazon_orders" (earliest_ship_date);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_latest_ship_date" ON "{CLIENT_ID}_amazon_orders" (latest_ship_date);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_earliest_delivery_date" ON "{CLIENT_ID}_amazon_orders" (earliest_delivery_date);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_latest_delivery_date" ON "{CLIENT_ID}_amazon_orders" (latest_delivery_date);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_is_prime" ON "{CLIENT_ID}_amazon_orders" (is_prime);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_is_replacement_order" ON "{CLIENT_ID}_amazon_orders" (is_replacement_order);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_total_items_quantity" ON "{CLIENT_ID}_amazon_orders" (total_items_quantity);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_seller_display_name" ON "{CLIENT_ID}_amazon_orders" (seller_display_name);

-- ========================================
-- JSON INDEXES FOR PERFORMANCE
-- ========================================
-- Index on SKUs within line items JSON
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_line_items_sku" ON "{CLIENT_ID}_amazon_orders" USING GIN ((line_items -> 'seller_sku'));

-- Index on ASINs within line items JSON
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_line_items_asin" ON "{CLIENT_ID}_amazon_orders" USING GIN ((line_items -> 'asin'));

-- Index on quantities within line items JSON
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_line_items_quantity" ON "{CLIENT_ID}_amazon_orders" USING GIN ((line_items -> 'quantity_ordered'));

-- Index on buyer email
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_buyer_email" ON "{CLIENT_ID}_amazon_orders" USING GIN ((buyer_info -> 'buyer_email'));

-- Index on shipping address country
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_orders_shipping_country" ON "{CLIENT_ID}_amazon_orders" USING GIN ((shipping_address -> 'country_code'));

-- ========================================
-- NOTES
-- ========================================
-- This schema supports ALL Amazon SP-API Orders fields
-- Line items contain complete order item details with pricing breakdowns
-- JSON columns enable flexible querying of complex nested data
-- Replace {CLIENT_ID} with actual client UUID (hyphens to underscores)
-- Example usage:
-- ALTER TABLE "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders" ADD COLUMN ...
