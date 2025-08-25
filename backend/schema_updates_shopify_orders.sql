-- ========================================
-- SHOPIFY ORDERS TABLE - ADD ALL MISSING COLUMNS
-- ========================================
-- This script adds ALL possible fields from the Shopify Orders API
-- Run this for each client's Shopify orders table by replacing the table name

-- Replace {CLIENT_ID} with actual client ID (with hyphens replaced by underscores)
-- Example: 3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders

-- ========================================
-- ENHANCED ORDER FIELDS
-- ========================================
ALTER TABLE "{CLIENT_ID}_shopify_orders"
ADD COLUMN IF NOT EXISTS name varchar(100),                        -- Order name like "#1001"
ADD COLUMN IF NOT EXISTS closed_at timestamptz,                    -- When order was closed
ADD COLUMN IF NOT EXISTS cancelled_at timestamptz,                 -- When order was cancelled
ADD COLUMN IF NOT EXISTS cancel_reason varchar(100),               -- Reason for cancellation
ADD COLUMN IF NOT EXISTS total_weight integer,                     -- Total weight in grams
ADD COLUMN IF NOT EXISTS total_discounts decimal(10,2),            -- Total discounts applied
ADD COLUMN IF NOT EXISTS total_line_items_price decimal(10,2),     -- Total line items price
ADD COLUMN IF NOT EXISTS taxes_included boolean,                   -- Whether taxes are included
ADD COLUMN IF NOT EXISTS confirmed boolean,                        -- Order confirmation status
ADD COLUMN IF NOT EXISTS total_price_usd decimal(10,2),           -- Total price in USD
ADD COLUMN IF NOT EXISTS checkout_id bigint,                       -- Checkout ID
ADD COLUMN IF NOT EXISTS reference varchar(255),                   -- External reference
ADD COLUMN IF NOT EXISTS user_id bigint,                          -- User who created order
ADD COLUMN IF NOT EXISTS location_id bigint,                       -- Location ID
ADD COLUMN IF NOT EXISTS source_identifier varchar(255),           -- Source identifier
ADD COLUMN IF NOT EXISTS source_url text,                          -- Source URL
ADD COLUMN IF NOT EXISTS processed_at timestamptz,                 -- When order was processed
ADD COLUMN IF NOT EXISTS device_id bigint,                        -- Device ID
ADD COLUMN IF NOT EXISTS phone varchar(20),                        -- Customer phone
ADD COLUMN IF NOT EXISTS customer_locale varchar(10),              -- Customer locale
ADD COLUMN IF NOT EXISTS app_id bigint,                           -- App ID
ADD COLUMN IF NOT EXISTS browser_ip inet,                          -- Browser IP address
ADD COLUMN IF NOT EXISTS landing_site text,                        -- Landing site URL
ADD COLUMN IF NOT EXISTS referring_site text,                      -- Referring site URL
ADD COLUMN IF NOT EXISTS order_status_url text,                    -- Order status URL
ADD COLUMN IF NOT EXISTS checkout_token varchar(255),              -- Checkout token
ADD COLUMN IF NOT EXISTS token varchar(255),                       -- Order token
ADD COLUMN IF NOT EXISTS cart_token varchar(255),                  -- Cart token

-- ========================================
-- ENHANCED LINE ITEMS (JSON)
-- ========================================
ADD COLUMN IF NOT EXISTS total_items_quantity integer,             -- Total quantity of all items
ADD COLUMN IF NOT EXISTS line_items jsonb,                         -- Enhanced line items with all fields

-- ========================================
-- CUSTOMER DATA (JSON)
-- ========================================
ADD COLUMN IF NOT EXISTS customer_data jsonb,                      -- Complete customer information

-- ========================================
-- FULFILLMENT DATA (JSON)
-- ========================================
ADD COLUMN IF NOT EXISTS fulfillments jsonb,                       -- All fulfillment information

-- ========================================
-- REFUND DATA (JSON)
-- ========================================
ADD COLUMN IF NOT EXISTS refunds jsonb,                            -- All refund information

-- ========================================
-- TRANSACTION DATA (JSON)
-- ========================================
ADD COLUMN IF NOT EXISTS transactions jsonb,                       -- All payment transactions

-- ========================================
-- SHIPPING DATA (JSON)
-- ========================================
ADD COLUMN IF NOT EXISTS shipping_lines jsonb,                     -- Enhanced shipping information

-- ========================================
-- ADDITIONAL JSON FIELDS
-- ========================================
ADD COLUMN IF NOT EXISTS discount_applications jsonb,              -- Discount applications
ADD COLUMN IF NOT EXISTS note_attributes jsonb,                    -- Note attributes
ADD COLUMN IF NOT EXISTS tax_lines jsonb,                          -- Tax line details
ADD COLUMN IF NOT EXISTS order_adjustments jsonb,                  -- Order adjustments
ADD COLUMN IF NOT EXISTS client_details jsonb,                     -- Client details
ADD COLUMN IF NOT EXISTS payment_gateway_names jsonb,              -- Payment gateway names
ADD COLUMN IF NOT EXISTS payment_details jsonb;                    -- Payment details

-- ========================================
-- INDEXES FOR NEW COLUMNS
-- ========================================
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_orders_name" ON "{CLIENT_ID}_shopify_orders" (name);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_orders_cancelled_at" ON "{CLIENT_ID}_shopify_orders" (cancelled_at);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_orders_cancel_reason" ON "{CLIENT_ID}_shopify_orders" (cancel_reason);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_orders_total_discounts" ON "{CLIENT_ID}_shopify_orders" (total_discounts);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_orders_confirmed" ON "{CLIENT_ID}_shopify_orders" (confirmed);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_orders_checkout_id" ON "{CLIENT_ID}_shopify_orders" (checkout_id);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_orders_location_id" ON "{CLIENT_ID}_shopify_orders" (location_id);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_orders_total_items_quantity" ON "{CLIENT_ID}_shopify_orders" (total_items_quantity);

-- ========================================
-- NOTES
-- ========================================
-- This schema supports ALL Shopify Orders API fields
-- JSON columns contain complete nested data structures
-- Replace {CLIENT_ID} with actual client UUID (hyphens to underscores)
-- Example usage:
-- ALTER TABLE "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders" ADD COLUMN ...
