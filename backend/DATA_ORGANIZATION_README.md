# Data Organization System

This system organizes client data from the `client_data` table into structured tables based on platform (Shopify, Amazon) and data type (orders, products).

## Overview

The data organization system extracts JSON data from the `client_data` table and reorganizes it into structured, queryable tables. This makes it much easier to generate analytics and dashboard queries.

## Client ID

**Target Client**: `3b619a14-3cd8-49fa-9c24-d8df5e54c452`

## Organization Structure

The system creates the following organized table structures:

### Shopify Orders
Table: `{client_id}_shopify_orders`
- Extracts order data from Shopify platform
- Columns: order_id, total_price, customer_email, status, etc.
- Handles billing/shipping addresses as JSON

### Shopify Products  
Table: `{client_id}_shopify_products`
- Extracts product catalog data from Shopify
- Columns: product_id, title, handle, vendor, variants, etc.
- Handles product variants and options as JSON

### Amazon Orders
Table: `{client_id}_amazon_orders` 
- Extracts order data from Amazon platform
- Columns: order_id, total_price, marketplace_id, fulfillment_channel, etc.
- Handles Amazon-specific fields like premium/business orders

### Amazon Products
Table: `{client_id}_amazon_products`
- Extracts product data from Amazon platform  
- Columns: asin, sku, title, price, quantity, etc.
- Handles Amazon marketplace specifics

## Usage

### 1. API Endpoints

#### Get Data Summary
```bash
GET /api/superadmin/client-data-summary/{client_id}
```
Returns analysis of current data structure and organization status.

#### Organize Data
```bash
POST /api/superadmin/organize-data/{client_id}
```
Runs the full data organization process.

### 2. Direct Script Usage

```bash
cd Analytics_AI_Dashboard/backend
python data_organizer.py --client-id 3b619a14-3cd8-49fa-9c24-d8df5e54c452
```

### 3. Test Scripts

#### Test Data Organization
```bash
python test_data_organization.py
```

#### Test API Endpoints
```bash
python test_organization_api.py
```

## Data Flow

1. **Fetch Raw Data**: Retrieves all data for the client from `client_data` table
2. **Categorize**: Analyzes JSON structure to determine platform and data type
3. **Transform**: Converts JSON data to structured format matching table schemas
4. **Insert**: Stores organized data in structured tables (currently in `client_data` with `organized_` prefix)

## Schema Design

Each organized table includes:
- **Primary Key**: UUID for unique identification
- **Client ID**: Links back to the original client
- **Platform Fields**: Specific to each platform's data structure
- **Raw Data**: Original JSON preserved for reference
- **Processed At**: Timestamp of organization

## Data Types Supported

### Shopify
- **Orders**: Identified by `order_id`, `customer_email`, `financial_status`
- **Products**: Identified by `title`, `handle`, `variants`

### Amazon  
- **Orders**: Identified by `order_id`, `marketplace_id`, `order_status`
- **Products**: Identified by `asin`, `sku`, `price`

## Benefits

1. **Faster Queries**: Structured tables with proper indexes
2. **Better Analytics**: Easy aggregations and joins
3. **Dashboard Performance**: Direct SQL queries instead of JSON parsing
4. **Data Integrity**: Proper data types and constraints
5. **Scalability**: Indexed tables for large datasets

## Future Enhancements

1. **True Table Creation**: Currently uses `client_data` with prefixes, can be enhanced to create actual separate tables
2. **Additional Platforms**: Support for WooCommerce, BigCommerce, etc.
3. **Real-time Sync**: Automatic organization of new data as it arrives
4. **Data Validation**: Enhanced validation and error handling
5. **Performance Monitoring**: Query performance analytics

## Error Handling

The system includes comprehensive error handling:
- Graceful failure for malformed JSON
- Automatic retry for database timeouts
- Detailed logging for troubleshooting
- Fallback categorization for unknown data types

## Monitoring

Check logs for:
- Organization progress
- Data categorization results
- Error patterns
- Performance metrics
