-- Create Amazon tables for client: 6ee35b37-57af-4b70-bc62-1eddf1d0fd15
-- Run this in your Supabase SQL Editor

-- Amazon Orders Table
CREATE TABLE IF NOT EXISTS "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders" (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id uuid NOT NULL,
    order_id varchar(100) UNIQUE NOT NULL,
    order_number varchar(100),
    platform varchar(20) DEFAULT 'amazon',
    currency varchar(3),
    total_price decimal(10,2),
    order_status varchar(50),
    sales_channel varchar(100),
    marketplace_id varchar(50),
    payment_method varchar(100),
    fulfillment_channel varchar(50),
    is_premium_order boolean,
    is_business_order boolean,
    number_of_items_shipped integer,
    number_of_items_unshipped integer,
    created_at timestamptz,
    updated_at timestamptz,
    raw_data jsonb,
    processed_at timestamptz DEFAULT now()
);

-- Indexes for Amazon Orders
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders_order_id" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders" (order_id);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders_client_id" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders" (client_id);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders_marketplace_id" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders" (marketplace_id);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders_created_at" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders" (created_at);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders_status" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders" (order_status);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders_total_price" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_orders" (total_price);

-- Amazon Products Table
CREATE TABLE IF NOT EXISTS "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products" (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id uuid NOT NULL,
    asin varchar(20),
    sku varchar(100),
    title varchar(500),
    platform varchar(20) DEFAULT 'amazon',
    brand varchar(255),
    category varchar(255),
    price decimal(10,2),
    quantity integer,
    status varchar(50),
    marketplace_id varchar(50),
    product_type varchar(100),
    fulfillment_channel varchar(50),
    condition_type varchar(50),
    raw_data jsonb,
    processed_at timestamptz DEFAULT now()
);

-- Indexes for Amazon Products
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products_asin" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products" (asin);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products_sku" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products" (sku);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products_client_id" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products" (client_id);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products_marketplace_id" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products" (marketplace_id);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products_price" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products" (price);
CREATE INDEX IF NOT EXISTS "idx_6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products_quantity" ON "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_products" (quantity);
