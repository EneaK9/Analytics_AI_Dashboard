-- LLM Response Cache Table Migration
-- Run this in your Supabase SQL Editor to create the cache table

-- Create the llm_response_cache table
CREATE TABLE IF NOT EXISTS llm_response_cache (
    id SERIAL PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    data_hash VARCHAR(64) NOT NULL,
    llm_response JSONB NOT NULL,
    data_type VARCHAR(50) DEFAULT 'unknown',
    total_records INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one cache entry per client
    UNIQUE(client_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_llm_cache_client_id ON llm_response_cache(client_id);
CREATE INDEX IF NOT EXISTS idx_llm_cache_data_hash ON llm_response_cache(data_hash);
CREATE INDEX IF NOT EXISTS idx_llm_cache_created_at ON llm_response_cache(created_at);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_llm_cache_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER trigger_update_llm_cache_updated_at
    BEFORE UPDATE ON llm_response_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_llm_cache_updated_at();

-- Add Row Level Security (RLS) policies
ALTER TABLE llm_response_cache ENABLE ROW LEVEL SECURITY;

-- Policy: Clients can only see their own cache entries
CREATE POLICY "Clients can view own cache" ON llm_response_cache
    FOR SELECT USING (auth.uid()::text = client_id::text);

-- Policy: Service role has full access (for admin operations)
CREATE POLICY "Service role full access" ON llm_response_cache
    FOR ALL USING (auth.role() = 'service_role');

-- Create a view for cache statistics
CREATE OR REPLACE VIEW llm_cache_stats AS
SELECT 
    COUNT(*) as total_entries,
    AVG(EXTRACT(EPOCH FROM (NOW() - created_at))/86400) as avg_age_days,
    MIN(EXTRACT(EPOCH FROM (NOW() - created_at))/86400) as newest_cache_days,
    MAX(EXTRACT(EPOCH FROM (NOW() - created_at))/86400) as oldest_cache_days,
    COUNT(CASE WHEN EXTRACT(EPOCH FROM (NOW() - created_at))/86400 > 7 THEN 1 END) as expired_entries
FROM llm_response_cache;

-- Create a function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_llm_cache(max_age_days INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM llm_response_cache 
    WHERE created_at < NOW() - INTERVAL '1 day' * max_age_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON llm_response_cache TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON llm_response_cache TO service_role;
GRANT SELECT ON llm_cache_stats TO authenticated;
GRANT SELECT ON llm_cache_stats TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_expired_llm_cache TO service_role;

-- Insert a sample record for testing (optional - remove in production)
-- INSERT INTO llm_response_cache (client_id, data_hash, llm_response, data_type, total_records)
-- VALUES (
--     '00000000-0000-0000-0000-000000000000',
--     'test_hash_1234567890abcdef',
--     '{"test": "response"}',
--     'test',
--     0
-- );

COMMENT ON TABLE llm_response_cache IS 'Cache for LLM responses to avoid regeneration when client data is unchanged';
COMMENT ON COLUMN llm_response_cache.data_hash IS 'SHA256 hash of client data to detect changes';
COMMENT ON COLUMN llm_response_cache.llm_response IS 'Cached LLM response as JSONB';
COMMENT ON COLUMN llm_response_cache.created_at IS 'When this cache entry was created';
COMMENT ON COLUMN llm_response_cache.updated_at IS 'When this cache entry was last updated'; 