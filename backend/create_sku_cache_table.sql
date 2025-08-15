-- SKU Cache Table for Performance Optimization
-- This table stores cached SKU inventory data to prevent timeouts with large datasets

CREATE TABLE IF NOT EXISTS sku_cache (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    data_type VARCHAR(50) NOT NULL DEFAULT 'sku_list',
    data JSONB NOT NULL,
    total_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sku_cache_client_id ON sku_cache(client_id);
CREATE INDEX IF NOT EXISTS idx_sku_cache_data_type ON sku_cache(data_type);
CREATE INDEX IF NOT EXISTS idx_sku_cache_created_at ON sku_cache(created_at);

-- Create composite index for fast lookups
CREATE INDEX IF NOT EXISTS idx_sku_cache_client_data_type ON sku_cache(client_id, data_type);

-- Add a trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_sku_cache_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_sku_cache_updated_at
    BEFORE UPDATE ON sku_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_sku_cache_updated_at();

-- Clean up old cache entries (older than 24 hours) - run this periodically
-- DELETE FROM sku_cache WHERE created_at < NOW() - INTERVAL '24 hours';
