-- ========================================
-- SHOPIFY PRODUCTS TABLE - ADD ALL MISSING COLUMNS
-- ========================================
-- This script adds ALL possible fields from the Shopify Products API
-- Run this for each client's Shopify products table by replacing the table name

-- Replace {CLIENT_ID} with actual client ID (with hyphens replaced by underscores)
-- Example: 3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products

-- ========================================
-- ENHANCED PRODUCT FIELDS
-- ========================================
ALTER TABLE "{CLIENT_ID}_shopify_products"
ADD COLUMN IF NOT EXISTS body_html text,                           -- Product description HTML
ADD COLUMN IF NOT EXISTS published_at timestamptz,                 -- When product was published
ADD COLUMN IF NOT EXISTS template_suffix varchar(100),             -- Template suffix
ADD COLUMN IF NOT EXISTS published_scope varchar(50),              -- Published scope
ADD COLUMN IF NOT EXISTS admin_graphql_api_id varchar(255),        -- GraphQL API ID
ADD COLUMN IF NOT EXISTS seo_title varchar(255),                   -- SEO title
ADD COLUMN IF NOT EXISTS seo_description text,                     -- SEO description
ADD COLUMN IF NOT EXISTS created_at timestamptz,                   -- Product creation date
ADD COLUMN IF NOT EXISTS updated_at timestamptz,                   -- Product update date

-- ========================================
-- ENHANCED VARIANTS (JSON)
-- ========================================
-- The variants column will now contain ALL variant fields:
-- - variant_id, product_id, title, price, sku, position
-- - inventory_policy, compare_at_price, fulfillment_service
-- - inventory_management, option1, option2, option3
-- - created_at, updated_at, taxable, barcode, grams
-- - image_id, weight, weight_unit, inventory_item_id
-- - inventory_quantity, old_inventory_quantity, requires_shipping
-- - admin_graphql_api_id

-- ========================================
-- ENHANCED OPTIONS (JSON)
-- ========================================
-- Enhanced options column will contain:
-- - option_id, product_id, name, position, values[]

-- ========================================
-- ENHANCED IMAGES (JSON)
-- ========================================
-- Enhanced images column will contain:
-- - image_id, product_id, position, created_at, updated_at
-- - alt, width, height, src, variant_ids[]

-- ========================================
-- COUNT FIELDS
-- ========================================
ADD COLUMN IF NOT EXISTS variants_count integer,                   -- Number of variants
ADD COLUMN IF NOT EXISTS options_count integer,                    -- Number of options

-- ========================================
-- IMAGE DATA (JSON)
-- ========================================
ADD COLUMN IF NOT EXISTS image jsonb;                             -- Featured image data

-- ========================================
-- INDEXES FOR NEW COLUMNS
-- ========================================
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_products_published_at" ON "{CLIENT_ID}_shopify_products" (published_at);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_products_published_scope" ON "{CLIENT_ID}_shopify_products" (published_scope);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_products_template_suffix" ON "{CLIENT_ID}_shopify_products" (template_suffix);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_products_variants_count" ON "{CLIENT_ID}_shopify_products" (variants_count);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_products_options_count" ON "{CLIENT_ID}_shopify_products" (options_count);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_products_created_at" ON "{CLIENT_ID}_shopify_products" (created_at);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_products_updated_at" ON "{CLIENT_ID}_shopify_products" (updated_at);

-- ========================================
-- JSON INDEXES FOR PERFORMANCE
-- ========================================
-- Index on SKUs within variants JSON
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_products_variants_sku" ON "{CLIENT_ID}_shopify_products" USING GIN ((variants -> 'sku'));

-- Index on inventory quantities within variants JSON
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_products_variants_inventory" ON "{CLIENT_ID}_shopify_products" USING GIN ((variants -> 'inventory_quantity'));

-- Index on variant prices
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_shopify_products_variants_price" ON "{CLIENT_ID}_shopify_products" USING GIN ((variants -> 'price'));

-- ========================================
-- NOTES
-- ========================================
-- This schema supports ALL Shopify Products API fields
-- Variants, options, and images are stored as complete JSON objects
-- JSON indexes enable efficient querying of nested data
-- Replace {CLIENT_ID} with actual client UUID (hyphens to underscores)
-- Example usage:
-- ALTER TABLE "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products" ADD COLUMN ...
