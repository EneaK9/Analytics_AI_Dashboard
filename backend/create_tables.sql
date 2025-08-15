-- SQL to create organized data tables in Supabase
-- Run this in your Supabase SQL Editor

-- Shopify Orders Table
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

-- Shopify Products Table  
CREATE TABLE IF NOT EXISTS "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products" (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id uuid NOT NULL,
    product_id bigint,
    title varchar(500),
    handle varchar(255),
    vendor varchar(255),
    platform varchar(20) DEFAULT 'shopify',
    status varchar(50),
    tags text,
    variants jsonb,
    options jsonb,
    images jsonb,
    raw_data jsonb,
    processed_at timestamptz DEFAULT now()
);

-- Indexes for Shopify Products
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products_product_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products" (product_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products_client_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products" (client_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products_handle" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products" (handle);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products_vendor" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_shopify_products" (vendor);

-- Amazon Orders Table
CREATE TABLE IF NOT EXISTS "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_orders" (
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
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_orders_order_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_orders" (order_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_orders_client_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_orders" (client_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_orders_marketplace_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_orders" (marketplace_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_orders_created_at" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_orders" (created_at);

-- Amazon Products Table
CREATE TABLE IF NOT EXISTS "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_products" (
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
    raw_data jsonb,
    processed_at timestamptz DEFAULT now()
);

-- Indexes for Amazon Products
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_products_asin" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_products" (asin);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_products_sku" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_products" (sku);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_products_client_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_products" (client_id);
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_products_marketplace_id" ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_amazon_products" (marketplace_id);
