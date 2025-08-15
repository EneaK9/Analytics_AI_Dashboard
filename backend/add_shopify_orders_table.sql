-- Add Shopify orders table for comprehensive analytics
-- Run this in your Supabase SQL Editor

-- Shopify Orders Table for client: 3b619a14-3cd8-49fa-9c24-d8df5e54c452
CREATE TABLE IF NOT EXISTS "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders" (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id uuid NOT NULL,
    order_id bigint UNIQUE NOT NULL,
    order_number varchar(50),
    platform varchar(20) DEFAULT 'shopify',
    currency varchar(3),
    total_price decimal(10,2),
    subtotal_price decimal(10,2),
    total_tax decimal(10,2),
    financial_status varchar(50),
    fulfillment_status varchar(50),
    customer_id bigint,
    customer_email varchar(255),
    created_at timestamptz,
    updated_at timestamptz,
    source_name varchar(100),
    line_items_count integer,
    tags text,
    billing_address jsonb,
    shipping_address jsonb,
    discount_codes jsonb,
    raw_data jsonb,
    processed_at timestamptz DEFAULT now()
);

-- Indexes for Shopify Orders
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders_order_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders" (order_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders_client_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders" (client_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders_customer_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders" (customer_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders_created_at" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders" (created_at);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders_financial_status" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders" (financial_status);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders_total_price" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_orders" (total_price);

-- Add similar table for Amazon client if needed
CREATE TABLE IF NOT EXISTS "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_shopify_orders" (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id uuid NOT NULL,
    order_id bigint UNIQUE NOT NULL,
    order_number varchar(50),
    platform varchar(20) DEFAULT 'shopify',
    currency varchar(3),
    total_price decimal(10,2),
    subtotal_price decimal(10,2),
    total_tax decimal(10,2),
    financial_status varchar(50),
    fulfillment_status varchar(50),
    customer_id bigint,
    customer_email varchar(255),
    created_at timestamptz,
    updated_at timestamptz,
    source_name varchar(100),
    line_items_count integer,
    tags text,
    billing_address jsonb,
    shipping_address jsonb,
    discount_codes jsonb,
    raw_data jsonb,
    processed_at timestamptz DEFAULT now()
);

-- Indexes for second client Shopify Orders
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_shopify_orders_order_id" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_shopify_orders" (order_id);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_shopify_orders_client_id" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_shopify_orders" (client_id);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_shopify_orders_customer_id" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_shopify_orders" (customer_id);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_shopify_orders_created_at" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_shopify_orders" (created_at);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_shopify_orders_financial_status" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_shopify_orders" (financial_status);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_shopify_orders_total_price" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_shopify_orders" (total_price);
