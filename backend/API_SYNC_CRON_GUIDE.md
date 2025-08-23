# 🔄 API Sync Cron System - PERFECT VERSION

## 🚀 Overview

The API Sync Cron System automatically syncs new data from Shopify and Amazon APIs every 24 hours (or based on each client's custom sync frequency). This ensures your dashboard always has the latest data without manual intervention.

## ⚙️ How It Works

### 1. **Automatic Scheduling**

- Each client has API credentials with `sync_frequency_hours` (default: 24 hours)
- System tracks `last_sync_at` and `next_sync_at` timestamps
- Cron job runs every hour checking for clients due for sync

### 2. **Smart Sync Process**

- **Connection Test**: Verifies API credentials before syncing
- **Data Fetching**: Gets orders, products, customers from APIs
- **Deduplication**: Only stores NEW data (no duplicates)
- **Same Tables**: Data goes to existing table names (no changes)
- **Comprehensive Logging**: Tracks every step with detailed logs

### 3. **Perfect Integration**

- Uses existing `client_api_credentials` table
- Stores data in same `client_{id}_data` tables
- Updates sync timestamps automatically
- Logs results in `client_api_sync_results` table

## 📂 Files Created/Updated

### **New Files:**

- `api_sync_cron.py` - **THE MAIN CRON JOB** for API sync
- `test_api_sync_now.py` - Manual testing script
- `cron_setup.sh` - Linux/Mac cron setup
- `API_SYNC_CRON_GUIDE.md` - This documentation

### **Updated Files:**

- `cron_setup.bat` - Windows Task Scheduler (now includes API sync)
- `docker-cron` - Docker/Render cron configuration
- `app.py` - Added `/api/admin/trigger-api-sync` endpoint

## 🛠️ Setup Instructions

### **Development (Windows):**

```bash
# Run as Administrator
cd backend
cron_setup.bat
```

### **Development (Linux/Mac):**

```bash
cd backend
chmod +x cron_setup.sh
./cron_setup.sh
```

### **Production (Render/Docker):**

- Cron is automatically configured in `docker-cron`
- API sync runs daily at midnight
- SKU analysis runs every 8 hours

## 🔧 Manual Operations

### **Test API Sync Immediately:**

```bash
cd backend
python test_api_sync_now.py
```

### **Force Sync Specific Client:**

```bash
python test_api_sync_now.py CLIENT_ID
python test_api_sync_now.py CLIENT_ID shopify
python test_api_sync_now.py CLIENT_ID amazon
```

### **Trigger via API (Admin Only):**

```bash
# Sync all clients due for sync
POST /api/admin/trigger-api-sync

# Force sync all clients (ignores schedule)
POST /api/admin/trigger-api-sync?force_sync=true

# Sync specific client
POST /api/admin/trigger-api-sync?client_id_filter=CLIENT_ID&force_sync=true

# Sync specific platform only
POST /api/admin/trigger-api-sync?platform_filter=shopify&force_sync=true
```

## 📊 Schedule Details

### **API Sync Cron Job:**

- **Frequency**: Every 24 hours (or client's custom `sync_frequency_hours`)
- **Default Time**: Midnight (00:00)
- **What it does**:
  - Fetches NEW data from Shopify/Amazon APIs
  - Stores data in same table names as always
  - Updates sync timestamps
  - Comprehensive logging

### **SKU Analysis Cron Job:**

- **Frequency**: Every 8 hours (01:00, 09:00, 17:00)
- **What it does**:
  - Analyzes stored data to generate SKU cache
  - Improves dashboard performance

## 📈 What Gets Synced

### **Shopify:**

- ✅ **Orders** - New orders and updates
- ✅ **Products** - Product info and variants
- ✅ **Customers** - Customer data
- ✅ **Inventory** - Stock levels

### **Amazon:**

- ✅ **Orders** - SP-API order data
- ✅ **Products** - Product catalog
- ✅ **Inventory** - Stock levels

### **Data Storage:**

- **Table**: `client_{client_id}_data` (SAME as always)
- **Deduplication**: Only new records stored
- **Format**: JSON data with metadata
- **Indexing**: Optimized for fast queries

## 🔍 Monitoring & Logs

### **Log Files:**

- `logs/api_sync_cron.log` - Main API sync logs
- `logs/sku_analysis_cron.log` - SKU analysis logs

### **Log Information:**

- 🕐 **Timestamps**: When sync started/completed
- 📊 **Statistics**: Records fetched, stored, processing time
- ✅ **Success/Failure**: Per client and platform
- 🔗 **API Calls**: Connection tests and data fetching
- 🗄️ **Database**: Deduplication and storage results

### **Example Log Output:**

```
2024-01-15 00:00:01 - api_sync_cron - INFO - 🚀 Starting full API sync cron job
2024-01-15 00:00:02 - api_sync_cron - INFO - 🔍 Found 2 API integrations due for sync
2024-01-15 00:00:03 - api_sync_cron - INFO - 🔄 Starting API sync for Client abc123 (shopify - Main Store)
2024-01-15 00:00:04 - api_sync_cron - INFO - ✅ API connection successful for shopify
2024-01-15 00:00:05 - api_sync_cron - INFO - 📥 Fetching new data from shopify API...
2024-01-15 00:00:08 - api_sync_cron - INFO - ✅ Stored 45 new orders records (after deduplication)
2024-01-15 00:00:09 - api_sync_cron - INFO - ✅ Stored 12 new products records (after deduplication)
2024-01-15 00:00:10 - api_sync_cron - INFO - ✅ API sync completed for Client abc123 (shopify)
2024-01-15 00:00:11 - api_sync_cron - INFO - 📅 Next sync scheduled for: 2024-01-16T00:00:00
```

## 🚨 Troubleshooting

### **No New Data Synced:**

1. Check if client is due for sync: Look at `next_sync_at` timestamp
2. Verify API credentials are still valid
3. Check API connection: Use test script
4. Review logs for specific errors

### **API Connection Errors:**

1. **Shopify**: Verify access token and shop domain
2. **Amazon**: Check seller ID and refresh token
3. **Rate Limits**: Sync will retry with backoff
4. **Credentials**: May need to refresh/update

### **Cron Not Running:**

1. **Linux**: `sudo systemctl status cron`
2. **Windows**: Check Task Scheduler
3. **Docker**: Check container logs and cron daemon

### **Database Issues:**

1. Check Supabase connection
2. Verify table permissions
3. Review deduplication logic

## 📊 Database Schema

### **client_api_credentials** (tracks sync status):

```sql
- credential_id (UUID)
- client_id (UUID)
- platform_type (text)
- status (text) -- connected/error/pending
- last_sync_at (timestamp)
- next_sync_at (timestamp)
- sync_frequency_hours (integer)
- error_message (text)
```

### **client_api_sync_results** (sync history):

```sql
- client_id (UUID)
- credential_id (UUID)
- platform_type (text)
- records_fetched (integer)
- records_stored (integer)
- sync_duration_seconds (float)
- success (boolean)
- data_types_synced (json)
- sync_triggered_by (text)
```

## 🎯 Benefits

✅ **Automatic**: No manual intervention needed  
✅ **Smart**: Only syncs when due, stores only new data  
✅ **Reliable**: Comprehensive error handling and logging  
✅ **Scalable**: Handles unlimited clients and platforms  
✅ **Consistent**: Same table names and data structure  
✅ **Monitored**: Full visibility into sync process  
✅ **Flexible**: Custom sync frequencies per client

## ⚡ Performance

- **Deduplication**: Prevents duplicate records
- **Batch Processing**: Efficient database operations
- **Smart Scheduling**: Avoids unnecessary API calls
- **Parallel Processing**: Multiple clients can sync simultaneously
- **Error Recovery**: Failed syncs are retried automatically

## 🔐 Security

- **Encrypted Credentials**: API keys stored securely
- **Connection Validation**: Tests before syncing
- **Admin-Only Triggers**: Manual sync requires authentication
- **Audit Trail**: Complete sync history logged
- **Rate Limit Handling**: Respects API limitations

---

## 🚀 Quick Start Checklist

1. ✅ **Setup cron jobs**: Run `cron_setup.bat` (Windows) or `cron_setup.sh` (Linux/Mac)
2. ✅ **Test immediately**: Run `python test_api_sync_now.py`
3. ✅ **Check logs**: View `logs/api_sync_cron.log`
4. ✅ **Verify data**: Check dashboard for new data
5. ✅ **Monitor**: Logs show sync status and results

**Your API sync system is now PERFECT! 🎉**
