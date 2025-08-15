-- Update the Shopify products table to include variant columns
-- Run this in your Supabase SQL Editor to add variant columns

-- Add variant-specific columns to the existing shopify_products table
ALTER TABLE "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products" 
ADD COLUMN IF NOT EXISTS variant_id bigint,
ADD COLUMN IF NOT EXISTS sku varchar(100),
ADD COLUMN IF NOT EXISTS variant_title varchar(200),
ADD COLUMN IF NOT EXISTS price decimal(10,2),
ADD COLUMN IF NOT EXISTS weight decimal(8,3),
ADD COLUMN IF NOT EXISTS inventory_quantity integer,
ADD COLUMN IF NOT EXISTS requires_shipping boolean DEFAULT true,
ADD COLUMN IF NOT EXISTS position integer,
ADD COLUMN IF NOT EXISTS option1 varchar(100), -- Color, Size, etc.
ADD COLUMN IF NOT EXISTS option2 varchar(100),
ADD COLUMN IF NOT EXISTS option3 varchar(100),
ADD COLUMN IF NOT EXISTS barcode varchar(100),
ADD COLUMN IF NOT EXISTS compare_at_price decimal(10,2),
ADD COLUMN IF NOT EXISTS fulfillment_service varchar(50),
ADD COLUMN IF NOT EXISTS inventory_management varchar(50),
ADD COLUMN IF NOT EXISTS inventory_policy varchar(50);

-- Add indexes for variant-specific queries
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products_variant_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products" (variant_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products_sku" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products" (sku);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products_inventory" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products" (inventory_quantity);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products_price" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products" (price);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products_option1" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products" (option1);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products_option2" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products" (option2);
