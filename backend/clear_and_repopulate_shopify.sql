-- Clear existing shopify products and repopulate properly
-- Run this in your Supabase SQL Editor

-- Clear existing data from shopify products table
DELETE FROM "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products";

-- Confirm deletion
SELECT COUNT(*) as remaining_rows FROM "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products";
