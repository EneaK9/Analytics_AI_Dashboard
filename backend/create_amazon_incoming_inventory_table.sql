-- ========================================
-- AMAZON INCOMING INVENTORY TABLE - CREATE NEW TABLE
-- ========================================
-- This script creates a new table for Amazon FBA incoming inventory/shipments
-- Run this for each client by replacing the table name

-- Replace {CLIENT_ID} with actual client ID (with hyphens replaced by underscores)
-- Example: 6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_incoming_inventory

-- ========================================
-- CREATE AMAZON INCOMING INVENTORY TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS "{CLIENT_ID}_amazon_incoming_inventory" (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id uuid NOT NULL,
    shipment_id varchar(100) UNIQUE NOT NULL,                      -- Amazon shipment ID
    shipment_name varchar(255),                                    -- Shipment name
    shipment_status varchar(50),                                   -- Shipment status
    platform varchar(20) DEFAULT 'amazon',                        -- Platform identifier
    destination_fulfillment_center_id varchar(100),               -- Destination FC ID
    label_prep_preference varchar(50),                             -- Label prep preference
    are_cases_required boolean DEFAULT false,                      -- Cases required
    confirmed_need_by_date timestamptz,                           -- Confirmed need by date
    box_contents_source varchar(50),                              -- Box contents source
    estimated_box_contents_fee decimal(10,2),                     -- Estimated fee
    created_at timestamptz,                                       -- Record creation
    raw_data jsonb,                                               -- Complete raw API data
    processed_at timestamptz DEFAULT now()                        -- Processing timestamp
);

-- ========================================
-- INDEXES FOR AMAZON INCOMING INVENTORY
-- ========================================
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_incoming_inventory_shipment_id" ON "{CLIENT_ID}_amazon_incoming_inventory" (shipment_id);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_incoming_inventory_client_id" ON "{CLIENT_ID}_amazon_incoming_inventory" (client_id);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_incoming_inventory_status" ON "{CLIENT_ID}_amazon_incoming_inventory" (shipment_status);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_incoming_inventory_created_at" ON "{CLIENT_ID}_amazon_incoming_inventory" (created_at);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_incoming_inventory_destination_fc" ON "{CLIENT_ID}_amazon_incoming_inventory" (destination_fulfillment_center_id);
CREATE INDEX IF NOT EXISTS "idx_{CLIENT_ID}_amazon_incoming_inventory_confirmed_date" ON "{CLIENT_ID}_amazon_incoming_inventory" (confirmed_need_by_date);

-- ========================================
-- NOTES
-- ========================================
-- This table stores Amazon FBA incoming inventory/shipment data
-- Supports all Amazon SP-API FBA Inbound fields
-- Replace {CLIENT_ID} with actual client UUID (hyphens to underscores)
-- Example usage:
-- CREATE TABLE "6ee35b37_57af_4b70_bc62_1eddf1d0fd15_amazon_incoming_inventory" (...)
