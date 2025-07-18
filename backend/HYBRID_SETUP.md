# Hybrid Data Storage Setup Guide

This guide explains how to set up the hybrid data storage approach for client-specific data tables.

## 🎯 Overview

The hybrid approach provides:

- **Data Isolation**: Each client's data is logically separated
- **Flexible Schema**: AI-detected schemas with JSONB storage
- **Performance**: Optimized indexes and query functions
- **Scalability**: Easy to manage and query across clients

## 🛠️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    clients      │    │ client_schemas  │    │   client_data   │
│                 │    │                 │    │                 │
│ • client_id     │◄───┤ • client_id     │◄───┤ • client_id     │
│ • company_name  │    │ • table_name    │    │ • table_name    │
│ • email         │    │ • schema_def    │    │ • data (JSONB)  │
│ • password_hash │    │ • data_type     │    │ • created_at    │
└─────────────────┘    │ • data_stored   │    └─────────────────┘
                       │ • row_count     │
                       └─────────────────┘
```

## 📋 Setup Instructions

### 1. Database Migration

Run the migration script in your Supabase SQL Editor:

```bash
# Navigate to Supabase Dashboard > SQL Editor
# Copy and paste the contents of hybrid_migration.sql
# Execute the script
```

### 2. Verify Table Creation

Check that the following tables were created:

- `client_data` - Main data storage table
- Updated `client_schemas` - Now tracks `data_stored` and `row_count`

### 3. Test the Setup

Run a test query to verify:

```sql
-- Test the helper function
SELECT * FROM get_client_data_count('00000000-0000-0000-0000-000000000000');

-- Check the summary view
SELECT * FROM client_data_summary LIMIT 5;
```

## 🚀 Usage

### Creating Client Data

When a client is created with data:

1. **Schema Analysis**: AI analyzes the data structure
2. **Schema Storage**: Schema stored in `client_schemas` table
3. **Data Processing**: Data cleaned and prepared for insertion
4. **Data Storage**: Records stored in `client_data` with JSONB format
5. **Metadata Update**: Row counts and flags automatically updated

### Table Naming Convention

Tables are named using the pattern:

- `client_{uuid}_{data_type}` (e.g., `client_123e4567_ecommerce`)
- `client_{uuid}_data` (for general data)

### Retrieving Client Data

```python
# Get all data for a client
data = await ai_analyzer.get_client_data(client_id)

# Get specific table data
data = await ai_analyzer.get_client_data(client_id, table_name)

# Get limited results
data = await ai_analyzer.get_client_data(client_id, limit=50)
```

### API Endpoints

- `GET /api/data/{client_id}` - Get client data
- `GET /api/data/{client_id}?limit=50` - Get limited results
- `POST /api/superadmin/clients` - Create client with data

## 🔧 Database Functions

### `get_client_data_filtered()`

Retrieves client data with optional filtering:

```sql
SELECT * FROM get_client_data_filtered(
    '123e4567-e89b-12d3-a456-426614174000',  -- client_id
    'client_123e4567_ecommerce',             -- table_name (optional)
    100                                      -- limit (optional)
);
```

### `get_client_data_count()`

Gets the count of records for a client:

```sql
SELECT get_client_data_count(
    '123e4567-e89b-12d3-a456-426614174000',  -- client_id
    'client_123e4567_ecommerce'              -- table_name (optional)
);
```

## 📊 Performance Optimization

### Indexes

- `idx_client_data_client_id` - Fast client lookups
- `idx_client_data_table_name` - Fast table filtering
- `idx_client_data_client_table` - Combined lookups
- `idx_client_data_jsonb` - GIN index for JSONB queries

### Query Optimization

```sql
-- Efficient client data queries
SELECT data FROM client_data
WHERE client_id = $1 AND table_name = $2
ORDER BY created_at DESC LIMIT $3;

-- JSONB field queries
SELECT data->'product_name' as product_name
FROM client_data
WHERE client_id = $1 AND data->>'category' = 'electronics';
```

## 🔒 Security

### Row Level Security (RLS)

- Clients can only access their own data
- Service role has full access for admin operations

### Data Isolation

- Each client's data is logically separated
- Client ID is enforced at the database level
- JSONB structure prevents data leakage

## 📈 Monitoring

### View Client Data Summary

```sql
SELECT * FROM client_data_summary
WHERE company_name = 'Example Corp';
```

### Check Data Storage Status

```sql
SELECT
    company_name,
    data_type,
    data_stored,
    row_count,
    actual_row_count
FROM client_data_summary
WHERE data_stored = TRUE;
```

## 🐛 Troubleshooting

### Common Issues

1. **"client_data table doesn't exist"**

   - Run the migration script
   - Check Supabase permissions

2. **"No data returned"**

   - Verify client_id exists in clients table
   - Check that data was actually inserted
   - Verify RLS policies

3. **"Schema not found"**
   - Ensure client has uploaded data
   - Check client_schemas table for records

### Debug Queries

```sql
-- Check if client exists
SELECT * FROM clients WHERE email = 'client@example.com';

-- Check client schema
SELECT * FROM client_schemas WHERE client_id = 'your-client-id';

-- Check actual data
SELECT COUNT(*) FROM client_data WHERE client_id = 'your-client-id';
```

## 🔄 Migration from Previous System

If upgrading from the previous system:

1. Run the migration script
2. Existing client_schemas will be preserved
3. Data from data_uploads can be migrated:

```sql
-- Example migration query (customize as needed)
INSERT INTO client_data (client_id, table_name, data)
SELECT
    client_id,
    'migrated_data',
    jsonb_build_object('legacy_data', 'true')
FROM data_uploads
WHERE status = 'completed';
```

## 📝 Best Practices

1. **Batch Operations**: Use batch inserts for large datasets
2. **Index Usage**: Always filter by client_id first
3. **JSONB Queries**: Use appropriate operators (`->`, `->>`, `@>`)
4. **Monitoring**: Regularly check the client_data_summary view
5. **Cleanup**: Set up periodic cleanup of old data if needed

## 🎉 Success!

Your hybrid data storage system is now ready! Clients can upload data, and it will be:

- Analyzed by AI for structure
- Stored in optimized JSONB format
- Easily queryable with proper indexing
- Isolated per client for security

---

For questions or issues, check the application logs or contact your system administrator.
