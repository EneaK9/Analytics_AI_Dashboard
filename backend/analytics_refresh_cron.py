#!/usr/bin/env python3
"""
Analytics Refresh Cron Job - AUTOMATED ENDPOINT TRIGGER
Automatically calls the inventory-analytics endpoint with force_refresh=true
The endpoint handles all cache removal and storage internally
Runs every 5 minutes to keep dashboard data fresh - FOR TESTING ONLY
"""

import asyncio
import logging
import sys
import os
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
# Optional dotenv import for local development
try:
    from dotenv import load_dotenv
    load_dotenv_available = True
except ImportError:
    load_dotenv_available = False

# Setup comprehensive logging with safe file handling
handlers = [logging.StreamHandler(sys.stdout)]

# Try to add file handler, but don't fail if logs directory doesn't exist
try:
    os.makedirs('logs', exist_ok=True)
    handlers.append(logging.FileHandler('logs/analytics_refresh_cron.log', mode='a'))
except (OSError, PermissionError) as e:
    # Fall back to stdout-only logging in deployment environments
    print(f"Warning: Could not create analytics log file, using stdout only: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)

# Load environment variables (optional for local development)
if load_dotenv_available:
    load_dotenv()

class AnalyticsRefreshCronJob:
    """Automated analytics refresh cron job - keeps dashboard data fresh"""
    
    def __init__(self):
        self.platforms = ["shopify", "amazon", "all"]
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.timeout = 300  # 5 minutes timeout
        self.use_direct_calls = True  # Use direct function calls instead of HTTP
        logger.info("📊 Analytics Refresh Cron Job initialized - DIRECT CALLS MODE (no HTTP)")
    
    def _get_admin_client(self):
        """Get Supabase admin client"""
        try:
            from database import get_admin_client
            return get_admin_client()
        except Exception as e:
            logger.error(f"Failed to get admin client: {e}")
            return None
    
    async def get_active_clients(self) -> List[str]:
        """Get all active clients that have API integrations"""
        try:
            db_client = self._get_admin_client()
            if not db_client:
                logger.error("❌ No database connection")
                return []
            
            # Get all clients with connected API credentials
            response = db_client.table("client_api_credentials").select(
                "client_id"
            ).eq("status", "connected").execute()
            
            if not response.data:
                logger.warning("⚠️ No active clients found")
                return []
            
            # Get unique client IDs
            client_ids = list(set([row['client_id'] for row in response.data]))
            logger.info(f"📋 Found {len(client_ids)} active clients for analytics refresh")
            
            return client_ids
            
        except Exception as e:
            logger.error(f"Failed to get active clients: {e}")
            return []
    
    async def generate_client_token(self, client_id: str) -> Optional[str]:
        """Generate a temporary token for API calls"""
        try:
            # Import JWT functions
            from datetime import timedelta
            import jwt
            from datetime import datetime
            
            # JWT configuration (same as in app.py)
            JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key")
            JWT_ALGORITHM = "HS256"
            
            # Create token data
            to_encode = {
                "client_id": client_id,
                "email": f"system@{client_id}",  # System email
                "role": "client"
            }
            
            # Set expiration to 1 hour
            expire = datetime.utcnow() + timedelta(hours=1)
            to_encode.update({"exp": expire})
            
            # Create the token
            token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
            
            logger.info(f"Generated temporary token for client {client_id}")
            return token
                
        except Exception as e:
            logger.error(f"Token generation failed for {client_id}: {e}")
            return None
    
    async def refresh_analytics_for_client(self, client_id: str, platform: str) -> Dict[str, Any]:
        """Refresh analytics for a specific client and platform"""
        try:
            logger.info(f"🔄 DIRECT REFRESH: analytics for client {client_id} (platform: {platform})")
            
            # Generate token for this client
            token = await self.generate_client_token(client_id)
            if not token:
                return {"success": False, "error": "Failed to generate client token"}
            
            # Call the inventory-analytics endpoint with force_refresh
            url = f"{self.base_url}/api/dashboard/inventory-analytics"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            params = {
                "platform": platform,
                "force_refresh": "true",  # Force fresh calculation
                "fast_mode": "true"       # Use optimized processing
            }
            
            if self.use_direct_calls:
                # Use DIRECT CALLS instead of HTTP - fixes deployment connection issues
                logger.info(f"🔧 DIRECT: Calling get_inventory_analytics for {client_id} ({platform})")
                
                # Import the inventory analytics function directly from app.py
                import sys
                import os
                
                # Add backend to path if needed
                if '/opt/render/project/src/backend' not in sys.path:
                    sys.path.append('/opt/render/project/src/backend')
                if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                
                # Import required modules
                from fastapi import BackgroundTasks
                from fastapi.security import HTTPBearer
                
                # Create a mock HTTPBearer token
                class MockHTTPAuthorizationCredentials:
                    def __init__(self, token):
                        self.scheme = "Bearer"
                        self.credentials = token
                
                mock_token = MockHTTPAuthorizationCredentials(token)
                background_tasks = BackgroundTasks()
                
                # Import the function from app.py
                from app import get_inventory_analytics
                
                # Call the inventory analytics function directly
                result = await get_inventory_analytics(
                    token=mock_token,
                    fast_mode=True,
                    force_refresh=True,
                    platform=platform,
                    start_date=None,
                    end_date=None,
                    background_tasks=background_tasks
                )
                
                if result and result.get("success"):
                    analytics_data = result.get("inventory_analytics", {})
                    platforms_count = len(analytics_data.get("platforms", {}))
                    total_skus = len(analytics_data.get("sku_inventory", {}).get("skus", []))
                    
                    logger.info(f"✅ DIRECT SUCCESS - {client_id} ({platform}): {platforms_count} platforms, {total_skus} SKUs (via get_inventory_analytics)")
                    
                    return {
                        "success": True,
                        "client_id": client_id,
                        "platform": platform,
                        "platforms_analyzed": platforms_count,
                        "skus_found": total_skus,
                        "direct_call": True,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"⚠️ DIRECT PARTIAL - {client_id} ({platform}): get_inventory_analytics returned no data")
                    return {"success": False, "error": "No analytics data from direct call"}
            
            else:
                # Fallback HTTP method
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.info(f"📡 HTTP FALLBACK: Calling {url} for {client_id} ({platform})")
                    response = await client.get(url, headers=headers, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get("success") and data.get("inventory_analytics"):
                            analytics_data = data["inventory_analytics"]
                            platforms_count = len(analytics_data.get("platforms", {}))
                            total_skus = len(analytics_data.get("sku_inventory", {}).get("skus", []))
                            
                            logger.info(f"✅ HTTP SUCCESS - {client_id} ({platform}): {platforms_count} platforms, {total_skus} SKUs")
                            
                            return {
                                "success": True,
                                "client_id": client_id,
                                "platform": platform,
                                "platforms_analyzed": platforms_count,
                                "skus_found": total_skus,
                                "endpoint_cached": True,
                                "timestamp": datetime.now().isoformat()
                            }
                        else:
                            error_msg = data.get("error", "No analytics data returned")
                            logger.error(f"❌ HTTP Invalid response for {client_id} ({platform}): {error_msg}")
                            return {"success": False, "error": error_msg}
                    
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.text}"
                        logger.error(f"❌ HTTP call failed for {client_id} ({platform}): {error_msg}")
                        return {"success": False, "error": error_msg}
                    
        except Exception as e:
            logger.error(f"❌ DIRECT CALL ERROR for {client_id} ({platform}): {e}")
            return {"success": False, "error": f"Direct call failed: {str(e)}"}
    
    # REMOVED: cache_analytics_response() method - endpoint handles all caching
    
    async def run_full_analytics_refresh(self) -> Dict[str, Any]:
        """Run full analytics refresh for all active clients and platforms"""
        start_time = datetime.now()
        logger.info("🚀 Starting analytics refresh cron job - DIRECT CALLS (no HTTP failures)")
        
        results = {
            "success": True,
            "timestamp": start_time.isoformat(),
            "total_jobs": 0,
            "successful_refreshes": 0,
            "failed_refreshes": 0,
            "client_results": {},
            "duration_seconds": 0
        }
        
        try:
            # Get all active clients
            active_clients = await self.get_active_clients()
            
            if not active_clients:
                logger.info("ℹ️ No active clients found for analytics refresh")
                results["total_jobs"] = 0
                results["duration_seconds"] = (datetime.now() - start_time).total_seconds()
                return results
            
            # Calculate total jobs (clients × platforms)
            results["total_jobs"] = len(active_clients) * len(self.platforms)
            logger.info(f"📋 Processing {len(active_clients)} clients × {len(self.platforms)} platforms = {results['total_jobs']} refresh jobs")
            
            # Process each client and platform combination
            for client_id in active_clients:
                client_results = {}
                
                for platform in self.platforms:
                    try:
                        result = await self.refresh_analytics_for_client(client_id, platform)
                        client_results[platform] = result
                        
                        if result.get("success"):
                            results["successful_refreshes"] += 1
                        else:
                            results["failed_refreshes"] += 1
                            logger.warning(f"⚠️ FAILED - {client_id} ({platform}): {result.get('error')}")
                            
                    except Exception as e:
                        logger.error(f"❌ Exception processing {client_id} ({platform}): {e}")
                        client_results[platform] = {"success": False, "error": str(e)}
                        results["failed_refreshes"] += 1
                
                results["client_results"][client_id] = client_results
            
            # Calculate final results
            duration = (datetime.now() - start_time).total_seconds()
            results["duration_seconds"] = duration
            
            logger.info(f"🏁 Analytics refresh cron job completed in {duration:.2f} seconds")
            logger.info(f"✅ Results: {results['successful_refreshes']} successful, {results['failed_refreshes']} failed out of {results['total_jobs']} total jobs")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Fatal error in analytics refresh cron job: {e}")
            results["success"] = False
            results["error"] = str(e)
            results["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            return results

# Global instance
analytics_refresh_cron = AnalyticsRefreshCronJob()

if __name__ == "__main__":
    async def main():
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        logger.info("=" * 80)
        logger.info("STARTING ANALYTICS REFRESH CRON JOB - TESTING MODE (5 minutes)")
        logger.info("=" * 80)
        
        results = await analytics_refresh_cron.run_full_analytics_refresh()
        
        logger.info("=" * 80)
        logger.info("FINAL RESULTS:")
        logger.info(f"Successful refreshes: {results.get('successful_refreshes', 0)}")
        logger.info(f"Failed refreshes: {results.get('failed_refreshes', 0)}")
        logger.info(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")
        logger.info("=" * 80)
    
    asyncio.run(main())
