-- Add Amazon integration manually to existing client
-- Replace the credentials with real Amazon API credentials

INSERT INTO client_api_credentials (
    client_id,
    platform_type,
    connection_name,
    credentials,
    sync_frequency_hours,
    status,
    created_at,
    updated_at
) VALUES (
    '3b619a14-3cd8-49fa-9c24-d8df5e54c452',
    'amazon',
    'Main Amazon Store',
    '{
        "seller_id": "YOUR_AMAZON_SELLER_ID",
        "marketplace_ids": ["ATVPDKIKX0DER"],
        "access_key_id": "YOUR_ACCESS_KEY_ID", 
        "secret_access_key": "YOUR_SECRET_ACCESS_KEY",
        "refresh_token": "YOUR_REFRESH_TOKEN",
        "region": "us-east-1"
    }'::json,
    24,
    'connected',
    NOW(),
    NOW()
);

-- Verify both integrations exist
SELECT 
    client_id,
    platform_type,
    connection_name,
    status,
    created_at
FROM client_api_credentials 
WHERE client_id = '3b619a14-3cd8-49fa-9c24-d8df5e54c452'
ORDER BY platform_type;
