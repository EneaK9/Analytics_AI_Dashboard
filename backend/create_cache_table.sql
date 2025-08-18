-- SQL to create cache table for daily response caching in Supabase
-- Run this in your Supabase SQL Editor

-- Cache Table for Client: 3b619a14-3cd8-49fa-9c24-d8df5e54c452
CREATE TABLE IF NOT EXISTS "3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses" (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id uuid NOT NULL,
    endpoint_url text NOT NULL,
    cache_key text NOT NULL,
    response_data jsonb NOT NULL,
    created_at timestamptz DEFAULT now(),
    expires_at timestamptz NOT NULL,
    UNIQUE(cache_key)
);

-- Indexes for Cache Table Performance
CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses_cache_key" 
ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses" (cache_key);

CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses_expires_at" 
ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses" (expires_at);

CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses_client_id" 
ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses" (client_id);

CREATE INDEX IF NOT EXISTS "idx_3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses_endpoint" 
ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses" (endpoint_url);

-- Add Row Level Security (RLS) policy to ensure clients can only access their own cached data
ALTER TABLE "3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only access their own cached responses" 
ON "3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses"
FOR ALL USING (client_id = '3b619a14-3cd8-49fa-9c24-d8df5e54c452'::uuid);

-- Create function to automatically clean up expired cache entries (optional)
CREATE OR REPLACE FUNCTION cleanup_expired_cache_3b619a14_3cd8_49fa_9c24_d8df5e54c452()
RETURNS void AS $$
BEGIN
    DELETE FROM "3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses" 
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Verify table creation
SELECT 
    'Cache table created successfully!' as status,
    COUNT(*) as initial_record_count
FROM "3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses";
