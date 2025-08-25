-- ========================================
-- AMAZON PRODUCTS TABLE - ADD ALL MISSING COLUMNS
-- ========================================
-- This script adds ALL possible fields from the Amazon SP-API Catalog
-- Run this for each client's Amazon products table by replacing the table name

-- Replace {CLIENT_ID} with actual client ID (with hyphens replaced by underscores)
-- Example: 6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products

-- ========================================
-- ENHANCED PRODUCT IDENTIFICATION FIELDS
-- ========================================
ALTER TABLE "{CLIENT_ID}_amazon_products"
ADD COLUMN IF NOT EXISTS manufacturer varchar(255),                -- Product manufacturer
ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now(),     -- Record creation time

-- ========================================
-- MARKETPLACE INFORMATION
-- ========================================
ADD COLUMN IF NOT EXISTS marketplace_ids jsonb,                    -- All marketplace IDs

-- ========================================
-- ENHANCED PRODUCT DATA (JSON)
-- ========================================
ADD COLUMN IF NOT EXISTS images jsonb,                             -- Product images from catalog
ADD COLUMN IF NOT EXISTS sales_rank jsonb,                         -- Sales ranking data
ADD COLUMN IF NOT EXISTS relationships jsonb;                      -- Product relationships

-- ========================================
-- INDEXES FOR NEW COLUMNS
-- ========================================
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_products_manufacturer" ON "{CLIENT_ID}_amazon_products" (manufacturer);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_products_created_at" ON "{CLIENT_ID}_amazon_products" (created_at);

-- ========================================
-- JSON INDEXES FOR PERFORMANCE
-- ========================================
-- Index on marketplace IDs
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_products_marketplace_ids" ON "{CLIENT_ID}_amazon_products" USING GIN (marketplace_ids);

-- Index on images data
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_products_images" ON "{CLIENT_ID}_amazon_products" USING GIN (images);

-- Index on sales rank data
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_products_sales_rank" ON "{CLIENT_ID}_amazon_products" USING GIN (sales_rank);

-- Index on relationships data
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_products_relationships" ON "{CLIENT_ID}_amazon_products" USING GIN (relationships);

-- ========================================
-- NOTES
-- ========================================
-- This schema supports ALL Amazon SP-API Catalog fields
-- Enhanced with manufacturer, marketplace data, images, sales rankings
-- JSON columns contain complete catalog API response data
-- Replace {CLIENT_ID} with actual client UUID (hyphens to underscores)
-- Example usage:
-- ALTER TABLE "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products" ADD COLUMN ...
