-- Update existing cache table to allow NULL expires_at
-- Run this in your Supabase SQL Editor if the table already exists

-- Make expires_at column nullable in existing table
ALTER TABLE "3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses" 
ALTER COLUMN expires_at DROP NOT NULL;

-- Verify the change
SELECT 
    column_name, 
    is_nullable, 
    data_type 
FROM information_schema.columns 
WHERE table_name = '3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses' 
    AND column_name = 'expires_at';

-- Update existing cache entries to set expires_at to NULL (optional)
UPDATE "3b619a14_3cd8_49fa_9c24_d8df5e54c452_cached_responses" 
SET expires_at = NULL;

SELECT 'Cache table updated successfully!' as status;
