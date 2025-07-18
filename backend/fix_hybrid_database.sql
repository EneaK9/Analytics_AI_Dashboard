-- Fix Hybrid Database Setup
-- This script adds missing columns and updates existing data

-- 1. Add missing columns to client_schemas table
ALTER TABLE client_schemas 
ADD COLUMN IF NOT EXISTS data_stored BOOLEAN DEFAULT FALSE;

ALTER TABLE client_schemas 
ADD COLUMN IF NOT EXISTS row_count INTEGER DEFAULT 0;

-- 2. Update existing schemas to mark them as having data
UPDATE client_schemas 
SET data_stored = TRUE, 
    row_count = (
        SELECT COUNT(*) 
        FROM client_data 
        WHERE client_data.client_id = client_schemas.client_id
    )
WHERE client_id IN (
    SELECT DISTINCT client_id 
    FROM client_data
);

-- 3. Verify the updates
SELECT 
    c.company_name,
    cs.data_type,
    cs.data_stored,
    cs.row_count,
    (SELECT COUNT(*) FROM client_data WHERE client_id = c.client_id) as actual_count
FROM clients c
LEFT JOIN client_schemas cs ON c.client_id = cs.client_id
ORDER BY c.created_at DESC; 