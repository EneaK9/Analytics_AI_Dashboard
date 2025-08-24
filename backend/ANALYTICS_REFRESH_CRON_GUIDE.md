# Analytics Refresh Cron System Guide

## 🚀 Overview

The **Analytics Refresh Cron Job** automatically calls the `/api/dashboard/inventory-analytics` endpoint every 2 hours to keep dashboard data fresh and cached. This ensures users always get instant responses from pre-computed analytics data.

## ⚙️ How It Works

### 1. **Automated Endpoint Triggering**

- Calls `/api/dashboard/inventory-analytics` endpoint with `force_refresh=true`
- Processes **all active clients** and **all platforms** (Shopify, Amazon, Combined)  
- **Endpoint handles all cache removal and storage internally**
- Cron job just triggers the calculations, endpoint does the caching

### 2. **2-Hour Schedule**

- Analytics refresh runs **every 2 hours** automatically
- Ensures dashboard data is never more than 2 hours old
- Runs at: 00:00, 02:00, 04:00, 06:00, 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00, 22:00
- Comprehensive logging for monitoring

### 3. **Endpoint-Managed Caching**

- Uses existing endpoint caching logic (`save_cached_response()` in app.py)
- Endpoint removes old cache and stores fresh cache automatically  
- No duplicate caching logic - follows single responsibility principle
- Leverages existing cache infrastructure seamlessly

## 📂 Files Added/Modified

### **New Files:**

- `analytics_refresh_cron.py` - Main analytics refresh cron job
- `test_analytics_refresh_now.py` - Manual testing script
- `ANALYTICS_REFRESH_CRON_GUIDE.md` - This documentation

### **Modified Files:**

- `cron_setup.sh` - Added analytics refresh cron (Linux/Mac)
- `cron_setup.bat` - Added analytics refresh task (Windows)
- `docker-cron` - Added analytics refresh for production
- All existing cron configuration files updated

## 🛠️ Setup Instructions

### **Development (Windows):**

```bash
# Run as Administrator (includes new analytics refresh task)
cd backend
cron_setup.bat
```

### **Development (Linux/Mac):**

```bash
# Includes new analytics refresh cron
cd backend
chmod +x cron_setup.sh
./cron_setup.sh
```

### **Production (Render/Docker):**

- Analytics refresh is automatically configured in `docker-cron`
- Runs every 2 hours starting at midnight
- No additional setup required

## 🔧 Manual Operations

### **Test Analytics Refresh Manually:**

```bash
cd backend
python test_analytics_refresh_now.py
```

### **Run Analytics Refresh for Specific Client:**

```bash
# Edit analytics_refresh_cron.py to target specific client
python analytics_refresh_cron.py
```

### **Check Analytics Refresh Status:**

```bash
# Linux/Mac
tail -f logs/analytics_refresh_cron.log

# Windows  
type logs\analytics_refresh_cron.log
```

## 📊 Schedule Summary

| Cron Job | Frequency | Purpose | Calls Endpoint |
|----------|-----------|---------|----------------|
| `api_sync_cron.py` | Every 2 hours | Fetch fresh API data | ❌ No |
| `sku_analysis_cron.py` | Every 2 hours | Process & cache SKUs | ❌ No |
| `analytics_refresh_cron.py` | **Every 2 hours** | **Refresh analytics cache** | **✅ YES** |

## 🎯 What Gets Refreshed

### **For Each Active Client:**

- ✅ **Shopify Analytics** - Complete inventory analytics with KPIs
- ✅ **Amazon Analytics** - Complete inventory analytics with SKUs  
- ✅ **Combined Analytics** - Multi-platform consolidated view

### **Analytics Data Includes:**

- **KPIs**: Total sales, inventory levels, turnover rates
- **SKU Analysis**: Product performance, stock levels
- **Trend Analysis**: Sales trends, growth metrics
- **Platform Comparisons**: Cross-platform insights
- **Cache Optimization**: Pre-computed for instant access

## 🔍 Monitoring & Logs

### **Log Files:**

```bash
# Analytics refresh logs
logs/analytics_refresh_cron.log

# Related cron logs  
logs/api_sync_cron.log
logs/sku_analysis_cron.log
```

### **Log Content Examples:**

```
2024-01-15 08:00:01 - Starting analytics refresh cron job - AUTOMATED CACHE REFRESH
2024-01-15 08:00:02 - Found 1 active clients for analytics refresh  
2024-01-15 08:00:03 - Processing 1 clients × 3 platforms = 3 refresh jobs
2024-01-15 08:00:05 - ✅ SUCCESS - 3b619a14-3cd8-49fa-9c24-d8df5e54c452 (shopify): 1 platforms, 45 SKUs
2024-01-15 08:00:12 - ✅ SUCCESS - 3b619a14-3cd8-49fa-9c24-d8df5e54c452 (amazon): 1 platforms, 23 SKUs  
2024-01-15 08:00:18 - ✅ SUCCESS - 3b619a14-3cd8-49fa-9c24-d8df5e54c452 (all): 2 platforms, 68 SKUs
2024-01-15 08:00:19 - Results: 3 successful, 0 failed out of 3 total jobs
```

### **Windows Task Management:**

```bash
# Check task status
schtasks /Query /TN "Analytics_Refresh_Cron"

# Run task manually  
schtasks /Run /TN "Analytics_Refresh_Cron"

# Delete task
schtasks /Delete /TN "Analytics_Refresh_Cron" /F
```

### **Linux/Mac Cron Management:**

```bash
# View current cron jobs
crontab -l

# Edit cron jobs
crontab -e

# Check cron service status
service cron status
```

## 🚨 Troubleshooting

### **Common Issues:**

1. **"No active clients found"**
   - Check `client_api_credentials` table has `status = 'connected'` entries
   - Verify API integrations are properly configured

2. **"Failed to generate client token"**
   - Check `api_key_auth.py` token generation system
   - Verify client authentication is working

3. **"HTTP 500 errors"**
   - Check main application logs
   - Verify database connections are healthy
   - Check inventory-analytics endpoint functionality

4. **"Cache operation failed"**
   - Check database permissions
   - Verify client cache tables exist (`{client_id}_cached_responses`)
   - Check disk space on database server

### **Health Check:**

```bash
# Test the system end-to-end
cd backend
python test_analytics_refresh_now.py

# Check if cron is running (Linux/Mac)
ps aux | grep analytics_refresh_cron

# Check if task is running (Windows)
schtasks /Query /TN "Analytics_Refresh_Cron" /V
```

## ⚡ Performance Impact

- **Positive**: Users get instant dashboard responses (cached data)
- **Resource Usage**: Moderate - runs every 2 hours, not continuously  
- **Database Impact**: Minimal - uses existing caching infrastructure
- **API Load**: Controlled - only calls endpoints every 2 hours per client

## 🎯 Benefits

✅ **Always Fresh Data** - Dashboard data never more than 2 hours old  
✅ **Instant User Experience** - No waiting for analytics to load  
✅ **Automated Operations** - No manual intervention required  
✅ **Robust Error Handling** - Continues working even if some clients fail  
✅ **Comprehensive Monitoring** - Full logging and error tracking  
✅ **Resource Efficient** - Smart caching prevents duplicate work  

The analytics refresh cron job ensures your dashboard always provides lightning-fast analytics while keeping the data fresh and relevant for business decision-making.
