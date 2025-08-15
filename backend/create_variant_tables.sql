-- Additional SQL to create product variant tables for better organization
-- Run this in your Supabase SQL Editor AFTER the main tables

-- Shopify Product Variants Table
CREATE TABLE IF NOT EXISTS "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_variants" (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id uuid NOT NULL,
    product_id bigint NOT NULL,
    variant_id bigint UNIQUE NOT NULL,
    sku varchar(100),
    title varchar(200),
    price decimal(10,2),
    weight decimal(8,3),
    inventory_quantity integer,
    requires_shipping boolean DEFAULT true,
    position integer,
    option1 varchar(100), -- Size, Color, etc.
    option2 varchar(100),
    option3 varchar(100),
    barcode varchar(100),
    compare_at_price decimal(10,2),
    fulfillment_service varchar(50),
    inventory_management varchar(50),
    inventory_policy varchar(50),
    created_at timestamptz,
    updated_at timestamptz,
    processed_at timestamptz DEFAULT now(),
    
    -- Foreign key reference to parent product
    FOREIGN KEY (client_id) REFERENCES "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products"(client_id)
);

-- Indexes for Shopify Variants
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_variants_variant_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_variants" (variant_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_variants_product_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_variants" (product_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_variants_sku" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_variants" (sku);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_variants_client_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_variants" (client_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_variants_inventory" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_variants" (inventory_quantity);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_variants_price" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_variants" (price);

-- Amazon Product Variants Table (for products with multiple options)
CREATE TABLE IF NOT EXISTS "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_variants" (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id uuid NOT NULL,
    parent_asin varchar(20),
    asin varchar(20) UNIQUE NOT NULL,
    sku varchar(100),
    title varchar(500),
    price decimal(10,2),
    quantity integer,
    variation_attributes jsonb, -- Store color, size, etc. as JSON
    marketplace_id varchar(50),
    status varchar(50),
    created_at timestamptz,
    updated_at timestamptz,
    processed_at timestamptz DEFAULT now(),
    
    -- Foreign key reference to parent product  
    FOREIGN KEY (client_id) REFERENCES "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_products"(client_id)
);

-- Indexes for Amazon Variants
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_variants_asin" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_variants" (asin);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_variants_parent_asin" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_variants" (parent_asin);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_variants_sku" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_variants" (sku);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_variants_client_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_variants" (client_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_variants_quantity" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_variants" (quantity);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_variants_price" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_variants" (price);
