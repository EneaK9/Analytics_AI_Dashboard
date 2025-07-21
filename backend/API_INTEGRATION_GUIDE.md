# 🔗 API Integration Guide

Complete guide for setting up and using Shopify, Amazon, and WooCommerce integrations in the Analytics AI Dashboard.

## 🎯 Overview

The Analytics AI Dashboard now supports direct API integrations with major e-commerce platforms, allowing automatic data syncing instead of manual CSV uploads.

### ✅ Supported Platforms

- **Shopify** - Complete orders, products, and customer data
- **Amazon Seller** - SP-API for orders and inventory data
- **WooCommerce** - REST API for WordPress stores
- **Manual Upload** - CSV, JSON, XML file uploads (existing)

## 🚀 Setup Instructions

### 1. Database Migration

First, run the API integration migration in your Supabase SQL Editor:

```bash
# Navigate to your Supabase Dashboard > SQL Editor
# Copy and paste the contents of: backend/api_integration_migration.sql
# Click "Run" to execute the migration
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Environment Variables

Add these to your `.env` file if using external API services:

```bash
# Optional: For enhanced API features
REDIS_URL=redis://localhost:6379
```

## 📊 Platform Setup Guides

### 🛍️ Shopify Integration

#### What You Need:

- Shopify store with Admin access
- Private app credentials

#### Setup Steps:

1. **Go to Shopify Admin** → Apps → "App and sales channel settings"
2. **Click "Develop apps"** → "Create an app"
3. **Configure Admin API scopes:**
   - `read_orders` - Access to order data
   - `read_products` - Product information
   - `read_customers` - Customer data
   - `read_analytics` - Store analytics
4. **Install the app** and copy the **Access Token**
5. **Get your shop domain** (e.g., `mystore.myshopify.com`)

#### In SuperAdmin Dashboard:

- **Platform**: Select Shopify
- **Shop Domain**: `mystore.myshopify.com` (without https://)
- **Access Token**: Your private app access token
- **Connection Name**: "Main Store" or similar

---

### 📦 Amazon Seller Integration

#### What You Need:

- Amazon Seller Central account
- SP-API access (requires approval)
- AWS IAM credentials

#### Setup Steps:

1. **Apply for SP-API access** in Seller Central
2. **Create AWS IAM user** with SP-API permissions
3. **Generate LWA refresh token** through Amazon's OAuth flow
4. **Get your Seller ID** from Seller Central settings

#### Required Information:

- **Seller ID**: Found in Seller Central → Settings → Account Info
- **Marketplace IDs**:
  - US: `ATVPDKIKX0DER`
  - CA: `A2EUQ1WTGCTBG2`
  - UK: `A1F83G8C2ARO7P`
- **AWS Access Key ID**: From IAM user
- **Secret Access Key**: From IAM user
- **Refresh Token**: From LWA OAuth flow

#### In SuperAdmin Dashboard:

- **Platform**: Select Amazon
- **Seller ID**: Your Amazon Seller ID
- **Marketplace IDs**: Comma-separated (e.g., `ATVPDKIKX0DER,A2EUQ1WTGCTBG2`)
- **Access Key ID**: AWS IAM Access Key
- **Secret Access Key**: AWS IAM Secret Key
- **Refresh Token**: LWA refresh token
- **Region**: `us-east-1` (or your preferred AWS region)

---

### 🌐 WooCommerce Integration

#### What You Need:

- WordPress site with WooCommerce
- Admin access to create API keys

#### Setup Steps:

1. **Go to WooCommerce** → Settings → Advanced → REST API
2. **Click "Add Key"**
3. **Set permissions** to "Read/Write"
4. **Generate key** and copy Consumer Key & Secret

#### In SuperAdmin Dashboard:

- **Platform**: Select WooCommerce
- **Site URL**: `https://mystore.com`
- **Consumer Key**: From WooCommerce REST API
- **Consumer Secret**: From WooCommerce REST API
- **API Version**: `wc/v3` (recommended)

## 🔧 Using the SuperAdmin Dashboard

### Creating API-Integrated Clients

1. **Navigate to SuperAdmin Dashboard**
2. **Click "Add Client"**
3. **Fill in basic client information**:
   - Company Name
   - Email
   - Password
4. **Select "API" as Input Method**
5. **Choose your e-commerce platform**
6. **Fill in platform-specific credentials**
7. **Click "Test API Connection"** to verify
8. **Set sync frequency** (hourly, daily, etc.)
9. **Click "Create Client"**

### Connection Testing

The system will automatically:

- ✅ Test API credentials
- ✅ Verify permissions
- ✅ Fetch sample data
- ✅ Display connection status

### Automatic Data Sync

Once connected, the system will:

- 🔄 Sync data at specified intervals
- 📊 Generate dashboards automatically
- ⚡ Process orders, products, customers
- 🛡️ Handle rate limiting and errors

## 📈 Data Types Synced

### Shopify

- **Orders**: Sales, revenue, order details, customer info
- **Products**: Inventory, pricing, variants, categories
- **Customers**: Demographics, purchase history, LTV

### Amazon

- **Orders**: Order details, fulfillment status, marketplace data
- **Inventory**: Stock levels, product performance
- **Financial**: Settlement data, fees, refunds

### WooCommerce

- **Orders**: WooCommerce order data, payment methods
- **Products**: Product catalog, stock, categories
- **Customers**: Customer accounts and order history

## 🛡️ Security Features

### Data Protection

- 🔒 **Encrypted credentials** stored in database
- 🔐 **API key hashing** for security
- 🛡️ **Row-level security** policies
- 🚦 **Rate limiting** to prevent abuse

### Access Control

- 👤 **Client isolation** - each client sees only their data
- 🔑 **Superadmin controls** - manage all integrations
- 📝 **Audit logs** - track all API operations

## ⚡ Performance Optimization

### Smart Syncing

- 📅 **Incremental sync** - only new/updated data
- ⏰ **Configurable frequency** - hourly to weekly
- 🔄 **Retry logic** - automatic error recovery
- 💾 **Caching** - faster dashboard generation

### Rate Limiting

- 🚦 **Shopify**: 40 requests/second
- 🚦 **Amazon**: 5 requests/second with burst
- 🚦 **WooCommerce**: 10 requests/second (configurable)

## 🚨 Error Handling

### Common Issues & Solutions

#### Shopify Errors

- **401 Unauthorized**: Check access token
- **403 Forbidden**: Verify app permissions/scopes
- **429 Rate Limited**: System will auto-retry

#### Amazon Errors

- **401 Invalid Token**: Refresh token expired
- **403 Access Denied**: Check SP-API permissions
- **429 Throttled**: Rate limiting - will retry

#### WooCommerce Errors

- **401 Unauthorized**: Check consumer key/secret
- **404 Not Found**: Verify site URL and API version
- **SSL Errors**: Ensure HTTPS is properly configured

### Monitoring & Logs

- 📊 **Connection status** in SuperAdmin dashboard
- 📈 **Sync history** and success rates
- 🚨 **Error alerts** for failed syncs
- 📝 **Detailed logs** for troubleshooting

## 🔄 Migration from Manual Upload

Existing clients can be upgraded to API integration:

1. **Contact SuperAdmin** to add API credentials
2. **Test connection** before switching
3. **Gradual rollout** - keep manual backup initially
4. **Monitor dashboards** for data consistency

## 📚 API Reference

### Endpoints

- `POST /api/superadmin/clients/api-integration` - Create client with API
- `GET /api/superadmin/api-platforms` - Get platform configurations
- `POST /api/superadmin/test-api-connection` - Test API credentials

### Database Tables

- `client_api_credentials` - Store encrypted API keys
- `client_api_sync_results` - Track sync history
- `api_platform_configs` - Platform configuration data

## 🎯 Next Steps

### Planned Features

- 🔄 **Webhook support** for real-time updates
- 📊 **Multi-store aggregation** for enterprise clients
- 🌍 **Additional platforms** (BigCommerce, Etsy, etc.)
- 🤖 **AI-powered insights** from integrated data
- 📈 **Advanced analytics** across platforms

### Getting Support

- 📧 **Documentation**: Check this guide first
- 🐛 **Bug Reports**: Include connection logs
- 💡 **Feature Requests**: Submit via admin panel
- 🚨 **Urgent Issues**: Contact system administrator

---

## ✅ Success Checklist

- [ ] Database migration completed
- [ ] Dependencies installed
- [ ] Platform credentials obtained
- [ ] Test connection successful
- [ ] Client created with API integration
- [ ] Dashboard generated successfully
- [ ] Data syncing correctly
- [ ] Error monitoring set up

**🎉 Congratulations! Your API integration is now live and automatically syncing data!**
