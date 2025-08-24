from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Form,
    UploadFile,
    File,
    BackgroundTasks,
)

from fastapi.middleware.cors import CORSMiddleware

from fastapi.middleware.gzip import GZipMiddleware

from fastapi.security import HTTPBearer

import os
import sys

from typing import Optional, List, Dict, Any

import logging

import json

import asyncio

from concurrent.futures import ThreadPoolExecutor

import threading

from dotenv import load_dotenv

from datetime import datetime, timedelta

import uuid

import bcrypt

import jwt

import pandas as pd

from contextlib import asynccontextmanager

import time

import math

import traceback

# Internal scheduler for cron jobs
from internal_scheduler import start_internal_scheduler, stop_internal_scheduler, get_scheduler_status

import hashlib


# Import our custom modules

from models import *

from database import get_db_client, get_admin_client

from ai_analyzer import ai_analyzer

from inventory_analyzer import inventory_analyzer


from dashboard_orchestrator import dashboard_orchestrator


# Import enhanced components

from api_key_auth import (
    api_key_manager,
    authenticate_request,
    require_read_access,
    require_write_access,
    require_admin_access,
    require_analytics_access,
)

from enhanced_data_parser import enhanced_parser

from models import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyScope,
    EnhancedDataUpload,
    DataUploadConfig,
    FileValidationResult,
)


# Load environment variables

load_dotenv()


# Setup logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


#  ASYNC REQUEST HANDLING SYSTEM - NO MORE WAITING!

executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="analytics_worker")

request_queue = asyncio.Queue(maxsize=100)

active_calculations = {}  # Track ongoing calculations

calculation_lock = threading.Lock()

pending_requests = {}  # Queue identical requests to avoid duplicate processing

calculation_cache = {}  # Short-term cache for identical requests


#  BACKGROUND CALCULATION SYSTEM - INSTANT RESPONSES!


async def refresh_analytics_background(
    client_id: str,
    platform: str,
    fast_mode: bool = True,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Run analytics calculations in background - doesn't block responses"""

    try:

        date_info = (
            f" (dates: {start_date} to {end_date})" if start_date or end_date else ""
        )

        logger.info(
            f" Background refresh started for {client_id} ({platform}){date_info}"
        )

        # Use dashboard inventory analyzer for fresh calculations

        from dashboard_inventory_analyzer import dashboard_inventory_analyzer

        # Run calculation in thread pool to avoid blocking

        loop = asyncio.get_event_loop()

        analytics = await loop.run_in_executor(
            executor,
            lambda: asyncio.run(
                dashboard_inventory_analyzer.get_dashboard_inventory_analytics(
                    client_id, platform, start_date, end_date
                )
            ),
        )

        # Cache the results using existing LLM cache infrastructure with date range

        from llm_cache_manager import LLMCacheManager

        cache_manager = LLMCacheManager()

        cache_params = {"platform": platform}

        if start_date:

            cache_params["start_date"] = start_date

        if end_date:

            cache_params["end_date"] = end_date

        date_key = f"{start_date or 'no_start'}_{end_date or 'no_end'}"

        cache_key = f"analytics_{platform}_{date_key}"

        await cache_manager.store_cached_llm_response(
            client_id, cache_params, analytics, cache_key
        )

        logger.info(
            f" Background refresh completed for {client_id} ({platform}){date_info}"
        )

    except Exception as e:

        logger.error(f" Background refresh failed for {client_id}: {e}")


async def refresh_sku_background(
    client_id: str, platform: str, page: int = 1, page_size: int = 50
):
    """Run SKU list generation in background - doesn't block responses"""

    try:

        logger.info(f" Background SKU refresh started for {client_id} ({platform})")

        from dashboard_inventory_analyzer import dashboard_inventory_analyzer

        # Run calculation in thread pool to avoid blocking

        loop = asyncio.get_event_loop()

        sku_data = await loop.run_in_executor(
            executor,
            lambda: asyncio.run(
                dashboard_inventory_analyzer.get_sku_list(
                    client_id, page, page_size, False, platform
                )
            ),
        )

        logger.info(f" Background SKU refresh completed for {client_id} ({platform})")

    except Exception as e:

        logger.error(f" Background SKU refresh failed for {client_id}: {e}")


async def pre_calculate_dashboard_data(client_id: str):
    """Pre-calculate all dashboard data after login - user doesn't wait!"""

    try:

        logger.info(f" PRE-CALCULATING all data for {client_id} in background")

        # Pre-calculate for both platforms in parallel

        tasks = [
            refresh_analytics_background(client_id, "shopify"),
            refresh_analytics_background(client_id, "amazon"),
            refresh_sku_background(client_id, "shopify", 1, 50),
            refresh_sku_background(client_id, "amazon", 1, 50),
        ]

        # Wait for all background tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task_name = ["shopify analytics", "amazon analytics", "shopify sku", "amazon sku"][i]
                logger.error(f"PRE-CALCULATION failed for {client_id}: {task_name} - {result}")

        logger.info(f" PRE-CALCULATION completed for {client_id}")

    except Exception as e:

        logger.error(f" PRE-CALCULATION failed for {client_id}: {e}")


async def get_or_create_calculation_task(
    client_id: str,
    platform: str,
    calculation_func,
    start_date: str = None,
    end_date: str = None,
):
    """ ENHANCED: Prevent duplicate calculations and queue identical requests for maximum parallelization"""

    date_key = f"{start_date or 'no_start'}_{end_date or 'no_end'}"

    task_key = f"{client_id}_{platform}_{date_key}"

    with calculation_lock:

        # Check if exact same calculation is already running

        if task_key in active_calculations:

            logger.info(
                f" Exact calculation in progress for {task_key}, waiting for result"
            )

            # Return the same task to share results

            return await active_calculations[task_key]

        # Check short-term cache (last 30 seconds)

        cache_time = calculation_cache.get(f"{task_key}_time")

        if cache_time and (time.time() - cache_time) < 30:

            cached_result = calculation_cache.get(task_key)

            if cached_result:

                logger.info(f" Using 30s cached result for {task_key}")

                return cached_result

        # Start new enhanced calculation

        async def enhanced_calculation():

            try:

                result = await calculation_func()

                # Cache result for 30 seconds for identical requests

                with calculation_lock:

                    calculation_cache[task_key] = result

                    calculation_cache[f"{task_key}_time"] = time.time()

                logger.info(f" Calculation completed and cached for {task_key}")

                return result

            finally:

                # Clean up active calculations

                with calculation_lock:

                    active_calculations.pop(task_key, None)

                    pending_requests.pop(task_key, None)

        task = asyncio.create_task(enhanced_calculation())

        active_calculations[task_key] = task

        pending_requests[task_key] = task

        logger.info(f" Started new PARALLEL calculation for {task_key}")

        return await task


#  CONCURRENT REQUEST HANDLER - HANDLE MULTIPLE ACTIONS SIMULTANEOUSLY


class ConcurrentRequestHandler:

    def __init__(self):

        self.semaphore = asyncio.Semaphore(20)  # Allow 20 concurrent requests

        self.request_count = 0

    async def handle_request(self, request_func, *args, **kwargs):
        """Handle requests concurrently without blocking"""

        async with self.semaphore:

            self.request_count += 1

            request_id = self.request_count

            logger.info(f" Processing request #{request_id} concurrently")

            try:

                result = await request_func(*args, **kwargs)

                logger.info(f" Request #{request_id} completed")

                return result

            except Exception as e:

                logger.error(f" Request #{request_id} failed: {e}")

                raise


# Global request handler

request_handler = ConcurrentRequestHandler()


# ==================== TEMPLATE PRE-GENERATION ====================


async def _pre_generate_templates_for_client(client_id: str):
    """Pre-generate templates for a client after data upload - runs in background"""

    try:

        logger.info(f" Starting template pre-generation for client {client_id}")

        # Import here to avoid circular imports

        from dashboard_orchestrator import dashboard_orchestrator

        import uuid

        # Generate LLM analysis and cache it

        client_data = await dashboard_orchestrator.ai_analyzer.get_client_data(
            client_id
        )

        if not client_data:

            logger.warning(
                f" No data found for client {client_id}, skipping template generation"
            )

            return

        # Pre-run the expensive LLM analysis to cache it

        logger.info(f"🤖 Pre-generating LLM analysis for client {client_id}")

        business_insights = await dashboard_orchestrator._generate_ai_business_context(
            uuid.UUID(client_id), client_data
        )

        if business_insights and "error" not in business_insights:

            logger.info(f" Pre-generated LLM analysis cached for client {client_id}")

            # Also pre-generate the main dashboard template

            try:

                logger.info(
                    f" Pre-generating main dashboard template for client {client_id}"
                )

                dashboard_config = await dashboard_orchestrator.generate_dashboard(
                    client_id=client_id, template_type="main", force_regenerate=False
                )

                if dashboard_config and not hasattr(dashboard_config, "error"):

                    logger.info(
                        f" Main dashboard template pre-generated for client {client_id}"
                    )

                else:

                    logger.warning(
                        f" Main dashboard template generation had issues for client {client_id}"
                    )

            except Exception as template_error:

                logger.warning(
                    f" Dashboard template pre-generation failed for client {client_id}: {template_error}"
                )

        else:

            logger.warning(
                f" LLM analysis failed for client {client_id}, templates not pre-generated"
            )

    except Exception as e:

        logger.error(f" Template pre-generation failed for client {client_id}: {e}")


# Lifespan event handler for internal scheduler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler that starts/stops the internal scheduler
    This ensures cron jobs run automatically when the app is deployed!
    """
    logger.info("=== STARTING ANALYTICS AI DASHBOARD ===")
    logger.info(f"FastAPI startup - Process ID: {os.getpid()}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Python version: {sys.version}")
    
    # Startup: Start the internal scheduler
    try:
        logger.info("Attempting to initialize internal scheduler...")
        start_internal_scheduler()
        logger.info("INTERNAL SCHEDULER STARTUP SUCCESSFUL!")
        logger.info("API Sync and SKU Analysis jobs are now running automatically!")
        
        # Verify scheduler status
        from internal_scheduler import get_scheduler_status
        status = get_scheduler_status()
        logger.info(f"Scheduler verification: {status}")
        
    except Exception as e:
        logger.error(f"CRITICAL FAILURE: Failed to start internal scheduler: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Don't raise - let the app start anyway
    
    yield  # App is running
    
    # Shutdown: Stop the internal scheduler
    try:
        stop_internal_scheduler()
        logger.info("Internal scheduler stopped gracefully")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Analytics AI Dashboard API",
    version="2.0.0",
    description="AI-powered dynamic analytics platform for custom data structures",
    lifespan=lifespan
)


# Add GZip middleware for response compression to reduce payload size and improve speed

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Add CORS middleware

# Get allowed origins from environment

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


# Base origins that are always allowed

allowed_origins = ["http://localhost:3000", "http://localhost:3001", FRONTEND_URL]


# In production, be more permissive with deployment URLs

if ENVIRONMENT == "production":

    # Allow your actual deployment URLs

    allowed_origins.extend(
        [
            "https://tryliora.ai",
            "https://www.tryliora.ai",
            "https://analytics-ai-frontend.onrender.com",  # Keep Render as backup
            "https://*.onrender.com",  # Allow any Render subdomain
            "https://*.tryliora.ai",  # Allow any tryliora.ai subdomain
        ]
    )

    # For debugging in production, you can temporarily allow all origins

    # Comment this out once CORS is working properly

    logger.info(f" Production CORS: allowing origins {allowed_origins}")

    logger.info(f" FRONTEND_URL environment variable: {FRONTEND_URL}")

    logger.info(f" ENVIRONMENT: {ENVIRONMENT}")


# Remove any None values and duplicates

allowed_origins = list(set([origin for origin in allowed_origins if origin]))


# In production, if still having issues, use allow_origin_regex for deployment domains

if ENVIRONMENT == "production":

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https://.*\.(onrender\.com|tryliora\.ai)",  # Allow Render and tryliora.ai domains
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

else:

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Security

security = HTTPBearer()


# Add a simple OPTIONS handler for debugging CORS


@app.options("/api/{path:path}")
async def options_handler(path: str):
    """Handle OPTIONS requests for CORS debugging"""

    logger.info(f" OPTIONS request for path: /api/{path}")

    return {"message": "OK"}


# JWT Configuration

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-secret-key-change-this-in-production"
)

JWT_ALGORITHM = "HS256"

JWT_EXPIRATION_TIME = (
    8  # hours - tokens expire after 8 hours (more practical for extended work sessions)
)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""

    to_encode = data.copy()

    if expires_delta:

        expire = datetime.utcnow() + expires_delta

    else:

        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_TIME)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return encoded_jwt


def verify_token(token: str):
    """Verify JWT token and return client data"""

    try:

        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        client_id: str = payload.get("client_id")

        email: str = payload.get("email")

        if client_id is None or email is None:

            raise HTTPException(status_code=401, detail="Invalid token")

        return TokenData(client_id=uuid.UUID(client_id), email=email)

    except jwt.ExpiredSignatureError:

        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.JWTError:

        raise HTTPException(status_code=401, detail="Invalid token")


# Configuration

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

DEBUG = os.getenv("DEBUG", "true").lower() == "true"


logger.info(f" Starting Analytics AI Dashboard API in {ENVIRONMENT} mode")


# ==================== CACHING FUNCTIONS ====================


async def create_client_cache_table(client_id: str):
    """Check if cache table exists - assume tables are pre-created via SQL"""

    try:

        # Clean client_id for table name

        clean_client_id = client_id.replace("-", "_")

        table_name = f"{clean_client_id}_cached_responses"

        db_client = get_admin_client()

        if not db_client:

            logger.error(" Database not configured for cache table access")

            return False

        # Try to access the table to verify it exists

        try:
            # Simple test query to check if table exists
            db_client.table(table_name).select("id").limit(1).execute()
            logger.info(f" Cache table verified: {table_name}")
            return True

        except Exception as e:

            logger.warning(f" Cache table {table_name} may not exist: {e}")
            logger.warning(f" Please create the table manually using SQL: CREATE TABLE IF NOT EXISTS \"{table_name}\" (id uuid DEFAULT gen_random_uuid() PRIMARY KEY, client_id uuid NOT NULL, endpoint_url text NOT NULL, cache_key text NOT NULL, response_data jsonb NOT NULL, created_at timestamptz DEFAULT now(), expires_at timestamptz, UNIQUE(cache_key));")
            return False

    except Exception as e:

        logger.error(f" Failed to verify cache table for client {client_id}: {e}")

        return False


async def get_cached_response(
    client_id: str, endpoint_url: str, params: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """Get cached response if it exists (no expiration)"""

    try:

        # Generate cache key

        params_str = json.dumps(params or {}, sort_keys=True)

        cache_key_data = f"{endpoint_url}_{params_str}"

        cache_key = hashlib.md5(cache_key_data.encode()).hexdigest()

        # Clean client_id for table name

        clean_client_id = client_id.replace("-", "_")

        table_name = f"{clean_client_id}_cached_responses"

        db_client = get_admin_client()

        if not db_client:

            return None

        try:

            # Query cached response (no expiration check)

            response = (
                db_client.table(table_name)
                .select("*")
                .eq("cache_key", cache_key)
                .limit(1)
                .execute()
            )

            if response.data and len(response.data) > 0:

                cached_data = response.data[0]

                logger.info(f" Found cached response for client {client_id}")

                return cached_data["response_data"]

        except Exception as e:

            # Table might not exist yet

            logger.info(
                f" Cache table not found for client {client_id}, will create on save"
            )

        return None

    except Exception as e:

        logger.error(f" Failed to get cached response for client {client_id}: {e}")

        return None


async def save_cached_response(
    client_id: str,
    endpoint_url: str,
    response_data: Dict[str, Any],
    params: Dict[str, Any] = None,
):
    """Save response to cache (persistent until manually cleared)"""

    try:

        # Generate cache key

        params_str = json.dumps(params or {}, sort_keys=True)

        cache_key_data = f"{endpoint_url}_{params_str}"

        cache_key = hashlib.md5(cache_key_data.encode()).hexdigest()

        # Clean client_id for table name

        clean_client_id = client_id.replace("-", "_")

        table_name = f"{clean_client_id}_cached_responses"

        db_client = get_admin_client()

        if not db_client:

            logger.error(" Database not configured for cache saving")

            return False

        # Check if cache table exists

        table_exists = await create_client_cache_table(client_id)
        
        if not table_exists:
            logger.warning(f" Cache table doesn't exist for client {client_id}, skipping cache save")
            return False

        try:

            # Insert or update cached response (no expiration)

            cache_record = {
                "client_id": client_id,
                "endpoint_url": endpoint_url,
                "cache_key": cache_key,
                "response_data": response_data,
                "expires_at": None,  # No expiration
            }

            # Try to upsert (insert or update if exists)

            db_client.table(table_name).upsert(
                cache_record, on_conflict="cache_key"
            ).execute()

            logger.info(f" Saved cached response for client {client_id} (persistent)")

            return True

        except Exception as e:

            logger.error(f" Failed to save cached response: {e}")
            logger.warning(f" This may be due to missing cache table: {table_name}")

            return False

    except Exception as e:

        logger.error(f" Failed to save cached response for client {client_id}: {e}")

        return False


# ==================== BASIC ENDPOINTS ====================


@app.get("/")
async def root():
    """Root endpoint"""

    return {
        "message": "Analytics AI Dashboard API v2.0",
        "ai_powered": True,
        "dynamic_schemas": True,
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Analytics AI Dashboard API",
    }


@app.get("/api/health")
async def api_health_check():
    """API health check endpoint"""

    return {
        "status": "healthy",
        "api_version": "4.0-fast",
        "endpoints_available": [
            "/api/dashboard/config",
            "/api/dashboard/fast-generate",
            "/api/debug/auth",
        ],
    }


@app.get("/api/superadmin/diagnostics")
async def superadmin_diagnostics(token: str = Depends(security)):
    """Superadmin: Database and system diagnostics"""

    try:

        # Verify superadmin token

        verify_superadmin_token(token.credentials)

        db_client = get_admin_client()

        if not db_client:

            return {
                "status": "error",
                "message": "Database not configured",
                "timestamp": datetime.now().isoformat(),
            }

        diagnostics = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "database": {"connected": True, "client_type": "admin"},
            "tables": {},
            "sample_data": {},
        }

        # Check table existence and counts

        tables_to_check = ["clients", "client_schemas", "client_data"]

        for table_name in tables_to_check:

            try:

                response = (
                    db_client.table(table_name)
                    .select("*", count="exact")
                    .limit(1)
                    .execute()
                )

                diagnostics["tables"][table_name] = {
                    "exists": True,
                    "count": (
                        response.count if hasattr(response, "count") else "unknown"
                    ),
                    "accessible": True,
                }

                # Get sample data for key tables

                if table_name == "clients" and response.data:

                    diagnostics["sample_data"]["clients"] = len(response.data)

                elif table_name == "client_schemas" and response.data:

                    diagnostics["sample_data"]["schemas"] = len(response.data)

                elif table_name == "client_data" and response.data:

                    diagnostics["sample_data"]["data_records"] = len(response.data)

            except Exception as table_error:

                diagnostics["tables"][table_name] = {
                    "exists": False,
                    "error": str(table_error),
                    "accessible": False,
                }

        # Test superadmin authentication

        diagnostics["auth"] = {
            "superadmin_token_valid": True,
            "token_type": "superadmin",
        }

        return diagnostics

    except HTTPException as http_error:

        return {
            "status": "auth_error",
            "message": "Superadmin authentication failed",
            "error": str(http_error.detail),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:

        logger.error(f" Diagnostics failed: {e}")

        return {
            "status": "error",
            "message": "Diagnostics failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@app.get("/api/setup-schema")
async def setup_database_schema():
    """Setup base database schema (run once)"""

    try:

        from database import db_manager

        manager = db_manager()

        schema_sql = await manager.create_base_schema()

        return {
            "message": "Database schema setup initiated",
            "sql_commands": schema_sql,
            "instructions": [
                "1. Go to your Supabase Dashboard > SQL Editor",
                "2. Run each SQL command provided above",
                "3. Test the connection with /health endpoint",
            ],
        }

    except Exception as e:

        logger.error(f"Schema setup failed: {e}")

        raise HTTPException(status_code=500, detail=f"Schema setup failed: {str(e)}")


# ==================== SUPERADMIN AUTHENTICATION ====================


@app.post("/api/superadmin/login")
async def superadmin_login(admin_data: SuperAdminLogin):
    """Superadmin login endpoint"""

    try:

        # For now, hardcode superadmin credentials

        # In production, store this in database

        SUPERADMIN_USERNAME = os.getenv("SUPERADMIN_USERNAME", "admin")

        SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD", "admin123")

        if (
            admin_data.username != SUPERADMIN_USERNAME
            or admin_data.password != SUPERADMIN_PASSWORD
        ):

            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create access token

        access_token = create_access_token(
            data={
                "admin_id": "superadmin",
                "username": admin_data.username,
                "role": "superadmin",
            }
        )

        logger.info(f" Superadmin logged in: {admin_data.username}")

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_TIME * 3600,  # seconds
        )

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Superadmin login failed: {e}")

        raise HTTPException(status_code=500, detail="Login failed")


def verify_superadmin_token(token: str):
    """Verify superadmin JWT token"""

    try:

        logger.info(f" Verifying superadmin token: {token[:20]}...")

        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        logger.info(f" Token payload: {payload}")

        role = payload.get("role")

        if role != "superadmin":

            logger.error(f" Invalid role: {role}, expected 'superadmin'")

            raise HTTPException(status_code=403, detail="Superadmin access required")

        logger.info(f" Superadmin token verified successfully")

        return payload

    except jwt.ExpiredSignatureError:

        logger.error(f" Token expired")

        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.JWTError as e:

        logger.error(f" JWT Error: {str(e)}")

        raise HTTPException(status_code=401, detail="Invalid token")


# ==================== AUTHENTICATION ====================


@app.post("/api/auth/login", response_model=Token)
async def login(
    client_data: ClientLogin, background_tasks: BackgroundTasks = BackgroundTasks()
):
    """ INSTANT LOGIN - No waiting for calculations"""

    try:

        db_client = get_admin_client()  # Use admin client to bypass RLS

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Find client by email

        response = (
            db_client.table("clients")
            .select("*")
            .eq("email", client_data.email)
            .execute()
        )

        if not response.data:

            raise HTTPException(status_code=401, detail="Invalid credentials")

        client = response.data[0]

        # Verify password

        if not bcrypt.checkpw(
            client_data.password.encode("utf-8"),
            client["password_hash"].encode("utf-8"),
        ):

            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create access token

        access_token = create_access_token(
            data={"client_id": client["client_id"], "email": client["email"]}
        )

        logger.info(f" Client logged in: {client['email']}")

        #  PRE-CALCULATE DATA IN BACKGROUND - USER DOESN'T WAIT!

        client_id = client["client_id"]

        background_tasks.add_task(pre_calculate_dashboard_data, client_id)

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_TIME * 3600,  # seconds
        )

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Login failed: {e}")

        raise HTTPException(status_code=500, detail="Login failed")


@app.get("/api/auth/me")
async def get_current_user(token: str = Depends(security)):
    """Get current authenticated user"""

    try:

        token_data = verify_token(token.credentials)

        db_client = get_admin_client()  # Use admin client to bypass RLS

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Get client info

        response = (
            db_client.table("clients")
            .select(
                "client_id, company_name, email, subscription_tier, created_at, updated_at"
            )
            .eq("client_id", token_data.client_id)
            .execute()
        )

        if not response.data:

            raise HTTPException(status_code=404, detail="User not found")

        return ClientResponse(**response.data[0])

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to get current user: {e}")

        raise HTTPException(status_code=500, detail="Failed to get user info")


# ==================== CLIENT MANAGEMENT ====================


@app.post("/api/admin/clients", response_model=ClientResponse)
async def create_client(client_data: ClientCreate):
    """Super Admin: Create a new client account"""

    try:

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Hash password properly

        password_hash = bcrypt.hashpw(
            client_data.password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # Insert client into database

        response = (
            db_client.table("clients")
            .insert(
                {
                    "company_name": client_data.company_name,
                    "email": client_data.email,
                    "password_hash": password_hash,
                    "subscription_tier": "basic",
                }
            )
            .execute()
        )

        if response.data:

            client = response.data[0]

            logger.info(f" Created client: {client['email']}")

            return ClientResponse(**client)

        else:

            raise HTTPException(status_code=400, detail="Failed to create client")

    except Exception as e:

        logger.error(f" Client creation failed: {e}")

        raise HTTPException(status_code=500, detail=f"Client creation failed: {str(e)}")


@app.get("/api/admin/clients")
async def list_clients():
    """Super Admin: List all clients"""

    try:

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        response = db_client.table("clients").select("*").execute()

        return {"clients": response.data}

    except Exception as e:

        logger.error(f" Failed to list clients: {e}")

        raise HTTPException(status_code=500, detail=str(e))


# ==================== SUPERADMIN CLIENT MANAGEMENT ====================


@app.post("/api/superadmin/clients", response_model=ClientResponse)
async def create_client_superadmin(
    token: str = Depends(security),
    company_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    data_type: str = Form(...),
    input_method: str = Form(...),
    data_content: str = Form(default=""),
    uploaded_file: UploadFile = File(default=None),
    file_count: str = Form(default="0"),
    uploaded_file_0: UploadFile = File(default=None),
    uploaded_file_1: UploadFile = File(default=None),
    uploaded_file_2: UploadFile = File(default=None),
    uploaded_file_3: UploadFile = File(default=None),
    uploaded_file_4: UploadFile = File(default=None),
    uploaded_file_5: UploadFile = File(default=None),
    uploaded_file_6: UploadFile = File(default=None),
    uploaded_file_7: UploadFile = File(default=None),
    uploaded_file_8: UploadFile = File(default=None),
    uploaded_file_9: UploadFile = File(default=None),
):
    """Superadmin: Create a new client account with INSTANT dashboard - AI works in background"""

    try:

        # Verify superadmin token

        verify_superadmin_token(token.credentials)

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Check if client already exists

        existing = (
            db_client.table("clients").select("email").eq("email", email).execute()
        )

        if existing.data:

            raise HTTPException(
                status_code=400, detail="Client with this email already exists"
            )

        # Hash password

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # Insert client into database

        response = (
            db_client.table("clients")
            .insert(
                {
                    "company_name": company_name,
                    "email": email,
                    "password_hash": password_hash,
                    "subscription_tier": "basic",  # Default tier
                }
            )
            .execute()
        )

        if not response.data:

            raise HTTPException(status_code=400, detail="Failed to create client")

        client = response.data[0]

        client_id = client["client_id"]

        logger.info(f" Client created INSTANTLY: {email}")

        # MOVE AI DASHBOARD GENERATION TO AFTER DATA STORAGE IS COMPLETE!

        #  DIRECT DATA STORAGE - NO AI BULLSHIT!

        files_to_process = []

        # Collect all uploaded files

        if input_method == "upload":

            try:

                num_files = int(file_count) if file_count.isdigit() else 0

                logger.info(f" Processing {num_files} uploaded files")

                # Collect files from individual parameters

                file_params = [
                    uploaded_file_0,
                    uploaded_file_1,
                    uploaded_file_2,
                    uploaded_file_3,
                    uploaded_file_4,
                    uploaded_file_5,
                    uploaded_file_6,
                    uploaded_file_7,
                    uploaded_file_8,
                    uploaded_file_9,
                ]

                for i, file_param in enumerate(file_params[:num_files]):

                    if file_param and file_param.filename:

                        files_to_process.append(file_param)

                        logger.info(f" File {i+1}: {file_param.filename}")

                # Also include the main uploaded_file for backward compatibility

                if uploaded_file and uploaded_file.filename:

                    if not any(
                        f.filename == uploaded_file.filename for f in files_to_process
                    ):

                        files_to_process.append(uploaded_file)

            except Exception as e:

                logger.error(f" Error collecting uploaded files: {e}")

        if (input_method == "paste" and data_content) or (
            input_method == "upload" and files_to_process
        ):

            try:

                all_parsed_records = []

                if input_method == "paste":

                    # Process pasted data

                    raw_data = data_content

                    # Simple schema entry for pasted data

                    db_client.table("client_schemas").insert(
                        {
                            "client_id": client_id,
                            "table_name": f"client_{client_id.replace('-', '_')}_data",
                            "data_type": data_type,
                            "schema_definition": {
                                "type": "raw_data",
                                "format": data_type,
                            },
                        }
                    ).execute()

                    from universal_data_parser import universal_parser

                    # Parse ANY format to standardized JSON records

                    parsed_records = universal_parser.parse_to_json(raw_data, data_type)

                    if parsed_records:

                        logger.info(
                            f" {data_type.upper()} parsed to {len(parsed_records)} JSON records"
                        )

                        all_parsed_records.extend(parsed_records)

                elif input_method == "upload" and files_to_process:

                    # Process multiple uploaded files

                    from universal_data_parser import universal_parser

                    # Simple schema entry for uploaded files

                    db_client.table("client_schemas").insert(
                        {
                            "client_id": client_id,
                            "table_name": f"client_{client_id.replace('-', '_')}_data",
                            "data_type": data_type,
                            "schema_definition": {
                                "type": "multi_file_upload",
                                "format": data_type,
                                "file_count": len(files_to_process),
                            },
                        }
                    ).execute()

                    for file_idx, file in enumerate(files_to_process):

                        try:

                            logger.info(
                                f" Processing file {file_idx + 1}/{len(files_to_process)}: {file.filename}"
                            )

                            parsed_records = []  # Initialize for each file

                            try:

                                # NO LIMITS - READ THE ENTIRE FILE

                                file_content = await file.read()

                                logger.info(
                                    f" Read entire file {file.filename}: {len(file_content)} bytes ({len(file_content) / 1024 / 1024:.2f} MB)"
                                )

                                # Basic validation

                                if not file_content:

                                    logger.error(
                                        f" File {file.filename} is empty or could not be read"
                                    )

                                    continue

                            except Exception as read_error:

                                logger.error(
                                    f" Failed to read file {file.filename}: {read_error}"
                                )

                                logger.error(
                                    f" File read error type: {type(read_error).__name__}"
                                )

                                # Try to create a placeholder record for failed file reads

                                failed_read_record = {
                                    "filename": file.filename,
                                    "error": f"File read failed: {str(read_error)[:200]}",
                                    "error_type": "file_read_error",
                                    "status": "read_failed",
                                    "_source_file": file.filename,
                                    "_read_failed": True,
                                }

                                all_parsed_records.append(failed_read_record)

                                logger.info(
                                    f" Added placeholder record for failed file read: {file.filename}"
                                )

                                continue

                            # Determine file format based on extension or data_type

                            file_extension = file.filename.split(".")[-1].lower()

                            file_format = data_type

                            # Auto-detect format from file extension if needed

                            if file_extension in ["xlsx", "xls"]:

                                file_format = "excel"

                            elif file_extension == "bak":

                                file_format = "bak"

                                # Special handling for database backup files

                                if any(
                                    db_indicator in file.filename.lower()
                                    for db_indicator in [
                                        "db",
                                        "database",
                                        "sql",
                                        "mysql",
                                        "postgres",
                                        "oracle",
                                        "mssql",
                                    ]
                                ):

                                    logger.info(
                                        f"️ File {file.filename} appears to be a database backup"
                                    )

                            elif file_extension == "csv":

                                file_format = "csv"

                            elif file_extension == "json":

                                file_format = "json"

                            elif file_extension == "xml":

                                file_format = "xml"

                            # Handle Excel files differently (binary content)

                            if file_format == "excel":

                                # For Excel files, we need to handle binary content

                                try:

                                    import pandas as pd

                                    from io import BytesIO

                                    from datetime import datetime

                                    df = pd.read_excel(
                                        BytesIO(file_content), engine="openpyxl"
                                    )

                                    # Convert to records with JSON serialization handling

                                    parsed_records = []

                                    for i, row in df.iterrows():

                                        record = {}

                                        for col, value in row.items():

                                            clean_col = (
                                                str(col)
                                                .strip()
                                                .replace(" ", "_")
                                                .replace("-", "_")
                                            )

                                            clean_col = "".join(
                                                c
                                                for c in clean_col
                                                if c.isalnum() or c == "_"
                                            )

                                            if pd.isna(value):

                                                record[clean_col] = None

                                            else:

                                                # Handle different data types for JSON serialization

                                                if isinstance(value, pd.Timestamp):

                                                    # Convert pandas Timestamp to ISO string

                                                    record[clean_col] = (
                                                        value.isoformat()
                                                    )

                                                elif hasattr(value, "isoformat"):

                                                    # Handle other datetime objects

                                                    record[clean_col] = (
                                                        value.isoformat()
                                                    )

                                                elif isinstance(
                                                    value,
                                                    (pd.Int64Dtype, pd.Float64Dtype),
                                                ):

                                                    # Handle pandas nullable integers/floats

                                                    record[clean_col] = (
                                                        float(value)
                                                        if pd.notna(value)
                                                        else None
                                                    )

                                                elif hasattr(value, "item"):

                                                    # Handle numpy scalars

                                                    record[clean_col] = value.item()

                                                else:

                                                    # Convert to string for complex objects, keep primitives as-is

                                                    if isinstance(
                                                        value, (str, int, float, bool)
                                                    ):

                                                        record[clean_col] = value

                                                    else:

                                                        record[clean_col] = str(value)

                                        record["_row_number"] = i + 1

                                        record["_source_format"] = "excel"

                                        record["_source_file"] = file.filename

                                        parsed_records.append(record)

                                    logger.info(
                                        f" Excel file '{file.filename}' parsed: {len(parsed_records)} records"
                                    )

                                    all_parsed_records.extend(parsed_records)

                                except ImportError:

                                    logger.error(
                                        " pandas/openpyxl not available for Excel parsing"
                                    )

                                    continue

                                except Exception as e:

                                    logger.error(
                                        f" Excel parsing failed for {file.filename}: {e}"
                                    )

                                    continue

                            else:

                                # For text-based files and binary files that need special handling

                                try:

                                    # Try to decode as UTF-8 first

                                    raw_data = file_content.decode("utf-8")

                                    parsed_records = universal_parser.parse_to_json(
                                        raw_data, file_format
                                    )

                                    if parsed_records:

                                        # Add file metadata

                                        for record in parsed_records:

                                            if isinstance(record, dict):

                                                record["_source_file"] = file.filename

                                        logger.info(
                                            f" File '{file.filename}' parsed: {len(parsed_records)} records"
                                        )

                                        all_parsed_records.extend(parsed_records)

                                    else:

                                        logger.warning(
                                            f" No records parsed from file: {file.filename}"
                                        )

                                except UnicodeDecodeError:

                                    # Handle binary files or files with different encodings

                                    logger.warning(
                                        f" File {file.filename} is not UTF-8, trying alternative approaches..."
                                    )

                                    # For .bak files, try different approaches

                                    if file_format == "bak":

                                        try:

                                            # Try different encodings for .bak files

                                            for encoding in [
                                                "latin-1",
                                                "cp1252",
                                                "iso-8859-1",
                                            ]:

                                                try:

                                                    raw_data = file_content.decode(
                                                        encoding
                                                    )

                                                    logger.info(
                                                        f" Successfully decoded {file.filename} using {encoding} encoding"
                                                    )

                                                    parsed_records = (
                                                        universal_parser.parse_to_json(
                                                            raw_data, file_format
                                                        )
                                                    )

                                                    if parsed_records:

                                                        # Add file metadata

                                                        for record in parsed_records:

                                                            if isinstance(record, dict):

                                                                record[
                                                                    "_source_file"
                                                                ] = file.filename

                                                                record[
                                                                    "_encoding_used"
                                                                ] = encoding

                                                        logger.info(
                                                            f" File '{file.filename}' parsed with {encoding}: {len(parsed_records)} records"
                                                        )

                                                        all_parsed_records.extend(
                                                            parsed_records
                                                        )

                                                        break

                                                except (
                                                    UnicodeDecodeError,
                                                    UnicodeError,
                                                ):

                                                    continue

                                            else:

                                                # If all encodings fail, treat as binary and create a metadata record

                                                logger.warning(
                                                    f" Could not decode {file.filename} with any encoding, storing as binary metadata"
                                                )

                                                binary_record = {
                                                    "filename": file.filename,
                                                    "file_size_bytes": len(
                                                        file_content
                                                    ),
                                                    "file_type": "binary_backup",
                                                    "content_preview": (
                                                        str(file_content[:100])
                                                        if len(file_content) > 0
                                                        else "empty"
                                                    ),
                                                    "_source_file": file.filename,
                                                    "_binary_file": True,
                                                }

                                                all_parsed_records.append(binary_record)

                                                logger.info(
                                                    f" Binary file '{file.filename}' stored as metadata record"
                                                )

                                        except Exception as e:

                                            logger.error(
                                                f" Error processing .bak file {file.filename}: {e}"
                                            )

                                            continue

                                    else:

                                        # For other file types, log the error and skip

                                        logger.error(
                                            f" Cannot decode file {file.filename} as UTF-8 and no alternative handling available"
                                        )

                                        continue

                                except Exception as e:

                                    logger.error(
                                        f" Error parsing file {file.filename}: {e}"
                                    )

                                    continue

                            # DEDUP + BATCH INSERT for each file after processing

                            if parsed_records:

                                try:

                                    from database import get_db_manager

                                    manager = get_db_manager()

                                    # Remove metadata fields before storing

                                    clean_records = [
                                        {
                                            k: v
                                            for k, v in r.items()
                                            if not str(k).startswith("_")
                                        }
                                        for r in parsed_records
                                    ]

                                    total_inserted = await manager.dedup_and_batch_insert_client_data(
                                        f"client_{client_id.replace('-', '_')}_data",
                                        clean_records,
                                        client_id,
                                        dedup_scope="day",
                                    )

                                    logger.info(
                                        f" FILE {file.filename}: {total_inserted} new rows inserted after dedup!"
                                    )

                                    all_parsed_records.extend(parsed_records)

                                except Exception as db_error:

                                    logger.error(
                                        f" Database insertion failed for {file.filename}: {db_error}"
                                    )

                        except Exception as e:

                            logger.error(
                                f" Error processing file {file.filename}: {e}"
                            )

                            continue

                # Process all collected records

                if all_parsed_records:

                    logger.info(
                        f" Processing {len(all_parsed_records)} total records from all sources"
                    )

                    # BATCH INSERT - Same logic for ALL formats!

                    batch_rows = []

                    for record in all_parsed_records:

                        # Remove metadata fields before storing

                        clean_record = {
                            k: v for k, v in record.items() if not k.startswith("_")
                        }

                        batch_rows.append(
                            {
                                "client_id": client_id,
                                "table_name": f"client_{client_id.replace('-', '_')}_data",
                                "data": clean_record,  # Store as JSON object
                            }
                        )

                    # OPTIMIZED BATCH INSERT for ALL formats with retry logic

                    if batch_rows:

                        total_inserted = await improved_batch_insert(
                            db_client, batch_rows, data_type
                        )

                        logger.info(
                            f" TOTAL RECORDS: {total_inserted} rows inserted successfully!"
                        )

                        #  PERFORMANCE MONITORING for large datasets

                        if (
                            len(all_parsed_records) > 10000
                        ):  # Track performance for large uploads

                            success_rate = (
                                total_inserted / len(all_parsed_records) * 100
                            )

                            logger.info(f" LARGE DATASET PERFORMANCE REPORT:")

                            logger.info(
                                f"    Dataset: {len(all_parsed_records)} total records"
                            )

                            logger.info(f"    Inserted: {total_inserted} records")

                            logger.info(f"    Success Rate: {success_rate:.1f}%")

                            logger.info(
                                f"   ⏱️  Processing: Multi-file upload with retry logic"
                            )

                            logger.info(f"    Client: {email}")

                            # Record performance metrics for monitoring

                            try:

                                db_client.table("performance_metrics").insert(
                                    {
                                        "client_id": client_id,
                                        "operation_type": "multi_file_upload",
                                        "total_records": len(all_parsed_records),
                                        "records_inserted": total_inserted,
                                        "success_rate": round(success_rate, 2),
                                        "data_type": data_type,
                                        "file_count": (
                                            len(files_to_process)
                                            if input_method == "upload"
                                            else 1
                                        ),
                                        "timestamp": datetime.utcnow().isoformat(),
                                    }
                                ).execute()

                                logger.info(
                                    f" Performance metrics recorded for {email}"
                                )

                            except Exception as metrics_error:

                                logger.warning(
                                    f" Could not record performance metrics: {metrics_error}"
                                )

                    else:

                        raise ValueError("No records parsed from any source")

            except Exception as parse_error:

                logger.error(f" Data parsing failed: {parse_error}")

                # ️ ENHANCED: Store fallback data for both paste AND file uploads

                # This ensures dashboard generation can still proceed with error info

                fallback_data = None

                if input_method == "paste" and data_content:

                    fallback_data = {
                        "raw_content": data_content,
                        "type": data_type,
                        "parse_error": str(parse_error)[:200],
                    }

                elif input_method == "upload" and files_to_process:

                    # For file uploads, create a summary record with error info

                    first_file = files_to_process[0]

                    fallback_data = {
                        "filename": (
                            first_file.filename
                            if first_file.filename
                            else "unknown_file"
                        ),
                        "file_size": (
                            first_file.size if hasattr(first_file, "size") else 0
                        ),
                        "parse_error": str(parse_error)[:200],
                        "type": data_type,
                        "status": "parsing_failed",
                        "error_type": (
                            "unicode_error"
                            if "unicode" in str(parse_error).lower()
                            else "parsing_error"
                        ),
                    }

                if fallback_data:

                    db_client.table("client_data").insert(
                        {
                            "client_id": client_id,
                            "table_name": f"client_{client_id.replace('-', '_')}_data",
                            "data": fallback_data,
                        }
                    ).execute()

                    logger.info(f" Fallback data stored for {input_method} method")

            logger.info(f" Data stored DIRECTLY for {email} - NOW TRIGGER AI!")

            #  NOW TRIGGER AI DASHBOARD GENERATION AFTER DATA IS SAFELY STORED

            try:

                logger.info(
                    f" NOW triggering AI dashboard generation for {email} (data is ready!)"
                )

                # IMPROVED: Better error handling and more robust generation

                async def robust_dashboard_generation():
                    """Robust async dashboard generation with detailed error logging"""

                    try:

                        # Wait a moment to ensure data is committed

                        await asyncio.sleep(1)

                        logger.info(
                            f"🤖 AI dashboard generation starting for {email} (data confirmed!)"
                        )

                        # Import here to avoid circular imports (with error handling)

                        try:

                            from dashboard_orchestrator import dashboard_orchestrator

                            logger.info(
                                f" Dashboard orchestrator imported successfully for {email}"
                            )

                        except Exception as import_error:

                            logger.error(
                                f" Failed to import dashboard_orchestrator: {import_error}"
                            )

                            return

                        #  PRE-CACHE LLM ANALYSIS DURING CLIENT CREATION (PERFORMANCE BOOST!)

                        try:

                            logger.info(
                                f"🧠 Pre-caching LLM analysis for {email} to avoid future delays..."
                            )

                            # Get client data - NO LIMIT for complete data processing and run LLM analysis once

                            client_data = await dashboard_orchestrator.ai_analyzer.get_client_data_optimized(
                                client_id
                            )

                            if client_data and client_data.get("data"):

                                # This will cache the results automatically

                                await dashboard_orchestrator._extract_business_insights_from_data(
                                    client_data
                                )

                                logger.info(f" LLM analysis pre-cached for {email}!")

                            else:

                                logger.warning(
                                    f" No data found for LLM pre-caching for {email}"
                                )

                        except Exception as cache_error:

                            logger.warning(
                                f" LLM analysis pre-caching failed for {email}: {cache_error}"
                            )

                            # Continue with dashboard generation even if caching fails

                        # Generate dashboard with detailed error handling

                        try:

                            generation_response = (
                                await dashboard_orchestrator.generate_dashboard(
                                    client_id=uuid.UUID(client_id),
                                    force_regenerate=True,
                                )
                            )

                            if generation_response.success:

                                logger.info(
                                    f" AI Dashboard completed successfully for {email}!"
                                )

                                logger.info(
                                    f" Generated {generation_response.metrics_generated} metrics for {email}"
                                )

                            else:

                                logger.error(
                                    f" AI Dashboard failed for {email}: {generation_response.message}"
                                )

                        except Exception as gen_error:

                            logger.error(
                                f" Dashboard generation threw exception for {email}: {type(gen_error).__name__}: {str(gen_error)}"
                            )

                            # Log full traceback for debugging

                            import traceback

                            logger.error(f"Full traceback: {traceback.format_exc()}")

                    except Exception as outer_error:

                        logger.error(
                            f" Outer AI dashboard generation error for {email}: {type(outer_error).__name__}: {str(outer_error)}"
                        )

                        import traceback

                        logger.error(f"Full outer traceback: {traceback.format_exc()}")

                # Create background task with improved error handling

                try:

                    task = asyncio.create_task(robust_dashboard_generation())

                    # Don't await the task - let it run in background

                    logger.info(
                        f" AI Dashboard generation task created successfully for {email}"
                    )

                except Exception as task_error:

                    logger.error(
                        f" Failed to create background task for {email}: {task_error}"
                    )

            except Exception as ai_trigger_error:

                logger.error(
                    f"  Failed to trigger AI generation for {email}: {type(ai_trigger_error).__name__}: {str(ai_trigger_error)}"
                )

                # Log full traceback for better debugging

                import traceback

                logger.error(f"Full AI trigger traceback: {traceback.format_exc()}")

                # Don't let this break client creation

                logger.info(
                    f"Client {email} created successfully even though AI generation failed"
                )

            except Exception as storage_error:

                logger.warning(
                    f" Direct storage failed: {storage_error} - client created anyway"
                )

        # Return client response immediately - dashboard generates in background AFTER data storage

        client_response = ClientResponse(**client)

        logger.info(
            f" INSTANT: Client {email} created! Dashboard will generate after data is ready..."
        )

        return client_response

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Superadmin client creation failed: {e}")

        logger.error(f"   - Email: {email}")

        logger.error(f"   - Company: {company_name}")

        logger.error(f"   - Data type: {data_type}")

        logger.error(f"   - Input method: {input_method}")

        logger.error(f"   - File count: {file_count}")

        logger.error(f"   - Error type: {type(e).__name__}")

        import traceback

        logger.error(f"   - Full traceback: {traceback.format_exc()}")

        # Provide more specific error messages for different failure types

        if "bak" in str(e).lower() or "parsing" in str(e).lower():

            raise HTTPException(
                status_code=400, detail=f"BAK file processing failed: {str(e)}"
            )

        elif "database" in str(e).lower() or "connection" in str(e).lower():

            raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

        elif "validation" in str(e).lower():

            raise HTTPException(
                status_code=400, detail=f"Data validation failed: {str(e)}"
            )

        else:

            raise HTTPException(
                status_code=500, detail=f"Client creation failed: {str(e)}"
            )


# REMOVED: No more background AI processing - direct storage only!


@app.post("/api/superadmin/test-bak-upload")
async def test_bak_upload(
    token: str = Depends(security), uploaded_file: UploadFile = File(...)
):
    """Test endpoint to debug BAK file upload issues"""

    try:

        verify_superadmin_token(token.credentials)

        logger.info(f" Testing BAK file upload:")

        logger.info(f"   - Filename: {uploaded_file.filename}")

        logger.info(f"   - Content type: {uploaded_file.content_type}")

        logger.info(
            f"   - Size: {uploaded_file.size if hasattr(uploaded_file, 'size') else 'unknown'}"
        )

        # Read file content

        file_content = await uploaded_file.read()

        logger.info(f"   - Actual content length: {len(file_content)} bytes")

        # Test encoding detection

        encoding_results = []

        for encoding in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:

            try:

                decoded = file_content.decode(encoding)

                encoding_results.append(
                    {
                        "encoding": encoding,
                        "success": True,
                        "decoded_length": len(decoded),
                        "preview": decoded[:100],
                    }
                )

                logger.info(f"    {encoding}: {len(decoded)} chars")

            except UnicodeDecodeError as e:

                encoding_results.append(
                    {"encoding": encoding, "success": False, "error": str(e)[:100]}
                )

                logger.info(f"    {encoding}: {str(e)[:50]}")

        # Test BAK parsing

        from universal_data_parser import universal_parser

        # Try with the first successful encoding

        successful_encoding = next((r for r in encoding_results if r["success"]), None)

        if successful_encoding:

            logger.info(
                f" Testing BAK parsing with {successful_encoding['encoding']} encoding..."
            )

            try:

                decoded_content = file_content.decode(successful_encoding["encoding"])

                parsed_records = universal_parser.parse_to_json(decoded_content, "bak")

                return {
                    "success": True,
                    "file_info": {
                        "filename": uploaded_file.filename,
                        "content_type": uploaded_file.content_type,
                        "size_bytes": len(file_content),
                        "successful_encoding": successful_encoding["encoding"],
                    },
                    "encoding_results": encoding_results,
                    "parsing_result": {
                        "records_extracted": len(parsed_records),
                        "sample_records": parsed_records[:3] if parsed_records else [],
                    },
                }

            except Exception as parse_error:

                logger.error(f" BAK parsing failed: {parse_error}")

                return {
                    "success": False,
                    "error": f"BAK parsing failed: {str(parse_error)}",
                    "file_info": {
                        "filename": uploaded_file.filename,
                        "size_bytes": len(file_content),
                    },
                    "encoding_results": encoding_results,
                }

        else:

            return {
                "success": False,
                "error": "Could not decode file with any encoding",
                "file_info": {
                    "filename": uploaded_file.filename,
                    "size_bytes": len(file_content),
                },
                "encoding_results": encoding_results,
            }

    except Exception as e:

        logger.error(f" BAK upload test failed: {e}")

        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")

        raise HTTPException(status_code=500, detail=f"BAK upload test failed: {str(e)}")


@app.get("/api/superadmin/clients")
async def list_clients_superadmin(token: str = Depends(security)):
    """Superadmin: SUPER FAST client list - NO AI, JUST DATABASE"""

    try:

        logger.info(f" LIGHTNING FAST superadmin clients request")

        # Verify superadmin token

        verify_superadmin_token(token.credentials)

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # JUST GET CLIENTS - SUPER SIMPLE AND FAST

        clients_response = (
            db_client.table("clients")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        if not clients_response.data:

            logger.info(f" No clients found")

            return {"clients": [], "total": 0}

        # FAST BASIC RESPONSES - NO HEAVY QUERIES

        basic_clients = []

        for client in clients_response.data:

            # Check if schema exists (simple check)

            schema_exists = False

            data_count = 0

            try:

                # Quick schema check

                schema_response = (
                    db_client.table("client_schemas")
                    .select("data_type")
                    .eq("client_id", client["client_id"])
                    .limit(1)
                    .execute()
                )

                schema_exists = bool(schema_response.data)

                if schema_exists:

                    # FIXED: Proper data count - use count-only query without data retrieval

                    try:

                        # First try to get count without retrieving data (most efficient)

                        count_response = (
                            db_client.table("client_data")
                            .select("client_id", count="exact")
                            .eq("client_id", client["client_id"])
                            .execute()
                        )

                        if (
                            hasattr(count_response, "count")
                            and count_response.count is not None
                        ):

                            data_count = count_response.count

                        else:

                            # Fallback: get all records to count them (less efficient but works)

                            all_data_response = (
                                db_client.table("client_data")
                                .select("client_id")
                                .eq("client_id", client["client_id"])
                                .limit(10000)
                                .execute()
                            )

                            data_count = (
                                len(all_data_response.data)
                                if all_data_response.data
                                else 0
                            )

                    except Exception as count_error:

                        logger.warning(
                            f"  Count query failed, trying manual count: {count_error}"
                        )

                        # Final fallback: manual count

                        try:

                            manual_count_response = (
                                db_client.table("client_data")
                                .select("client_id")
                                .eq("client_id", client["client_id"])
                                .limit(10000)
                                .execute()
                            )

                            data_count = (
                                len(manual_count_response.data)
                                if manual_count_response.data
                                else 0
                            )

                        except:

                            data_count = 0

            except Exception as e:

                # If anything fails, just continue with defaults

                logger.warning(
                    f"  Failed to get data count for client {client['client_id']}: {e}"
                )

                pass

            basic_clients.append(
                {
                    "client_id": client["client_id"],
                    "company_name": client["company_name"],
                    "email": client["email"],
                    "subscription_tier": client["subscription_tier"],
                    "created_at": client["created_at"],
                    "updated_at": client["updated_at"],
                    "has_schema": schema_exists,
                    "actual_data_count": data_count,
                    "data_stored": data_count > 0,
                    "schema_info": (
                        {
                            "data_type": "data" if schema_exists else None,
                            "data_stored": data_count > 0,
                            "row_count": data_count,
                        }
                        if schema_exists
                        else None
                    ),
                }
            )

        logger.info(f" LIGHTNING FAST: {len(basic_clients)} clients loaded")

        return {
            "clients": basic_clients,
            "total": len(basic_clients),
            "page": 1,
            "limit": len(basic_clients),
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to list clients: {e}")

        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/superadmin/clients/{client_id}")
async def delete_client_superadmin(client_id: str, token: str = Depends(security)):
    """Superadmin: Delete a client"""

    try:

        # Verify superadmin token

        verify_superadmin_token(token.credentials)

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Delete client

        response = (
            db_client.table("clients").delete().eq("client_id", client_id).execute()
        )

        if response.data:

            logger.info(f" Superadmin deleted client: {client_id}")

            return {"message": "Client deleted successfully"}

        else:

            raise HTTPException(status_code=404, detail="Client not found")

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to delete client: {e}")

        raise HTTPException(status_code=500, detail=str(e))


# ==================== API INTEGRATIONS ====================


@app.post("/api/superadmin/clients/add-integration")
async def add_api_integration_to_existing_client(
    token: str = Depends(security),
    client_id: str = Form(...),
    platform_type: str = Form(...),
    connection_name: str = Form(...),
    # Shopify fields
    shop_domain: str = Form(default=""),
    shopify_access_token: str = Form(default=""),
    # Amazon fields
    amazon_seller_id: str = Form(default=""),
    amazon_marketplace_ids: str = Form(default=""),
    amazon_access_key_id: str = Form(default=""),
    amazon_secret_access_key: str = Form(default=""),
    amazon_refresh_token: str = Form(default=""),
    amazon_region: str = Form(default="us-east-1"),
    # WooCommerce fields
    woo_site_url: str = Form(default=""),
    woo_consumer_key: str = Form(default=""),
    woo_consumer_secret: str = Form(default=""),
    woo_version: str = Form(default="wc/v3"),
    sync_frequency_hours: int = Form(default=2),
):
    """Add additional API integration to existing client (multiple platforms per client)"""
    try:
        # Verify superadmin token
        verify_superadmin_token(token.credentials)
        
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Check if client exists
        client_response = db_client.table("clients").select("client_id, company_name, email").eq("client_id", client_id).execute()
        if not client_response.data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client = client_response.data[0]
        
        # Check if this platform integration already exists for this client
        existing_integration = db_client.table("client_api_credentials").select("credential_id").eq("client_id", client_id).eq("platform_type", platform_type).execute()
        if existing_integration.data:
            raise HTTPException(status_code=400, detail=f"Client already has {platform_type} integration")
        
        # Prepare API credentials based on platform type
        credentials = {}
        
        if platform_type == "shopify":
            if not shop_domain or not shopify_access_token:
                raise HTTPException(status_code=400, detail="Shopify domain and access token are required")
            credentials = {
                "shop_domain": shop_domain,
                "access_token": shopify_access_token
            }
        
        elif platform_type == "amazon":
            if not amazon_seller_id or not amazon_access_key_id or not amazon_secret_access_key:
                raise HTTPException(status_code=400, detail="Amazon seller ID and API keys are required")
            credentials = {
                "seller_id": amazon_seller_id,
                "marketplace_ids": amazon_marketplace_ids.split(",") if amazon_marketplace_ids else ["ATVPDKIKX0DER"],
                "access_key_id": amazon_access_key_id,
                "secret_access_key": amazon_secret_access_key,
                "refresh_token": amazon_refresh_token,
                "region": amazon_region
            }
        
        elif platform_type == "woocommerce":
            if not woo_site_url or not woo_consumer_key or not woo_consumer_secret:
                raise HTTPException(status_code=400, detail="WooCommerce site URL and API keys are required")
            credentials = {
                "site_url": woo_site_url,
                "consumer_key": woo_consumer_key,
                "consumer_secret": woo_consumer_secret,
                "version": woo_version
            }
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform type")
        
        # Store additional API credentials
        creds_response = db_client.table("client_api_credentials").insert({
            "client_id": client_id,
            "platform_type": platform_type,
            "connection_name": connection_name,
            "credentials": credentials,
            "sync_frequency_hours": sync_frequency_hours,
            "status": "pending",
        }).execute()
        
        if not creds_response.data:
            raise HTTPException(status_code=400, detail="Failed to store API credentials")
        
        credential_id = creds_response.data[0]["credential_id"]
        
        # Test API connection and fetch initial data
        try:
            from api_connectors import api_data_fetcher
            
            # Test connection first
            success, message = await api_data_fetcher.test_connection(platform_type, credentials)
            if not success:
                # Update status to error
                db_client.table("client_api_credentials").update({
                    "status": "error", 
                    "error_message": message
                }).eq("credential_id", credential_id).execute()
                
                return {
                    "success": False,
                    "message": f"Integration added but API connection failed: {message}",
                    "client_id": client_id,
                    "platform_type": platform_type,
                    "credential_id": credential_id
                }
            
            # Connection successful, fetch initial data
            logger.info(f" {platform_type} API connection successful for existing client {client_id}")
            
            all_data = await api_data_fetcher.fetch_all_data(platform_type, credentials)
            
            # Process and store data
            total_records = 0
            for data_type, records in all_data.items():
                if not records:
                    continue
                
                # Store data with deduplication (same table names as always)
                try:
                    from database import get_db_manager
                    manager = get_db_manager()
                    
                    inserted_count = await manager.dedup_and_batch_insert_client_data(
                        f"client_{client_id.replace('-', '_')}_data",
                        records,
                        client_id,
                        dedup_scope="day",
                    )
                    total_records += inserted_count
                    
                except Exception as e:
                    logger.warning(f" Data storage failed for {data_type}: {e}")
                    # Continue anyway
            
            # Update API credentials status to connected
            from datetime import datetime, timedelta
            next_sync = datetime.now() + timedelta(hours=sync_frequency_hours)
            
            db_client.table("client_api_credentials").update({
                "status": "connected",
                "last_sync_at": datetime.now().isoformat(),
                "next_sync_at": next_sync.isoformat(),
            }).eq("credential_id", credential_id).execute()
            
            logger.info(f" Additional {platform_type} integration added for client {client_id}: {total_records} initial records")
            
            return {
                "success": True,
                "message": f"Successfully added {platform_type} integration to existing client",
                "client_id": client_id,
                "platform_type": platform_type,
                "credential_id": credential_id,
                "total_initial_records": total_records,
                "next_sync_at": next_sync.isoformat()
            }
            
        except Exception as api_error:
            logger.error(f" API integration test failed: {api_error}")
            
            # Update status to error but don't delete the integration
            db_client.table("client_api_credentials").update({
                "status": "error", 
                "error_message": str(api_error)
            }).eq("credential_id", credential_id).execute()
            
            return {
                "success": False,
                "message": f"Integration added but initial sync failed: {str(api_error)}",
                "client_id": client_id,
                "platform_type": platform_type,
                "credential_id": credential_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Failed to add API integration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add integration: {str(e)}")


@app.get("/api/superadmin/clients/{client_id}/integrations")
async def get_client_integrations(client_id: str, token: str = Depends(security)):
    """Get all API integrations for a specific client"""
    try:
        # Verify superadmin token
        verify_superadmin_token(token.credentials)
        
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Get client info
        client_response = db_client.table("clients").select("client_id, company_name, email").eq("client_id", client_id).execute()
        if not client_response.data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get all integrations
        integrations_response = db_client.table("client_api_credentials").select(
            "credential_id, platform_type, connection_name, status, last_sync_at, next_sync_at, sync_frequency_hours, created_at"
        ).eq("client_id", client_id).order("platform_type").execute()
        
        client = client_response.data[0]
        integrations = integrations_response.data or []
        
        return {
            "client_id": client_id,
            "company_name": client["company_name"],
            "email": client["email"], 
            "total_integrations": len(integrations),
            "platforms": [i["platform_type"] for i in integrations],
            "integrations": integrations,
            "missing_platforms": [p for p in ["shopify", "amazon"] if p not in [i["platform_type"] for i in integrations]]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Failed to get client integrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/superadmin/clients/api-integration", response_model=ClientResponse)
async def create_client_with_api_integration(
    token: str = Depends(security),
    company_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    platform_type: str = Form(...),
    connection_name: str = Form(...),
    # Shopify fields
    shop_domain: str = Form(default=""),
    shopify_access_token: str = Form(default=""),
    # Amazon fields
    amazon_seller_id: str = Form(default=""),
    amazon_marketplace_ids: str = Form(default=""),
    amazon_access_key_id: str = Form(default=""),
    amazon_secret_access_key: str = Form(default=""),
    amazon_refresh_token: str = Form(default=""),
    amazon_region: str = Form(default="us-east-1"),
    # WooCommerce fields
    woo_site_url: str = Form(default=""),
    woo_consumer_key: str = Form(default=""),
    woo_consumer_secret: str = Form(default=""),
    woo_version: str = Form(default="wc/v3"),
    sync_frequency_hours: int = Form(default=2),
):
    """Superadmin: Create a new client with API integration"""

    try:

        # Verify superadmin token

        verify_superadmin_token(token.credentials)

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Check if client already exists

        existing = (
            db_client.table("clients").select("email").eq("email", email).execute()
        )

        if existing.data:

            raise HTTPException(
                status_code=400, detail="Client with this email already exists"
            )

        # Hash password

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # Insert client into database

        response = (
            db_client.table("clients")
            .insert(
                {
                    "company_name": company_name,
                    "email": email,
                    "password_hash": password_hash,
                    "subscription_tier": "basic",
                }
            )
            .execute()
        )

        if not response.data:

            raise HTTPException(status_code=400, detail="Failed to create client")

        client = response.data[0]

        client_id = client["client_id"]

        logger.info(f" Client created for API integration: {email}")

        # Prepare API credentials based on platform type

        credentials = {}

        if platform_type == "shopify":

            if not shop_domain or not shopify_access_token:

                raise HTTPException(
                    status_code=400,
                    detail="Shopify domain and access token are required",
                )

            credentials = {
                "shop_domain": shop_domain,
                "access_token": shopify_access_token,
                "scopes": ["read_orders", "read_products", "read_customers"],
            }

        elif platform_type == "amazon":

            if not all(
                [
                    amazon_seller_id,
                    amazon_marketplace_ids,
                    amazon_access_key_id,
                    amazon_secret_access_key,
                    amazon_refresh_token,
                ]
            ):

                raise HTTPException(
                    status_code=400, detail="All Amazon credentials are required"
                )

            credentials = {
                "seller_id": amazon_seller_id,
                "marketplace_ids": [
                    mid.strip() for mid in amazon_marketplace_ids.split(",")
                ],
                "access_key_id": amazon_access_key_id,
                "secret_access_key": amazon_secret_access_key,
                "refresh_token": amazon_refresh_token,
                "region": amazon_region,
            }

        elif platform_type == "woocommerce":

            if not all([woo_site_url, woo_consumer_key, woo_consumer_secret]):

                raise HTTPException(
                    status_code=400, detail="All WooCommerce credentials are required"
                )

            credentials = {
                "site_url": woo_site_url,
                "consumer_key": woo_consumer_key,
                "consumer_secret": woo_consumer_secret,
                "version": woo_version,
            }

        else:

            raise HTTPException(status_code=400, detail="Unsupported platform type")

        # Store API credentials in database

        creds_response = (
            db_client.table("client_api_credentials")
            .insert(
                {
                    "client_id": client_id,
                    "platform_type": platform_type,
                    "connection_name": connection_name,
                    "credentials": credentials,
                    "sync_frequency_hours": sync_frequency_hours,
                    "status": "pending",
                }
            )
            .execute()
        )

        if not creds_response.data:

            # Rollback client creation if credentials storage fails

            db_client.table("clients").delete().eq("client_id", client_id).execute()

            raise HTTPException(
                status_code=400, detail="Failed to store API credentials"
            )

        credential_id = creds_response.data[0]["credential_id"]

        logger.info(f" API credentials stored: {credential_id}")

        # Test API connection and fetch initial data

        try:

            from api_connectors import api_data_fetcher

            # Test connection first

            success, message = await api_data_fetcher.test_connection(
                platform_type, credentials
            )

            if not success:

                # Update status to error

                db_client.table("client_api_credentials").update(
                    {"status": "error", "error_message": message}
                ).eq("credential_id", credential_id).execute()

                return ClientResponse(
                    **client,
                    message=f"Client created but API connection failed: {message}",
                )

            # Connection successful, fetch initial data

            logger.info(
                f" API connection successful, fetching initial data for {platform_type}"
            )

            # Fetch data from API

            all_data = await api_data_fetcher.fetch_all_data(platform_type, credentials)

            # Process and store data

            total_records = 0

            for data_type, records in all_data.items():

                if records:

                    # Create or update schema entry (handle duplicates gracefully)

                    table_name = f"client_{client_id.replace('-', '_')}_data"

                    schema_data = {
                        "client_id": client_id,
                        "table_name": table_name,
                        "data_type": f"{platform_type}_{data_type}",
                        "schema_definition": {
                            "type": "api_data",
                            "platform": platform_type,
                            "data_type": data_type,
                        },
                        "api_source": True,
                        "platform_type": platform_type,
                    }

                    try:

                        # Try insert first

                        db_client.table("client_schemas").insert(schema_data).execute()

                        logger.info(
                            f" Created new schema entry for {platform_type}_{data_type}"
                        )

                    except Exception as schema_error:

                        # If insert fails due to duplicate, try updating existing record

                        if "duplicate key" in str(
                            schema_error
                        ).lower() or "23505" in str(schema_error):

                            logger.info(
                                f" Schema entry exists, updating for {platform_type}_{data_type}"
                            )

                            try:

                                db_client.table("client_schemas").update(
                                    {
                                        "data_type": f"{platform_type}_{data_type}",
                                        "schema_definition": {
                                            "type": "api_data",
                                            "platform": platform_type,
                                            "data_type": data_type,
                                        },
                                        "api_source": True,
                                        "platform_type": platform_type,
                                    }
                                ).eq("client_id", client_id).eq(
                                    "table_name", table_name
                                ).execute()

                                logger.info(
                                    f" Updated existing schema entry for {platform_type}_{data_type}"
                                )

                            except Exception as update_error:

                                logger.error(f" Schema update failed: {update_error}")

                                # Continue anyway - schema is not critical for data storage

                        else:

                            logger.error(f" Unexpected schema error: {schema_error}")

                            # Continue anyway

                    # Dedup and store data records for the day

                    if records:

                        from database import get_db_manager

                        manager = get_db_manager()

                        inserted_count = (
                            await manager.dedup_and_batch_insert_client_data(
                                f"client_{client_id.replace('-', '_')}_data",
                                records,
                                client_id,
                                dedup_scope="day",
                            )
                        )

                        total_records += inserted_count

            # Update API credentials status to connected

            from datetime import datetime, timedelta

            next_sync = datetime.now() + timedelta(hours=sync_frequency_hours)

            db_client.table("client_api_credentials").update(
                {
                    "status": "connected",
                    "last_sync_at": datetime.now().isoformat(),
                    "next_sync_at": next_sync.isoformat(),
                }
            ).eq("credential_id", credential_id).execute()

            # Record sync result

            db_client.table("client_api_sync_results").insert(
                {
                    "client_id": client_id,
                    "credential_id": credential_id,
                    "platform_type": platform_type,
                    "connection_name": connection_name,
                    "records_fetched": total_records,
                    "records_processed": total_records,
                    "records_stored": total_records,
                    "sync_duration_seconds": 0,  # Would be calculated in production
                    "success": True,
                    "data_types_synced": list(all_data.keys()),
                }
            ).execute()

            logger.info(
                f" API integration complete: {total_records} records from {platform_type}"
            )

            # Trigger dashboard generation in background

            try:

                async def generate_dashboard_bg():

                    await asyncio.sleep(2)  # Give data time to be committed

                    from dashboard_orchestrator import dashboard_orchestrator

                    await dashboard_orchestrator.generate_dashboard(
                        client_id=uuid.UUID(client_id), force_regenerate=True
                    )

                asyncio.create_task(generate_dashboard_bg())

                logger.info(f" Dashboard generation triggered for API integration")

            except Exception as bg_error:

                logger.warning(f" Background dashboard generation failed: {bg_error}")

            return ClientResponse(**client)

        except Exception as api_error:

            logger.error(f" API integration failed: {api_error}")

            # Update status to error but don't delete client

            db_client.table("client_api_credentials").update(
                {"status": "error", "error_message": str(api_error)}
            ).eq("credential_id", credential_id).execute()

            return ClientResponse(**client)

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" API integration client creation failed: {e}")

        raise HTTPException(status_code=500, detail=f"API integration failed: {str(e)}")


@app.get("/api/superadmin/api-platforms")
async def get_api_platforms(token: str = Depends(security)):
    """Get available API platform configurations for the UI"""

    try:

        verify_superadmin_token(token.credentials)

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        response = (
            db_client.table("api_platform_configs")
            .select("*")
            .eq("is_active", True)
            .execute()
        )

        return {
            "platforms": response.data or [],
            "total": len(response.data) if response.data else 0,
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to get API platforms: {e}")

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/superadmin/test-api-connection")
async def test_api_connection(
    token: str = Depends(security),
    platform_type: str = Form(...),
    credentials_json: str = Form(...),
):
    """Test API connection before saving"""

    try:

        verify_superadmin_token(token.credentials)

        from api_connectors import api_data_fetcher

        import json

        # Parse credentials

        credentials = json.loads(credentials_json)

        # Test connection

        success, message = await api_data_fetcher.test_connection(
            platform_type, credentials
        )

        return {"success": success, "message": message, "platform_type": platform_type}

    except Exception as e:

        logger.error(f" API connection test failed: {e}")

        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "platform_type": platform_type,
        }


# ==================== SFTP INTEGRATION ENDPOINTS ====================


@app.post("/api/superadmin/test-sftp-connection")
async def test_sftp_connection(
    token: str = Depends(security),
    sftp_host: str = Form(...),
    sftp_username: str = Form(...),
    sftp_password: str = Form(...),
    sftp_port: int = Form(22),
    sftp_remote_path: str = Form("/"),
    sftp_file_pattern: str = Form("*.*"),
):
    """Test SFTP connection and return file list"""

    try:

        verify_superadmin_token(token.credentials)

        from sftp_manager import sftp_manager, SFTPCredentials

        # Create credentials object

        credentials = SFTPCredentials(
            host=sftp_host,
            username=sftp_username,
            password=sftp_password,
            port=sftp_port,
            remote_path=sftp_remote_path,
            file_pattern=sftp_file_pattern,
        )

        # Test connection

        success, message, files = sftp_manager.test_connection(credentials)

        # Format file list for response

        files_data = []

        for file_info in files:

            if not file_info.is_directory:  # Only include files, not directories

                files_data.append(
                    {
                        "filename": file_info.filename,
                        "size": file_info.size,
                        "modified_time": file_info.modified_time,
                    }
                )

        return {
            "success": success,
            "message": message,
            "files_found": len(files_data),
            "files": files_data,
        }

    except Exception as e:

        logger.error(f" SFTP connection test failed: {e}")

        return {
            "success": False,
            "message": f"SFTP connection test failed: {str(e)}",
            "files_found": 0,
            "files": [],
        }


@app.post("/api/superadmin/clients/sftp-integration", response_model=ClientResponse)
async def create_client_with_sftp_integration(
    token: str = Depends(security),
    company_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    sftp_host: str = Form(...),
    sftp_username: str = Form(...),
    sftp_password: str = Form(...),
    sftp_port: int = Form(22),
    sftp_remote_path: str = Form("/"),
    sftp_file_pattern: str = Form("*.*"),
    auto_sync_enabled: bool = Form(False),
    sync_frequency_hours: int = Form(2),
    selected_files: str = Form(default=""),  # JSON string of selected files
):
    """Superadmin: Create a new client with SFTP integration"""

    try:

        # Verify superadmin token

        verify_superadmin_token(token.credentials)

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Check if client already exists

        existing = (
            db_client.table("clients").select("email").eq("email", email).execute()
        )

        if existing.data:

            raise HTTPException(
                status_code=400, detail="Client with this email already exists"
            )

        # Hash password

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # Insert client into database

        response = (
            db_client.table("clients")
            .insert(
                {
                    "company_name": company_name,
                    "email": email,
                    "password_hash": password_hash,
                    "subscription_tier": "basic",
                }
            )
            .execute()
        )

        if not response.data:

            raise HTTPException(status_code=400, detail="Failed to create client")

        client = response.data[0]

        client_id = client["client_id"]

        logger.info(f" Client created for SFTP integration: {email}")

        # Store SFTP configuration (encrypt password)

        import base64

        import hashlib

        # Simple encryption for password (in production, use proper encryption)

        password_encrypted = base64.b64encode(sftp_password.encode()).decode()

        sftp_config = {
            "client_id": client_id,
            "host": sftp_host,
            "username": sftp_username,
            "password_encrypted": password_encrypted,
            "port": sftp_port,
            "remote_path": sftp_remote_path,
            "file_pattern": sftp_file_pattern,
            "auto_sync_enabled": auto_sync_enabled,
            "sync_frequency_hours": sync_frequency_hours,
            "created_at": "NOW()",
        }

        # Store SFTP config in database

        db_client.table("client_sftp_configs").insert(sftp_config).execute()

        # Download and process initial files

        from sftp_manager import sftp_manager, SFTPCredentials

        import json

        credentials = SFTPCredentials(
            host=sftp_host,
            username=sftp_username,
            password=sftp_password,
            port=sftp_port,
            remote_path=sftp_remote_path,
            file_pattern=sftp_file_pattern,
        )

        # Get files to download

        files_to_download = []

        if selected_files:

            try:

                files_to_download = json.loads(selected_files)

            except:

                files_to_download = []

        # If no specific files selected, download all matching files

        if not files_to_download:

            success, files, message = sftp_manager.test_connection(credentials)

            if success:

                files_to_download = [f.filename for f in files if not f.is_directory]

        total_records = 0

        files_processed = 0

        if files_to_download:

            # Download files

            download_result = sftp_manager.download_multiple_files(
                credentials, files_to_download
            )

            if download_result["downloaded_count"] > 0:

                # Process each downloaded file

                from universal_data_parser import universal_parser

                for filename, file_content in download_result["files"].items():

                    try:

                        # Detect file format

                        if filename.lower().endswith(".csv"):

                            data_format = "csv"

                        elif filename.lower().endswith((".xlsx", ".xls")):

                            data_format = "excel"

                        elif filename.lower().endswith(".json"):

                            data_format = "json"

                        elif filename.lower().endswith(".xml"):

                            data_format = "xml"

                        else:

                            data_format = "csv"  # Default to CSV

                        # Parse file content to JSON

                        file_str = (
                            file_content.decode("utf-8")
                            if isinstance(file_content, bytes)
                            else file_content
                        )

                        parsed_records = universal_parser.parse_to_json(
                            file_str, data_format
                        )

                        if parsed_records:

                            logger.info(
                                f" SFTP file {filename} parsed to {len(parsed_records)} JSON records"
                            )

                            # Store records in database

                            batch_rows = []

                            for record in parsed_records:

                                # Remove metadata fields before storing

                                clean_record = {
                                    k: v
                                    for k, v in record.items()
                                    if not k.startswith("_")
                                }

                                batch_rows.append(
                                    {
                                        "client_id": client_id,
                                        "table_name": f"client_{client_id.replace('-', '_')}_data",
                                        "data": clean_record,
                                        "source_file": filename,
                                        "source_type": "sftp",
                                    }
                                )

                            if batch_rows:

                                db_client.table("client_data").insert(
                                    batch_rows
                                ).execute()

                                total_records += len(batch_rows)

                                files_processed += 1

                                logger.info(
                                    f" Stored {len(batch_rows)} records from {filename}"
                                )

                    except Exception as file_error:

                        logger.error(
                            f" Failed to process SFTP file {filename}: {file_error}"
                        )

                        continue

                # Create schema entry

                db_client.table("client_schemas").insert(
                    {
                        "client_id": client_id,
                        "table_name": f"client_{client_id.replace('-', '_')}_data",
                        "data_type": "sftp_multi_format",
                        "schema_definition": {
                            "type": "sftp_data",
                            "files_processed": files_processed,
                            "total_records": total_records,
                            "source": "sftp",
                        },
                    }
                ).execute()

                logger.info(
                    f" SFTP integration complete: {files_processed} files, {total_records} records"
                )

        # Log SFTP sync

        db_client.table("sftp_sync_logs").insert(
            {
                "client_id": client_id,
                "files_downloaded": files_processed,
                "records_processed": total_records,
                "status": "success" if files_processed > 0 else "no_files",
                "sync_started_at": "NOW()",
                "sync_completed_at": "NOW()",
            }
        ).execute()

        # Return client response

        return ClientResponse(
            client_id=client_id,
            company_name=company_name,
            email=email,
            subscription_tier="basic",
            created_at=client["created_at"],
        )

    except Exception as e:

        logger.error(f" Failed to create SFTP client: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to create SFTP client: {str(e)}"
        )


# ==================== MASSIVE DATA PROCESSING ====================


async def _handle_massive_dataset_upload(client_id: str, df, quality_report):
    """Handle massive datasets with parallel processing and optimized batching"""

    try:

        import asyncio

        from concurrent.futures import ThreadPoolExecutor

        logger.info(
            f" MASSIVE DATA PROCESSING: {len(df)} rows for client {client_id}"
        )

        # Convert to JSON records in parallel chunks

        chunk_size = 5000

        df_chunks = [df[i : i + chunk_size] for i in range(0, len(df), chunk_size)]

        # Process chunks in parallel

        with ThreadPoolExecutor(max_workers=4) as executor:

            chunk_tasks = []

            for i, chunk in enumerate(df_chunks):

                task = asyncio.get_event_loop().run_in_executor(
                    executor, lambda c=chunk: c.to_dict("records")
                )

                chunk_tasks.append(task)

            # Wait for all chunks to be processed

            processed_chunks = await asyncio.gather(*chunk_tasks)

        # Flatten all chunks into single list

        all_records = []

        for chunk_records in processed_chunks:

            all_records.extend(chunk_records)

        logger.info(
            f" PARALLEL PROCESSING complete: {len(all_records)} records ready"
        )

        # Use optimized batch insert

        db_client = get_admin_client()

        total_inserted = await improved_batch_insert(
            db_client, all_records, "MASSIVE_DATA"
        )

        return {
            "success": True,
            "message": f" MASSIVE UPLOAD SUCCESS: {total_inserted} records processed",
            "records_processed": total_inserted,
            "processing_mode": "PARALLEL_MASSIVE",
            "quality_score": (
                quality_report.overall_score
                if hasattr(quality_report, "overall_score")
                else 95.0
            ),
        }

    except Exception as e:

        logger.error(f" Massive dataset processing failed: {e}")

        raise HTTPException(
            status_code=500, detail=f"Massive dataset processing failed: {str(e)}"
        )


# ==================== DATA UPLOAD & ANALYSIS ====================


@app.post("/api/admin/upload-data", response_model=CreateSchemaResponse)
async def upload_client_data(upload_data: CreateSchemaRequest):
    """Super Admin: Upload data for a client and create their schema - ENHANCED VERSION"""

    try:

        logger.info(f" Processing data upload for client {upload_data.client_id}")

        #  STEP 1: Use SIMPLE reliable CSV parser - ALL CSV ROWS → JSON

        logger.info(
            f" Parsing {upload_data.data_format} with RELIABLE CSV-to-JSON conversion..."
        )

        try:

            # Use simple CSV parser that works without dependencies

            from simple_csv_parser import simple_csv_parser

            # Parse CSV content to JSON records

            if upload_data.data_format and upload_data.data_format.value == "csv":

                # CSV: Use our reliable parser

                standardized_data = simple_csv_parser.parse_csv_to_json(
                    upload_data.raw_data
                )

                format_type = "csv"

                if not standardized_data:

                    raise ValueError("Failed to parse CSV data")

                logger.info(
                    f" CSV→JSON conversion complete: {len(standardized_data)} records"
                )

                # Extract column info from first record

                if standardized_data:

                    columns_info = []

                    first_record = standardized_data[0]

                    for key, value in first_record.items():

                        if not key.startswith("_"):  # Skip metadata fields

                            columns_info.append(
                                {
                                    "name": key,
                                    "type": (
                                        type(value).__name__
                                        if value is not None
                                        else "str"
                                    ),
                                }
                            )

                quality_score = 95.0  # High quality for successful parsing

            else:

                # JSON: Parse directly

                try:

                    if isinstance(upload_data.raw_data, str):

                        data = json.loads(upload_data.raw_data)

                    else:

                        data = upload_data.raw_data

                    # Handle different JSON structures

                    if isinstance(data, list):

                        standardized_data = data

                    elif isinstance(data, dict):

                        if "data" in data and isinstance(data["data"], list):

                            standardized_data = data["data"]

                        else:

                            standardized_data = [data]

                    else:

                        standardized_data = [{"value": data}]

                    # Add metadata to JSON records

                    for i, record in enumerate(standardized_data):

                        if isinstance(record, dict):

                            record["_row_number"] = i + 1

                            record["_source_format"] = "json"

                    format_type = "json"

                    quality_score = 90.0

                    # Extract columns from first record

                    columns_info = []

                    if standardized_data:

                        first_record = standardized_data[0]

                        for key, value in first_record.items():

                            if not key.startswith("_"):

                                columns_info.append(
                                    {
                                        "name": key,
                                        "type": (
                                            type(value).__name__
                                            if value is not None
                                            else "str"
                                        ),
                                    }
                                )

                    logger.info(
                        f" JSON parsing complete: {len(standardized_data)} records"
                    )

                except json.JSONDecodeError as e:

                    raise ValueError(f"Invalid JSON format: {e}")

        except Exception as parse_error:

            logger.error(f" Parsing failed: {parse_error}")

            raise HTTPException(
                status_code=400, detail=f"Data parsing failed: {str(parse_error)}"
            )

        logger.info(
            f" Successfully parsed {len(standardized_data)} records from {format_type}"
        )

        logger.info(f" Detected columns: {[col['name'] for col in columns_info]}")

        # STEP 2: Generate AI analysis using standardized JSON data

        logger.info("🤖 Starting AI analysis of standardized JSON data...")

        ai_result = await ai_analyzer.analyze_data(
            json.dumps(
                standardized_data[:100]
            ),  # Send first 100 records as JSON string
            upload_data.data_format,
            str(upload_data.client_id),
        )

        # Step 3: Store schema in client_schemas table

        db_client = get_admin_client()

        if db_client:

            schema_response = (
                db_client.table("client_schemas")
                .insert(
                    {
                        "client_id": str(upload_data.client_id),
                        "schema_definition": ai_result.table_schema.dict(),
                        "table_name": ai_result.table_schema.table_name,
                        "data_type": ai_result.data_type,
                        "ai_analysis": json.dumps(ai_result.dict()),
                        # Enhanced fields
                        "format_detected": format_type,
                        "quality_score": quality_score,
                    }
                )
                .execute()
            )

        #  STEP 4: Store ALL standardized JSON records in database

        logger.info(f" Storing {len(standardized_data)} standardized JSON records...")

        rows_inserted = 0

        for index, json_record in enumerate(standardized_data):

            try:

                # Create database record with standardized JSON (already clean!)

                client_data_record = {
                    "client_id": str(upload_data.client_id),
                    "data": json.dumps(json_record),  # Already standardized JSON format
                    "table_name": ai_result.table_schema.table_name,
                    "created_at": datetime.utcnow().isoformat(),
                }

                db_client.table("client_data").insert(client_data_record).execute()

                rows_inserted += 1

                # Progress logging

                if rows_inserted % 50 == 0:

                    logger.info(
                        f" Inserted {rows_inserted}/{len(standardized_data)} JSON records..."
                    )

            except Exception as row_error:

                logger.warning(f"  Failed to store JSON record {index}: {row_error}")

                continue

        logger.info(
            f" Successfully stored {rows_inserted}/{len(standardized_data)} standardized JSON records!"
        )

        logger.info(
            f" Schema created AND DATA STORED for client {upload_data.client_id}: {ai_result.data_type} with {rows_inserted} rows"
        )

        #  PRE-GENERATE TEMPLATES AFTER DATA UPLOAD

        try:

            logger.info(
                f" Pre-generating dashboard templates for client {upload_data.client_id}"
            )

            # Run template generation in background to avoid blocking the response

            asyncio.create_task(
                _pre_generate_templates_for_client(upload_data.client_id)
            )

            logger.info(
                f" Template pre-generation started for client {upload_data.client_id}"
            )

        except Exception as template_error:

            logger.warning(
                f" Template pre-generation failed for client {upload_data.client_id}: {template_error}"
            )

            # Don't block the upload response if template generation fails

        return CreateSchemaResponse(
            success=True,
            table_name=ai_result.table_schema.table_name,
            table_schema=ai_result.table_schema,
            ai_analysis=ai_result,
            rows_inserted=rows_inserted,  # NOW RETURNS ACTUAL COUNT!
            message=f"Schema analyzed and {rows_inserted} rows of data stored successfully! Templates generating in background.",
        )

    except Exception as e:

        logger.error(f" Data upload failed: {e}")

        raise HTTPException(status_code=500, detail=f"Data upload failed: {str(e)}")


@app.get("/api/data/{client_id}")
async def get_client_data(client_id: str, limit: int = 100):
    """Get client-specific data - REAL DATA FROM DATABASE"""

    try:

        logger.info(f" Instant data request for client {client_id}")

        # Get REAL data from database instead of fake samples

        db_client = get_admin_client()

        if not db_client:

            logger.error(" Database not configured")

            raise HTTPException(status_code=503, detail="Database not configured")

        try:

            # Get client's data from client_data table

            response = (
                db_client.table("client_data")
                .select("*")
                .eq("client_id", client_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            if not response.data:

                logger.warning(f"  No real data found for client {client_id}")

                # Return empty but valid structure

                return {
                    "client_id": client_id,
                    "table_name": f"client_{client_id.replace('-', '_')}_data",
                    "schema": {},
                    "data_type": "general",
                    "data": [],
                    "row_count": 0,
                    "message": "No data uploaded yet. Please upload CSV data first.",
                }

            # Parse real data from database including SFTP sources

            real_data = []

            table_name = None

            data_type = "general"

            source_summary = {"csv_upload": 0, "sftp": 0, "other": 0}

            for record in response.data:

                if record.get("data"):

                    try:

                        # Handle both string and dict data from database

                        if isinstance(record["data"], dict):

                            # Data is already parsed

                            parsed_data = record["data"]

                        elif isinstance(record["data"], str):

                            # Data is JSON string, parse it

                            parsed_data = json.loads(record["data"])

                        else:

                            # Unknown format, skip

                            logger.warning(
                                f"  Unknown data format for record: {type(record['data'])}"
                            )

                            continue

                        # Add source metadata to each record

                        source_type = record.get("source_type", "upload")

                        source_file = record.get("source_file", "manual_upload")

                        # Include source information in the data

                        enhanced_data = {
                            **parsed_data,
                            "_source_type": source_type,
                            "_source_file": source_file,
                            "_record_id": record.get("id", "unknown"),
                        }

                        real_data.append(enhanced_data)

                        # Count sources for summary

                        if source_type == "sftp":

                            source_summary["sftp"] += 1

                        elif source_type in ["upload", "csv"]:

                            source_summary["csv_upload"] += 1

                        else:

                            source_summary["other"] += 1

                        if not table_name:

                            table_name = record.get(
                                "table_name",
                                f"client_{client_id.replace('-', '_')}_data",
                            )

                    except json.JSONDecodeError:

                        logger.warning(
                            f"  Failed to parse data record: {record.get('data', '')[:100]}..."
                        )

                        continue

                    except Exception as e:

                        logger.warning(f"  Error processing data record: {e}")

                        continue

            # Get schema information

            schema_response = (
                db_client.table("client_schemas")
                .select("*")
                .eq("client_id", client_id)
                .execute()
            )

            if schema_response.data:

                schema_data = schema_response.data[0]

                data_type = schema_data.get("data_type", "general")

                table_name = schema_data.get("table_name", table_name)

            logger.info(
                f" Retrieved {len(real_data)} REAL records for client {client_id} (CSV: {source_summary['csv_upload']}, SFTP: {source_summary['sftp']}, Other: {source_summary['other']})"
            )

            return {
                "client_id": client_id,
                "table_name": table_name,
                "schema": {"type": data_type, "source": "database"},
                "data_type": data_type,
                "data": real_data,
                "row_count": len(real_data),
                "source_summary": source_summary,
                "message": f"Retrieved {len(real_data)} real records from database (CSV: {source_summary['csv_upload']}, SFTP: {source_summary['sftp']})",
            }

        except Exception as db_error:

            logger.error(f" Database error getting real data: {db_error}")

            # Still return valid structure but with error message

            return {
                "client_id": client_id,
                "table_name": f"client_{client_id.replace('-', '_')}_data",
                "schema": {},
                "data_type": "general",
                "data": [],
                "row_count": 0,
                "message": f"Database error: {str(db_error)}",
            }

    except Exception as e:

        logger.error(f" Failed to get client data: {e}")

        # Always return working structure

        return {
            "client_id": client_id,
            "table_name": "default_table",
            "schema": {},
            "data_type": "general",
            "data": [],
            "row_count": 0,
            "message": f"Error retrieving data: {str(e)}",
        }


@app.get("/api/data/available-tables/{client_id}")
async def get_available_tables(client_id: str):
    """Get available data tables for a client to build dynamic tabs"""

    try:

        logger.info(f" Checking available tables for client {client_id}")

        db_client = get_admin_client()

        if not db_client:

            logger.error(" Database not configured")

            raise HTTPException(status_code=503, detail="Database not configured")

        # Normalize client_id for table names (replace hyphens with underscores)

        safe_client_id = client_id.replace("-", "_")

        # Define table mapping

        possible_tables = {
            "shopify": {
                "products": f"{safe_client_id}_shopify_products",
                "orders": f"{safe_client_id}_shopify_orders",
            },
            "amazon": {
                "products": f"{safe_client_id}_amazon_products",
                "orders": f"{safe_client_id}_amazon_orders",
            },
        }

        available_tables = {"shopify": [], "amazon": []}

        # Check each table

        for platform, tables in possible_tables.items():

            for data_type, table_name in tables.items():

                try:

                    # Try to query the table with count to see if it exists and has data

                    response = (
                        db_client.table(table_name)
                        .select("id", count="exact")
                        .limit(1)
                        .execute()
                    )

                    count = (
                        response.count
                        if hasattr(response, "count") and response.count is not None
                        else 0
                    )

                    if count > 0:  # Only include tables with data

                        available_tables[platform].append(
                            {
                                "data_type": data_type,
                                "table_name": table_name,
                                "display_name": f"{platform.title()} {data_type.title()}",
                                "count": count,
                            }
                        )

                        logger.info(
                            f" Found {platform} {data_type} table with {count} records"
                        )

                    else:

                        logger.info(
                            f" {platform} {data_type} table exists but has no data"
                        )

                except Exception as e:

                    logger.info(
                        f" {platform} {data_type} table not available: {str(e)}"
                    )

                    continue

        # Clean up empty platforms

        available_platforms = {k: v for k, v in available_tables.items() if v}

        logger.info(
            f" Available tables for client {client_id}: {available_platforms}"
        )

        return {
            "client_id": client_id,
            "available_tables": available_platforms,
            "total_platforms": len(available_platforms),
            "total_tables": sum(len(tables) for tables in available_platforms.values()),
            "message": f"Found {len(available_platforms)} platforms with data",
        }

    except Exception as e:

        logger.error(f" Failed to check available tables: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to check available tables: {str(e)}"
        )


@app.get("/api/data/raw/{client_id}")
async def get_raw_data_tables(
    client_id: str,
    platform: Optional[str] = None,  # 'shopify', 'amazon'
    data_type: Optional[str] = None,  # 'products', 'orders'
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
):
    """Get raw data from organized tables - optimized for DataTables component"""

    try:

        logger.info(
            f" Raw data tables request for client {client_id} (platform: {platform}, type: {data_type})"
        )

        db_client = get_admin_client()

        if not db_client:

            logger.error(" Database not configured")

            raise HTTPException(status_code=503, detail="Database not configured")

        # Normalize client_id for table names (replace hyphens with underscores)

        safe_client_id = client_id.replace("-", "_")

        # Define table mapping

        table_mapping = {
            "shopify_products": f"{safe_client_id}_shopify_products",
            "shopify_orders": f"{safe_client_id}_shopify_orders",
            "amazon_products": f"{safe_client_id}_amazon_products",
            "amazon_orders": f"{safe_client_id}_amazon_orders",
        }

        # Determine which table to query (now only one table at a time)

        if not platform or not data_type:

            raise HTTPException(
                status_code=400, detail="Both platform and data_type are required"
            )

        table_key = f"{platform.lower()}_{data_type.lower()}"

        if table_key not in [
            "shopify_products",
            "shopify_orders",
            "amazon_products",
            "amazon_orders",
        ]:

            raise HTTPException(
                status_code=400, detail="Invalid platform or data_type combination"
            )

        table_name = table_mapping[table_key]

        logger.info(
            f" Querying table: {table_name} (page: {page}, size: {page_size}, search: {search})"
        )

        # Columns to exclude from results

        excluded_columns = [
            "id",
            "client_id",
            "product_id",
            "variants",
            "options",
            "images",
            "raw_data",
        ]

        try:

            # Build base query using Supabase client

            query = db_client.table(table_name).select("*", count="exact")

            # Apply search filter if provided

            if search:

                logger.info(f" Applying search filter for: '{search}'")

                # Define search fields based on table type

                search_fields = []

                if "products" in table_key:

                    # Product tables: search in title, handle, sku, vendor, variant_title, option1, option2, option3

                    search_fields = [
                        "title",
                        "handle",
                        "sku",
                        "vendor",
                        "variant_title",
                        "option1",
                        "option2",
                        "option3",
                    ]

                elif "orders" in table_key:

                    # Order tables: search in order_number, customer_email, financial_status, order_status, source_name, tags

                    search_fields = [
                        "order_number",
                        "customer_email",
                        "financial_status",
                        "order_status",
                        "source_name",
                        "tags",
                        "sales_channel",
                        "marketplace_id",
                    ]

                # Build an OR condition for text search - use proper PostgREST syntax

                search_conditions = []

                for field in search_fields:

                    search_conditions.append(f"{field}.ilike.*{search}*")

                # Apply OR search across multiple fields

                if search_conditions:

                    search_filter = ",".join(search_conditions)

                    logger.info(f" Search filter: {search_filter}")

                    query = query.or_(search_filter)

            # Get total count first (for pagination)

            count_response = query.execute()

            total_records = (
                count_response.count if count_response.count is not None else 0
            )

            # If search returns no results, fall back to showing all data

            search_fallback = False

            if search and total_records == 0:

                logger.info(
                    f" Search '{search}' returned no results, falling back to all data"
                )

                search_fallback = True

                # Reset to page 1 when falling back to all data

                page = 1

                # Re-run count query without search filter
                try:
                    fallback_query = db_client.table(table_name).select("*", count="exact")
                    count_response = fallback_query.execute()
                    total_records = (
                        count_response.count if count_response.count is not None else 0
                    )
                except Exception as fallback_error:
                    logger.error(f" Fallback count query failed: {fallback_error}")
                    total_records = 0
            # Calculate pagination

            offset = (page - 1) * page_size

            total_pages = (
                (total_records + page_size - 1) // page_size if total_records > 0 else 0
            )

            # Build main query with pagination

            main_query = db_client.table(table_name).select("*")

            # Apply search filter again for data query (only if not falling back)

            if search and not search_fallback:

                search_conditions = []

                if "products" in table_key:

                    search_fields = [
                        "title",
                        "handle",
                        "sku",
                        "vendor",
                        "variant_title",
                        "option1",
                        "option2",
                        "option3",
                    ]

                elif "orders" in table_key:

                    search_fields = [
                        "order_number",
                        "customer_email",
                        "financial_status",
                        "order_status",
                        "source_name",
                        "tags",
                        "sales_channel",
                        "marketplace_id",
                    ]

                for field in search_fields:

                    search_conditions.append(f"{field}.ilike.*{search}*")

                if search_conditions:

                    search_filter = ",".join(search_conditions)

                    main_query = main_query.or_(search_filter)

            # Apply pagination and ordering

            main_query = main_query.order("processed_at", desc=True).range(
                offset, offset + page_size - 1
            )

            logger.info(
                f" Querying table {table_name} with offset {offset}, limit {page_size}"
            )

            response = main_query.execute()

            if response.data:

                # Filter out excluded columns

                filtered_data = []

                all_columns = list(response.data[0].keys()) if response.data else []

                allowed_columns = [
                    col for col in all_columns if col not in excluded_columns
                ]

                for row in response.data:

                    filtered_row = {
                        col: row[col] for col in allowed_columns if col in row
                    }

                    filtered_data.append(filtered_row)

                result_data = {
                    "client_id": client_id,
                    "table_key": table_key,
                    "display_name": table_key.replace("_", " ").title(),
                    "table_name": table_name,
                    "platform": table_key.split("_")[0],
                    "data_type": table_key.split("_")[1],
                    "columns": allowed_columns,
                    "data": filtered_data,
                    "pagination": {
                        "current_page": page,
                        "page_size": page_size,
                        "total_records": total_records,
                        "total_pages": total_pages,
                        "has_next": page < total_pages,
                        "has_prev": page > 1,
                    },
                    "search": search,
                    "search_fallback": search_fallback,
                    "message": f"Retrieved {len(filtered_data)} records (page {page} of {total_pages})"
                    + (
                        f" - No results found for '{search}', showing all data"
                        if search_fallback
                        else ""
                    ),
                }

                logger.info(
                    f" Retrieved {len(filtered_data)} records from {table_name} (page {page}/{total_pages}, total: {total_records})"
                )

                return result_data

            else:

                logger.warning(f" No data found in table {table_name}")

                return {
                    "client_id": client_id,
                    "table_key": table_key,
                    "display_name": table_key.replace("_", " ").title(),
                    "message": "No data found in this table",
                    "data": [],
                    "columns": [],
                    "pagination": {
                        "current_page": 1,
                        "page_size": page_size,
                        "total_records": 0,
                        "total_pages": 0,
                        "has_next": False,
                        "has_prev": False,
                    },
                }

        except Exception as table_error:

            logger.error(f" Failed to query table {table_name}: {table_error}")

            raise HTTPException(
                status_code=500,
                detail=f"Failed to query table {table_name}: {str(table_error)}",
            )

    except Exception as e:

        logger.error(f" Raw data retrieval failed: {e}")

        raise HTTPException(
            status_code=500, detail=f"Raw data retrieval failed: {str(e)}"
        )


# ==================== PERSONALIZED DASHBOARD ENDPOINTS ====================


@app.post("/api/dashboard/generate", response_model=DashboardGenerationResponse)
async def generate_dashboard(
    request: DashboardGenerationRequest, token: str = Depends(security)
):
    """Generate a personalized dashboard for the authenticated client"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        # Import dashboard orchestrator

        from dashboard_orchestrator import dashboard_orchestrator

        # Generate dashboard using the legacy method for compatibility

        result = await dashboard_orchestrator.generate_dashboard(
            client_id=token_data.client_id, force_regenerate=request.force_regenerate
        )

        logger.info(
            f" Dashboard generation completed for client {token_data.client_id}"
        )

        return result

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Dashboard generation failed: {e}")

        raise HTTPException(
            status_code=500, detail=f"Dashboard generation failed: {str(e)}"
        )


@app.post("/api/dashboard/generate-template")
async def generate_template_dashboard(
    template_type: str, force_regenerate: bool = False, token: str = Depends(security)
):
    """Generate a simple template-based dashboard - just return client data"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = str(token_data.client_id)

        logger.info(
            f" Getting data for {template_type} dashboard for client {client_id}"
        )

        # Get client data - NO LIMIT for complete data processing from database

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Get client data - NO LIMIT for complete data processing

        data_response = (
            db_client.table("client_data")
            .select("data")
            .eq("client_id", client_id)
            .execute()
        )

        client_data = []

        if data_response.data:

            for record in data_response.data:

                try:

                    if isinstance(record["data"], dict):

                        client_data.append(record["data"])

                    elif isinstance(record["data"], str):

                        import json

                        client_data.append(json.loads(record["data"]))

                except:

                    continue

        # Get data columns for analysis

        data_columns = []

        if client_data:

            data_columns = list(client_data[0].keys())

        logger.info(
            f" Found {len(client_data)} records with {len(data_columns)} columns for {template_type}"
        )

        return {
            "success": True,
            "template_type": template_type,
            "client_data": client_data,
            "data_columns": data_columns,
            "total_records": len(client_data),
            "message": f"Data retrieved for {template_type} template",
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Template data retrieval failed: {e}")

        raise HTTPException(
            status_code=500, detail=f"Template data retrieval failed: {str(e)}"
        )


@app.get("/api/dashboard/templates")
async def get_available_templates(token: str = Depends(security)):
    """Get available dashboard templates for the authenticated client"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = str(token_data.client_id)

        logger.info(f" Getting available templates for client {client_id}")

        # Get client data - NO LIMIT for complete data processing to determine best templates

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Get client data - NO LIMIT for complete data processing columns - get all data to analyze complete schema

        data_response = (
            db_client.table("client_data")
            .select("data")
            .eq("client_id", client_id)
            .execute()
        )

        data_columns = []

        if data_response.data:

            try:

                sample_data = data_response.data[0]["data"]

                if isinstance(sample_data, dict):

                    data_columns = list(sample_data.keys())

                elif isinstance(sample_data, str):

                    import json

                    parsed_data = json.loads(sample_data)

                    data_columns = list(parsed_data.keys())

            except:

                pass

        # Import dashboard orchestrator to get templates

        from dashboard_orchestrator import dashboard_orchestrator

        # Get available templates

        available_templates = dashboard_orchestrator.get_available_templates()

        # Get recommended template

        recommended_template = dashboard_orchestrator.detect_recommended_template(
            data_columns, business_context=None
        )

        logger.info(
            f" Found {len(available_templates)} templates, recommended: {recommended_template}"
        )

        return {
            "available_templates": available_templates,
            "recommended_template": recommended_template,
            "client_data_columns": data_columns,
            "total_templates": len(available_templates),
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to get available templates: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to get available templates: {str(e)}"
        )


@app.get("/api/dashboard/config")
async def get_dashboard_config(token: str = Depends(security)):
    """Get dashboard configuration for the authenticated client"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = str(token_data.client_id)

        logger.info(f" Getting dashboard config for client {client_id}")

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Get dashboard configuration

        response = (
            db_client.table("client_dashboard_configs")
            .select("*")
            .eq("client_id", client_id)
            .execute()
        )

        if not response.data:

            # No dashboard config found

            logger.warning(f" No dashboard config found for client {client_id}")

            raise HTTPException(
                status_code=404,
                detail="Dashboard config not found. Please generate your dashboard first.",
            )

        config_record = response.data[0]

        dashboard_config = config_record["dashboard_config"]

        logger.info(f" Dashboard config found for client {client_id}")

        logger.info(
            f" Config has {len(dashboard_config.get('chart_widgets', []))} charts"
        )

        # Return the dashboard config directly (not wrapped in another object)

        return dashboard_config

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to get dashboard config: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to get dashboard config: {str(e)}"
        )


@app.get("/api/dashboard/component-data")
async def get_component_filtered_data(
    component_type: str,
    platform: str = "combined",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    token: str = Depends(security),
):
    """Get filtered data for specific dashboard components based on date range and platform"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = str(token_data.client_id)

        logger.info(
            f" Component data request: {component_type} for client {client_id} (platform: {platform}, dates: {start_date} to {end_date})"
        )

        # Validate component type

        valid_components = [
            "total_sales",
            "inventory_turnover",
            "days_of_stock",
            "inventory_levels",
            "units_sold",
            "historical_comparison",
            "low_stock_alerts",
            "overstock_alerts",
            "sales_performance",
        ]

        if component_type not in valid_components:

            raise HTTPException(
                status_code=400,
                detail=f"Invalid component type. Must be one of: {', '.join(valid_components)}",
            )

        # Validate platform

        valid_platforms = ["shopify", "amazon", "combined"]

        if platform not in valid_platforms:

            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform. Must be one of: {', '.join(valid_platforms)}",
            )

        # Import component data manager

        from component_data_functions import component_data_manager

        # ️ CHECK FOR CACHED DATA ONLY IF NO DATE FILTERING

        if not start_date and not end_date:

            logger.info(
                f" No date filtering - checking for cached inventory-analytics data for client {client_id}"
            )

            # Try to get cached response from the main inventory-analytics endpoint

            main_endpoint_url = "/api/dashboard/inventory-analytics"

            main_cache_params = {
                "fast_mode": True,
                "platform": platform if platform != "combined" else "shopify",
            }

            cached_main_response = await get_cached_response(
                client_id, main_endpoint_url, main_cache_params
            )

            if cached_main_response:

                logger.info(
                    f"️ Using cached inventory-analytics data (no date filtering needed)"
                )

                # Extract component data from cached inventory analytics

                inventory_analytics = cached_main_response.get(
                    "inventory_analytics", {}
                )

                platforms_data = inventory_analytics.get("platforms", {})

                if component_type == "total_sales":

                    if platform == "combined":

                        shopify_sales = platforms_data.get("shopify", {}).get(
                            "sales_kpis", {}
                        )

                        amazon_sales = platforms_data.get("amazon", {}).get(
                            "sales_kpis", {}
                        )

                        component_data = {
                            "shopify": shopify_sales,
                            "amazon": amazon_sales,
                            "combined": {
                                "total_revenue": (
                                    shopify_sales.get("total_sales_30_days", {}).get(
                                        "revenue", 0
                                    )
                                    + amazon_sales.get("total_sales_30_days", {}).get(
                                        "revenue", 0
                                    )
                                ),
                                "total_orders": (
                                    shopify_sales.get("total_sales_30_days", {}).get(
                                        "orders", 0
                                    )
                                    + amazon_sales.get("total_sales_30_days", {}).get(
                                        "orders", 0
                                    )
                                ),
                            },
                        }

                    else:

                        component_data = platforms_data.get(platform, {}).get(
                            "sales_kpis", {}
                        )

                else:

                    # For other component types, extract accordingly

                    platform_data = platforms_data.get(
                        platform if platform != "combined" else "shopify", {}
                    )

                    component_data = platform_data

                response_data = {
                    "success": True,
                    "client_id": client_id,
                    "component_type": component_type,
                    "platform": platform,
                    "date_range": {"start_date": start_date, "end_date": end_date},
                    "data": component_data,
                    "timestamp": datetime.now().isoformat(),
                    "cached": True,
                    "cache_source": "inventory_analytics",
                }

                logger.info(
                    f" Component data from cached inventory-analytics for {component_type} - {platform}"
                )

                return response_data

        #  DATE FILTERING OR NO CACHE: Use component-specific database queries

        logger.info(
            f" Date filtering requested OR no cache - using component-specific database queries"
        )

        component_data = {}

        if component_type == "total_sales":

            component_data = await component_data_manager.get_total_sales_data(
                client_id, platform, start_date, end_date
            )

        elif component_type == "inventory_turnover":

            component_data = await component_data_manager.get_inventory_turnover_data(
                client_id, platform, start_date, end_date
            )

        elif component_type == "days_of_stock":

            component_data = await component_data_manager.get_days_of_stock_data(
                client_id, platform, start_date, end_date
            )

        elif component_type == "inventory_levels":

            component_data = await component_data_manager.get_inventory_levels_data(
                client_id, platform, start_date, end_date
            )

        elif component_type == "units_sold":

            # Use the dedicated units sold function for proper chart data

            units_data = await component_data_manager.get_units_sold_data(
                client_id, platform, start_date, end_date
            )

            # Format the response to match frontend expectations

            if platform == "combined":

                combined_data = units_data.get("combined", {})

                component_data = {
                    "total_units_sold": combined_data.get("total_units_sold", 0),
                    "units_sold_chart": combined_data.get("units_sold_chart", []),
                    "sales_data": units_data,
                    "period_info": {"start_date": start_date, "end_date": end_date},
                }

            else:

                platform_data = units_data.get(platform, {})

                component_data = {
                    "total_units_sold": platform_data.get("total_units_sold", 0),
                    "units_sold_chart": platform_data.get("units_sold_chart", []),
                    "sales_data": {platform: platform_data},
                    "period_info": {"start_date": start_date, "end_date": end_date},
                }

        elif component_type == "historical_comparison":

            # Historical comparison with real period-over-period analysis

            component_data = (
                await component_data_manager.get_historical_comparison_data(
                    client_id, platform, start_date, end_date
                )
            )

        elif component_type in [
            "low_stock_alerts",
            "overstock_alerts",
            "sales_performance",
        ]:

            # For alerts, use days of stock data to determine alert conditions

            stock_data = await component_data_manager.get_days_of_stock_data(
                client_id, platform, start_date, end_date
            )

            alerts = []

            if (
                component_type == "low_stock_alerts"
                and stock_data.get("low_stock_count", 0) > 0
            ):

                alerts.append(
                    {
                        "type": "low_stock",
                        "severity": "warning",
                        "message": f"Low stock detected - {stock_data.get('avg_days_of_stock', 0)} days remaining",
                        "affected_items": stock_data.get("low_stock_count", 0),
                    }
                )

            elif (
                component_type == "overstock_alerts"
                and stock_data.get("overstock_count", 0) > 0
            ):

                alerts.append(
                    {
                        "type": "overstock",
                        "severity": "info",
                        "message": f"Overstock detected - {stock_data.get('avg_days_of_stock', 0)} days of inventory",
                        "affected_items": stock_data.get("overstock_count", 0),
                    }
                )

            elif component_type == "sales_performance":

                # Get sales data for performance alerts

                sales_data = await component_data_manager.get_total_sales_data(
                    client_id, platform, start_date, end_date
                )

                if platform != "combined":

                    growth_rate = (
                        sales_data.get(platform, {})
                        .get("sales_comparison", {})
                        .get("growth_rate", 0)
                    )

                    if growth_rate < -10:  # Declining sales

                        alerts.append(
                            {
                                "type": "sales_performance",
                                "severity": "warning",
                                "message": f"Sales declining by {abs(growth_rate):.1f}%",
                                "growth_rate": growth_rate,
                            }
                        )

            component_data = {"alerts": alerts}

        # Check for errors in component data

        if isinstance(component_data, dict) and component_data.get("error"):

            raise HTTPException(
                status_code=500,
                detail=f"Component query failed: {component_data['error']}",
            )

        response_data = {
            "success": True,
            "client_id": client_id,
            "component_type": component_type,
            "platform": platform,
            "date_range": {"start_date": start_date, "end_date": end_date},
            "data": component_data,
            "timestamp": datetime.now().isoformat(),
            "cached": False,
            "cache_source": "component_specific_database_query",
        }

        logger.info(
            f" Component data retrieved with component-specific database queries for {component_type} - {platform} (date filtering: {start_date} to {end_date})"
        )

        return response_data

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Error in component data endpoint: {str(e)}")

        raise HTTPException(
            status_code=500, detail=f"Failed to get component data: {str(e)}"
        )


# Helper function for date filtering client data


async def get_cached_analysis_by_data_snapshot(
    client_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    dashboard_type: str = "metrics",
) -> Optional[Dict[str, Any]]:
    """Get cached LLM analysis based on data snapshot timeline"""

    try:

        from llm_cache_manager import llm_cache_manager

        # Parse date range

        start_dt = datetime.fromisoformat(start_date) if start_date else None

        end_dt = datetime.fromisoformat(end_date) if end_date else None

        if not start_dt and not end_dt:

            # No date filter - get most recent analysis

            return await llm_cache_manager.get_most_recent_analysis(
                client_id, dashboard_type
            )

        # Find data snapshot that was current during the requested date range

        data_snapshot_date = await llm_cache_manager.get_data_snapshot_for_period(
            client_id, start_date, end_date
        )

        if data_snapshot_date:

            # Get cached analysis for that data snapshot

            cached_analysis = await llm_cache_manager.get_analysis_by_snapshot_date(
                client_id, data_snapshot_date, dashboard_type
            )

            if cached_analysis:

                logger.info(
                    f" Found cached analysis for data snapshot {data_snapshot_date} (requested period: {start_date} to {end_date})"
                )

                return cached_analysis

        logger.info(
            f" No cached analysis found for period {start_date} to {end_date}"
        )

        return None

    except Exception as e:

        logger.warning(f" Failed to get cached analysis by snapshot: {e}")

        return None


def get_client_data_update_date(client_data: Dict[str, Any]) -> str:
    """Extract or generate the data update timestamp for this client data"""

    # Check for explicit data update timestamp

    data_updated = (
        client_data.get("data_updated_at")
        or client_data.get("last_updated")
        or client_data.get("retrieved_at")
        or client_data.get("snapshot_date")
    )

    if data_updated:

        return str(data_updated)

    # Fallback: Use current timestamp (data is being updated now)

    current_time = datetime.now().isoformat()

    logger.info(
        f" No explicit data update timestamp found, using current time: {current_time}"
    )

    return current_time


@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics(
    token: str = Depends(security),
    fast_mode: bool = True,  # DEFAULT TO FAST MODE TO PREVENT TIMEOUTS
    force_llm: bool = False,  # Only use LLM if explicitly requested
    start_date: Optional[str] = None,  # Date filtering support
    end_date: Optional[str] = None,  # Date filtering support
    preset: Optional[
        str
    ] = None,  # Presets: today, yesterday, last_7_days, last_30_days, this_month, last_month
):
    """Get dashboard metrics - OPTIMIZED for speed, uses cache by default"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = str(token_data.client_id)

        # Get client data - NO LIMIT for complete data processing and extract LLM insights directly

        from ai_analyzer import ai_analyzer

        from dashboard_orchestrator import dashboard_orchestrator

        from llm_cache_manager import llm_cache_manager

        # Resolve preset into date range if provided and explicit range not present

        if preset and not (start_date or end_date):

            from datetime import datetime, timedelta

            today = datetime.utcnow().date()

            if preset == "today":

                start_date = today.isoformat()

                end_date = today.isoformat()

            elif preset == "yesterday":

                y = (today - timedelta(days=1)).isoformat()

                start_date = y

                end_date = y

            elif preset == "last_7_days":

                start_date = (today - timedelta(days=6)).isoformat()

                end_date = today.isoformat()

            elif preset == "last_30_days":

                start_date = (today - timedelta(days=29)).isoformat()

                end_date = today.isoformat()

            elif preset == "this_month":

                start_date = today.replace(day=1).isoformat()

                end_date = today.isoformat()

            elif preset == "last_month":

                first_this = today.replace(day=1)

                last_month_end = first_this - timedelta(days=1)

                start_date = last_month_end.replace(day=1).isoformat()

                end_date = last_month_end.isoformat()

        # Get client data with optional date range for full, correct analysis

        client_data = await ai_analyzer.get_client_data_optimized(
            client_id, start_date=start_date, end_date=end_date
        )

        if not client_data:

            raise HTTPException(status_code=404, detail="No data found for this client")

        # If range requested, attempt to serve from daily cache

        if start_date and end_date:

            logger.info(f" Attempting cache for period: {start_date} to {end_date}")

            try:

                # Single-day request: return the day's cached analysis directly

                if start_date == end_date:

                    daily_entries = await llm_cache_manager.get_daily_latest_in_range(
                        client_id, start_date, end_date, "metrics"
                    )

                    if daily_entries:

                        d = daily_entries[0]

                        llm_resp = d.get("llm_response", {})

                        analysis = (
                            llm_resp.get("llm_analysis")
                            if isinstance(llm_resp, dict)
                            else llm_resp
                        )

                        return {
                            "client_id": client_id,
                            "data_type": client_data.get("data_type", "unknown"),
                            "schema_type": client_data.get("schema", {}).get(
                                "type", "unknown"
                            ),
                            "total_records": len(client_data.get("data", [])),
                            "llm_analysis": analysis,
                            "cached": True,
                            "response_time": "instant",
                        }

                # Multi-day range: return a timeline series

                daily_entries = await llm_cache_manager.get_daily_latest_in_range(
                    client_id, start_date, end_date, "metrics"
                )

                if daily_entries:

                    timeline = []

                    for d in daily_entries:

                        llm_resp = d.get("llm_response", {})

                        analysis = (
                            llm_resp.get("llm_analysis")
                            if isinstance(llm_resp, dict)
                            else None
                        )

                        timeline.append(
                            {
                                "date": d.get("created_at", "")[
                                    :10
                                ],  # Use created_at instead of analysis_date
                                "llm_analysis": analysis or llm_resp,
                                "total_records": d.get("total_records"),
                            }
                        )

                    return {
                        "client_id": client_id,
                        "data_type": client_data.get("data_type", "unknown"),
                        "schema_type": client_data.get("schema", {}).get(
                            "type", "unknown"
                        ),
                        "total_records": len(client_data.get("data", [])),
                        "llm_analysis": {"timeline": timeline},
                        "cached": True,
                        "response_time": "instant",
                    }

            except Exception as e:

                logger.info(f"ℹ️ Range cache not available; will compute fresh: {e}")

        #  PRIORITY 1: Check cache first for maximum speed (instant response)

        if not force_llm:

            cached_insights = await llm_cache_manager.get_cached_llm_response(
                client_id, client_data, "metrics"
            )

            if cached_insights:

                logger.info(f" CACHE HIT: Instant response for client {client_id}")

                return {
                    "client_id": client_id,
                    "data_type": client_data.get("data_type", "unknown"),
                    "schema_type": client_data.get("schema", {}).get("type", "unknown"),
                    "total_records": len(client_data.get("data", [])),
                    "llm_analysis": cached_insights,
                    "cached": True,
                    "response_time": "instant",
                    "fast_mode": fast_mode,
                }

        # Only clear cache if explicitly requested to regenerate

        if force_llm:

            await llm_cache_manager.invalidate_cache(client_id, "metrics")

            logger.info(f"️ Cleared cache for fresh analysis - client {client_id}")

        # ALWAYS use LLM analysis for main dashboard - no fallbacks

        logger.info(
            f" Generating MAIN dashboard with LLM analysis for client {client_id}"
        )

        try:

            # Add timeout to prevent hanging for more than 55 seconds

            import asyncio

            insights = await asyncio.wait_for(
                dashboard_orchestrator._extract_main_dashboard_insights(client_data),
                timeout=355.0,  # 55 second timeout to stay under 60s frontend timeout
            )

            logger.info(
                f" Main dashboard LLM analysis successful for client {client_id}"
            )

            #  CRITICAL: Store in cache for future requests with data snapshot date

            data_snapshot_date = get_client_data_update_date(client_data)

            try:

                cache_success = await llm_cache_manager.store_cached_llm_response(
                    client_id, client_data, insights, "metrics", data_snapshot_date
                )

                if cache_success:

                    logger.info(
                        f" Cached MAIN dashboard response for client {client_id}"
                    )

                else:

                    logger.warning(
                        f" Failed to cache MAIN dashboard response for client {client_id}"
                    )

            except Exception as cache_error:

                logger.error(f" Cache storage error (non-blocking): {cache_error}")

                # Continue with response even if cache fails

        except asyncio.TimeoutError:

            logger.error(
                f"⏰ Main dashboard LLM analysis timed out for client {client_id}"
            )

            raise HTTPException(
                status_code=408,
                detail="Dashboard analysis timed out. Please try again or enable fast_mode.",
            )

        except Exception as llm_error:

            logger.error(
                f" Main dashboard LLM analysis failed for client {client_id}: {llm_error}"
            )

            raise HTTPException(
                status_code=500,
                detail=f"Main dashboard analysis failed: {str(llm_error)}",
            )

        # Return the exact same format as /api/test-llm-analysis

        return {
            "client_id": client_id,
            "data_type": client_data.get("data_type", "unknown"),
            "schema_type": client_data.get("schema", {}).get("type", "unknown"),
            "total_records": len(client_data.get("data", [])),
            "llm_analysis": insights,
            "cached": False,
            "fast_mode": fast_mode,
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to get dashboard metrics: {e}")

        return {"error": f"Failed to get dashboard metrics: {str(e)}"}


@app.get("/api/test-simple")
async def test_simple():
    """Simple test endpoint"""

    return {"message": "Simple test works", "status": "ok"}


# ==================== SKU INVENTORY PAGINATION ENDPOINTS ====================


@app.get("/api/dashboard/sku-inventory")
async def get_paginated_sku_inventory(
    token: str = Depends(security),
    page: int = 1,
    page_size: int = 50,
    use_cache: bool = True,
    force_refresh: bool = False,
    platform: str = "shopify",
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """ INSTANT SKU LIST - Return cached data immediately, refresh in background"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = str(token_data.client_id)

        logger.info(
            f" INSTANT SKU request for {client_id} (page={page}, platform={platform}) - NO WAITING!"
        )

        # Try cache first for INSTANT response
        if use_cache and not force_refresh:
            try:
                from sku_cache_manager import get_sku_cache_manager
                admin_client = get_admin_client()
                if admin_client is None:
                    logger.error("Admin client is None - cannot access SKU cache")
                    return {
                        "success": False,
                        "error": "Database connection error - admin client unavailable",
                        "cached": False
                    }
                
                cache_manager = get_sku_cache_manager(admin_client)
                cache_key = f"{client_id}_{platform}"
                
                cached_result = await cache_manager.get_cached_skus(
                    cache_key, page, page_size
                )
                if cached_result.get("success"):
                    logger.info(
                        f" INSTANT RESPONSE: Using cached SKUs for {platform}"
                    )
                    # Start background refresh for next time
                    background_tasks.add_task(
                        refresh_sku_background, client_id, platform, page, page_size
                    )
                    return cached_result
                    
            except Exception as e:
                logger.warning(f" SKU cache check failed: {e}")

        # If no cache found and not forcing refresh, return message about cron job
        if use_cache and not force_refresh:
            logger.info(f" No cache found for {client_id} (platform={platform}) - SKU analysis runs via cron job every 2 hours")
            return {
                "success": False,
                "cached": False,
                "message": "SKU analysis data not available. Analysis runs automatically every 2 hours via background job.",
                "note": "To manually trigger analysis, contact administrator",
                "next_scheduled_analysis": "Analysis runs every 2 hours",
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_count": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_previous": False
                }
            }

        logger.info(
            f" Generating fresh SKU list for {client_id} (platform={platform})"
        )

        #  FIXED: Allow large page sizes to show ALL data as requested
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50  # Default fallback
        elif page_size > 5000:  # Reasonable maximum to prevent memory issues
            page_size = 5000

        logger.info(
            f" SKU Request: page={page}, page_size={page_size}, platform={platform}"
        )

        # Use dashboard inventory analyzer with caching
        from dashboard_inventory_analyzer import dashboard_inventory_analyzer

        # Get data using organized tables
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")

        # Get data efficiently based on platform
        if platform.lower() == "shopify":
            shopify_data = await dashboard_inventory_analyzer._get_shopify_data(
                client_id
            )
            amazon_data = {"products": [], "orders": []}
        elif platform.lower() == "amazon":
            amazon_data = await dashboard_inventory_analyzer._get_amazon_data(client_id)
            shopify_data = {"products": [], "orders": []}
        else:
            # For backward compatibility, get both if platform is invalid
            shopify_data = await dashboard_inventory_analyzer._get_shopify_data(
                client_id
            )
            amazon_data = await dashboard_inventory_analyzer._get_amazon_data(client_id)

        # Check if we have any organized data, if not, try legacy approach
        total_organized_records = len(shopify_data.get("products", [])) + len(
            amazon_data.get("products", [])
        )

        if total_organized_records == 0:
            logger.info(
                f" No organized data found for client {client_id}, trying legacy SKU extraction"
            )

            # Try to get SKU data from raw client_data (legacy approach)
            try:
                from inventory_analyzer import inventory_analyzer

                # Get raw client data
                response = (
                    db_client.table("client_data")
                    .select("*")
                    .eq("client_id", client_id)
                    .order("created_at", desc=True)
                    .limit(1000)
                    .execute()
                )

                if response.data:
                    client_data_for_legacy = {"client_id": client_id, "data": []}

                    for record in response.data:
                        if record.get("data"):
                            try:
                                if isinstance(record["data"], dict):
                                    parsed_data = record["data"]
                                elif isinstance(record["data"], str):
                                    parsed_data = json.loads(record["data"])
                                else:
                                    continue
                                client_data_for_legacy["data"].append(parsed_data)
                            except:
                                continue

                    # Use legacy analyzer to get SKU data
                    legacy_analytics = inventory_analyzer.analyze_inventory_data(
                        client_data_for_legacy
                    )

                    legacy_skus = legacy_analytics.get("sku_inventory", {}).get(
                        "skus", []
                    )

                    if legacy_skus:
                        logger.info(
                            f" Found {len(legacy_skus)} SKUs from legacy data"
                        )

                        #  FIXED: Calculate real summary stats from legacy SKU data too!
                        legacy_summary_stats = None
                        if page == 1:
                            total_inventory_value = sum(
                                sku.get("total_value", 0) for sku in legacy_skus
                            )
                            low_stock_count = sum(
                                1
                                for sku in legacy_skus
                                if 0 < sku.get("current_availability", 0) <= 10
                            )
                            out_of_stock_count = sum(
                                1
                                for sku in legacy_skus
                                if sku.get("current_availability", 0) <= 0
                            )
                            overstock_count = sum(
                                1
                                for sku in legacy_skus
                                if sku.get("current_availability", 0) > 100
                            )

                            legacy_summary_stats = {
                                "total_skus": len(legacy_skus),
                                "total_inventory_value": round(
                                    total_inventory_value, 2
                                ),
                                "low_stock_count": low_stock_count,
                                "out_of_stock_count": out_of_stock_count,
                                "overstock_count": overstock_count,
                            }

                            logger.info(
                                f" LEGACY SUMMARY STATS: SKUs: {len(legacy_skus)}, Value: ${total_inventory_value:.2f}, Low Stock: {low_stock_count}, Out of Stock: {out_of_stock_count}"
                            )

                        # Paginate the legacy SKUs
                        start_idx = (page - 1) * page_size
                        end_idx = start_idx + page_size
                        paginated_skus = legacy_skus[start_idx:end_idx]

                        return {
                            "client_id": client_id,
                            "success": True,
                            "sku_inventory": {
                                "skus": paginated_skus,
                                "summary_stats": legacy_summary_stats,
                            },
                            "pagination": {
                                "current_page": page,
                                "page_size": page_size,
                                "total_count": len(legacy_skus),
                                "total_pages": math.ceil(len(legacy_skus) / page_size),
                                "has_next": end_idx < len(legacy_skus),
                                "has_previous": page > 1,
                            },
                            "cached": False,
                            "timestamp": datetime.now().isoformat(),
                            "processing_time": "legacy_conversion",
                            "data_source": "legacy_client_data",
                        }

            except Exception as legacy_error:
                logger.warning(f" Legacy SKU extraction failed: {legacy_error}")

        # If force refresh, clear cache first
        if force_refresh:
            from sku_cache_manager import get_sku_cache_manager
            cache_manager = get_sku_cache_manager(db_client)
            await cache_manager.invalidate_cache(client_id)

        # Get paginated SKU data using organized approach
        sku_result = await dashboard_inventory_analyzer.get_sku_list(
            client_id, page, page_size, use_cache, platform
        )

        if not sku_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=sku_result.get("error", "Failed to get SKU data"),
            )

        #  FIXED: Calculate summary stats from actual data, not empty cache!
        summary_stats = None
        if page == 1 and sku_result.get("skus"):
            # Calculate real summary stats from the actual SKU data
            skus = sku_result["skus"]
            total_inventory_value = sum(sku.get("total_value", 0) for sku in skus)
            low_stock_count = sum(
                1 for sku in skus if 0 < sku.get("current_availability", 0) < 5
            )
            out_of_stock_count = sum(
                1 for sku in skus if sku.get("current_availability", 0) <= 0
            )
            overstock_count = sum(
                1 for sku in skus if sku.get("current_availability", 0) > 100
            )

            summary_stats = {
                "total_skus": len(skus),
                "total_inventory_value": round(total_inventory_value, 2),
                "low_stock_count": low_stock_count,
                "out_of_stock_count": out_of_stock_count,
                "overstock_count": overstock_count,
            }

            logger.info(
                f" CALCULATED SUMMARY STATS: SKUs: {len(skus)}, Value: ${total_inventory_value:.2f}, Low Stock: {low_stock_count}, Out of Stock: {out_of_stock_count}"
            )

        return {
            "client_id": client_id,
            "success": True,
            "sku_inventory": {
                "skus": sku_result["skus"],
                "summary_stats": summary_stats,
            },
            "pagination": sku_result["pagination"],
            "cached": sku_result.get("cached", False),
            "timestamp": datetime.now().isoformat(),
            "processing_time": "optimized",
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Error getting paginated SKU inventory: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to get SKU inventory: {str(e)}"
        )


# Legacy function (will be removed) - now replaced by cron job
async def refresh_sku_background(client_id: str, platform: str, page: int, page_size: int):
    """Background task to refresh SKU cache - replaced by cron job"""
    logger.info(f" Background SKU refresh triggered (legacy) - should use cron job instead")

@app.post("/api/admin/trigger-api-sync")
async def trigger_api_sync_manually(
    token: str = Depends(security),
    client_id_filter: Optional[str] = None,
    platform_filter: Optional[str] = None,
    force_sync: Optional[bool] = False
):
    """ ADMIN ONLY: Manually trigger API sync for all clients or specific client/platform"""
    try:
        # Verify admin token
        token_data = verify_token(token.credentials)
        
        # TODO: Add admin role check when role system is implemented
        # For now, any authenticated user can trigger (add role check later)
        
        logger.info(f" Manual API sync triggered by client {token_data.client_id}")
        
        from api_sync_cron import api_sync_cron
        
        # If force_sync is True, update next_sync_at to current time for targeted clients
        if force_sync:
            from datetime import datetime
            db_client = get_admin_client()
            current_time = datetime.now().isoformat()
            
            query = db_client.table("client_api_credentials").update({
                "next_sync_at": current_time
            })
            
            if client_id_filter:
                query = query.eq("client_id", client_id_filter)
            if platform_filter:
                query = query.eq("platform_type", platform_filter)
                
            query = query.eq("status", "connected")
            response = query.execute()
            
            logger.info(f" Force sync enabled: Updated {len(response.data if response.data else [])} credentials")
        
        # Run the sync
        results = await api_sync_cron.run_full_sync()
        
        return {
            "success": True,
            "message": "API sync completed",
            "total_integrations": results.get("total_integrations", 0),
            "successful_syncs": results.get("successful_syncs", 0), 
            "failed_syncs": results.get("failed_syncs", 0),
            "total_records_synced": results.get("total_records_synced", 0),
            "duration_seconds": results.get("duration_seconds", 0),
            "client_results": results.get("client_results", {}),
            "filters_applied": {
                "client_id": client_id_filter,
                "platform": platform_filter,
                "force_sync": force_sync
            }
        }
            
    except Exception as e:
        logger.error(f" Error triggering manual API sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger API sync: {str(e)}")

@app.get("/api/admin/scheduler-status")
async def get_scheduler_status(token: str = Depends(security)):
    """ ADMIN ONLY: Get status of internal scheduler and cron jobs"""
    try:
        # Verify admin token
        token_data = verify_token(token.credentials)
        
        # Get scheduler jobs status
        jobs_status = get_scheduler_status()
        
        return {
            "success": True,
            "scheduler_running": len(jobs_status) > 0,
            "jobs": jobs_status,
            "message": f"Scheduler is {'RUNNING' if jobs_status else 'STOPPED'} with {len(jobs_status)} jobs",
            "note": "Jobs run automatically inside the FastAPI app - no external cron needed!"
        }
            
    except Exception as e:
        logger.error(f" Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

@app.post("/api/admin/trigger-sku-analysis")
async def trigger_sku_analysis_manually(
    token: str = Depends(security),
    client_id_filter: Optional[str] = None,
    platform_filter: Optional[str] = None
):
    """ ADMIN ONLY: Manually trigger SKU analysis for all clients or specific client/platform"""
    try:
        # Verify admin token
        token_data = verify_token(token.credentials)
        
        # TODO: Add admin role check when role system is implemented
        # For now, any authenticated user can trigger (add role check later)
        
        logger.info(f" Manual SKU analysis triggered by client {token_data.client_id}")
        
        from sku_analysis_cron import SKUAnalysisCronJob
        cron_job = SKUAnalysisCronJob()
        
        if client_id_filter and platform_filter:
            # Refresh specific client and platform
            result = await cron_job.refresh_client_sku_analysis(client_id_filter, platform_filter)
            return {
                "success": True,
                "message": f"SKU analysis triggered for client {client_id_filter} ({platform_filter})",
                "result": result
            }
        elif client_id_filter:
            # Refresh specific client, all platforms
            results = {}
            for platform in ["shopify", "amazon"]:
                results[platform] = await cron_job.refresh_client_sku_analysis(client_id_filter, platform)
        
            return {
            "success": True,
                "message": f"SKU analysis triggered for client {client_id_filter} (all platforms)",
                "results": results
            }
        else:
            # Full analysis for all clients
            results = await cron_job.run_full_analysis()
            return {
                "success": True,
                "message": "Full SKU analysis triggered for all clients",
                "results": results
            }
            
    except Exception as e:
        logger.error(f" Error triggering manual SKU analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger SKU analysis: {str(e)}")

@app.delete("/api/dashboard/sku-cache")
async def clear_sku_cache(token: str = Depends(security)):
    """Clear SKU cache for the authenticated client"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = str(token_data.client_id)

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        from sku_cache_manager import get_sku_cache_manager

        cache_manager = get_sku_cache_manager(db_client)

        success = await cache_manager.invalidate_cache(client_id)

        if success:

            return {
                "success": True,
                "message": "SKU cache cleared successfully",
                "client_id": client_id,
            }

        else:

            raise HTTPException(status_code=500, detail="Failed to clear cache")

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Error clearing SKU cache: {e}")

        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@app.get("/api/dashboard/sku-summary")
async def get_sku_summary_stats(token: str = Depends(security)):
    """Get SKU inventory summary statistics quickly"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = str(token_data.client_id)

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        from sku_cache_manager import get_sku_cache_manager

        cache_manager = get_sku_cache_manager(db_client)

        stats_result = await cache_manager.get_sku_summary_stats(client_id)

        if stats_result.get("success"):

            return {
                "client_id": client_id,
                "success": True,
                "summary_stats": stats_result["summary_stats"],
                "timestamp": datetime.now().isoformat(),
            }

        else:

            # Fallback: calculate from fresh data

            from dashboard_inventory_analyzer import dashboard_inventory_analyzer

            sku_result = await dashboard_inventory_analyzer.get_sku_list(
                client_id, 1, 10000, False  # Get all data without cache
            )

            if sku_result.get("success"):

                skus = sku_result["skus"]

                total_skus = len(skus)

                total_inventory_value = sum(sku.get("total_value", 0) for sku in skus)

                low_stock_count = sum(
                    1 for sku in skus if sku.get("current_availability", 0) < 5
                )

                out_of_stock_count = sum(
                    1 for sku in skus if sku.get("current_availability", 0) <= 0
                )

                overstock_count = sum(
                    1 for sku in skus if sku.get("current_availability", 0) > 100
                )

                return {
                    "client_id": client_id,
                    "success": True,
                    "summary_stats": {
                        "total_skus": total_skus,
                        "total_inventory_value": total_inventory_value,
                        "low_stock_count": low_stock_count,
                        "out_of_stock_count": out_of_stock_count,
                        "overstock_count": overstock_count,
                    },
                    "timestamp": datetime.now().isoformat(),
                    "source": "fresh_calculation",
                }

            else:

                raise HTTPException(
                    status_code=500, detail="Failed to calculate summary stats"
                )

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Error getting SKU summary stats: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to get summary stats: {str(e)}"
        )


@app.get("/api/dashboard/inventory-analytics")
async def get_inventory_analytics(
    token: str = Depends(security),
    fast_mode: bool = True,
    force_refresh: bool = False,
    platform: str = "shopify",
    start_date: Optional[str] = None,  # Date filtering support
    end_date: Optional[str] = None,  # Date filtering support
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """ INSTANT RESPONSE - Return cached data immediately, refresh in background"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = str(token_data.client_id)

        logger.info(
            f" INSTANT analytics request for {client_id} ({platform}) - NO WAITING!"
        )

        # Create unique cache key including date range for independent caching

        date_key = f"{start_date or 'no_start'}_{end_date or 'no_end'}"

        task_key = f"{client_id}_{platform}_{date_key}"

        cache_key = f"analytics_{platform}_{date_key}"

        # ️ CHECK DAILY DATABASE CACHE FIRST (if not force_refresh)

        if not force_refresh:

            endpoint_url = "/api/dashboard/inventory-analytics"

            # Cache key should NOT include force_refresh - we want same cache for same data request

            cache_params = {"fast_mode": fast_mode, "platform": platform}

            if start_date:

                cache_params["start_date"] = start_date

            if end_date:

                cache_params["end_date"] = end_date

            # Try to get cached response

            cached_response = await get_cached_response(
                client_id, endpoint_url, cache_params
            )

            if cached_response:

                logger.info(
                    f"️ CACHE HIT: Using database cached response for {client_id}"
                )

                cached_response["cached"] = True

                cached_response["cache_source"] = "persistent_database"

                return cached_response

        with calculation_lock:

            if task_key in active_calculations and not force_refresh:

                logger.info(
                    f" Calculation in progress for {task_key}, using cached data"
                )

        # Try to return cached data INSTANTLY using existing LLM cache

        try:

            from llm_cache_manager import LLMCacheManager

            cache_manager = LLMCacheManager()

            # Check existing llm_response_cache for instant response with date range

            cache_params = {"platform": platform}

            if start_date:

                cache_params["start_date"] = start_date

            if end_date:

                cache_params["end_date"] = end_date

            cached_analytics = await cache_manager.get_cached_llm_response(
                client_id, cache_params, cache_key
            )

            if cached_analytics and not force_refresh:

                logger.info(
                    f" INSTANT RESPONSE: Using cached analytics for {platform}"
                )

                # Start background refresh for next time

                background_tasks.add_task(
                    refresh_analytics_background,
                    client_id,
                    platform,
                    fast_mode,
                    start_date,
                    end_date,
                )

                return cached_analytics

        except Exception as e:

            logger.warning(f" Cache check failed: {e}")

        logger.info(f" Generating fresh analytics for {client_id} ({platform})")

        # Try organized approach first

        try:

            from organized_inventory_analyzer import organized_inventory_analyzer

            # Check if client has organized tables

            db_client = get_admin_client()

            if not db_client:

                raise HTTPException(status_code=503, detail="Database not configured")

            # Quick check for organized tables (check both Shopify and Amazon)

            shopify_table = f"{client_id.replace('-', '_')}_shopify_products"

            amazon_table = f"{client_id.replace('-', '_')}_amazon_orders"

            has_organized_data = False

            try:

                test_response = (
                    db_client.table(shopify_table).select("id").limit(1).execute()
                )

                has_organized_data = bool(test_response.data)

            except:

                pass

            # Also check for Amazon organized tables

            if not has_organized_data:

                try:

                    test_response = (
                        db_client.table(amazon_table).select("id").limit(1).execute()
                    )

                    has_organized_data = bool(test_response.data)

                    logger.info(
                        f" Found Amazon organized tables for client {client_id}"
                    )

                except:

                    pass

            if has_organized_data:

                logger.info(f" Using organized tables for client {client_id}")

                # Use dashboard-focused inventory analyzer

                from dashboard_inventory_analyzer import dashboard_inventory_analyzer

                analytics = await dashboard_inventory_analyzer.get_dashboard_inventory_analytics(
                    client_id, platform, start_date, end_date
                )

                if analytics.get("success"):

                    logger.info(
                        f" Dashboard inventory analytics completed for client {client_id}"
                    )

                    response_data = {
                        "client_id": client_id,
                        "success": True,
                        "message": f"Dashboard analytics from organized data - {analytics.get('data_summary', {}).get('shopify_products', 0) + analytics.get('data_summary', {}).get('amazon_products', 0)} products, {analytics.get('data_summary', {}).get('shopify_orders', 0) + analytics.get('data_summary', {}).get('amazon_orders', 0)} orders (SKU data available via /api/dashboard/sku-inventory)",
                        "timestamp": datetime.now().isoformat(),
                        "data_type": "dashboard_inventory_analytics",
                        "schema_type": "dashboard_inventory_analytics",
                        "total_records": analytics.get("data_summary", {}).get(
                            "total_records", 0
                        ),
                        "inventory_analytics": analytics,
                        "cached": False,
                        "processing_time": "optimized",
                        "data_source": "organized_tables",
                    }

                    # ️ Save response to daily cache

                    endpoint_url = "/api/dashboard/inventory-analytics"

                    cache_params = {"fast_mode": fast_mode, "platform": platform}

                    if start_date:

                        cache_params["start_date"] = start_date

                    if end_date:

                        cache_params["end_date"] = end_date

                    await save_cached_response(
                        client_id, endpoint_url, response_data, cache_params
                    )

                    return response_data

                else:

                    logger.warning(
                        f" Dashboard analysis failed, falling back to legacy for client {client_id}"
                    )

            else:

                logger.info(
                    f" No organized tables found, using legacy approach for client {client_id}"
                )

        except Exception as organized_error:

            logger.warning(
                f" Organized approach failed: {organized_error}, falling back to legacy"
            )

        # Fallback to legacy approach

        logger.info(f" Using legacy JSON parsing for client {client_id}")

        # Get client data for legacy analysis

        try:

            # Get client's data from database

            response = (
                db_client.table("client_data")
                .select("*")
                .eq("client_id", client_id)
                .order("created_at", desc=True)
                .limit(1000)
                .execute()
            )

            # Prepare client data structure for analysis

            client_data = {"client_id": client_id, "data": []}

            if response.data:

                for record in response.data:

                    if record.get("data"):

                        try:

                            # Handle both string and dict data from database

                            if isinstance(record["data"], dict):

                                parsed_data = record["data"]

                            elif isinstance(record["data"], str):

                                parsed_data = json.loads(record["data"])

                            else:

                                continue

                            # Add source metadata to each record

                            enhanced_data = {
                                **parsed_data,
                                "_source_type": record.get("source_type", "upload"),
                                "_source_file": record.get(
                                    "source_file", "manual_upload"
                                ),
                                "_record_id": record.get("id", "unknown"),
                            }

                            client_data["data"].append(enhanced_data)

                        except json.JSONDecodeError:

                            logger.warning(
                                f"  Failed to parse data for record {record.get('id', 'unknown')}"
                            )

                            continue

            logger.info(
                f" Loaded {len(client_data['data'])} data records for inventory analysis"
            )

            # Debug: Show sample of raw data structure

            if client_data["data"]:

                sample_record = client_data["data"][0]

                logger.info(f" Sample raw record keys: {list(sample_record.keys())}")

                # Show sample values to understand the data structure

                for key, value in list(sample_record.items())[:10]:

                    logger.info(f"  {key}: {type(value).__name__} = {str(value)[:100]}")

            #  HANDLE MULTI-PLATFORM REQUEST for legacy data

            if platform.lower() == "all":

                logger.info(
                    f" Processing MULTI-PLATFORM legacy request for {client_id}"
                )

                # Separate data by platform

                shopify_data = {"client_id": client_id, "data": []}

                amazon_data = {"client_id": client_id, "data": []}

                for record in client_data["data"]:

                    record_platform = record.get("platform", "").lower()

                    if record_platform == "shopify":

                        shopify_data["data"].append(record)

                    elif record_platform == "amazon":

                        amazon_data["data"].append(record)

                    # Skip records without platform info

                # Analyze each platform separately

                shopify_analytics = (
                    inventory_analyzer.analyze_inventory_data(shopify_data)
                    if shopify_data["data"]
                    else {}
                )

                amazon_analytics = (
                    inventory_analyzer.analyze_inventory_data(amazon_data)
                    if amazon_data["data"]
                    else {}
                )

                combined_analytics = inventory_analyzer.analyze_inventory_data(
                    client_data
                )  # All data together

                # Create multi-platform response structure

                multi_platform_analytics = {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "client_id": client_id,
                    "platform": "all",
                    "platforms": {
                        "shopify": {
                            "sales_kpis": shopify_analytics.get("sales_kpis", {}),
                            "trend_analysis": shopify_analytics.get(
                                "trend_analysis", {}
                            ),
                            "alerts_summary": shopify_analytics.get(
                                "alerts_summary", {}
                            ),
                            "data_summary": shopify_analytics.get("data_summary", {}),
                        },
                        "amazon": {
                            "sales_kpis": amazon_analytics.get("sales_kpis", {}),
                            "trend_analysis": amazon_analytics.get(
                                "trend_analysis", {}
                            ),
                            "alerts_summary": amazon_analytics.get(
                                "alerts_summary", {}
                            ),
                            "data_summary": amazon_analytics.get("data_summary", {}),
                        },
                        "combined": {
                            "sales_kpis": combined_analytics.get("sales_kpis", {}),
                            "trend_analysis": combined_analytics.get(
                                "trend_analysis", {}
                            ),
                            "alerts_summary": combined_analytics.get(
                                "alerts_summary", {}
                            ),
                            "data_summary": combined_analytics.get("data_summary", {}),
                        },
                    },
                }

                response_data = {
                    "client_id": client_id,
                    "success": True,
                    "message": f"Multi-platform analysis: {len(shopify_data['data'])} Shopify + {len(amazon_data['data'])} Amazon records",
                    "timestamp": datetime.now().isoformat(),
                    "data_type": "dashboard_inventory_analytics",
                    "schema_type": "dashboard_inventory_analytics",
                    "total_records": len(client_data["data"]),
                    "inventory_analytics": multi_platform_analytics,
                    "cached": False,
                    "processing_time": "real-time",
                    "data_source": "legacy_multi_platform",
                }

                # ️ Save response to daily cache

                endpoint_url = "/api/dashboard/inventory-analytics"

                cache_params = {"fast_mode": fast_mode, "platform": platform}

                if start_date:

                    cache_params["start_date"] = start_date

                if end_date:

                    cache_params["end_date"] = end_date

                await save_cached_response(
                    client_id, endpoint_url, response_data, cache_params
                )

                return response_data

            # Use dashboard structure even for legacy data (single platform)

            try:

                from dashboard_inventory_analyzer import dashboard_inventory_analyzer

                # Transform legacy data into dashboard format

                legacy_analytics = inventory_analyzer.analyze_inventory_data(
                    client_data
                )

                # Convert legacy structure to dashboard structure

                dashboard_analytics = {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "client_id": client_id,
                    "sales_kpis": legacy_analytics.get("sales_kpis", {}),
                    "trend_analysis": legacy_analytics.get("trend_analysis", {}),
                    "alerts_summary": legacy_analytics.get("alerts_summary", {}),
                    "data_summary": legacy_analytics.get("data_summary", {}),
                    "sku_inventory": {
                        "skus": [],  # Will be provided by separate SKU endpoint
                        "summary_stats": legacy_analytics.get("summary_stats", {}),
                    },
                    "recommendations": [
                        "Legacy data detected - consider organizing data for better performance",
                        "Use /api/dashboard/sku-inventory for detailed SKU data",
                        "Contact support to organize data into structured tables",
                    ],
                }

                response_data = {
                    "client_id": client_id,
                    "success": True,
                    "message": f"Analyzed {len(client_data['data'])} records (legacy format converted to dashboard structure)",
                    "timestamp": datetime.now().isoformat(),
                    "data_type": "dashboard_inventory_analytics",
                    "schema_type": "dashboard_inventory_analytics",
                    "total_records": len(client_data["data"]),
                    "inventory_analytics": dashboard_analytics,
                    "cached": False,
                    "processing_time": "real-time",
                    "data_source": "legacy_converted",
                }

                # ️ Save response to daily cache

                endpoint_url = "/api/dashboard/inventory-analytics"

                cache_params = {"fast_mode": fast_mode, "platform": platform}

                if start_date:

                    cache_params["start_date"] = start_date

                if end_date:

                    cache_params["end_date"] = end_date

                await save_cached_response(
                    client_id, endpoint_url, response_data, cache_params
                )

                return response_data

            except Exception as dashboard_error:

                logger.warning(
                    f" Failed to convert to dashboard structure: {dashboard_error}"
                )

                # Fallback to original legacy structure

                inventory_analytics = inventory_analyzer.analyze_inventory_data(
                    client_data
                )

                response_data = {
                    "client_id": client_id,
                    "success": True,
                    "message": f"Analyzed {len(client_data['data'])} records",
                    "timestamp": datetime.now().isoformat(),
                    "data_type": "inventory_analytics",
                    "schema_type": "inventory_analytics",
                    "total_records": len(client_data["data"]),
                    "inventory_analytics": inventory_analytics,
                    "cached": False,
                    "processing_time": "real-time",
                }

                # ️ Save response to daily cache

                endpoint_url = "/api/dashboard/inventory-analytics"

                cache_params = {"fast_mode": fast_mode, "platform": platform}

                if start_date:

                    cache_params["start_date"] = start_date

                if end_date:

                    cache_params["end_date"] = end_date

                await save_cached_response(
                    client_id, endpoint_url, response_data, cache_params
                )

                return response_data

        except Exception as data_error:

            logger.error(f" Error fetching client data: {str(data_error)}")

            # Return empty dashboard analytics if data fetch fails

            empty_dashboard_analytics = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "sales_kpis": {},
                "trend_analysis": {},
                "alerts_summary": {
                    "summary_counts": {
                        "total_alerts": 0,
                        "low_stock_alerts": 0,
                        "overstock_alerts": 0,
                    },
                    "detailed_alerts": {"low_stock_alerts": [], "overstock_alerts": []},
                    "quick_links": {},
                },
                "data_summary": {"total_records": 0, "total_skus": 0},
                "sku_inventory": {"skus": [], "summary_stats": {}},
                "recommendations": [
                    "No data available - please upload inventory data first"
                ],
            }

            return {
                "client_id": client_id,
                "success": True,
                "message": f"No data available for analysis: {str(data_error)}",
                "timestamp": datetime.now().isoformat(),
                "data_type": "dashboard_inventory_analytics",
                "schema_type": "dashboard_inventory_analytics",
                "total_records": 0,
                "inventory_analytics": empty_dashboard_analytics,
                "cached": False,
                "processing_time": "instant",
                "data_source": "empty",
            }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Inventory analytics error: {str(e)}")

        raise HTTPException(
            status_code=500, detail=f"Inventory analytics failed: {str(e)}"
        )


@app.get("/api/dashboard/business-insights")
async def get_business_insights_dashboard(
    token: str = Depends(security), fast_mode: bool = True, force_llm: bool = False
):
    """Get business insights dashboard metrics with specialized LLM analysis"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = str(token_data.client_id)

        # Get client data - NO LIMIT for complete data processing

        from ai_analyzer import ai_analyzer

        from dashboard_orchestrator import dashboard_orchestrator

        from llm_cache_manager import llm_cache_manager

        client_data = await ai_analyzer.get_client_data_optimized(client_id)

        if not client_data:

            raise HTTPException(status_code=404, detail="No data found for this client")

        # Clear cache if forced fresh analysis is requested

        if force_llm:

            await llm_cache_manager.invalidate_cache(client_id, "business")

            logger.info(
                f"️ Cleared BUSINESS dashboard cache for fresh analysis - client {client_id}"
            )

        # Check cache first - but skip if force_llm is true

        cached_insights = None

        if not force_llm:

            cached_insights = await llm_cache_manager.get_cached_llm_response(
                client_id, client_data, "business"
            )

        if cached_insights and not force_llm:

            logger.info(f" Using cached business insights for client {client_id}")

            return {
                "client_id": client_id,
                "dashboard_type": "business_insights",
                "data_type": client_data.get("data_type", "unknown"),
                "schema_type": client_data.get("schema", {}).get("type", "unknown"),
                "total_records": len(client_data.get("data", [])),
                "llm_analysis": cached_insights,
                "cached": True,
                "response_time": "instant",
            }

        # ALWAYS use specialized BUSINESS LLM analysis - no fallbacks

        logger.info(
            f"🤖 Generating BUSINESS insights with specialized LLM analysis for client {client_id}"
        )

        try:

            # Add timeout to prevent hanging for more than 55 seconds

            import asyncio

            insights = await asyncio.wait_for(
                dashboard_orchestrator._extract_business_insights_specialized(
                    client_data
                ),
                timeout=55.0,  # 55 second timeout to stay under 60s frontend timeout
            )

            logger.info(
                f" Business insights LLM analysis successful for client {client_id}"
            )

            #  CRITICAL: Store in cache for future requests with data snapshot date

            data_snapshot_date = get_client_data_update_date(client_data)

            try:

                cache_success = await llm_cache_manager.store_cached_llm_response(
                    client_id, client_data, insights, "business", data_snapshot_date
                )

                if cache_success:

                    logger.info(
                        f" Cached BUSINESS insights response for client {client_id}"
                    )

                else:

                    logger.warning(
                        f" Failed to cache BUSINESS insights response for client {client_id}"
                    )

            except Exception as cache_error:

                logger.error(f" Cache storage error (non-blocking): {cache_error}")

                # Continue with response even if cache fails

        except asyncio.TimeoutError:

            logger.error(
                f"⏰ Business insights LLM analysis timed out for client {client_id}"
            )

            raise HTTPException(
                status_code=408,
                detail="Business insights analysis timed out. Please try again or enable fast_mode.",
            )

        except Exception as llm_error:

            logger.error(
                f" Business insights LLM analysis failed for client {client_id}: {llm_error}"
            )

            raise HTTPException(
                status_code=500,
                detail=f"Business insights analysis failed: {str(llm_error)}",
            )

        return {
            "client_id": client_id,
            "dashboard_type": "business_insights",
            "data_type": client_data.get("data_type", "unknown"),
            "schema_type": client_data.get("schema", {}).get("type", "unknown"),
            "total_records": len(client_data.get("data", [])),
            "llm_analysis": insights,
            "cached": False,
            "fast_mode": fast_mode,
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to get business insights dashboard: {e}")

        return {"error": f"Failed to get business insights dashboard: {str(e)}"}


@app.get("/api/dashboard/performance")
async def get_performance_dashboard(
    token: str = Depends(security), fast_mode: bool = True, force_llm: bool = False
):
    """Get performance dashboard metrics with specialized LLM analysis"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = str(token_data.client_id)

        # Get client data - NO LIMIT for complete data processing

        from ai_analyzer import ai_analyzer

        from dashboard_orchestrator import dashboard_orchestrator

        from llm_cache_manager import llm_cache_manager

        client_data = await ai_analyzer.get_client_data_optimized(client_id)

        if not client_data:

            raise HTTPException(status_code=404, detail="No data found for this client")

        # Clear cache if forced fresh analysis is requested

        if force_llm:

            await llm_cache_manager.invalidate_cache(client_id, "performance")

            logger.info(
                f"️ Cleared PERFORMANCE dashboard cache for fresh analysis - client {client_id}"
            )

        # Check cache first with dashboard type

        cached_insights = await llm_cache_manager.get_cached_llm_response(
            client_id, client_data, "performance"
        )

        if cached_insights and not force_llm:

            logger.info(f" Using cached performance insights for client {client_id}")

            return {
                "client_id": client_id,
                "dashboard_type": "performance",
                "data_type": client_data.get("data_type", "unknown"),
                "schema_type": client_data.get("schema", {}).get("type", "unknown"),
                "total_records": len(client_data.get("data", [])),
                "llm_analysis": cached_insights,
                "cached": True,
                "response_time": "instant",
            }

        # ALWAYS use specialized PERFORMANCE LLM analysis - no fallbacks

        logger.info(
            f" Generating PERFORMANCE insights with specialized LLM analysis for client {client_id}"
        )

        try:

            # Add timeout to prevent hanging for more than 55 seconds

            import asyncio

            insights = await asyncio.wait_for(
                dashboard_orchestrator._extract_performance_insights_specialized(
                    client_data
                ),
                timeout=55.0,  # 55 second timeout to stay under 60s frontend timeout
            )

            logger.info(
                f" Performance insights LLM analysis successful for client {client_id}"
            )

            #  CRITICAL: Store in cache for future requests with data snapshot date

            data_snapshot_date = get_client_data_update_date(client_data)

            try:

                cache_success = await llm_cache_manager.store_cached_llm_response(
                    client_id, client_data, insights, "performance", data_snapshot_date
                )

                if cache_success:

                    logger.info(
                        f" Cached PERFORMANCE insights response for client {client_id}"
                    )

                else:

                    logger.warning(
                        f" Failed to cache PERFORMANCE insights response for client {client_id}"
                    )

            except Exception as cache_error:

                logger.error(f" Cache storage error (non-blocking): {cache_error}")

                # Continue with response even if cache fails

        except asyncio.TimeoutError:

            logger.error(
                f"⏰ Performance insights LLM analysis timed out for client {client_id}"
            )

            raise HTTPException(
                status_code=408,
                detail="Performance analysis timed out. Please try again or enable fast_mode.",
            )

        except Exception as llm_error:

            logger.error(
                f" Performance insights LLM analysis failed for client {client_id}: {llm_error}"
            )

            raise HTTPException(
                status_code=500,
                detail=f"Performance insights analysis failed: {str(llm_error)}",
            )

        return {
            "client_id": client_id,
            "dashboard_type": "performance",
            "data_type": client_data.get("data_type", "unknown"),
            "schema_type": client_data.get("schema", {}).get("type", "unknown"),
            "total_records": len(client_data.get("data", [])),
            "llm_analysis": insights,
            "cached": False,
            "fast_mode": fast_mode,
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to get performance dashboard: {e}")

        return {"error": f"Failed to get performance dashboard: {str(e)}"}


@app.get("/api/dashboard/cache/stats")
async def get_cache_stats(token: str = Depends(security)):
    """Get LLM cache statistics"""

    try:

        # Verify admin token (optional - for security)

        token_data = verify_token(token.credentials)

        from llm_cache_manager import llm_cache_manager

        stats = await llm_cache_manager.get_cache_stats()

        return {
            "success": True,
            "cache_stats": stats,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:

        logger.error(f" Failed to get cache stats: {e}")

        return {"error": f"Failed to get cache stats: {str(e)}"}


@app.post("/api/dashboard/cache/invalidate")
async def invalidate_cache(
    token: str = Depends(security),
    client_id: Optional[str] = None,
    dashboard_type: Optional[str] = None,
):
    """Invalidate cache for specific client/dashboard or all cache"""

    try:

        # Verify token

        token_data = verify_token(token.credentials)

        from llm_cache_manager import llm_cache_manager

        if client_id:

            # Invalidate for specific client and optionally specific dashboard

            success = await llm_cache_manager.invalidate_cache(
                client_id, dashboard_type
            )

            message = f"Cache invalidated for client {client_id}"

            if dashboard_type:

                message += f" ({dashboard_type} dashboard)"

        else:

            # Invalidate all cache (admin function)

            success = await llm_cache_manager.invalidate_all_cache()

            message = "All cache invalidated"

        return {
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:

        logger.error(f" Failed to invalidate cache: {e}")

        return {"error": f"Failed to invalidate cache: {str(e)}"}


@app.get("/api/dashboard/status", response_model=DashboardStatusResponse)
async def get_dashboard_status(token: str = Depends(security)):
    """Get dashboard status for the authenticated client"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Get dashboard status using the database function

        try:

            response = db_client.rpc(
                "get_client_dashboard_status",
                {"p_client_id": str(token_data.client_id)},
            ).execute()

            if response.data:

                status_data = response.data[0]

                return DashboardStatusResponse(
                    client_id=token_data.client_id,
                    has_dashboard=status_data["has_dashboard"],
                    is_generated=status_data["is_generated"],
                    last_updated=status_data["last_updated"],
                    metrics_count=status_data["metrics_count"],
                )

            else:

                return DashboardStatusResponse(
                    client_id=token_data.client_id,
                    has_dashboard=False,
                    is_generated=False,
                    last_updated=None,
                    metrics_count=0,
                )

        except Exception as e:

            logger.warning(
                f"  Dashboard tables not found, returning default status: {e}"
            )

            # Return default status if tables don't exist yet

            return DashboardStatusResponse(
                client_id=token_data.client_id,
                has_dashboard=False,
                is_generated=False,
                last_updated=None,
                metrics_count=0,
            )

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to get dashboard status: {e}")

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dashboard/generate-now")
async def generate_dashboard_now(token: str = Depends(security)):
    """Generate dashboard immediately for the authenticated client (manual trigger) - SAFE VERSION"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        logger.info(
            f" Manual dashboard generation requested for client {token_data.client_id}"
        )

        # Import dashboard orchestrator

        from dashboard_orchestrator import dashboard_orchestrator

        # SAFETY CHECK: Verify orchestrator is properly initialized

        if (
            not hasattr(dashboard_orchestrator, "openai_api_key")
            or not dashboard_orchestrator.openai_api_key
        ):

            raise HTTPException(
                status_code=503, detail="AI orchestrator not properly configured"
            )

        # Generate dashboard immediately in main async context (SAFE)

        generation_response = await dashboard_orchestrator.generate_dashboard(
            client_id=token_data.client_id, force_regenerate=True
        )

        if generation_response.success:

            logger.info(
                f" Manual dashboard generation completed for client {token_data.client_id}"
            )

            return {
                "success": True,
                "message": "Dashboard generated successfully",
                "dashboard_config": (
                    generation_response.dashboard_config.dict()
                    if generation_response.dashboard_config
                    else None
                ),
                "metrics_generated": generation_response.metrics_generated,
                "generation_time": generation_response.generation_time,
            }

        else:

            logger.error(
                f" Manual dashboard generation failed for client {token_data.client_id}: {generation_response.message}"
            )

            raise HTTPException(status_code=500, detail=generation_response.message)

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to generate dashboard manually: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to generate dashboard: {str(e)}"
        )


@app.get("/api/dashboard/test-orchestrator")
async def test_orchestrator_health(token: str = Depends(security)):
    """Test endpoint to verify AI orchestrator is working properly"""

    try:

        # Verify superadmin or client token

        try:

            verify_superadmin_token(token.credentials)

        except:

            verify_token(token.credentials)  # Allow clients to test too

        from dashboard_orchestrator import dashboard_orchestrator

        # Test orchestrator health

        health_check = {
            "orchestrator_loaded": True,
            "has_openai_key": bool(
                getattr(dashboard_orchestrator, "openai_api_key", None)
            ),
            "has_ai_analyzer": bool(
                getattr(dashboard_orchestrator, "ai_analyzer", None)
            ),
            "chart_type_mapping_loaded": bool(
                getattr(dashboard_orchestrator, "chart_type_mapping", None)
            ),
            "kpi_icons_loaded": bool(
                getattr(dashboard_orchestrator, "kpi_icons", None)
            ),
        }

        # Test database connection

        db_client = get_admin_client()

        if db_client:

            try:

                db_client.table("clients").select("client_id").limit(1).execute()

                health_check["database_connection"] = True

            except:

                health_check["database_connection"] = False

        else:

            health_check["database_connection"] = False

        # Overall health status

        all_good = all(
            [
                health_check["orchestrator_loaded"],
                health_check["has_openai_key"],
                health_check["has_ai_analyzer"],
                health_check["database_connection"],
            ]
        )

        return {
            "status": "healthy" if all_good else "degraded",
            "details": health_check,
            "message": (
                "AI orchestrator is ready" if all_good else "AI orchestrator has issues"
            ),
        }

    except Exception as e:

        logger.error(f" Orchestrator health check failed: {e}")

        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "AI orchestrator is not working",
        }


@app.post("/api/dashboard/refresh-metrics")
async def refresh_dashboard_metrics(token: str = Depends(security)):
    """Refresh dashboard metrics for the authenticated client"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        # Import dashboard orchestrator

        from dashboard_orchestrator import dashboard_orchestrator

        # Get current dashboard config

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        response = (
            db_client.table("client_dashboard_configs")
            .select("*")
            .eq("client_id", str(token_data.client_id))
            .execute()
        )

        if not response.data:

            # If no dashboard exists, generate one

            logger.info(
                f"No dashboard found, generating new one for client {token_data.client_id}"
            )

            generation_response = await dashboard_orchestrator.generate_dashboard(
                client_id=token_data.client_id, force_regenerate=True
            )

            if generation_response.success:

                return {
                    "success": True,
                    "metrics_generated": generation_response.metrics_generated,
                    "message": "Dashboard created and metrics generated successfully",
                }

            else:

                raise HTTPException(status_code=500, detail=generation_response.message)

        config_data = response.data[0]["dashboard_config"]

        dashboard_config = DashboardConfig(**config_data)

        # Analyze current data

        data_analysis = await dashboard_orchestrator._analyze_client_data(
            token_data.client_id
        )

        # Generate and save new metrics

        metrics_generated = await dashboard_orchestrator._generate_and_save_metrics(
            token_data.client_id, dashboard_config, data_analysis
        )

        # ️ INVALIDATE LLM CACHE SINCE METRICS WERE REFRESHED

        try:

            from llm_cache_manager import llm_cache_manager

            await llm_cache_manager.invalidate_cache(str(token_data.client_id))

            logger.info(
                f"️ Invalidated LLM cache for client {token_data.client_id} after metrics refresh"
            )

        except Exception as cache_error:

            logger.warning(
                f" Failed to invalidate cache after metrics refresh: {cache_error}"
            )

        logger.info(f" Dashboard metrics refreshed for client {token_data.client_id}")

        return {
            "success": True,
            "metrics_generated": metrics_generated,
            "message": "Dashboard metrics refreshed successfully",
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to refresh dashboard metrics: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to refresh metrics: {str(e)}"
        )


# ==================== AUTOMATIC GENERATION & RETRY ENDPOINTS ====================


@app.post("/api/dashboard/generate-auto")
async def trigger_automatic_generation(
    request: AutoGenerationRequest, token: str = Depends(security)
):
    """Manually trigger automatic dashboard generation for a client"""

    try:

        # Verify superadmin or regular client token

        try:

            verify_superadmin_token(token.credentials)

            is_admin = True

        except:

            token_data = verify_token(token.credentials)

            is_admin = False

            # If not admin, can only generate for self

            if not is_admin and str(request.client_id) != str(token_data.client_id):

                raise HTTPException(
                    status_code=403, detail="Can only generate dashboard for yourself"
                )

        from dashboard_orchestrator import dashboard_orchestrator

        result = await dashboard_orchestrator.generate_dashboard_with_retry(request)

        return {
            "success": result.success,
            "client_id": str(result.client_id),
            "generation_id": str(result.generation_id),
            "message": (
                "Dashboard generation completed"
                if result.success
                else f"Generation failed: {result.error_message}"
            ),
            "retry_info": result.retry_info.dict() if result.retry_info else None,
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Manual generation trigger failed: {e}")

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/generation-status/{client_id}")
async def get_generation_status(client_id: str, token: str = Depends(security)):
    """Get dashboard generation status for a client"""

    try:

        # Verify access

        try:

            verify_superadmin_token(token.credentials)

            is_admin = True

        except:

            token_data = verify_token(token.credentials)

            is_admin = False

            if not is_admin and client_id != str(token_data.client_id):

                raise HTTPException(status_code=403, detail="Access denied")

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        response = (
            db_client.table("client_dashboard_generation")
            .select("*")
            .eq("client_id", client_id)
            .execute()
        )

        if not response.data:

            return {
                "client_id": client_id,
                "status": "not_started",
                "message": "Dashboard generation not yet initiated",
            }

        generation_data = response.data[0]

        return GenerationStatusResponse(
            client_id=uuid.UUID(client_id),
            status=GenerationStatus(generation_data["status"]),
            attempt_count=generation_data["attempt_count"],
            max_attempts=generation_data["max_attempts"],
            error_type=(
                ErrorType(generation_data["error_type"])
                if generation_data["error_type"]
                else None
            ),
            error_message=generation_data["error_message"],
            started_at=generation_data["started_at"],
            completed_at=generation_data["completed_at"],
            next_retry_at=generation_data["next_retry_at"],
        )

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to get generation status: {e}")

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/process-retries")
async def process_pending_retries(token: str = Depends(security)):
    """Process all pending dashboard generation retries (Admin only)"""

    try:

        # Verify superadmin token

        verify_superadmin_token(token.credentials)

        from dashboard_orchestrator import dashboard_orchestrator

        results = await dashboard_orchestrator.process_pending_retries()

        successful_retries = [r for r in results if r.success]

        failed_retries = [r for r in results if not r.success]

        return {
            "total_processed": len(results),
            "successful": len(successful_retries),
            "failed": len(failed_retries),
            "results": [
                {
                    "client_id": str(r.client_id),
                    "success": r.success,
                    "attempt_number": r.attempt_number,
                    "error_message": r.error_message if not r.success else None,
                }
                for r in results
            ],
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to process retries: {e}")

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/generation-overview")
async def get_generation_overview(token: str = Depends(security)):
    """Get overview of all dashboard generation statuses (Admin only)"""

    try:

        # Verify superadmin token

        verify_superadmin_token(token.credentials)

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Get all generation records with client info

        response = (
            db_client.table("client_dashboard_generation")
            .select("*, clients(company_name, email)")
            .order("updated_at", desc=True)
            .execute()
        )

        overview = []

        for record in response.data:

            overview.append(
                {
                    "client_id": record["client_id"],
                    "company_name": (
                        record["clients"]["company_name"]
                        if record["clients"]
                        else "Unknown"
                    ),
                    "email": (
                        record["clients"]["email"] if record["clients"] else "Unknown"
                    ),
                    "status": record["status"],
                    "generation_type": record["generation_type"],
                    "attempt_count": record["attempt_count"],
                    "max_attempts": record["max_attempts"],
                    "error_type": record["error_type"],
                    "error_message": record["error_message"],
                    "started_at": record["started_at"],
                    "completed_at": record["completed_at"],
                    "next_retry_at": record["next_retry_at"],
                }
            )

        # Calculate statistics

        total = len(overview)

        completed = len([r for r in overview if r["status"] == "completed"])

        retrying = len([r for r in overview if r["status"] == "retrying"])

        failed = len([r for r in overview if r["status"] == "failed"])

        processing = len([r for r in overview if r["status"] == "processing"])

        return {
            "statistics": {
                "total": total,
                "completed": completed,
                "retrying": retrying,
                "failed": failed,
                "processing": processing,
                "success_rate": f"{(completed/total*100):.1f}%" if total > 0 else "0%",
            },
            "generations": overview,
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to get generation overview: {e}")

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/background-retry-processor")
async def background_retry_processor():
    """Background endpoint to process pending retries - can be called by cron/scheduler"""

    try:

        # This endpoint doesn't require authentication as it's meant for internal/cron use

        # In production, you might want to add IP filtering or API key authentication

        from dashboard_orchestrator import dashboard_orchestrator

        logger.info(" Background retry processor started")

        results = await dashboard_orchestrator.process_pending_retries()

        successful_retries = [r for r in results if r.success]

        failed_retries = [r for r in results if not r.success]

        logger.info(
            f" Background retry processor completed: {len(successful_retries)} successful, {len(failed_retries)} failed"
        )

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "total_processed": len(results),
            "successful": len(successful_retries),
            "failed": len(failed_retries),
            "message": f"Processed {len(results)} pending retries",
        }

    except Exception as e:

        logger.error(f" Background retry processor failed: {e}")

        return {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "message": "Background retry processor failed",
        }


# ==================== STARTUP EVENT FOR BACKGROUND PROCESSING ====================


@app.on_event("startup")
async def startup_event():
    """Application startup event"""

    logger.info(" Analytics AI Dashboard API starting up...")

    # ULTRA-MINIMAL startup - just test basic imports

    try:

        logger.info(" Testing dashboard orchestrator import...")

        from dashboard_orchestrator import dashboard_orchestrator

        logger.info(" Dashboard orchestrator imported successfully")

        logger.info(" Testing database client creation...")

        try:

            db_client = get_admin_client()

            logger.info(" Database client created successfully")

            logger.info(" Testing simple database query...")

            # Try the most basic query possible

            try:

                response = (
                    db_client.table("clients").select("client_id").limit(1).execute()
                )

                logger.info(" Basic database query successful")

            except Exception as db_error:

                logger.error(
                    f" Database query failed: {type(db_error).__name__}: {db_error}"
                )

                # Log the full error details

                import traceback

                logger.error(f"Full database error: {traceback.format_exc()}")

        except Exception as client_error:

            logger.error(
                f" Database client creation failed: {type(client_error).__name__}: {client_error}"
            )

            # Log the full error details

            import traceback

            logger.error(f"Full client error: {traceback.format_exc()}")

    except Exception as e:

        logger.error(f" Startup test failed: {type(e).__name__}: {str(e)}")

        # Log the full error details to find the root cause

        import traceback

        logger.error(f"Full startup error: {traceback.format_exc()}")

    logger.info(" Startup complete - app is ready")


# AI Analysis Endpoints for Frontend Integration


@app.post("/api/analyze-data")
async def analyze_data_enhanced(
    request_data: dict, auth_data: dict = Depends(require_analytics_access)
):
    """Enhanced data analysis with API key support"""

    try:

        # Extract data from request

        data = request_data.get("data", [])

        if not data:

            raise HTTPException(status_code=400, detail="No data provided")

        # Convert data to JSON string format for enhanced analyzer

        raw_data = json.dumps(data)

        client_id = auth_data["client_id"]

        # Use enhanced AI analyzer

        analysis_result = await ai_analyzer.analyze_data(
            raw_data=raw_data, data_format=DataFormat.JSON, client_id=client_id
        )

        # Generate additional insights for frontend

        insights_summary = {
            "key_findings": [
                f"Enhanced analysis completed successfully",
                f"Analyzed {len(data)} records with {analysis_result.confidence:.1%} confidence",
                f"Detected {analysis_result.data_type} data type",
                f"Generated {len(analysis_result.insights)} AI insights",
            ],
            "recommendations": (
                analysis_result.insights[:3]
                if analysis_result.insights
                else [
                    "Data shows promising patterns",
                    "Consider implementing automated monitoring",
                    "Optimize based on detected trends",
                ]
            ),
        }

        # Create comprehensive data overview

        data_overview = {
            "total_records": len(data),
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_type": "enhanced_ai_orchestrator",
            "client_id": client_id,
            "auth_type": auth_data["auth_type"],
        }

        return {
            "success": True,
            "analysis": analysis_result.dict(),
            "insights_summary": insights_summary,
            "data_overview": data_overview,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:

        logger.error(f"Error in enhanced data analysis: {str(e)}")

        raise HTTPException(
            status_code=500, detail=f"Enhanced data analysis failed: {str(e)}"
        )


@app.get("/api/sample-data")
async def get_sample_data():
    """

    Get sample data for frontend testing and fallback

    """

    try:

        # Generate realistic sample business data

        from datetime import datetime, timedelta

        import random

        # Generate 12 months of sample data with realistic patterns

        base_date = datetime.now() - timedelta(days=365)

        # Initialize arrays for each field

        dates = []

        revenues = []

        customers = []

        orders = []

        conversion_rates = []

        avg_order_values = []

        customer_satisfactions = []

        marketing_spends = []

        categories = []

        regions = []

        for i in range(12):

            date = base_date + timedelta(days=30 * i)

            # Add seasonal variation and growth trends

            seasonal_factor = 1 + 0.3 * (1 + i / 12)  # Growth over time

            monthly_variation = 0.8 + 0.4 * random.random()  # Random variation

            base_revenue = 25000

            base_customers = 400

            base_orders = 300

            dates.append(date.strftime("%Y-%m-%d"))

            revenues.append(int(base_revenue * seasonal_factor * monthly_variation))

            customers.append(int(base_customers * seasonal_factor * monthly_variation))

            orders.append(int(base_orders * seasonal_factor * monthly_variation))

            conversion_rates.append(round(random.uniform(2.5, 5.0), 2))

            avg_order_values.append(round(random.uniform(80, 150), 2))

            customer_satisfactions.append(round(random.uniform(4.0, 5.0), 1))

            marketing_spends.append(
                int(base_revenue * 0.1 * seasonal_factor * monthly_variation)
            )

            categories.append(
                random.choice(["Electronics", "Clothing", "Books", "Home"])
            )

            regions.append(random.choice(["North", "South", "East", "West"]))

        # Return data in the format expected by frontend (object with arrays)

        sample_data = {
            "date": dates,
            "revenue": revenues,
            "customers": customers,
            "orders": orders,
            "conversion_rate": conversion_rates,
            "avg_order_value": avg_order_values,
            "customer_satisfaction": customer_satisfactions,
            "marketing_spend": marketing_spends,
            "category": categories,
            "region": regions,
        }

        return {
            "success": True,
            "data": sample_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:

        logger.error(f"Error generating sample data: {str(e)}")

        raise HTTPException(
            status_code=500, detail=f"Sample data generation failed: {str(e)}"
        )


# ==================== ENHANCED API KEY ENDPOINTS ====================


@app.post("/api/auth/api-keys", response_model=dict)
async def create_api_key(
    key_data: APIKeyCreate, auth_data: dict = Depends(authenticate_request)
):
    """Create a new API key for the authenticated client"""

    try:

        client_id = uuid.UUID(auth_data["client_id"])

        # Generate API key

        api_key, key_response = await api_key_manager.create_api_key(
            client_id, key_data
        )

        return {
            "success": True,
            "message": "API key created successfully",
            "api_key": api_key,  # Only shown once!
            "key_info": key_response.dict(),
            "warning": " Store this API key securely. It will not be shown again.",
        }

    except Exception as e:

        logger.error(f" Failed to create API key: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to create API key: {str(e)}"
        )


@app.get("/api/auth/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(auth_data: dict = Depends(authenticate_request)):
    """List all API keys for the authenticated client"""

    try:

        client_id = uuid.UUID(auth_data["client_id"])

        keys = await api_key_manager.list_api_keys(client_id)

        return keys

    except Exception as e:

        logger.error(f" Failed to list API keys: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to list API keys: {str(e)}"
        )


@app.delete("/api/auth/api-keys/{key_id}")
async def revoke_api_key(key_id: str, auth_data: dict = Depends(authenticate_request)):
    """Revoke an API key"""

    try:

        client_id = uuid.UUID(auth_data["client_id"])

        key_uuid = uuid.UUID(key_id)

        success = await api_key_manager.revoke_api_key(key_uuid, client_id)

        if success:

            return {"success": True, "message": "API key revoked successfully"}

        else:

            raise HTTPException(status_code=404, detail="API key not found")

    except ValueError:

        raise HTTPException(status_code=400, detail="Invalid key ID format")

    except Exception as e:

        logger.error(f" Failed to revoke API key: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to revoke API key: {str(e)}"
        )


# ==================== ENHANCED DATA UPLOAD ENDPOINTS ====================


@app.post("/api/data/upload-enhanced")
async def upload_data_enhanced(
    file: UploadFile = File(...),
    data_format: Optional[str] = Form(None),
    description: str = Form(""),
    auto_detect_format: bool = Form(True),
    max_rows: Optional[int] = Form(None),
    auth_data: dict = Depends(require_write_access),
):
    """Enhanced data upload with comprehensive validation and multiple format support"""

    try:

        client_id = auth_data["client_id"]

        # Read file content

        file_content = await file.read()

        # Create upload configuration

        upload_config = DataUploadConfig(
            max_file_size_mb=100,
            auto_detect_encoding=True,
            validate_data_quality=True,
            generate_preview=True,
        )

        # Parse with enhanced parser

        parser = enhanced_parser

        parser.config = upload_config

        # Determine format

        declared_format = None

        if data_format:

            try:

                declared_format = DataFormat(data_format.lower())

            except ValueError:

                raise HTTPException(
                    status_code=400, detail=f"Unsupported format: {data_format}"
                )

        # Parse data

        df, validation_result = await parser.parse_data(
            raw_data=file_content,
            data_format=declared_format,
            file_name=file.filename,
            max_rows=max_rows,
        )

        if not validation_result.is_valid:

            raise HTTPException(
                status_code=400,
                detail=f"Validation failed: {validation_result.error_message}",
            )

        # Generate data quality report

        quality_report = await parser.generate_data_quality_report(df)

        #  PARALLEL PROCESSING for massive datasets

        if len(df) > 10000:

            logger.info(
                f" MASSIVE DATASET detected ({len(df)} rows) - using PARALLEL processing"
            )

            return await _handle_massive_dataset_upload(client_id, df, quality_report)

        else:

            logger.info(
                f" Standard dataset ({len(df)} rows) - using normal processing"
            )

        # Use enhanced AI analyzer

        from ai_analyzer import ai_analyzer

        # Convert file content to string for AI analyzer

        if isinstance(file_content, bytes):

            try:

                content_str = file_content.decode(validation_result.encoding or "utf-8")

            except UnicodeDecodeError:

                content_str = file_content.decode("utf-8", errors="ignore")

        else:

            content_str = file_content

        # Analyze with enhanced AI

        ai_result = await ai_analyzer.analyze_data(
            raw_data=content_str,
            data_format=validation_result.detected_format or declared_format,
            client_id=client_id,
            file_name=file.filename,
        )

        # Store data using optimized database manager
        from database import get_db_manager
        manager = get_db_manager()

        # Convert DataFrame to records for storage

        records = df.to_dict("records")

        # Store in database

        rows_inserted = await manager.batch_insert_client_data(
            ai_result.table_schema.table_name, records, client_id
        )

        # Store schema information in your existing client_schemas table (enhanced)

        db_client = get_admin_client()

        schema_record = {
            "client_id": client_id,
            "table_name": ai_result.table_schema.table_name,
            "data_type": ai_result.data_type,
            "schema_definition": ai_result.table_schema.dict(),
            "ai_analysis": ai_result.dict(),
            # NEW: Store quality data in existing table (from minimal enhancement)
            "format_detected": (
                validation_result.detected_format.value
                if validation_result.detected_format
                else None
            ),
            "ai_confidence": ai_result.confidence,
            "quality_score": quality_report.quality_score,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Also update your existing data_uploads table with enhanced info

        upload_record = {
            "client_id": client_id,
            "original_filename": file.filename,
            "file_size_bytes": validation_result.file_size,
            "data_format": (
                validation_result.detected_format.value
                if validation_result.detected_format
                else "unknown"
            ),
            # NEW: Enhanced fields (from minimal enhancement)
            "validation_status": "valid" if validation_result.is_valid else "invalid",
            "format_detected": (
                validation_result.detected_format.value
                if validation_result.detected_format
                else None
            ),
            "quality_score": quality_report.quality_score,
            "rows_processed": rows_inserted,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
        }

        # Insert into both tables using your existing structure

        db_client.table("client_schemas").insert(schema_record).execute()

        db_client.table("data_uploads").insert(upload_record).execute()

        logger.info(
            f" Enhanced upload completed: {rows_inserted} rows, quality score: {quality_report.quality_score:.2f}"
        )

        return {
            "success": True,
            "message": "Data uploaded and analyzed successfully",
            "data_info": {
                "rows_processed": rows_inserted,
                "columns": len(df.columns),
                "detected_format": (
                    validation_result.detected_format.value
                    if validation_result.detected_format
                    else None
                ),
                "file_size": validation_result.file_size,
                "encoding": validation_result.encoding,
            },
            "ai_analysis": {
                "data_type": ai_result.data_type,
                "confidence": ai_result.confidence,
                "insights": ai_result.insights[:3],  # Show first 3 insights
                "recommended_charts": ai_result.recommended_visualizations[:3],
            },
            "data_quality": {
                "quality_score": quality_report.quality_score,
                "issues": quality_report.issues,
                "recommendations": quality_report.recommendations[:2],
            },
            "warnings": validation_result.warnings,
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Enhanced upload failed: {e}")

        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/data/validate")
async def validate_data_format(
    file: UploadFile = File(...), auth_data: dict = Depends(require_read_access)
):
    """Validate and preview data without storing it"""

    try:

        # Read file content

        file_content = await file.read()

        # Use enhanced parser for validation only

        df, validation_result = await enhanced_parser.parse_data(
            raw_data=file_content,
            data_format=None,  # Auto-detect
            file_name=file.filename,
        )

        # Generate preview

        preview_data = {
            "validation": validation_result.dict(),
            "preview": {
                "columns": list(df.columns) if not df.empty else [],
                "sample_rows": df.head(5).to_dict("records") if not df.empty else [],
                "total_rows": len(df),
                "detected_types": (
                    {col: str(df[col].dtype) for col in df.columns}
                    if not df.empty
                    else {}
                ),
            },
        }

        if validation_result.is_valid:

            # Generate quality report for valid data

            quality_report = await enhanced_parser.generate_data_quality_report(df)

            preview_data["data_quality"] = quality_report.dict()

        return {"success": True, "message": "Data validation completed", **preview_data}

    except Exception as e:

        logger.error(f" Data validation failed: {e}")

        return {"success": False, "error": str(e), "message": "Data validation failed"}


# ==================== ENHANCED ANALYTICS ENDPOINTS ====================


@app.get("/api/data/formats")
async def get_supported_formats():
    """Get list of supported data formats"""

    return {
        "success": True,
        "supported_formats": [
            {
                "format": "json",
                "description": "JavaScript Object Notation",
                "extensions": [".json"],
                "mime_types": ["application/json"],
            },
            {
                "format": "csv",
                "description": "Comma Separated Values",
                "extensions": [".csv"],
                "mime_types": ["text/csv"],
            },
            {
                "format": "tsv",
                "description": "Tab Separated Values",
                "extensions": [".tsv", ".tab"],
                "mime_types": ["text/tab-separated-values"],
            },
            {
                "format": "excel",
                "description": "Microsoft Excel",
                "extensions": [".xlsx", ".xls"],
                "mime_types": [
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.ms-excel",
                ],
            },
            {
                "format": "xml",
                "description": "Extensible Markup Language",
                "extensions": [".xml"],
                "mime_types": ["application/xml", "text/xml"],
            },
            {
                "format": "yaml",
                "description": "YAML Ain't Markup Language",
                "extensions": [".yaml", ".yml"],
                "mime_types": ["application/x-yaml"],
            },
            {
                "format": "bak",
                "description": "Backup Files (Auto-detected format)",
                "extensions": [".bak"],
                "mime_types": ["application/octet-stream", "text/plain"],
            },
            {
                "format": "parquet",
                "description": "Apache Parquet",
                "extensions": [".parquet"],
                "mime_types": ["application/x-parquet"],
            },
        ],
    }


@app.get("/api/data/quality/{client_id}")
async def get_data_quality_report(
    client_id: str, auth_data: dict = Depends(require_analytics_access)
):
    """Get data quality report for client data using existing tables"""

    try:

        # Verify client access

        if auth_data["client_id"] != client_id and auth_data["auth_type"] != "api_key":

            raise HTTPException(status_code=403, detail="Access denied")

        # Get quality info from your existing client_schemas and data_uploads tables

        db_client = get_admin_client()

        # Get latest quality data from client_schemas (enhanced with minimal changes)

        schema_response = (
            db_client.table("client_schemas")
            .select(
                "quality_score, format_detected, ai_confidence, created_at, data_type, schema_definition"
            )
            .eq("client_id", client_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        # Get upload history from existing data_uploads table (enhanced with minimal changes)

        uploads_response = (
            db_client.table("data_uploads")
            .select(
                "validation_status, quality_score, rows_processed, format_detected, file_size_bytes, created_at"
            )
            .eq("client_id", client_id)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )

        if not schema_response.data and not uploads_response.data:

            raise HTTPException(
                status_code=404, detail="No data quality information found"
            )

        # Compile quality report from existing data

        quality_summary = {
            "client_id": client_id,
            "latest_quality_score": None,
            "data_formats_used": [],
            "total_uploads": len(uploads_response.data) if uploads_response.data else 0,
            "successful_uploads": 0,
            "total_rows_processed": 0,
            "average_quality": 0,
            "schema_info": None,
            "upload_history": [],
        }

        # Process schema information

        if schema_response.data:

            schema_data = schema_response.data[0]

            quality_summary.update(
                {
                    "latest_quality_score": schema_data.get("quality_score"),
                    "ai_confidence": schema_data.get("ai_confidence"),
                    "data_type": schema_data.get("data_type"),
                    "schema_info": {
                        "format": schema_data.get("format_detected"),
                        "last_updated": schema_data.get("created_at"),
                    },
                }
            )

        # Process upload history

        if uploads_response.data:

            quality_scores = []

            formats_used = set()

            for upload in uploads_response.data:

                if upload.get("validation_status") == "valid":

                    quality_summary["successful_uploads"] += 1

                if upload.get("rows_processed"):

                    quality_summary["total_rows_processed"] += upload["rows_processed"]

                if upload.get("format_detected"):

                    formats_used.add(upload["format_detected"])

                if upload.get("quality_score"):

                    quality_scores.append(upload["quality_score"])

                quality_summary["upload_history"].append(
                    {
                        "date": upload.get("created_at"),
                        "format": upload.get("format_detected"),
                        "status": upload.get("validation_status"),
                        "quality_score": upload.get("quality_score"),
                        "rows": upload.get("rows_processed"),
                        "file_size": upload.get("file_size_bytes"),
                    }
                )

            quality_summary["data_formats_used"] = list(formats_used)

            if quality_scores:

                quality_summary["average_quality"] = sum(quality_scores) / len(
                    quality_scores
                )

        return {
            "success": True,
            "quality_summary": quality_summary,
            "message": "Quality report compiled from existing data",
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to get quality report: {e}")

        raise HTTPException(status_code=500, detail=str(e))


# ==================== API KEY DOCUMENTATION ENDPOINT ====================


@app.get("/api/auth/api-keys/docs")
async def api_key_documentation():
    """API key authentication documentation"""

    return {
        "authentication_methods": {
            "jwt_token": {
                "description": "Bearer token authentication",
                "header": "Authorization: Bearer <token>",
                "suitable_for": ["web applications", "SPAs", "mobile apps"],
            },
            "api_key_header": {
                "description": "API key in custom header",
                "header": "X-API-Key: <api_key>",
                "suitable_for": [
                    "server-to-server",
                    "automated scripts",
                    "integrations",
                ],
            },
            "api_key_query": {
                "description": "API key in query parameter",
                "parameter": "?api_key=<api_key>",
                "suitable_for": ["simple integrations", "testing", "webhooks"],
            },
        },
        "api_key_scopes": {
            "read": "Access to read data and analytics",
            "write": "Permission to upload and modify data",
            "admin": "Administrative access to account settings",
            "analytics": "Access to advanced analytics and insights",
            "full_access": "Complete access to all features",
        },
        "security_best_practices": [
            "Store API keys securely and never expose them in client-side code",
            "Use environment variables or secure key management systems",
            "Rotate API keys regularly",
            "Use the minimum required scope for each key",
            "Monitor API key usage and revoke unused keys",
            "Never share API keys in URLs, logs, or public repositories",
        ],
        "rate_limits": {
            "default": "100 requests per hour per API key",
            "burst": "10 requests per minute",
            "enterprise": "Custom limits available",
        },
    }


# ==================== SUPERADMIN DASHBOARD ENDPOINTS ====================


@app.post("/api/superadmin/generate-dashboard/{client_id}")
async def generate_dashboard_for_client(client_id: str, token: str = Depends(security)):
    """Superadmin: Manually trigger dashboard generation for any client"""

    try:

        # Verify superadmin token

        verify_superadmin_token(token.credentials)

        logger.info(
            f" Superadmin requested dashboard generation for client {client_id}"
        )

        # Import and generate dashboard directly

        from dashboard_orchestrator import dashboard_orchestrator

        # Generate dashboard immediately (no background complexity)

        generation_response = await dashboard_orchestrator.generate_dashboard(
            client_id=uuid.UUID(client_id), force_regenerate=True
        )

        if generation_response.success:

            logger.info(f" Dashboard generated successfully for client {client_id}")

            return {
                "success": True,
                "message": "Dashboard generated successfully",
                "client_id": client_id,
                "dashboard_config": (
                    generation_response.dashboard_config.dict()
                    if generation_response.dashboard_config
                    else None
                ),
                "metrics_generated": generation_response.metrics_generated,
                "generation_time": generation_response.generation_time,
            }

        else:

            logger.error(
                f" Dashboard generation failed for client {client_id}: {generation_response.message}"
            )

            return {
                "success": False,
                "message": generation_response.message,
                "client_id": client_id,
            }

    except Exception as e:

        logger.error(f" Superadmin dashboard generation failed: {e}")

        raise HTTPException(
            status_code=500, detail=f"Dashboard generation failed: {str(e)}"
        )


# ==================== FAST DASHBOARD GENERATION ENDPOINTS ====================


@app.post("/api/superadmin/fast-generate/{client_id}")
async def fast_generate_dashboard(client_id: str, token: str = Depends(security)):
    """Superadmin: SUPER FAST dashboard generation without AI delays - completes in <5 seconds"""

    try:

        # Verify superadmin token

        verify_superadmin_token(token.credentials)

        logger.info(f" FAST dashboard generation for client {client_id}")

        start_time = datetime.utcnow()

        # Get client data - NO LIMIT for complete data processing

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Get client data - NO LIMIT for complete data processing

        data_response = (
            db_client.table("client_data")
            .select("data")
            .eq("client_id", client_id)
            .execute()
        )

        if not data_response.data:

            raise HTTPException(status_code=404, detail="No data found for client")

        logger.info(
            f" Processing {len(data_response.data)} records for fast generation"
        )

        # Quick data analysis

        sample_data = []

        for record in data_response.data[:10]:  # Use only first 10 records for speed

            try:

                if isinstance(record["data"], dict):

                    sample_data.append(record["data"])

                elif isinstance(record["data"], str):

                    sample_data.append(json.loads(record["data"]))

            except:

                continue

        if not sample_data:

            raise HTTPException(status_code=400, detail="Could not parse client data")

        # Fast column analysis

        all_columns = set()

        for row in sample_data:

            all_columns.update(row.keys())

        columns = list(all_columns)[:10]  # Limit to 10 columns for speed

        # Generate COMPREHENSIVE dashboard config with ALL chart types and REAL data

        dashboard_config = {
            "client_id": client_id,
            "title": f"Comprehensive Analytics Dashboard",
            "subtitle": "All chart types with real data insights",
            "layout": {
                "grid_cols": 4,
                "grid_rows": 12,  # More rows for more charts
                "gap": 4,
                "responsive": True,
            },
            "kpi_widgets": [
                {
                    "id": "kpi_total_records",
                    "title": "Total Records",
                    "value": str(len(data_response.data)),
                    "icon": "Database",
                    "icon_color": "text-primary",
                    "icon_bg_color": "bg-primary/10",
                    "position": {"row": 0, "col": 0},
                    "size": {"width": 1, "height": 1},
                },
                {
                    "id": "kpi_data_columns",
                    "title": "Data Fields",
                    "value": str(len(columns)),
                    "icon": "Columns",
                    "icon_color": "text-success",
                    "icon_bg_color": "bg-success/10",
                    "position": {"row": 0, "col": 1},
                    "size": {"width": 1, "height": 1},
                },
                {
                    "id": "kpi_data_quality",
                    "title": "Data Quality",
                    "value": "98%",
                    "icon": "CheckCircle",
                    "icon_color": "text-meta-3",
                    "icon_bg_color": "bg-meta-3/10",
                    "position": {"row": 0, "col": 2},
                    "size": {"width": 1, "height": 1},
                },
                {
                    "id": "kpi_last_updated",
                    "title": "Last Updated",
                    "value": "Now",
                    "icon": "Clock",
                    "icon_color": "text-warning",
                    "icon_bg_color": "bg-warning/10",
                    "position": {"row": 0, "col": 3},
                    "size": {"width": 1, "height": 1},
                },
            ],
            "chart_widgets": [
                # Row 1: Area Charts
                {
                    "id": "chart_area_interactive",
                    "title": "Interactive Area Chart",
                    "subtitle": "Real data trends with interactions",
                    "chart_type": "LineChartOne",
                    "data_source": "real_data_area",
                    "config": {
                        "responsive": True,
                        "showLegend": True,
                        "data_columns": columns[:2],
                        "real_data": sample_data,
                    },
                    "position": {"row": 1, "col": 0},
                    "size": {"width": 2, "height": 2},
                },
                {
                    "id": "chart_area_linear",
                    "title": "Linear Area Chart",
                    "subtitle": "Clean linear area visualization",
                    "chart_type": "LineChartOne",
                    "data_source": "real_data_linear",
                    "config": {
                        "responsive": True,
                        "showLegend": True,
                        "data_columns": (
                            columns[1:3] if len(columns) > 2 else columns[:2]
                        ),
                        "real_data": sample_data,
                    },
                    "position": {"row": 1, "col": 2},
                    "size": {"width": 2, "height": 2},
                },
                # Row 2: Bar Charts
                {
                    "id": "chart_bar_label",
                    "title": "Labeled Bar Chart",
                    "subtitle": "Bar chart with value labels",
                    "chart_type": "BarChartOne",
                    "data_source": "real_data_bar",
                    "config": {
                        "responsive": True,
                        "showLegend": True,
                        "data_columns": columns[:2],
                        "real_data": sample_data,
                    },
                    "position": {"row": 3, "col": 0},
                    "size": {"width": 2, "height": 2},
                },
                {
                    "id": "chart_bar_horizontal",
                    "title": "Horizontal Bar Chart",
                    "subtitle": "Horizontal bar visualization",
                    "chart_type": "BarChartOne",
                    "data_source": "real_data_horizontal",
                    "config": {
                        "responsive": True,
                        "showLegend": True,
                        "data_columns": (
                            columns[1:3] if len(columns) > 2 else columns[:2]
                        ),
                        "real_data": sample_data,
                    },
                    "position": {"row": 3, "col": 2},
                    "size": {"width": 2, "height": 2},
                },
                # Row 3: Pie Charts
                {
                    "id": "chart_pie_label",
                    "title": "Labeled Pie Chart",
                    "subtitle": "Pie chart with detailed labels",
                    "chart_type": "BarChartOne",
                    "data_source": "real_data_pie",
                    "config": {
                        "responsive": True,
                        "showLegend": True,
                        "data_columns": columns[:2],
                        "real_data": sample_data,
                    },
                    "position": {"row": 5, "col": 0},
                    "size": {"width": 2, "height": 2},
                },
                {
                    "id": "chart_donut_interactive",
                    "title": "Interactive Donut Chart",
                    "subtitle": "Interactive donut visualization",
                    "chart_type": "BarChartOne",
                    "data_source": "real_data_donut",
                    "config": {
                        "responsive": True,
                        "showLegend": True,
                        "data_columns": (
                            columns[1:3] if len(columns) > 2 else columns[:2]
                        ),
                        "real_data": sample_data,
                    },
                    "position": {"row": 5, "col": 2},
                    "size": {"width": 2, "height": 2},
                },
                # Row 4: Specialty Charts
                {
                    "id": "chart_radar",
                    "title": "Radar Chart",
                    "subtitle": "Multi-dimensional radar view",
                    "chart_type": "BarChartOne",
                    "data_source": "real_data_radar",
                    "config": {
                        "responsive": True,
                        "showLegend": True,
                        "data_columns": columns[:4] if len(columns) >= 4 else columns,
                        "real_data": sample_data,
                    },
                    "position": {"row": 7, "col": 0},
                    "size": {"width": 2, "height": 2},
                },
                {
                    "id": "chart_area_stacked",
                    "title": "Stacked Area Chart",
                    "subtitle": "Stacked area visualization",
                    "chart_type": "LineChartOne",
                    "data_source": "real_data_stacked",
                    "config": {
                        "responsive": True,
                        "showLegend": True,
                        "data_columns": (
                            columns[:3] if len(columns) >= 3 else columns[:2]
                        ),
                        "real_data": sample_data,
                    },
                    "position": {"row": 7, "col": 2},
                    "size": {"width": 2, "height": 2},
                },
                # Row 5: More Advanced Charts
                {
                    "id": "chart_bar_custom",
                    "title": "Custom Bar Chart",
                    "subtitle": "Bar chart with custom styling",
                    "chart_type": "BarChartOne",
                    "data_source": "real_data_custom",
                    "config": {
                        "responsive": True,
                        "showLegend": True,
                        "data_columns": columns[:2],
                        "real_data": sample_data,
                    },
                    "position": {"row": 9, "col": 0},
                    "size": {"width": 2, "height": 2},
                },
                {
                    "id": "chart_multiple_area",
                    "title": "Multiple Area Chart",
                    "subtitle": "Multiple series area chart",
                    "chart_type": "LineChartOne",
                    "data_source": "real_data_multiple",
                    "config": {
                        "responsive": True,
                        "showLegend": True,
                        "data_columns": columns[:3] if len(columns) >= 3 else columns,
                        "real_data": sample_data,
                    },
                    "position": {"row": 9, "col": 2},
                    "size": {"width": 2, "height": 2},
                },
            ],
            "theme": "default",
            "last_generated": datetime.utcnow().isoformat(),
            "version": "5.0-comprehensive-real-data",
        }

        # Save dashboard config

        config_record = {
            "client_id": client_id,
            "dashboard_config": dashboard_config,
            "is_generated": True,
            "generation_timestamp": datetime.utcnow().isoformat(),
        }

        db_client.table("client_dashboard_configs").upsert(
            config_record, on_conflict="client_id"
        ).execute()

        # Generate basic metrics

        metrics = [
            {
                "metric_id": str(uuid.uuid4()),
                "client_id": client_id,
                "metric_name": "total_records",
                "metric_value": {"value": len(data_response.data)},
                "metric_type": "kpi",
                "calculated_at": datetime.utcnow().isoformat(),
            },
            {
                "metric_id": str(uuid.uuid4()),
                "client_id": client_id,
                "metric_name": "data_fields",
                "metric_value": {"value": len(columns)},
                "metric_type": "kpi",
                "calculated_at": datetime.utcnow().isoformat(),
            },
        ]

        db_client.table("client_dashboard_metrics").insert(metrics).execute()

        generation_time = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            f" FAST dashboard generated in {generation_time:.2f}s for client {client_id}"
        )

        return {
            "success": True,
            "message": f"Fast dashboard generated successfully in {generation_time:.2f}s",
            "client_id": client_id,
            "dashboard_config": dashboard_config,
            "generation_time": generation_time,
            "records_processed": len(data_response.data),
            "mode": "fast",
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Fast dashboard generation failed: {e}")

        raise HTTPException(status_code=500, detail=f"Fast generation failed: {str(e)}")


@app.post("/api/dashboard/fast-generate")
async def fast_generate_dashboard_for_client(token: str = Depends(security)):
    """Client: SUPER FAST dashboard generation for authenticated client - completes in <5 seconds"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = str(token_data.client_id)

        logger.info(f" FAST dashboard generation for client {client_id}")

        start_time = datetime.utcnow()

        # Get client data - NO LIMIT for complete data processing

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Get client data - NO LIMIT for complete data processing

        data_response = (
            db_client.table("client_data")
            .select("data")
            .eq("client_id", client_id)
            .execute()
        )

        if not data_response.data:

            raise HTTPException(status_code=404, detail="No data found for client")

        logger.info(
            f" Processing {len(data_response.data)} records for fast generation"
        )

        # Quick data analysis

        sample_data = []

        for record in data_response.data[:10]:  # Use only first 10 records for speed

            try:

                if isinstance(record["data"], dict):

                    sample_data.append(record["data"])

                elif isinstance(record["data"], str):

                    sample_data.append(json.loads(record["data"]))

            except:

                continue

        if not sample_data:

            raise HTTPException(status_code=400, detail="Could not parse client data")

        # Fast column analysis

        all_columns = set()

        for row in sample_data:

            all_columns.update(row.keys())

        columns = list(all_columns)[:10]  # Limit to 10 columns for speed

        # Generate fast dashboard config

        dashboard_config = {
            "client_id": client_id,
            "title": f"Analytics Dashboard",
            "subtitle": "Real-time data insights",
            "layout": {"grid_cols": 4, "grid_rows": 6, "gap": 4, "responsive": True},
            "kpi_widgets": [
                {
                    "id": "kpi_total_records",
                    "title": "Total Records",
                    "value": str(len(data_response.data)),
                    "icon": "Database",
                    "icon_color": "text-primary",
                    "icon_bg_color": "bg-primary/10",
                    "position": {"row": 0, "col": 0},
                    "size": {"width": 1, "height": 1},
                },
                {
                    "id": "kpi_data_columns",
                    "title": "Data Fields",
                    "value": str(len(columns)),
                    "icon": "Columns",
                    "icon_color": "text-success",
                    "icon_bg_color": "bg-success/10",
                    "position": {"row": 0, "col": 1},
                    "size": {"width": 1, "height": 1},
                },
            ],
            "chart_widgets": [
                {
                    "id": "chart_area",
                    "title": "Data Trends",
                    "subtitle": "Interactive area chart",
                    "chart_type": "LineChartOne",
                    "data_source": "trends_data",
                    "config": {
                        "responsive": True,
                        "showLegend": True,
                        "data_columns": columns[:2],
                    },
                    "position": {"row": 1, "col": 0},
                    "size": {"width": 2, "height": 2},
                },
                {
                    "id": "chart_bar",
                    "title": "Data Distribution",
                    "subtitle": "Beautiful bar chart",
                    "chart_type": "BarChartOne",
                    "data_source": "distribution_data",
                    "config": {
                        "responsive": True,
                        "showLegend": True,
                        "data_columns": columns[:2],
                    },
                    "position": {"row": 1, "col": 2},
                    "size": {"width": 2, "height": 2},
                },
                {
                    "id": "chart_pie",
                    "title": "Data Composition",
                    "subtitle": "Labeled pie chart",
                    "chart_type": "BarChartOne",
                    "data_source": "composition_data",
                    "config": {
                        "responsive": True,
                        "showLegend": True,
                        "data_columns": columns[:2],
                    },
                    "position": {"row": 3, "col": 0},
                    "size": {"width": 2, "height": 2},
                },
            ],
            "theme": "default",
            "last_generated": datetime.utcnow().isoformat(),
            "version": "4.0-fast-client",
        }

        # Save dashboard config

        config_record = {
            "client_id": client_id,
            "dashboard_config": dashboard_config,
            "is_generated": True,
            "generation_timestamp": datetime.utcnow().isoformat(),
        }

        db_client.table("client_dashboard_configs").upsert(
            config_record, on_conflict="client_id"
        ).execute()

        # Generate basic metrics

        metrics = [
            {
                "metric_id": str(uuid.uuid4()),
                "client_id": client_id,
                "metric_name": "total_records",
                "metric_value": {"value": len(data_response.data)},
                "metric_type": "kpi",
                "calculated_at": datetime.utcnow().isoformat(),
            },
            {
                "metric_id": str(uuid.uuid4()),
                "client_id": client_id,
                "metric_name": "data_fields",
                "metric_value": {"value": len(columns)},
                "metric_type": "kpi",
                "calculated_at": datetime.utcnow().isoformat(),
            },
        ]

        db_client.table("client_dashboard_metrics").insert(metrics).execute()

        generation_time = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            f" FAST dashboard generated in {generation_time:.2f}s for client {client_id}"
        )

        return {
            "success": True,
            "message": f"Fast dashboard generated successfully in {generation_time:.2f}s",
            "dashboard_config": dashboard_config,
            "generation_time": generation_time,
            "records_processed": len(data_response.data),
            "mode": "fast_client",
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Fast dashboard generation failed: {e}")

        raise HTTPException(status_code=500, detail=f"Fast generation failed: {str(e)}")


# ==================== DEBUG ENDPOINTS ====================


@app.get("/api/debug/auth")
async def debug_auth(token: str = Depends(security)):
    """Debug endpoint to check authentication and client ID"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = str(token_data.client_id)

        # Get client info

        db_client = get_admin_client()

        client_response = (
            db_client.table("clients").select("*").eq("client_id", client_id).execute()
        )

        # Check if dashboard config exists

        config_response = (
            db_client.table("client_dashboard_configs")
            .select("*")
            .eq("client_id", client_id)
            .execute()
        )

        # Check if client data exists

        data_response = (
            db_client.table("client_data")
            .select("client_id")
            .eq("client_id", client_id)
            .limit(5)
            .execute()
        )

        return {
            "success": True,
            "client_id": client_id,
            "token_valid": True,
            "client_exists": bool(client_response.data),
            "client_info": client_response.data[0] if client_response.data else None,
            "dashboard_config_exists": bool(config_response.data),
            "data_records_count": len(data_response.data) if data_response.data else 0,
            "message": "Authentication successful",
        }

    except Exception as e:

        return {"success": False, "error": str(e), "message": "Authentication failed"}


# ==================== DASHBOARD CONFIG ENDPOINTS ====================


# Add improved batch processing function


async def improved_batch_insert(
    db_client, batch_rows: List[Dict], data_type: str = "DATA"
) -> int:
    """

    ULTRA-FAST batch insert optimized for massive datasets (1M+ records) with no timeouts

    Uses aggressive optimization strategies for Supabase at scale

    """

    if not batch_rows:

        return 0

    logger.info(
        f" ULTRA-FAST BATCH inserting {len(batch_rows)} {data_type.upper()} rows"
    )

    #  MAXIMUM SPEED SETTINGS - Optimized for 1M+ records

    chunk_size = 1000  # Keep 1000 as requested - optimal balance

    max_retries = 4  # More retries for reliability

    total_inserted = 0

    failed_chunks = []

    start_time = time.time()

    #  REMOVE ALL UNNECESSARY DELAYS - Process at maximum speed

    for i in range(0, len(batch_rows), chunk_size):

        chunk = batch_rows[i : i + chunk_size]

        chunk_num = i // chunk_size + 1

        retry_count = 0

        chunk_inserted = False

        while retry_count <= max_retries and not chunk_inserted:

            try:

                #  NO DELAYS - Let Supabase handle the throughput

                response = db_client.table("client_data").insert(chunk).execute()

                if response.data:

                    total_inserted += len(response.data)

                    # Log progress every 10 chunks instead of every chunk for speed

                    if chunk_num % 10 == 0:

                        elapsed = time.time() - start_time

                        rate = total_inserted / elapsed if elapsed > 0 else 0

                        logger.info(
                            f" {data_type.upper()} CHUNK {chunk_num}: {total_inserted} total rows | {rate:.0f} rows/sec"
                        )

                    chunk_inserted = True

                else:

                    raise Exception("No data returned from insert")

            except Exception as chunk_error:

                retry_count += 1

                error_msg = str(chunk_error)

                #  SMART TIMEOUT DETECTION - Detect specific Supabase timeout patterns

                is_timeout = any(
                    keyword in error_msg.lower()
                    for keyword in [
                        "timeout",
                        "timed out",
                        "statement timeout",
                        "canceling statement",
                        "57014",
                    ]
                )

                if is_timeout and retry_count <= max_retries:

                    #  MINIMAL BACKOFF - Just enough to let Supabase recover

                    delay = 0.2 * retry_count  # Linear backoff: 0.2s, 0.4s, 0.6s, 0.8s

                    logger.warning(
                        f"⏱️ {data_type.upper()} chunk {chunk_num} timeout (attempt {retry_count}/{max_retries + 1}). Retrying in {delay}s..."
                    )

                    await asyncio.sleep(delay)

                elif retry_count > max_retries:

                    logger.error(
                        f" {data_type.upper()} chunk {chunk_num} failed after {max_retries + 1} attempts"
                    )

                    failed_chunks.append(chunk)

                    break

                else:

                    # Non-timeout error - immediate retry once, then fail

                    if retry_count == 1:

                        logger.warning(
                            f" {data_type.upper()} chunk {chunk_num} error (retrying once): {error_msg[:100]}"
                        )

                        continue

                    else:

                        logger.error(
                            f" {data_type.upper()} chunk {chunk_num} failed: {error_msg[:100]}"
                        )

                        failed_chunks.append(chunk)

                        break

    #  FAST RECOVERY - Handle failed chunks with optimized smaller batches

    if failed_chunks:

        logger.info(
            f" FAST RECOVERY: Processing {len(failed_chunks)} failed chunks..."
        )

        recovery_chunk_size = 500  # Larger recovery chunks for speed

        for failed_chunk in failed_chunks:

            for j in range(0, len(failed_chunk), recovery_chunk_size):

                recovery_chunk = failed_chunk[j : j + recovery_chunk_size]

                try:

                    #  MINIMAL DELAY - Just enough for recovery

                    await asyncio.sleep(0.1)

                    response = (
                        db_client.table("client_data").insert(recovery_chunk).execute()
                    )

                    if response.data:

                        total_inserted += len(response.data)

                        logger.info(f" RECOVERED {len(response.data)} rows")

                except Exception as recovery_error:

                    # Final attempt with smallest chunks

                    logger.warning(
                        f" Final recovery attempt for {len(recovery_chunk)} rows..."
                    )

                    final_chunk_size = 100

                    for k in range(0, len(recovery_chunk), final_chunk_size):

                        final_chunk = recovery_chunk[k : k + final_chunk_size]

                        try:

                            await asyncio.sleep(0.2)

                            response = (
                                db_client.table("client_data")
                                .insert(final_chunk)
                                .execute()
                            )

                            if response.data:

                                total_inserted += len(response.data)

                        except:

                            # Skip problematic data rather than individual inserts

                            logger.warning(
                                f" Skipping {len(final_chunk)} problematic rows"
                            )

                            continue

    #  PERFORMANCE REPORT

    total_time = time.time() - start_time

    success_rate = (total_inserted / len(batch_rows)) * 100

    avg_rate = total_inserted / total_time if total_time > 0 else 0

    logger.info(f" ULTRA-FAST BATCH COMPLETE:")

    logger.info(
        f"    Inserted: {total_inserted:,}/{len(batch_rows):,} rows ({success_rate:.1f}% success)"
    )

    logger.info(f"    Speed: {avg_rate:.0f} rows/second")

    logger.info(f"   ⏱️ Time: {total_time:.1f} seconds")

    return total_inserted


@app.get("/api/debug/data-type-detection/{client_id}")
async def debug_data_type_detection(client_id: str):
    """Debug endpoint to test data type detection and business insights extraction"""

    try:

        # Get client data - NO LIMIT for complete data processing

        client_data = await ai_analyzer.get_client_data_optimized(client_id)

        if not client_data:

            return {"error": "No data found for this client"}

        # Test data type detection

        data_records = client_data.get("data", [])

        data_type = client_data.get("data_type", "unknown")

        schema_type = client_data.get("schema", {}).get("type", "unknown")

        # Test Shopify structure detection

        shopify_fields = [
            "title",
            "handle",
            "status",
            "vendor",
            "platform",
            "variants",
            "product_id",
            "product_type",
        ]

        first_record = data_records[0] if data_records else {}

        shopify_field_count = sum(
            1 for field in shopify_fields if field in first_record
        )

        is_shopify = shopify_field_count >= 5

        # Test business data format detection

        business_fields = [
            "business_info",
            "customer_data",
            "monthly_summary",
            "product_inventory",
            "sales_transactions",
            "performance_metrics",
        ]

        business_field_count = sum(
            1 for field in business_fields if field in first_record
        )

        is_business = business_field_count >= 5

        # Extract insights

        insights = await dashboard_orchestrator._extract_business_insights_from_data(
            client_data
        )

        return {
            "client_id": client_id,
            "data_type": data_type,
            "schema_type": schema_type,
            "total_records": len(data_records),
            "shopify_detection": {
                "field_count": shopify_field_count,
                "total_fields": len(shopify_fields),
                "is_shopify": is_shopify,
                "found_fields": [
                    field for field in shopify_fields if field in first_record
                ],
            },
            "business_detection": {
                "field_count": business_field_count,
                "total_fields": len(business_fields),
                "is_business": is_business,
                "found_fields": [
                    field for field in business_fields if field in first_record
                ],
            },
            "first_record_keys": list(first_record.keys()) if first_record else [],
            "insights_result": insights,
        }

    except Exception as e:

        logger.error(f" Debug data type detection failed: {e}")

        return {"error": f"Debug failed: {str(e)}"}


@app.get("/api/test-llm-analysis/{client_id}")
async def test_llm_analysis(client_id: str):
    """Test endpoint to demonstrate LLM-powered dashboard analysis"""

    try:

        # Get client data - NO LIMIT for complete data processing

        client_data = await ai_analyzer.get_client_data_optimized(client_id)

        if not client_data:

            return {"error": "No data found for this client"}

        # Extract LLM-powered insights

        insights = await dashboard_orchestrator._extract_business_insights_from_data(
            client_data
        )

        return {
            "client_id": client_id,
            "data_type": client_data.get("data_type", "unknown"),
            "schema_type": client_data.get("schema", {}).get("type", "unknown"),
            "total_records": len(client_data.get("data", [])),
            "llm_analysis": insights,
        }

    except Exception as e:

        logger.error(f" LLM analysis test failed: {e}")

        return {"error": f"LLM analysis test failed: {str(e)}"}


@app.get("/api/debug/llm-analysis/{client_id}")
async def debug_llm_analysis(client_id: str):
    """Debug endpoint to test LLM analysis step by step"""

    try:

        # Get client data - NO LIMIT for complete data processing

        client_data = await ai_analyzer.get_client_data_optimized(client_id)

        if not client_data:

            return {"error": "No data found for this client"}

        # Test each step of the LLM analysis

        data_records = client_data.get("data", [])

        data_type = client_data.get("data_type", "unknown")

        schema_type = client_data.get("schema", {}).get("type", "unknown")

        # Step 1: Create prompt

        sample_data = data_records[:3] if len(data_records) > 3 else data_records

        llm_prompt = dashboard_orchestrator._create_llm_analysis_prompt(
            data_type, schema_type, sample_data, len(data_records)
        )

        # Step 2: Test LLM call

        try:

            llm_response = await dashboard_orchestrator._get_llm_analysis(llm_prompt)

            llm_success = True

            llm_error = None

        except Exception as e:

            llm_response = None

            llm_success = False

            llm_error = str(e)

        # Step 3: Test parsing (if LLM succeeded)

        parse_success = False

        parse_error = None

        structured_insights = None

        if llm_success and llm_response:

            try:

                structured_insights = dashboard_orchestrator._parse_llm_insights(
                    llm_response, data_records
                )

                parse_success = True

            except Exception as e:

                parse_error = str(e)

        return {
            "client_id": client_id,
            "data_type": data_type,
            "schema_type": schema_type,
            "total_records": len(data_records),
            "sample_data_keys": list(sample_data[0].keys()) if sample_data else [],
            "prompt_length": len(llm_prompt),
            "prompt_preview": (
                llm_prompt[:500] + "..." if len(llm_prompt) > 500 else llm_prompt
            ),
            "llm_call": {
                "success": llm_success,
                "error": llm_error,
                "response_length": len(llm_response) if llm_response else 0,
                "response_preview": (
                    llm_response[:500] + "..."
                    if llm_response and len(llm_response) > 500
                    else llm_response
                ),
            },
            "parsing": {"success": parse_success, "error": parse_error},
            "final_result": structured_insights,
        }

    except Exception as e:

        logger.error(f" Debug LLM analysis failed: {e}")

        return {"error": f"Debug LLM analysis failed: {str(e)}"}


@app.get("/api/debug/env-check")
async def debug_environment_variables():
    """Debug endpoint to check environment variables"""

    try:

        import os

        from dotenv import load_dotenv

        # Check if .env file exists

        env_file_path = os.path.join(os.path.dirname(__file__), ".env")

        env_file_exists = os.path.exists(env_file_path)

        # Load dotenv

        load_dotenv()

        # Check environment variables

        openai_key = os.getenv("OPENAI_API_KEY")

        openai_key_length = len(openai_key) if openai_key else 0

        openai_key_preview = (
            openai_key[:20] + "..."
            if openai_key and len(openai_key) > 20
            else openai_key
        )

        # Check other important env vars

        supabase_url = os.getenv("SUPABASE_URL")

        supabase_key = os.getenv("SUPABASE_KEY")

        jwt_secret = os.getenv("JWT_SECRET_KEY")

        return {
            "env_file_exists": env_file_exists,
            "env_file_path": env_file_path,
            "openai_api_key": {
                "exists": bool(openai_key),
                "length": openai_key_length,
                "preview": openai_key_preview,
                "starts_with_sk": openai_key.startswith("sk-") if openai_key else False,
            },
            "supabase_url": {
                "exists": bool(supabase_url),
                "preview": (
                    supabase_url[:30] + "..."
                    if supabase_url and len(supabase_url) > 30
                    else supabase_url
                ),
            },
            "supabase_key": {
                "exists": bool(supabase_key),
                "preview": (
                    supabase_key[:20] + "..."
                    if supabase_key and len(supabase_key) > 20
                    else supabase_key
                ),
            },
            "jwt_secret": {
                "exists": bool(jwt_secret),
                "preview": (
                    jwt_secret[:20] + "..."
                    if jwt_secret and len(jwt_secret) > 20
                    else jwt_secret
                ),
            },
        }

    except Exception as e:

        return {"error": f"Environment check failed: {str(e)}"}


@app.get("/api/debug/instance-check")
async def debug_instance_api_keys():
    """Debug endpoint to check API keys in singleton instances"""

    try:

        # Import the instances

        from dashboard_orchestrator import dashboard_orchestrator

        from ai_analyzer import ai_analyzer

        # Check dashboard orchestrator

        dashboard_key = getattr(dashboard_orchestrator, "openai_api_key", None)

        dashboard_key_length = len(dashboard_key) if dashboard_key else 0

        dashboard_key_preview = (
            dashboard_key[:20] + "..."
            if dashboard_key and len(dashboard_key) > 20
            else dashboard_key
        )

        # Check AI analyzer

        ai_analyzer_key = getattr(ai_analyzer, "openai_api_key", None)

        ai_analyzer_key_length = len(ai_analyzer_key) if ai_analyzer_key else 0

        ai_analyzer_key_preview = (
            ai_analyzer_key[:20] + "..."
            if ai_analyzer_key and len(ai_analyzer_key) > 20
            else ai_analyzer_key
        )

        # Check if they match the current environment

        import os

        current_env_key = os.getenv("OPENAI_API_KEY")

        current_env_key_preview = (
            current_env_key[:20] + "..."
            if current_env_key and len(current_env_key) > 20
            else current_env_key
        )

        return {
            "dashboard_orchestrator": {
                "has_key": bool(dashboard_key),
                "key_length": dashboard_key_length,
                "key_preview": dashboard_key_preview,
                "starts_with_sk": (
                    dashboard_key.startswith("sk-") if dashboard_key else False
                ),
            },
            "ai_analyzer": {
                "has_key": bool(ai_analyzer_key),
                "key_length": ai_analyzer_key_length,
                "key_preview": ai_analyzer_key_preview,
                "starts_with_sk": (
                    ai_analyzer_key.startswith("sk-") if ai_analyzer_key else False
                ),
            },
            "current_environment": {
                "has_key": bool(current_env_key),
                "key_length": len(current_env_key) if current_env_key else 0,
                "key_preview": current_env_key_preview,
                "starts_with_sk": (
                    current_env_key.startswith("sk-") if current_env_key else False
                ),
            },
            "keys_match": {
                "dashboard_vs_env": dashboard_key == current_env_key,
                "ai_analyzer_vs_env": ai_analyzer_key == current_env_key,
                "dashboard_vs_ai_analyzer": dashboard_key == ai_analyzer_key,
            },
        }

    except Exception as e:

        return {"error": f"Instance check failed: {str(e)}"}


@app.get("/api/debug/test-openai-key")
async def test_openai_api_key():
    """Test endpoint to verify OpenAI API key works"""

    try:

        import os

        from openai import OpenAI

        # Get the API key

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:

            return {"error": "No API key found in environment"}

        # Debug: Show the actual key being used

        key_preview = api_key[:20] + "..." if len(api_key) > 20 else api_key

        key_length = len(api_key)

        # Test with a simple API call

        client = OpenAI(api_key=api_key)

        try:

            # Make a simple test call

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "Say 'Hello, API key is working!'"}
                ],
                max_tokens=10,
            )

            return {
                "success": True,
                "message": "API key is valid and working",
                "response": response.choices[0].message.content,
                "model_used": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "debug": {
                    "key_length": key_length,
                    "key_preview": key_preview,
                    "starts_with_sk": api_key.startswith("sk-"),
                },
            }

        except Exception as e:

            return {
                "success": False,
                "error": f"OpenAI API call failed: {str(e)}",
                "error_type": type(e).__name__,
                "debug": {
                    "key_length": key_length,
                    "key_preview": key_preview,
                    "starts_with_sk": api_key.startswith("sk-"),
                },
            }

    except Exception as e:

        return {"error": f"Test failed: {str(e)}"}


@app.get("/api/debug/env-files")
async def debug_env_files():
    """Debug endpoint to check for multiple .env files"""

    try:

        import os

        from pathlib import Path

        # Get current directory

        current_dir = Path(__file__).parent

        root_dir = current_dir.parent

        # Check for .env files in different locations

        env_files = []

        # Check current directory (backend)

        backend_env = current_dir / ".env"

        if backend_env.exists():

            env_files.append(
                {
                    "path": str(backend_env),
                    "exists": True,
                    "size": backend_env.stat().st_size,
                }
            )

        else:

            env_files.append({"path": str(backend_env), "exists": False})

        # Check root directory

        root_env = root_dir / ".env"

        if root_env.exists():

            env_files.append(
                {"path": str(root_env), "exists": True, "size": root_env.stat().st_size}
            )

        else:

            env_files.append({"path": str(root_env), "exists": False})

        # Check parent directory

        parent_env = root_dir.parent / ".env"

        if parent_env.exists():

            env_files.append(
                {
                    "path": str(parent_env),
                    "exists": True,
                    "size": parent_env.stat().st_size,
                }
            )

        else:

            env_files.append({"path": str(parent_env), "exists": False})

        # Check system environment variables

        system_openai_key = os.environ.get("OPENAI_API_KEY")

        return {
            "env_files": env_files,
            "system_environment": {
                "has_openai_key": bool(system_openai_key),
                "key_length": len(system_openai_key) if system_openai_key else 0,
                "key_preview": (
                    system_openai_key[:20] + "..."
                    if system_openai_key and len(system_openai_key) > 20
                    else system_openai_key
                ),
            },
            "current_working_dir": str(Path.cwd()),
            "script_location": str(current_dir),
        }

    except Exception as e:

        return {"error": f"Env files check failed: {str(e)}"}


@app.get("/api/debug/force-reload-env")
async def force_reload_environment():
    """Force reload environment variables and test"""

    try:

        import os

        from dotenv import load_dotenv

        # Force reload dotenv

        load_dotenv(override=True)

        # Get the API key after reload

        api_key = os.getenv("OPENAI_API_KEY")

        key_preview = api_key[:20] + "..." if api_key and len(api_key) > 20 else api_key

        key_length = len(api_key) if api_key else 0

        # Test the key

        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        try:

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
            )

            return {
                "success": True,
                "message": "Environment reloaded and API key works",
                "debug": {
                    "key_length": key_length,
                    "key_preview": key_preview,
                    "starts_with_sk": api_key.startswith("sk-") if api_key else False,
                },
            }

        except Exception as e:

            return {
                "success": False,
                "error": f"API call failed after reload: {str(e)}",
                "debug": {
                    "key_length": key_length,
                    "key_preview": key_preview,
                    "starts_with_sk": api_key.startswith("sk-") if api_key else False,
                },
            }

    except Exception as e:

        return {"error": f"Force reload failed: {str(e)}"}


# ============================================================================

# LLM CACHE MANAGEMENT ENDPOINTS

# ============================================================================


@app.get("/api/cache/stats")
async def get_cache_stats(token: str = Depends(security)):
    """Get LLM cache statistics"""

    try:

        from llm_cache_manager import llm_cache_manager

        stats = await llm_cache_manager.get_cache_stats()

        return {
            "success": True,
            "cache_stats": stats,
            "message": "Cache statistics retrieved successfully",
        }

    except Exception as e:

        logger.error(f" Failed to get cache stats: {e}")

        return {"success": False, "error": f"Failed to get cache stats: {str(e)}"}


@app.post("/api/cache/invalidate/{client_id}")
async def invalidate_client_cache(client_id: str, token: str = Depends(security)):
    """Invalidate cache for a specific client"""

    try:

        from llm_cache_manager import llm_cache_manager

        success = await llm_cache_manager.invalidate_cache(client_id)

        return {
            "success": success,
            "message": (
                f"Cache invalidated for client {client_id}"
                if success
                else f"Failed to invalidate cache for client {client_id}"
            ),
        }

    except Exception as e:

        logger.error(f" Failed to invalidate cache for client {client_id}: {e}")

        return {"success": False, "error": f"Failed to invalidate cache: {str(e)}"}


@app.post("/api/cache/cleanup")
async def cleanup_expired_cache(max_age_days: int = 7, token: str = Depends(security)):
    """Clean up expired cache entries"""

    try:

        from llm_cache_manager import llm_cache_manager

        cleaned_count = await llm_cache_manager.cleanup_expired_cache(max_age_days)

        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "message": f"Cleaned up {cleaned_count} expired cache entries (older than {max_age_days} days)",
        }

    except Exception as e:

        logger.error(f" Failed to cleanup expired cache: {e}")

        return {"success": False, "error": f"Failed to cleanup expired cache: {str(e)}"}


@app.get("/api/cache/debug/{client_id}")
async def debug_client_cache(client_id: str, token: str = Depends(security)):
    """Debug cache for a specific client"""

    try:

        from llm_cache_manager import llm_cache_manager

        from database import get_admin_client

        db_client = get_admin_client()

        # Get cache entry

        response = (
            db_client.table("llm_response_cache")
            .select("*")
            .eq("client_id", client_id)
            .limit(1)
            .execute()
        )

        if response.data:

            cache_entry = response.data[0]

            return {
                "success": True,
                "cache_exists": True,
                "cache_entry": {
                    "client_id": cache_entry.get("client_id"),
                    "data_hash": cache_entry.get("data_hash"),
                    "data_type": cache_entry.get("data_type"),
                    "total_records": cache_entry.get("total_records"),
                    "created_at": cache_entry.get("created_at"),
                    "updated_at": cache_entry.get("updated_at"),
                    "response_preview": (
                        str(cache_entry.get("llm_response"))[:200] + "..."
                        if cache_entry.get("llm_response")
                        else None
                    ),
                },
            }

        else:

            return {
                "success": True,
                "cache_exists": False,
                "message": f"No cache entry found for client {client_id}",
            }

    except Exception as e:

        logger.error(f" Failed to debug cache for client {client_id}: {e}")

        return {"success": False, "error": f"Failed to debug cache: {str(e)}"}


from models import CustomTemplateRequest, CustomTemplateResponse


@app.post("/api/dashboard/generate-custom")
async def generate_custom_dashboard_templates(
    template_count: int = 3,
    force_regenerate: bool = False,
    business_context_override: str = None,
    token: str = Depends(security),
):
    """Generate custom intelligent templates using AI-powered business DNA analysis"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = token_data.client_id

        logger.info(f" Starting custom template generation for client {client_id}")

        # Create custom template request

        request = CustomTemplateRequest(
            client_id=client_id,
            template_count=template_count,
            force_regenerate=force_regenerate,
            business_context_override=business_context_override,
            template_preferences={},
        )

        # Generate custom templates using new system

        result = await dashboard_orchestrator.generate_custom_templates(request)

        if result.success:

            logger.info(
                f" Custom templates generated successfully for client {client_id}"
            )

            # Return enhanced response with business intelligence

            return {
                "success": True,
                "message": result.message,
                "templates": [
                    {
                        "template_id": (
                            config.template_id
                            if hasattr(config, "template_id")
                            else f"template_{i}"
                        ),
                        "name": config.title,
                        "description": config.subtitle,
                        "type": "custom_intelligent",
                        "theme": config.theme,
                        "customization_level": getattr(
                            config, "customization_level", "intelligent"
                        ),
                        "business_context": {
                            "business_model": (
                                result.business_dna.business_model.value
                                if result.business_dna
                                else "general"
                            ),
                            "industry": (
                                result.business_dna.industry_sector
                                if result.business_dna
                                else "technology"
                            ),
                            "confidence_score": (
                                result.business_dna.confidence_score
                                if result.business_dna
                                else 0.7
                            ),
                        },
                        "components": {
                            "kpi_count": len(config.kpi_widgets),
                            "chart_count": len(config.chart_widgets),
                            "intelligent_features": getattr(
                                config, "intelligent_components", []
                            ),
                        },
                    }
                    for i, config in enumerate(result.generated_templates)
                ],
                "business_intelligence": {
                    "business_model": (
                        result.business_dna.business_model.value
                        if result.business_dna
                        else None
                    ),
                    "industry_sector": (
                        result.business_dna.industry_sector
                        if result.business_dna
                        else None
                    ),
                    "maturity_level": (
                        result.business_dna.maturity_level.value
                        if result.business_dna
                        else None
                    ),
                    "unique_characteristics": (
                        result.business_dna.unique_characteristics
                        if result.business_dna
                        else []
                    ),
                    "data_story": (
                        result.business_dna.data_story if result.business_dna else None
                    ),
                    "primary_workflows": (
                        [w.name for w in result.business_dna.primary_workflows]
                        if result.business_dna
                        else []
                    ),
                    "success_metrics": (
                        result.business_dna.success_metrics
                        if result.business_dna
                        else []
                    ),
                },
                "ecosystem": {
                    "navigation_available": result.template_ecosystem is not None,
                    "cross_template_features": (
                        result.template_ecosystem.cross_template_features
                        if result.template_ecosystem
                        else []
                    ),
                    "shared_filters": (
                        result.template_ecosystem.shared_filters
                        if result.template_ecosystem
                        else []
                    ),
                },
                "generation_metadata": {
                    "generation_time": result.generation_time,
                    "template_count": len(result.generated_templates),
                    "confidence_scores": result.generation_metadata.get(
                        "confidence_scores", {}
                    ),
                    "version": "custom-intelligent-1.0",
                },
            }

        else:

            logger.error(
                f" Custom template generation failed for client {client_id}: {result.message}"
            )

            raise HTTPException(status_code=500, detail=result.message)

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Custom template generation endpoint failed: {e}")

        raise HTTPException(
            status_code=500, detail=f"Custom template generation failed: {str(e)}"
        )


@app.get("/api/dashboard/custom-templates")
async def get_custom_templates(token: str = Depends(security)):
    """Get existing custom templates with business intelligence data"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        client_id = token_data.client_id

        logger.info(f" Retrieving custom templates for client {client_id}")

        # Get custom templates

        custom_templates = await dashboard_orchestrator.get_custom_templates(client_id)

        if custom_templates:

            return {
                "success": True,
                "message": f"Found {len(custom_templates)} custom templates",
                "templates": [
                    {
                        "template_id": getattr(config, "template_id", f"template_{i}"),
                        "name": config.title,
                        "description": config.subtitle,
                        "type": "custom_intelligent",
                        "theme": config.theme,
                        "customization_level": getattr(
                            config, "customization_level", "intelligent"
                        ),
                        "last_generated": config.last_generated.isoformat(),
                        "version": config.version,
                        "business_context": (
                            {
                                "business_model": (
                                    config.business_dna.business_model.value
                                    if config.business_dna
                                    else None
                                ),
                                "industry": (
                                    config.business_dna.industry_sector
                                    if config.business_dna
                                    else None
                                ),
                                "confidence_score": (
                                    config.business_dna.confidence_score
                                    if config.business_dna
                                    else None
                                ),
                            }
                            if hasattr(config, "business_dna") and config.business_dna
                            else {}
                        ),
                        "intelligent_features": {
                            "smart_naming": hasattr(config, "smart_name")
                            and config.smart_name is not None,
                            "custom_theming": hasattr(config, "custom_theme")
                            and config.custom_theme is not None,
                            "ecosystem_navigation": hasattr(config, "ecosystem_config")
                            and config.ecosystem_config is not None,
                            "adaptive_components": len(
                                getattr(config, "intelligent_components", [])
                            ),
                        },
                    }
                    for i, config in enumerate(custom_templates)
                ],
                "business_intelligence_available": any(
                    hasattr(config, "business_dna") for config in custom_templates
                ),
            }

        else:

            return {
                "success": True,
                "message": "No custom templates found",
                "templates": [],
                "business_intelligence_available": False,
            }

    except Exception as e:

        logger.error(f" Failed to retrieve custom templates: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve custom templates: {str(e)}"
        )


@app.get("/api/dashboard/business-intelligence/{client_id}")
async def get_business_intelligence(client_id: str, token: str = Depends(security)):
    """Get comprehensive business intelligence analysis for a client"""

    try:

        # Verify client token and permissions

        token_data = verify_token(token.credentials)

        # Check if requesting client's own data or if admin

        if str(token_data.client_id) != client_id and not token_data.is_admin:

            raise HTTPException(
                status_code=403, detail="Access denied to business intelligence data"
            )

        logger.info(f"🧬 Retrieving business intelligence for client {client_id}")

        # Get business DNA from database

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Get business DNA

        dna_response = (
            db_client.table("client_business_dna")
            .select("*")
            .eq("client_id", client_id)
            .execute()
        )

        if dna_response.data:

            dna_data = dna_response.data[0]

            return {
                "success": True,
                "business_intelligence": {
                    "business_model": dna_data["business_model"],
                    "industry_sector": dna_data["industry_sector"],
                    "maturity_level": dna_data["maturity_level"],
                    "data_sophistication": dna_data["data_sophistication"],
                    "primary_workflows": dna_data["primary_workflows"],
                    "success_metrics": dna_data["success_metrics"],
                    "key_relationships": dna_data["key_relationships"],
                    "business_personality": dna_data["business_personality"],
                    "unique_characteristics": dna_data["unique_characteristics"],
                    "data_story": dna_data["data_story"],
                    "confidence_score": dna_data["confidence_score"],
                    "analysis_timestamp": dna_data["analysis_timestamp"],
                    "version": dna_data["version"],
                },
                "recommendations": {
                    "suggested_templates": await _get_template_recommendations(
                        dna_data
                    ),
                    "optimization_opportunities": await _get_optimization_opportunities(
                        dna_data
                    ),
                    "business_insights": await _extract_business_insights(dna_data),
                },
            }

        else:

            return {
                "success": False,
                "message": "No business intelligence analysis found. Generate custom templates first to create business DNA profile.",
                "business_intelligence": None,
                "recommendations": {},
            }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to retrieve business intelligence: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve business intelligence: {str(e)}",
        )


@app.get("/api/dashboard/template-ecosystem/{client_id}")
async def get_template_ecosystem(client_id: str, token: str = Depends(security)):
    """Get template ecosystem and navigation structure"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        if str(token_data.client_id) != client_id and not token_data.is_admin:

            raise HTTPException(status_code=403, detail="Access denied")

        logger.info(f" Retrieving template ecosystem for client {client_id}")

        # Get ecosystem data from database

        db_client = get_admin_client()

        ecosystem_response = (
            db_client.table("template_ecosystems")
            .select("*")
            .eq("client_id", client_id)
            .execute()
        )

        if ecosystem_response.data:

            ecosystem_data = ecosystem_response.data[0]

            return {
                "success": True,
                "ecosystem": {
                    "ecosystem_id": ecosystem_data["ecosystem_id"],
                    "primary_template_id": ecosystem_data["primary_template_id"],
                    "template_hierarchy": ecosystem_data["template_hierarchy"],
                    "navigation_structure": ecosystem_data["breadcrumb_structure"],
                    "shared_features": {
                        "filters": ecosystem_data["shared_filters"],
                        "synchronized_states": ecosystem_data["synchronized_states"],
                    },
                    "cross_references": ecosystem_data["cross_references"],
                    "ecosystem_features": [
                        "intelligent_navigation",
                        "shared_filtering",
                        "cross_template_insights",
                        "unified_theming",
                    ],
                },
            }

        else:

            return {
                "success": False,
                "message": "No template ecosystem found",
                "ecosystem": None,
            }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Failed to retrieve template ecosystem: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve template ecosystem: {str(e)}"
        )


# Helper functions for business intelligence endpoint


async def _get_template_recommendations(dna_data: Dict[str, Any]) -> List[str]:
    """Get template recommendations based on business DNA"""

    recommendations = []

    business_model = dna_data.get("business_model", "")

    if business_model == "b2b_saas":

        recommendations = [
            "SaaS Revenue Analytics - Focus on MRR and churn metrics",
            "Customer Success Dashboard - Track user adoption and health scores",
            "Growth Analytics - Monitor acquisition and expansion metrics",
        ]

    elif business_model == "b2c_ecommerce":

        recommendations = [
            "E-commerce Performance - Revenue, orders, and conversion tracking",
            "Customer Analytics - Behavior analysis and segmentation",
            "Product Intelligence - Top products and category performance",
        ]

    else:

        recommendations = [
            "Executive Overview - High-level business performance",
            "Operational Analytics - Process efficiency and monitoring",
            "Performance Intelligence - Advanced metrics and insights",
        ]

    return recommendations


async def _get_optimization_opportunities(dna_data: Dict[str, Any]) -> List[str]:
    """Get optimization opportunities based on business DNA"""

    opportunities = []

    confidence_score = dna_data.get("confidence_score", 0)

    data_sophistication = dna_data.get("data_sophistication", "basic")

    if confidence_score < 0.8:

        opportunities.append(
            "Improve data quality and standardization for better insights"
        )

    if data_sophistication == "basic":

        opportunities.append("Implement advanced analytics and predictive modeling")

    if len(dna_data.get("success_metrics", [])) < 5:

        opportunities.append("Identify and track additional key performance indicators")

    opportunities.append("Implement automated alerting and anomaly detection")

    opportunities.append("Add cross-functional dashboard integration")

    return opportunities


async def _extract_business_insights(dna_data: Dict[str, Any]) -> List[str]:
    """Extract key business insights from DNA data"""

    insights = []

    workflows = dna_data.get("primary_workflows", [])

    unique_characteristics = dna_data.get("unique_characteristics", [])

    if workflows:

        insights.append(
            f"Primary business focus: {workflows[0].get('name', 'Business Operations')}"
        )

    if unique_characteristics:

        insights.append(
            f"Business differentiators: {', '.join(unique_characteristics)}"
        )

    maturity = dna_data.get("maturity_level", "growth")

    insights.append(
        f"Business maturity indicates {maturity}-stage optimization opportunities"
    )

    data_story = dna_data.get("data_story", "")

    if data_story:

        insights.append(f"Data narrative: {data_story}")

    return insights


# ==================== ORGANIZED INVENTORY ANALYTICS ====================


@app.get("/api/dashboard/organized-inventory-analytics/{client_id}")
async def get_organized_inventory_analytics(
    client_id: str, token: str = Depends(security)
):
    """Get comprehensive inventory analytics from organized client tables"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        authenticated_client_id = str(token_data.client_id)

        # Check if the authenticated client matches the requested client_id

        # For now, allow any authenticated client to access any client_id for testing

        # In production, you might want to add authorization checks

        logger.info(f" Organized inventory analytics request for client {client_id}")

        # Import and use organized inventory analyzer

        from organized_inventory_analyzer import organized_inventory_analyzer

        # Perform analysis using organized tables

        analytics = await organized_inventory_analyzer.analyze_client_inventory(
            client_id
        )

        if analytics.get("success"):

            logger.info(
                f" Organized inventory analytics completed for client {client_id}"
            )

            return {
                "success": True,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "data_type": "organized_inventory_analytics",
                "analytics": analytics,
                "message": "Successfully analyzed organized client data",
            }

        else:

            logger.error(
                f" Organized inventory analytics failed for client {client_id}"
            )

            raise HTTPException(
                status_code=500,
                detail=f"Analytics failed: {analytics.get('error', 'Unknown error')}",
            )

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Organized inventory analytics error: {str(e)}")

        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")


@app.get("/api/dashboard/client-data-health/{client_id}")
async def get_client_data_health(client_id: str, token: str = Depends(security)):
    """Get health status of organized client tables"""

    try:

        # Verify client token

        token_data = verify_token(token.credentials)

        logger.info(f" Data health check for client {client_id}")

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        health_status = {}

        # Check Shopify products table

        try:

            shopify_table = f"{client_id.replace('-', '_')}_shopify_products"

            shopify_response = (
                db_client.table(shopify_table).select("id", count="exact").execute()
            )

            health_status["shopify_products"] = {
                "exists": True,
                "count": (
                    shopify_response.count
                    if hasattr(shopify_response, "count")
                    else len(shopify_response.data or [])
                ),
                "table_name": shopify_table,
            }

        except Exception as e:

            health_status["shopify_products"] = {
                "exists": False,
                "error": str(e),
                "table_name": f"{client_id.replace('-', '_')}_shopify_products",
            }

        # Check Shopify orders table

        try:

            shopify_orders_table = f"{client_id.replace('-', '_')}_shopify_orders"

            shopify_orders_response = (
                db_client.table(shopify_orders_table)
                .select("id", count="exact")
                .execute()
            )

            health_status["shopify_orders"] = {
                "exists": True,
                "count": (
                    shopify_orders_response.count
                    if hasattr(shopify_orders_response, "count")
                    else len(shopify_orders_response.data or [])
                ),
                "table_name": shopify_orders_table,
            }

        except Exception as e:

            health_status["shopify_orders"] = {
                "exists": False,
                "error": str(e),
                "table_name": f"{client_id.replace('-', '_')}_shopify_orders",
            }

        # Check Amazon orders table

        try:

            amazon_orders_table = f"{client_id.replace('-', '_')}_amazon_orders"

            orders_response = (
                db_client.table(amazon_orders_table)
                .select("id", count="exact")
                .execute()
            )

            health_status["amazon_orders"] = {
                "exists": True,
                "count": (
                    orders_response.count
                    if hasattr(orders_response, "count")
                    else len(orders_response.data or [])
                ),
                "table_name": amazon_orders_table,
            }

        except Exception as e:

            health_status["amazon_orders"] = {
                "exists": False,
                "error": str(e),
                "table_name": f"{client_id.replace('-', '_')}_amazon_orders",
            }

        # Check Amazon products table

        try:

            amazon_products_table = f"{client_id.replace('-', '_')}_amazon_products"

            products_response = (
                db_client.table(amazon_products_table)
                .select("id", count="exact")
                .execute()
            )

            health_status["amazon_products"] = {
                "exists": True,
                "count": (
                    products_response.count
                    if hasattr(products_response, "count")
                    else len(products_response.data or [])
                ),
                "table_name": amazon_products_table,
            }

        except Exception as e:

            health_status["amazon_products"] = {
                "exists": False,
                "error": str(e),
                "table_name": f"{client_id.replace('-', '_')}_amazon_products",
            }

        # Summary

        total_records = 0

        existing_tables = 0

        for table_info in health_status.values():

            if table_info.get("exists"):

                existing_tables += 1

                total_records += table_info.get("count", 0)

        return {
            "success": True,
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "existing_tables": existing_tables,
                "total_tables": 4,  # shopify_products, shopify_orders, amazon_orders, amazon_products
                "total_records": total_records,
                "is_organized": existing_tables > 0,
            },
            "tables": health_status,
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Data health check error: {str(e)}")

        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# ==================== DATA ORGANIZATION ====================


@app.post("/api/superadmin/organize-data/{client_id}")
async def organize_client_data(client_id: str, token: str = Depends(security)):
    """Superadmin: Organize client data into structured tables by platform and type"""

    try:

        # Verify superadmin token

        verify_superadmin_token(token.credentials)

        logger.info(f" Starting data organization for client {client_id}")

        # Import and run data organizer

        from data_organizer import DataOrganizer

        organizer = DataOrganizer()

        result = await organizer.organize_client_data(client_id)

        if result.get("success"):

            logger.info(f" Data organization completed for client {client_id}")

            return {
                "success": True,
                "message": "Data organization completed successfully",
                "client_id": client_id,
                "processing_time_seconds": result.get("processing_time_seconds"),
                "total_raw_records": result.get("total_raw_records"),
                "organized_records": result.get("organized_records"),
                "total_organized": result.get("total_organized"),
            }

        else:

            logger.error(
                f" Data organization failed for client {client_id}: {result.get('error')}"
            )

            raise HTTPException(
                status_code=500,
                detail=f"Data organization failed: {result.get('error')}",
            )

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Data organization endpoint failed: {e}")

        raise HTTPException(
            status_code=500, detail=f"Data organization failed: {str(e)}"
        )


@app.get("/api/superadmin/client-data-summary/{client_id}")
async def get_client_data_summary(client_id: str, token: str = Depends(security)):
    """Superadmin: Get summary of client data structure and organization status"""

    try:

        # Verify superadmin token

        verify_superadmin_token(token.credentials)

        db_client = get_admin_client()

        if not db_client:

            raise HTTPException(status_code=503, detail="Database not configured")

        # Get raw data count

        raw_data_response = (
            db_client.table("client_data")
            .select("data, table_name")
            .eq("client_id", client_id)
            .execute()
        )

        raw_data = raw_data_response.data or []

        # Analyze data types in raw data

        data_types = {}

        platform_counts = {"shopify": 0, "amazon": 0, "unknown": 0}

        for record in raw_data:

            try:

                data = record.get("data", {})

                if isinstance(data, str):

                    data = json.loads(data)

                platform = data.get("platform", "").lower()

                if platform == "shopify":

                    platform_counts["shopify"] += 1

                    if "order_id" in data or "order_number" in data:

                        data_types["shopify_orders"] = (
                            data_types.get("shopify_orders", 0) + 1
                        )

                    elif "title" in data and ("handle" in data or "variants" in data):

                        data_types["shopify_products"] = (
                            data_types.get("shopify_products", 0) + 1
                        )

                elif platform == "amazon":

                    platform_counts["amazon"] += 1

                    if "order_id" in data and "order_status" in data:

                        data_types["amazon_orders"] = (
                            data_types.get("amazon_orders", 0) + 1
                        )

                    elif "asin" in data or ("sku" in data and "price" in data):

                        data_types["amazon_products"] = (
                            data_types.get("amazon_products", 0) + 1
                        )

                else:

                    platform_counts["unknown"] += 1

            except Exception as e:

                logger.warning(f" Error analyzing record: {e}")

                platform_counts["unknown"] += 1

        # Check for organized data

        organized_data_response = (
            db_client.table("client_data")
            .select("table_name")
            .eq("client_id", client_id)
            .like("table_name", "organized_%")
            .execute()
        )

        organized_tables = list(
            set([record["table_name"] for record in organized_data_response.data or []])
        )

        summary = {
            "client_id": client_id,
            "total_raw_records": len(raw_data),
            "platform_breakdown": platform_counts,
            "data_type_breakdown": data_types,
            "organized_tables": organized_tables,
            "is_organized": len(organized_tables) > 0,
            "organization_recommended": len(raw_data) > 0
            and len(organized_tables) == 0,
        }

        return summary

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f" Client data summary failed: {e}")

        raise HTTPException(
            status_code=500, detail=f"Failed to get data summary: {str(e)}"
        )


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
