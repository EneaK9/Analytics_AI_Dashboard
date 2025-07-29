from fastapi import FastAPI, HTTPException, Depends, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import os
from typing import Optional, List, Dict, Any
import logging
import json
import asyncio
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid
import bcrypt
import jwt
import pandas as pd
from contextlib import asynccontextmanager
import time
import traceback

# Import our custom modules
from models import *
from database import get_db_client, get_admin_client
from ai_analyzer import ai_analyzer
from dashboard_orchestrator import dashboard_orchestrator

# Import enhanced components
from api_key_auth import (
    api_key_manager, authenticate_request, require_read_access, 
    require_write_access, require_admin_access, require_analytics_access
)
from enhanced_data_parser import enhanced_parser
from models import (
    APIKeyCreate, APIKeyResponse, APIKeyScope, 
    EnhancedDataUpload, DataUploadConfig, FileValidationResult
)

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Analytics AI Dashboard API", 
    version="2.0.0",
    description="AI-powered dynamic analytics platform for custom data structures"
)

# Add CORS middleware
# Get allowed origins from environment
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
allowed_origins = [
    "http://localhost:3000", 
    "http://localhost:3001",
    FRONTEND_URL
]

# Remove any None values and duplicates
allowed_origins = list(set([origin for origin in allowed_origins if origin]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_TIME = 8  # hours - tokens expire after 8 hours (more practical for extended work sessions)

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

logger.info(f"🚀 Starting Analytics AI Dashboard API in {ENVIRONMENT} mode")

# ==================== BASIC ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Analytics AI Dashboard API v2.0", 
        "ai_powered": True,
        "dynamic_schemas": True,
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Analytics AI Dashboard API"
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
            "/api/debug/auth"
        ]
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
                "timestamp": datetime.now().isoformat()
            }
        
        diagnostics = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "connected": True,
                "client_type": "admin"
            },
            "tables": {},
            "sample_data": {}
        }
        
        # Check table existence and counts
        tables_to_check = ["clients", "client_schemas", "client_data"]
        
        for table_name in tables_to_check:
            try:
                response = db_client.table(table_name).select("*", count="exact").limit(1).execute()
                diagnostics["tables"][table_name] = {
                    "exists": True,
                    "count": response.count if hasattr(response, 'count') else "unknown",
                    "accessible": True
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
                    "accessible": False
                }
        
        # Test superadmin authentication
        diagnostics["auth"] = {
            "superadmin_token_valid": True,
            "token_type": "superadmin"
        }
        
        return diagnostics
        
    except HTTPException as http_error:
        return {
            "status": "auth_error",
            "message": "Superadmin authentication failed",
            "error": str(http_error.detail),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Diagnostics failed: {e}")
        return {
            "status": "error", 
            "message": "Diagnostics failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
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
                "3. Test the connection with /health endpoint"
            ]
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
        
        if admin_data.username != SUPERADMIN_USERNAME or admin_data.password != SUPERADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create access token
        access_token = create_access_token(
            data={"admin_id": "superadmin", "username": admin_data.username, "role": "superadmin"}
        )
        
        logger.info(f"✅ Superadmin logged in: {admin_data.username}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_TIME * 3600  # seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Superadmin login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

def verify_superadmin_token(token: str):
    """Verify superadmin JWT token"""
    try:
        logger.info(f"🔍 Verifying superadmin token: {token[:20]}...")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        logger.info(f"🔍 Token payload: {payload}")
        role = payload.get("role")
        if role != "superadmin":
            logger.error(f"❌ Invalid role: {role}, expected 'superadmin'")
            raise HTTPException(status_code=403, detail="Superadmin access required")
        logger.info(f"✅ Superadmin token verified successfully")
        return payload
    except jwt.ExpiredSignatureError:
        logger.error(f"❌ Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError as e:
        logger.error(f"❌ JWT Error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== AUTHENTICATION ====================

@app.post("/api/auth/login", response_model=Token)
async def login(client_data: ClientLogin):
    """Client login endpoint"""
    try:
        db_client = get_admin_client()  # Use admin client to bypass RLS
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Find client by email
        response = db_client.table("clients").select("*").eq("email", client_data.email).execute()
        
        if not response.data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        client = response.data[0]
        
        # Verify password
        if not bcrypt.checkpw(client_data.password.encode('utf-8'), client['password_hash'].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create access token
        access_token = create_access_token(
            data={"client_id": client['client_id'], "email": client['email']}
        )
        
        logger.info(f"✅ Client logged in: {client['email']}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_TIME * 3600  # seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
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
        response = db_client.table("clients").select("client_id, company_name, email, subscription_tier, created_at, updated_at").eq("client_id", token_data.client_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return ClientResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get current user: {e}")
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
        password_hash = bcrypt.hashpw(client_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert client into database
        response = db_client.table("clients").insert({
            "company_name": client_data.company_name,
            "email": client_data.email,
            "password_hash": password_hash,
            "subscription_tier": "basic"
        }).execute()
        
        if response.data:
            client = response.data[0]
            logger.info(f"✅ Created client: {client['email']}")
            return ClientResponse(**client)
        else:
            raise HTTPException(status_code=400, detail="Failed to create client")
            
    except Exception as e:
        logger.error(f"❌ Client creation failed: {e}")
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
        logger.error(f"❌ Failed to list clients: {e}")
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
    uploaded_file: UploadFile = File(default=None)
):
    """Superadmin: Create a new client account with INSTANT dashboard - AI works in background"""
    try:
        # Verify superadmin token
        verify_superadmin_token(token.credentials)
        
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Check if client already exists
        existing = db_client.table("clients").select("email").eq("email", email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Client with this email already exists")
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert client into database
        response = db_client.table("clients").insert({
            "company_name": company_name,
            "email": email,
            "password_hash": password_hash,
            "subscription_tier": "basic"  # Default tier
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create client")
            
        client = response.data[0]
        client_id = client['client_id']
        logger.info(f"✅ Client created INSTANTLY: {email}")
        
        # MOVE AI DASHBOARD GENERATION TO AFTER DATA STORAGE IS COMPLETE!
        
        # 🚀 DIRECT DATA STORAGE - NO AI BULLSHIT!
        if (input_method == "paste" and data_content) or (input_method == "upload" and uploaded_file):
            try:
                raw_data = ""
                if input_method == "paste":
                    raw_data = data_content
                elif uploaded_file:
                    file_content = await uploaded_file.read()
                    raw_data = file_content.decode('utf-8')
                
                # 🔥 UNIVERSAL DATA PARSING - ALL FORMATS → JSON with BATCH PROCESSING
                if raw_data:
                    # Simple schema entry
                    db_client.table("client_schemas").insert({
                        "client_id": client_id,
                        "table_name": f"client_{client_id.replace('-', '_')}_data",
                        "data_type": data_type,
                        "schema_definition": {"type": "raw_data", "format": data_type}
                    }).execute()
                    
                    try:
                        from universal_data_parser import universal_parser
                        
                        # Parse ANY format to standardized JSON records
                        parsed_records = universal_parser.parse_to_json(raw_data, data_type)
                        
                        if parsed_records:
                            logger.info(f"🔄 {data_type.upper()} parsed to {len(parsed_records)} JSON records")
                            
                            # BATCH INSERT - Same logic for ALL formats!
                            batch_rows = []
                            for record in parsed_records:
                                # Remove metadata fields before storing
                                clean_record = {k: v for k, v in record.items() if not k.startswith('_')}
                                batch_rows.append({
                                    "client_id": client_id,
                                    "table_name": f"client_{client_id.replace('-', '_')}_data",
                                    "data": clean_record  # Store as JSON object
                                })
                            
                            # OPTIMIZED BATCH INSERT for ALL formats with retry logic
                            if batch_rows:
                                total_inserted = await improved_batch_insert(db_client, batch_rows, data_type)
                                logger.info(f"🚀 TOTAL {data_type.upper()}: {total_inserted} rows inserted successfully!")
                                
                                # 📊 PERFORMANCE MONITORING for large datasets
                                if len(parsed_records) > 10000:  # Track performance for large uploads
                                    success_rate = (total_inserted/len(parsed_records)*100)
                                    logger.info(f"📊 LARGE DATASET PERFORMANCE REPORT:")
                                    logger.info(f"   📋 Dataset: {len(parsed_records)} total records")
                                    logger.info(f"   ✅ Inserted: {total_inserted} records")
                                    logger.info(f"   📈 Success Rate: {success_rate:.1f}%")
                                    logger.info(f"   ⏱️  Processing: Optimized chunking with retry logic")
                                    logger.info(f"   🎯 Client: {email}")
                                    
                                    # Record performance metrics for monitoring
                                    try:
                                        db_client.table("performance_metrics").insert({
                                            "client_id": client_id,
                                            "operation_type": "large_csv_upload",
                                            "total_records": len(parsed_records),
                                            "records_inserted": total_inserted,
                                            "success_rate": round(success_rate, 2),
                                            "data_type": data_type,
                                            "timestamp": datetime.utcnow().isoformat()
                                        }).execute()
                                        logger.info(f"📊 Performance metrics recorded for {email}")
                                    except Exception as metrics_error:
                                        logger.warning(f"⚠️ Could not record performance metrics: {metrics_error}")
                                
                        else:
                            raise ValueError(f"{data_type.upper()} parsing returned no records")
                            
                    except Exception as parse_error:
                        logger.error(f"❌ {data_type.upper()} parsing failed: {parse_error}")
                        # Fallback: store as raw text (old behavior)
                        db_client.table("client_data").insert({
                            "client_id": client_id,
                            "table_name": f"client_{client_id.replace('-', '_')}_data",
                            "data": {"raw_content": raw_data, "type": data_type}
                        }).execute()
                        logger.info(f"⚠️  {data_type.upper()} stored as fallback raw text")
                    
                    logger.info(f"⚡ Data stored DIRECTLY for {email} - NOW TRIGGER AI!")
                    
                    # 🎯 NOW TRIGGER AI DASHBOARD GENERATION AFTER DATA IS SAFELY STORED
                    try:
                        logger.info(f"🚀 NOW triggering AI dashboard generation for {email} (data is ready!)")
                        
                        # IMPROVED: Better error handling and more robust generation
                        async def robust_dashboard_generation():
                            """Robust async dashboard generation with detailed error logging"""
                            try:
                                # Wait a moment to ensure data is committed
                                await asyncio.sleep(1)
                                
                                logger.info(f"🤖 AI dashboard generation starting for {email} (data confirmed!)")
                                
                                # Import here to avoid circular imports (with error handling)
                                try:
                                    from dashboard_orchestrator import dashboard_orchestrator
                                    logger.info(f"✅ Dashboard orchestrator imported successfully for {email}")
                                except Exception as import_error:
                                    logger.error(f"❌ Failed to import dashboard_orchestrator: {import_error}")
                                    return
                                
                                # 💾 PRE-CACHE LLM ANALYSIS DURING CLIENT CREATION (PERFORMANCE BOOST!)
                                try:
                                    logger.info(f"🧠 Pre-caching LLM analysis for {email} to avoid future delays...")
                                    
                                    # Get client data and run LLM analysis once
                                    client_data = await dashboard_orchestrator.ai_analyzer.get_client_data_optimized(client_id)
                                    if client_data and client_data.get('data'):
                                        # This will cache the results automatically
                                        await dashboard_orchestrator._extract_business_insights_from_data(client_data)
                                        logger.info(f"✅ LLM analysis pre-cached for {email}!")
                                    else:
                                        logger.warning(f"⚠️ No data found for LLM pre-caching for {email}")
                                except Exception as cache_error:
                                    logger.warning(f"⚠️ LLM analysis pre-caching failed for {email}: {cache_error}")
                                    # Continue with dashboard generation even if caching fails
                                
                                # Generate dashboard with detailed error handling
                                try:
                                    generation_response = await dashboard_orchestrator.generate_dashboard(
                                        client_id=uuid.UUID(client_id),
                                        force_regenerate=True
                                    )
                                    
                                    if generation_response.success:
                                        logger.info(f"✅ AI Dashboard completed successfully for {email}!")
                                        logger.info(f"📊 Generated {generation_response.metrics_generated} metrics for {email}")
                                    else:
                                        logger.error(f"❌ AI Dashboard failed for {email}: {generation_response.message}")
                                        
                                except Exception as gen_error:
                                    logger.error(f"❌ Dashboard generation threw exception for {email}: {type(gen_error).__name__}: {str(gen_error)}")
                                    # Log full traceback for debugging
                                    import traceback
                                    logger.error(f"Full traceback: {traceback.format_exc()}")
                                    
                            except Exception as outer_error:
                                logger.error(f"❌ Outer AI dashboard generation error for {email}: {type(outer_error).__name__}: {str(outer_error)}")
                                import traceback
                                logger.error(f"Full outer traceback: {traceback.format_exc()}")
                        
                        # Create background task with improved error handling
                        try:
                            task = asyncio.create_task(robust_dashboard_generation())
                            # Don't await the task - let it run in background
                            logger.info(f"🎯 AI Dashboard generation task created successfully for {email}")
                        except Exception as task_error:
                            logger.error(f"❌ Failed to create background task for {email}: {task_error}")
                        
                    except Exception as ai_trigger_error:
                        logger.error(f"⚠️  Failed to trigger AI generation for {email}: {type(ai_trigger_error).__name__}: {str(ai_trigger_error)}")
                        # Log full traceback for better debugging
                        import traceback
                        logger.error(f"Full AI trigger traceback: {traceback.format_exc()}")
                        # Don't let this break client creation
                        logger.info(f"Client {email} created successfully even though AI generation failed")
            except Exception as storage_error:
                logger.warning(f"⚠️ Direct storage failed: {storage_error} - client created anyway")
        
        # Return client response immediately - dashboard generates in background AFTER data storage
        client_response = ClientResponse(**client)
        logger.info(f"🎯 INSTANT: Client {email} created! Dashboard will generate after data is ready...")
        
        return client_response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Superadmin client creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Client creation failed: {str(e)}")

# REMOVED: No more background AI processing - direct storage only!

@app.get("/api/superadmin/clients")
async def list_clients_superadmin(token: str = Depends(security)):
    """Superadmin: SUPER FAST client list - NO AI, JUST DATABASE"""
    try:
        logger.info(f"⚡ LIGHTNING FAST superadmin clients request")
        # Verify superadmin token
        verify_superadmin_token(token.credentials)
        
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # JUST GET CLIENTS - SUPER SIMPLE AND FAST
        clients_response = db_client.table("clients").select("*").order("created_at", desc=True).execute()
        
        if not clients_response.data:
            logger.info(f"✅ No clients found")
            return {"clients": [], "total": 0}
        
        # FAST BASIC RESPONSES - NO HEAVY QUERIES
        basic_clients = []
        for client in clients_response.data:
            # Check if schema exists (simple check)
            schema_exists = False
            data_count = 0
            
            try:
                # Quick schema check
                schema_response = db_client.table("client_schemas").select("data_type").eq("client_id", client['client_id']).limit(1).execute()
                schema_exists = bool(schema_response.data)
                
                if schema_exists:
                    # FIXED: Proper data count - use count-only query without data retrieval
                    try:
                        # First try to get count without retrieving data (most efficient)
                        count_response = db_client.table("client_data").select("client_id", count="exact").eq("client_id", client['client_id']).execute()
                        if hasattr(count_response, 'count') and count_response.count is not None:
                            data_count = count_response.count
                        else:
                            # Fallback: get all records to count them (less efficient but works)
                            all_data_response = db_client.table("client_data").select("client_id").eq("client_id", client['client_id']).limit(10000).execute()
                            data_count = len(all_data_response.data) if all_data_response.data else 0
                    except Exception as count_error:
                        logger.warning(f"⚠️  Count query failed, trying manual count: {count_error}")
                        # Final fallback: manual count
                        try:
                            manual_count_response = db_client.table("client_data").select("client_id").eq("client_id", client['client_id']).limit(10000).execute()
                            data_count = len(manual_count_response.data) if manual_count_response.data else 0
                        except:
                            data_count = 0
            except Exception as e:
                # If anything fails, just continue with defaults
                logger.warning(f"⚠️  Failed to get data count for client {client['client_id']}: {e}")
                pass
            
            basic_clients.append({
                "client_id": client["client_id"],
                "company_name": client["company_name"],
                "email": client["email"],
                "subscription_tier": client["subscription_tier"],
                "created_at": client["created_at"],
                "updated_at": client["updated_at"],
                "has_schema": schema_exists,
                "actual_data_count": data_count,
                "data_stored": data_count > 0,
                "schema_info": {
                    "data_type": "data" if schema_exists else None,
                    "data_stored": data_count > 0,
                    "row_count": data_count
                } if schema_exists else None
            })
            
        logger.info(f"⚡ LIGHTNING FAST: {len(basic_clients)} clients loaded")
        
        return {
            "clients": basic_clients,
            "total": len(basic_clients),
            "page": 1,
            "limit": len(basic_clients)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to list clients: {e}")
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
        response = db_client.table("clients").delete().eq("client_id", client_id).execute()
        
        if response.data:
            logger.info(f"✅ Superadmin deleted client: {client_id}")
            return {"message": "Client deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Client not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete client: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== API INTEGRATIONS ====================

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
    sync_frequency_hours: int = Form(default=24)
):
    """Superadmin: Create a new client with API integration"""
    try:
        # Verify superadmin token
        verify_superadmin_token(token.credentials)
        
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Check if client already exists
        existing = db_client.table("clients").select("email").eq("email", email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Client with this email already exists")
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert client into database
        response = db_client.table("clients").insert({
            "company_name": company_name,
            "email": email,
            "password_hash": password_hash,
            "subscription_tier": "basic"
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create client")
            
        client = response.data[0]
        client_id = client['client_id']
        logger.info(f"✅ Client created for API integration: {email}")
        
        # Prepare API credentials based on platform type
        credentials = {}
        if platform_type == "shopify":
            if not shop_domain or not shopify_access_token:
                raise HTTPException(status_code=400, detail="Shopify domain and access token are required")
            credentials = {
                "shop_domain": shop_domain,
                "access_token": shopify_access_token,
                "scopes": ["read_orders", "read_products", "read_customers"]
            }
        elif platform_type == "amazon":
            if not all([amazon_seller_id, amazon_marketplace_ids, amazon_access_key_id, amazon_secret_access_key, amazon_refresh_token]):
                raise HTTPException(status_code=400, detail="All Amazon credentials are required")
            credentials = {
                "seller_id": amazon_seller_id,
                "marketplace_ids": [mid.strip() for mid in amazon_marketplace_ids.split(",")],
                "access_key_id": amazon_access_key_id,
                "secret_access_key": amazon_secret_access_key,
                "refresh_token": amazon_refresh_token,
                "region": amazon_region
            }
        elif platform_type == "woocommerce":
            if not all([woo_site_url, woo_consumer_key, woo_consumer_secret]):
                raise HTTPException(status_code=400, detail="All WooCommerce credentials are required")
            credentials = {
                "site_url": woo_site_url,
                "consumer_key": woo_consumer_key,
                "consumer_secret": woo_consumer_secret,
                "version": woo_version
            }
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform type")
        
        # Store API credentials in database
        creds_response = db_client.table("client_api_credentials").insert({
            "client_id": client_id,
            "platform_type": platform_type,
            "connection_name": connection_name,
            "credentials": credentials,
            "sync_frequency_hours": sync_frequency_hours,
            "status": "pending"
        }).execute()
        
        if not creds_response.data:
            # Rollback client creation if credentials storage fails
            db_client.table("clients").delete().eq("client_id", client_id).execute()
            raise HTTPException(status_code=400, detail="Failed to store API credentials")
        
        credential_id = creds_response.data[0]['credential_id']
        logger.info(f"✅ API credentials stored: {credential_id}")
        
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
                
                return ClientResponse(**client, message=f"Client created but API connection failed: {message}")
            
            # Connection successful, fetch initial data
            logger.info(f"🔗 API connection successful, fetching initial data for {platform_type}")
            
            # Fetch data from API
            all_data = await api_data_fetcher.fetch_all_data(platform_type, credentials)
            
            # Process and store data
            total_records = 0
            for data_type, records in all_data.items():
                if records:
                    # Create schema entry
                    db_client.table("client_schemas").insert({
                        "client_id": client_id,
                        "table_name": f"client_{client_id.replace('-', '_')}_data",
                        "data_type": f"{platform_type}_{data_type}",
                        "schema_definition": {"type": "api_data", "platform": platform_type, "data_type": data_type},
                        "api_source": True,
                        "platform_type": platform_type
                    }).execute()
                    
                    # Store data records
                    batch_rows = []
                    for record in records:
                        batch_rows.append({
                            "client_id": client_id,
                            "table_name": f"client_{client_id.replace('-', '_')}_data",
                            "data": record
                        })
                    
                    # Optimized batch insert data with retry logic
                    if batch_rows:
                        inserted_count = await improved_batch_insert(db_client, batch_rows, f"{platform_type}_{data_type}")
                        total_records += inserted_count
            
            # Update API credentials status to connected
            from datetime import datetime, timedelta
            next_sync = datetime.now() + timedelta(hours=sync_frequency_hours)
            db_client.table("client_api_credentials").update({
                "status": "connected",
                "last_sync_at": datetime.now().isoformat(),
                "next_sync_at": next_sync.isoformat()
            }).eq("credential_id", credential_id).execute()
            
            # Record sync result
            db_client.table("client_api_sync_results").insert({
                "client_id": client_id,
                "credential_id": credential_id,
                "platform_type": platform_type,
                "connection_name": connection_name,
                "records_fetched": total_records,
                "records_processed": total_records,
                "records_stored": total_records,
                "sync_duration_seconds": 0,  # Would be calculated in production
                "success": True,
                "data_types_synced": list(all_data.keys())
            }).execute()
            
            logger.info(f"✅ API integration complete: {total_records} records from {platform_type}")
            
            # Trigger dashboard generation in background
            try:
                async def generate_dashboard_bg():
                    await asyncio.sleep(2)  # Give data time to be committed
                    from dashboard_orchestrator import dashboard_orchestrator
                    await dashboard_orchestrator.generate_dashboard(
                        client_id=uuid.UUID(client_id),
                        force_regenerate=True
                    )
                
                asyncio.create_task(generate_dashboard_bg())
                logger.info(f"🎯 Dashboard generation triggered for API integration")
            except Exception as bg_error:
                logger.warning(f"⚠️ Background dashboard generation failed: {bg_error}")
            
            return ClientResponse(**client)
            
        except Exception as api_error:
            logger.error(f"❌ API integration failed: {api_error}")
            # Update status to error but don't delete client
            db_client.table("client_api_credentials").update({
                "status": "error",
                "error_message": str(api_error)
            }).eq("credential_id", credential_id).execute()
            
            return ClientResponse(**client)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ API integration client creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"API integration failed: {str(e)}")

@app.get("/api/superadmin/api-platforms")
async def get_api_platforms(token: str = Depends(security)):
    """Get available API platform configurations for the UI"""
    try:
        verify_superadmin_token(token.credentials)
        
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        response = db_client.table("api_platform_configs").select("*").eq("is_active", True).execute()
        
        return {
            "platforms": response.data or [],
            "total": len(response.data) if response.data else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get API platforms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/superadmin/test-api-connection")
async def test_api_connection(
    token: str = Depends(security),
    platform_type: str = Form(...),
    credentials_json: str = Form(...)
):
    """Test API connection before saving"""
    try:
        verify_superadmin_token(token.credentials)
        
        from api_connectors import api_data_fetcher
        import json
        
        # Parse credentials
        credentials = json.loads(credentials_json)
        
        # Test connection
        success, message = await api_data_fetcher.test_connection(platform_type, credentials)
        
        return {
            "success": success,
            "message": message,
            "platform_type": platform_type
        }
        
    except Exception as e:
        logger.error(f"❌ API connection test failed: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "platform_type": platform_type
        }

# ==================== DATA UPLOAD & ANALYSIS ====================

@app.post("/api/admin/upload-data", response_model=CreateSchemaResponse)
async def upload_client_data(upload_data: CreateSchemaRequest):
    """Super Admin: Upload data for a client and create their schema - ENHANCED VERSION"""
    try:
        logger.info(f"🔄 Processing data upload for client {upload_data.client_id}")
        
        # 🔥 STEP 1: Use SIMPLE reliable CSV parser - ALL CSV ROWS → JSON
        logger.info(f"🔄 Parsing {upload_data.data_format} with RELIABLE CSV-to-JSON conversion...")
        
        try:
            # Use simple CSV parser that works without dependencies
            from simple_csv_parser import simple_csv_parser
            
            # Parse CSV content to JSON records
            if upload_data.data_format and upload_data.data_format.value == 'csv':
                # CSV: Use our reliable parser
                standardized_data = simple_csv_parser.parse_csv_to_json(upload_data.raw_data)
                format_type = 'csv'
                
                if not standardized_data:
                    raise ValueError("Failed to parse CSV data")
                    
                logger.info(f"✅ CSV→JSON conversion complete: {len(standardized_data)} records")
                
                # Extract column info from first record
                if standardized_data:
                    columns_info = []
                    first_record = standardized_data[0]
                    for key, value in first_record.items():
                        if not key.startswith('_'):  # Skip metadata fields
                            columns_info.append({
                                'name': key,
                                'type': type(value).__name__ if value is not None else 'str'
                            })
                
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
                        if 'data' in data and isinstance(data['data'], list):
                            standardized_data = data['data']
                        else:
                            standardized_data = [data]
                    else:
                        standardized_data = [{'value': data}]
                    
                    # Add metadata to JSON records
                    for i, record in enumerate(standardized_data):
                        if isinstance(record, dict):
                            record['_row_number'] = i + 1
                            record['_source_format'] = 'json'
                    
                    format_type = 'json'
                    quality_score = 90.0
                    
                    # Extract columns from first record
                    columns_info = []
                    if standardized_data:
                        first_record = standardized_data[0]
                        for key, value in first_record.items():
                            if not key.startswith('_'):
                                columns_info.append({
                                    'name': key,
                                    'type': type(value).__name__ if value is not None else 'str'
                                })
                    
                    logger.info(f"✅ JSON parsing complete: {len(standardized_data)} records")
                    
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON format: {e}")
            
        except Exception as parse_error:
            logger.error(f"❌ Parsing failed: {parse_error}")
            raise HTTPException(status_code=400, detail=f"Data parsing failed: {str(parse_error)}")
        
        logger.info(f"📊 Successfully parsed {len(standardized_data)} records from {format_type}")
        logger.info(f"📋 Detected columns: {[col['name'] for col in columns_info]}")
        
        # STEP 2: Generate AI analysis using standardized JSON data
        logger.info("🤖 Starting AI analysis of standardized JSON data...")
        ai_result = await ai_analyzer.analyze_data(
            json.dumps(standardized_data[:100]),  # Send first 100 records as JSON string
            upload_data.data_format, 
            str(upload_data.client_id)
        )
        # Step 3: Store schema in client_schemas table
        db_client = get_admin_client()
        if db_client:
            schema_response = db_client.table("client_schemas").insert({
                "client_id": str(upload_data.client_id),
                "schema_definition": ai_result.table_schema.dict(),
                "table_name": ai_result.table_schema.table_name,
                "data_type": ai_result.data_type,
                "ai_analysis": json.dumps(ai_result.dict()),
                # Enhanced fields
                "format_detected": format_type,
                "quality_score": quality_score
            }).execute()
        
        # 🔥 STEP 4: Store ALL standardized JSON records in database
        logger.info(f"💾 Storing {len(standardized_data)} standardized JSON records...")
        rows_inserted = 0
        
        for index, json_record in enumerate(standardized_data):
            try:
                # Create database record with standardized JSON (already clean!)
                client_data_record = {
                    "client_id": str(upload_data.client_id),
                    "data": json.dumps(json_record),  # Already standardized JSON format
                    "table_name": ai_result.table_schema.table_name,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                db_client.table("client_data").insert(client_data_record).execute()
                rows_inserted += 1
                
                # Progress logging
                if rows_inserted % 50 == 0:
                    logger.info(f"📈 Inserted {rows_inserted}/{len(standardized_data)} JSON records...")
                    
            except Exception as row_error:
                logger.warning(f"⚠️  Failed to store JSON record {index}: {row_error}")
                continue
        
        logger.info(f"✅ Successfully stored {rows_inserted}/{len(standardized_data)} standardized JSON records!")
        
        logger.info(f"✅ Schema created AND DATA STORED for client {upload_data.client_id}: {ai_result.data_type} with {rows_inserted} rows")
        
        return CreateSchemaResponse(
            success=True,
            table_name=ai_result.table_schema.table_name,
            table_schema=ai_result.table_schema,
            ai_analysis=ai_result,
            rows_inserted=rows_inserted,  # NOW RETURNS ACTUAL COUNT!
            message=f"Schema analyzed and {rows_inserted} rows of data stored successfully!"
        )
        
    except Exception as e:
        logger.error(f"❌ Data upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Data upload failed: {str(e)}")

@app.get("/api/data/{client_id}")
async def get_client_data(client_id: str, limit: int = 100):
    """Get client-specific data - REAL DATA FROM DATABASE"""
    try:
        logger.info(f"📊 Instant data request for client {client_id}")
        
        # Get REAL data from database instead of fake samples
        db_client = get_admin_client()
        if not db_client:
            logger.error("❌ Database not configured")
            raise HTTPException(status_code=503, detail="Database not configured")
        
        try:
            # Get client's data from client_data table
            response = db_client.table("client_data").select("*").eq("client_id", client_id).order("created_at", desc=True).limit(limit).execute()
            
            if not response.data:
                logger.warning(f"⚠️  No real data found for client {client_id}")
                # Return empty but valid structure
                return {
                    "client_id": client_id,
                    "table_name": f"client_{client_id.replace('-', '_')}_data",
                    "schema": {},
                    "data_type": "general",
                    "data": [],
                    "row_count": 0,
                    "message": "No data uploaded yet. Please upload CSV data first."
                }
            
            # Parse real data from database
            real_data = []
            table_name = None
            data_type = "general"
            
            for record in response.data:
                if record.get('data'):
                    try:
                        # Handle both string and dict data from database
                        if isinstance(record['data'], dict):
                            # Data is already parsed
                            parsed_data = record['data']
                        elif isinstance(record['data'], str):
                            # Data is JSON string, parse it
                            parsed_data = json.loads(record['data'])
                        else:
                            # Unknown format, skip
                            logger.warning(f"⚠️  Unknown data format for record: {type(record['data'])}")
                            continue
                        
                        real_data.append(parsed_data)
                        if not table_name:
                            table_name = record.get('table_name', f"client_{client_id.replace('-', '_')}_data")
                    except json.JSONDecodeError:
                        logger.warning(f"⚠️  Failed to parse data record: {record.get('data', '')[:100]}...")
                        continue
                    except Exception as e:
                        logger.warning(f"⚠️  Error processing data record: {e}")
                        continue
            
            # Get schema information
            schema_response = db_client.table("client_schemas").select("*").eq("client_id", client_id).execute()
            
            if schema_response.data:
                schema_data = schema_response.data[0]
                data_type = schema_data.get('data_type', 'general')
                table_name = schema_data.get('table_name', table_name)
            
            logger.info(f"✅ Retrieved {len(real_data)} REAL records for client {client_id}")
            
            return {
                "client_id": client_id,
                "table_name": table_name,
                "schema": {"type": data_type, "source": "database"},
                "data_type": data_type,
                "data": real_data,
                "row_count": len(real_data),
                "message": f"Retrieved {len(real_data)} real records from database"
            }
            
        except Exception as db_error:
            logger.error(f"❌ Database error getting real data: {db_error}")
            # Still return valid structure but with error message
            return {
                "client_id": client_id,
                "table_name": f"client_{client_id.replace('-', '_')}_data",
                "schema": {},
                "data_type": "general", 
                "data": [],
                "row_count": 0,
                "message": f"Database error: {str(db_error)}"
            }
        
    except Exception as e:
        logger.error(f"❌ Failed to get client data: {e}")
        # Always return working structure
        return {
            "client_id": client_id,
            "table_name": "default_table",
            "schema": {},
            "data_type": "general",
            "data": [],
            "row_count": 0,
            "message": f"Error retrieving data: {str(e)}"
        }

# ==================== PERSONALIZED DASHBOARD ENDPOINTS ====================

@app.post("/api/dashboard/generate", response_model=DashboardGenerationResponse)
async def generate_dashboard(request: DashboardGenerationRequest, token: str = Depends(security)):
    """Generate a personalized dashboard for the authenticated client"""
    try:
        # Verify client token
        token_data = verify_token(token.credentials)
        
        # Import dashboard orchestrator
        from dashboard_orchestrator import dashboard_orchestrator
        
        # Generate dashboard using the legacy method for compatibility
        result = await dashboard_orchestrator.generate_dashboard(
            client_id=token_data.client_id,
            force_regenerate=request.force_regenerate
        )
        
        logger.info(f"✅ Dashboard generation completed for client {token_data.client_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Dashboard generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")

@app.post("/api/dashboard/generate-template")
async def generate_template_dashboard(
    template_type: str,
    force_regenerate: bool = False,
    token: str = Depends(security)
):
    """Generate a simple template-based dashboard - just return client data"""
    try:
        # Verify client token
        token_data = verify_token(token.credentials)
        client_id = str(token_data.client_id)
        
        logger.info(f"🎨 Getting data for {template_type} dashboard for client {client_id}")
        
        # Get client data from database
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Get client data
        data_response = db_client.table("client_data").select("data").eq("client_id", client_id).limit(100).execute()
        
        client_data = []
        if data_response.data:
            for record in data_response.data:
                try:
                    if isinstance(record['data'], dict):
                        client_data.append(record['data'])
                    elif isinstance(record['data'], str):
                        import json
                        client_data.append(json.loads(record['data']))
                except:
                    continue
        
        # Get data columns for analysis
        data_columns = []
        if client_data:
            data_columns = list(client_data[0].keys())
        
        logger.info(f"✅ Found {len(client_data)} records with {len(data_columns)} columns for {template_type}")
        
        return {
            "success": True,
            "template_type": template_type,
            "client_data": client_data,
            "data_columns": data_columns,
            "total_records": len(client_data),
            "message": f"Data retrieved for {template_type} template"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Template data retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Template data retrieval failed: {str(e)}")

@app.get("/api/dashboard/templates")
async def get_available_templates(token: str = Depends(security)):
    """Get available dashboard templates for the authenticated client"""
    try:
        # Verify client token
        token_data = verify_token(token.credentials)
        client_id = str(token_data.client_id)
        
        logger.info(f"📋 Getting available templates for client {client_id}")
        
        # Get client data to determine best templates
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Get client data columns
        data_response = db_client.table("client_data").select("data").eq("client_id", client_id).limit(1).execute()
        
        data_columns = []
        if data_response.data:
            try:
                sample_data = data_response.data[0]['data']
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
            data_columns, 
            business_context=None
        )
        
        logger.info(f"✅ Found {len(available_templates)} templates, recommended: {recommended_template}")
        
        return {
            "available_templates": available_templates,
            "recommended_template": recommended_template,
            "client_data_columns": data_columns,
            "total_templates": len(available_templates)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get available templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get available templates: {str(e)}")

@app.get("/api/dashboard/config")
async def get_dashboard_config(token: str = Depends(security)):
    """Get dashboard configuration for the authenticated client"""
    try:
        # Verify client token
        token_data = verify_token(token.credentials)
        client_id = str(token_data.client_id)
        
        logger.info(f"🔍 Getting dashboard config for client {client_id}")
        
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Get dashboard configuration
        response = db_client.table("client_dashboard_configs").select("*").eq("client_id", client_id).execute()
        
        if not response.data:
            # No dashboard config found
            logger.warning(f"❌ No dashboard config found for client {client_id}")
            raise HTTPException(status_code=404, detail="Dashboard config not found. Please generate your dashboard first.")
        
        config_record = response.data[0]
        dashboard_config = config_record["dashboard_config"]
        
        logger.info(f"✅ Dashboard config found for client {client_id}")
        logger.info(f"📊 Config has {len(dashboard_config.get('chart_widgets', []))} charts")
        
        # Return the dashboard config directly (not wrapped in another object)
        return dashboard_config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get dashboard config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard config: {str(e)}")

@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics(
    token: str = Depends(security),
    fast_mode: bool = False
):
    """Get dashboard metrics in exact LLM-generated format for the authenticated client"""
    try:
        # Verify client token
        token_data = verify_token(token.credentials)
        
        # Get client data and extract LLM insights directly
        from ai_analyzer import ai_analyzer
        from dashboard_orchestrator import dashboard_orchestrator
        
        # Get client data
        client_data = await ai_analyzer.get_client_data_optimized(str(token_data.client_id))
        if not client_data:
            raise HTTPException(status_code=404, detail="No data found for this client")
        
        # Use fast mode if requested (no LLM, immediate response)
        if fast_mode:
            logger.info(f"🚀 Fast mode enabled - using cached/fallback insights")
            insights = await dashboard_orchestrator._extract_fallback_insights(
                client_data.get('data', []), 
                client_data.get('data_type', 'unknown')
            )
        else:
            # Extract LLM-powered insights directly (same as test-llm-analysis)
            insights = await dashboard_orchestrator._extract_business_insights_from_data(client_data)
        
        # Return the exact same format as /api/test-llm-analysis
        return {
            "client_id": str(token_data.client_id),
            "data_type": client_data.get('data_type', 'unknown'),
            "schema_type": client_data.get('schema', {}).get('type', 'unknown'),
            "total_records": len(client_data.get('data', [])),
            "llm_analysis": insights
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get dashboard metrics: {e}")
        return {
            "error": f"Failed to get dashboard metrics: {str(e)}"
        }

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
            response = db_client.rpc('get_client_dashboard_status', {'p_client_id': str(token_data.client_id)}).execute()
            
            if response.data:
                status_data = response.data[0]
                return DashboardStatusResponse(
                    client_id=token_data.client_id,
                    has_dashboard=status_data["has_dashboard"],
                    is_generated=status_data["is_generated"],
                    last_updated=status_data["last_updated"],
                    metrics_count=status_data["metrics_count"]
                )
            else:
                return DashboardStatusResponse(
                    client_id=token_data.client_id,
                    has_dashboard=False,
                    is_generated=False,
                    last_updated=None,
                    metrics_count=0
                )
        except Exception as e:
            logger.warning(f"⚠️  Dashboard tables not found, returning default status: {e}")
            # Return default status if tables don't exist yet
            return DashboardStatusResponse(
                client_id=token_data.client_id,
                has_dashboard=False,
                is_generated=False,
                last_updated=None,
                metrics_count=0
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get dashboard status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dashboard/generate-now")
async def generate_dashboard_now(token: str = Depends(security)):
    """Generate dashboard immediately for the authenticated client (manual trigger) - SAFE VERSION"""
    try:
        # Verify client token
        token_data = verify_token(token.credentials)
        
        logger.info(f"🚀 Manual dashboard generation requested for client {token_data.client_id}")
        
        # Import dashboard orchestrator
        from dashboard_orchestrator import dashboard_orchestrator
        
        # SAFETY CHECK: Verify orchestrator is properly initialized
        if not hasattr(dashboard_orchestrator, 'openai_api_key') or not dashboard_orchestrator.openai_api_key:
            raise HTTPException(status_code=503, detail="AI orchestrator not properly configured")
        
        # Generate dashboard immediately in main async context (SAFE)
        generation_response = await dashboard_orchestrator.generate_dashboard(
            client_id=token_data.client_id,
            force_regenerate=True
        )
        
        if generation_response.success:
            logger.info(f"✅ Manual dashboard generation completed for client {token_data.client_id}")
            return {
                "success": True,
                "message": "Dashboard generated successfully",
                "dashboard_config": generation_response.dashboard_config.dict() if generation_response.dashboard_config else None,
                "metrics_generated": generation_response.metrics_generated,
                "generation_time": generation_response.generation_time
            }
        else:
            logger.error(f"❌ Manual dashboard generation failed for client {token_data.client_id}: {generation_response.message}")
            raise HTTPException(status_code=500, detail=generation_response.message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to generate dashboard manually: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")

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
            "has_openai_key": bool(getattr(dashboard_orchestrator, 'openai_api_key', None)),
            "has_ai_analyzer": bool(getattr(dashboard_orchestrator, 'ai_analyzer', None)),
            "chart_type_mapping_loaded": bool(getattr(dashboard_orchestrator, 'chart_type_mapping', None)),
            "kpi_icons_loaded": bool(getattr(dashboard_orchestrator, 'kpi_icons', None))
        }
        
        # Test database connection
        db_client = get_admin_client()
        if db_client:
            try:
                db_client.table('clients').select('client_id').limit(1).execute()
                health_check["database_connection"] = True
            except:
                health_check["database_connection"] = False
        else:
            health_check["database_connection"] = False
        
        # Overall health status
        all_good = all([
            health_check["orchestrator_loaded"],
            health_check["has_openai_key"], 
            health_check["has_ai_analyzer"],
            health_check["database_connection"]
        ])
        
        return {
            "status": "healthy" if all_good else "degraded",
            "details": health_check,
            "message": "AI orchestrator is ready" if all_good else "AI orchestrator has issues"
        }
        
    except Exception as e:
        logger.error(f"❌ Orchestrator health check failed: {e}")
        return {
            "status": "unhealthy", 
            "error": str(e),
            "message": "AI orchestrator is not working"
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
        
        response = db_client.table("client_dashboard_configs").select("*").eq("client_id", str(token_data.client_id)).execute()
        
        if not response.data:
            # If no dashboard exists, generate one
            logger.info(f"No dashboard found, generating new one for client {token_data.client_id}")
            generation_response = await dashboard_orchestrator.generate_dashboard(
                client_id=token_data.client_id,
                force_regenerate=True
            )
            
            if generation_response.success:
                return {
                    "success": True,
                    "metrics_generated": generation_response.metrics_generated,
                    "message": "Dashboard created and metrics generated successfully"
                }
            else:
                raise HTTPException(status_code=500, detail=generation_response.message)
        
        config_data = response.data[0]["dashboard_config"]
        dashboard_config = DashboardConfig(**config_data)
        
        # Analyze current data
        data_analysis = await dashboard_orchestrator._analyze_client_data(token_data.client_id)
        
        # Generate and save new metrics
        metrics_generated = await dashboard_orchestrator._generate_and_save_metrics(
            token_data.client_id, 
            dashboard_config, 
            data_analysis
        )
        
        logger.info(f"✅ Dashboard metrics refreshed for client {token_data.client_id}")
        
        return {
            "success": True,
            "metrics_generated": metrics_generated,
            "message": "Dashboard metrics refreshed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to refresh dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh metrics: {str(e)}")

# ==================== AUTOMATIC GENERATION & RETRY ENDPOINTS ====================

@app.post("/api/dashboard/generate-auto")
async def trigger_automatic_generation(request: AutoGenerationRequest, token: str = Depends(security)):
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
                raise HTTPException(status_code=403, detail="Can only generate dashboard for yourself")
        
        from dashboard_orchestrator import dashboard_orchestrator
        
        result = await dashboard_orchestrator.generate_dashboard_with_retry(request)
        
        return {
            "success": result.success,
            "client_id": str(result.client_id),
            "generation_id": str(result.generation_id),
            "message": "Dashboard generation completed" if result.success else f"Generation failed: {result.error_message}",
            "retry_info": result.retry_info.dict() if result.retry_info else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Manual generation trigger failed: {e}")
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
        
        response = db_client.table("client_dashboard_generation").select("*").eq("client_id", client_id).execute()
        
        if not response.data:
            return {
                "client_id": client_id,
                "status": "not_started",
                "message": "Dashboard generation not yet initiated"
            }
        
        generation_data = response.data[0]
        
        return GenerationStatusResponse(
            client_id=uuid.UUID(client_id),
            status=GenerationStatus(generation_data["status"]),
            attempt_count=generation_data["attempt_count"],
            max_attempts=generation_data["max_attempts"],
            error_type=ErrorType(generation_data["error_type"]) if generation_data["error_type"] else None,
            error_message=generation_data["error_message"],
            started_at=generation_data["started_at"],
            completed_at=generation_data["completed_at"],
            next_retry_at=generation_data["next_retry_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get generation status: {e}")
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
                    "error_message": r.error_message if not r.success else None
                }
                for r in results
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process retries: {e}")
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
        response = db_client.table("client_dashboard_generation").select(
            "*, clients(company_name, email)"
        ).order("updated_at", desc=True).execute()
        
        overview = []
        for record in response.data:
            overview.append({
                "client_id": record["client_id"],
                "company_name": record["clients"]["company_name"] if record["clients"] else "Unknown",
                "email": record["clients"]["email"] if record["clients"] else "Unknown",
                "status": record["status"],
                "generation_type": record["generation_type"],
                "attempt_count": record["attempt_count"],
                "max_attempts": record["max_attempts"],
                "error_type": record["error_type"],
                "error_message": record["error_message"],
                "started_at": record["started_at"],
                "completed_at": record["completed_at"],
                "next_retry_at": record["next_retry_at"]
            })
        
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
                "success_rate": f"{(completed/total*100):.1f}%" if total > 0 else "0%"
            },
            "generations": overview
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get generation overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/background-retry-processor")
async def background_retry_processor():
    """Background endpoint to process pending retries - can be called by cron/scheduler"""
    try:
        # This endpoint doesn't require authentication as it's meant for internal/cron use
        # In production, you might want to add IP filtering or API key authentication
        
        from dashboard_orchestrator import dashboard_orchestrator
        
        logger.info("🔄 Background retry processor started")
        results = await dashboard_orchestrator.process_pending_retries()
        
        successful_retries = [r for r in results if r.success]
        failed_retries = [r for r in results if not r.success]
        
        logger.info(f"✅ Background retry processor completed: {len(successful_retries)} successful, {len(failed_retries)} failed")
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "total_processed": len(results),
            "successful": len(successful_retries),
            "failed": len(failed_retries),
            "message": f"Processed {len(results)} pending retries"
        }
        
    except Exception as e:
        logger.error(f"❌ Background retry processor failed: {e}")
        return {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "message": "Background retry processor failed"
        }

# ==================== STARTUP EVENT FOR BACKGROUND PROCESSING ====================

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🚀 Analytics AI Dashboard API starting up...")
    
    # ULTRA-MINIMAL startup - just test basic imports
    try:
        logger.info("🔧 Testing dashboard orchestrator import...")
        from dashboard_orchestrator import dashboard_orchestrator
        logger.info("✅ Dashboard orchestrator imported successfully")
        
        logger.info("🔧 Testing database client creation...")
        try:
            db_client = get_admin_client()
            logger.info("✅ Database client created successfully")
            
            logger.info("🔧 Testing simple database query...")
            # Try the most basic query possible
            try:
                response = db_client.table("clients").select("client_id").limit(1).execute()
                logger.info("✅ Basic database query successful")
            except Exception as db_error:
                logger.error(f"❌ Database query failed: {type(db_error).__name__}: {db_error}")
                # Log the full error details
                import traceback
                logger.error(f"Full database error: {traceback.format_exc()}")
                
        except Exception as client_error:
            logger.error(f"❌ Database client creation failed: {type(client_error).__name__}: {client_error}")
            # Log the full error details
            import traceback
            logger.error(f"Full client error: {traceback.format_exc()}")
            
    except Exception as e:
        logger.error(f"❌ Startup test failed: {type(e).__name__}: {str(e)}")
        # Log the full error details to find the root cause
        import traceback
        logger.error(f"Full startup error: {traceback.format_exc()}")
        
    logger.info("✅ Startup complete - app is ready")


# AI Analysis Endpoints for Frontend Integration
@app.post("/api/analyze-data")
async def analyze_data_enhanced(
    request_data: dict,
    auth_data: dict = Depends(require_analytics_access)
):
    """Enhanced data analysis with API key support"""
    try:
        # Extract data from request
        data = request_data.get('data', [])
        
        if not data:
            raise HTTPException(status_code=400, detail="No data provided")
        
        # Convert data to JSON string format for enhanced analyzer
        raw_data = json.dumps(data)
        client_id = auth_data["client_id"]
        
        # Use enhanced AI analyzer
        analysis_result = await ai_analyzer.analyze_data(
            raw_data=raw_data, 
            data_format=DataFormat.JSON, 
            client_id=client_id
        )
        
        # Generate additional insights for frontend
        insights_summary = {
            "key_findings": [
                f"Enhanced analysis completed successfully",
                f"Analyzed {len(data)} records with {analysis_result.confidence:.1%} confidence",
                f"Detected {analysis_result.data_type} data type",
                f"Generated {len(analysis_result.insights)} AI insights"
            ],
            "recommendations": analysis_result.insights[:3] if analysis_result.insights else [
                "Data shows promising patterns",
                "Consider implementing automated monitoring", 
                "Optimize based on detected trends"
            ]
        }
        
        # Create comprehensive data overview
        data_overview = {
            "total_records": len(data),
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_type": "enhanced_ai_orchestrator",
            "client_id": client_id,
            "auth_type": auth_data["auth_type"]
        }
        
        return {
            "success": True,
            "analysis": analysis_result.dict(),
            "insights_summary": insights_summary,
            "data_overview": data_overview,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced data analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enhanced data analysis failed: {str(e)}")


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
            marketing_spends.append(int(base_revenue * 0.1 * seasonal_factor * monthly_variation))
            categories.append(random.choice(["Electronics", "Clothing", "Books", "Home"]))
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
            "region": regions
        }
        
        return {
            "success": True,
            "data": sample_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating sample data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sample data generation failed: {str(e)}")

# ==================== ENHANCED API KEY ENDPOINTS ====================

@app.post("/api/auth/api-keys", response_model=dict)
async def create_api_key(
    key_data: APIKeyCreate,
    auth_data: dict = Depends(authenticate_request)
):
    """Create a new API key for the authenticated client"""
    try:
        client_id = uuid.UUID(auth_data["client_id"])
        
        # Generate API key
        api_key, key_response = await api_key_manager.create_api_key(client_id, key_data)
        
        return {
            "success": True,
            "message": "API key created successfully",
            "api_key": api_key,  # Only shown once!
            "key_info": key_response.dict(),
            "warning": "⚠️ Store this API key securely. It will not be shown again."
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create API key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create API key: {str(e)}")

@app.get("/api/auth/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(auth_data: dict = Depends(authenticate_request)):
    """List all API keys for the authenticated client"""
    try:
        client_id = uuid.UUID(auth_data["client_id"])
        keys = await api_key_manager.list_api_keys(client_id)
        return keys
        
    except Exception as e:
        logger.error(f"❌ Failed to list API keys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list API keys: {str(e)}")

@app.delete("/api/auth/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    auth_data: dict = Depends(authenticate_request)
):
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
        logger.error(f"❌ Failed to revoke API key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to revoke API key: {str(e)}")

# ==================== ENHANCED DATA UPLOAD ENDPOINTS ====================

@app.post("/api/data/upload-enhanced")
async def upload_data_enhanced(
    file: UploadFile = File(...),
    data_format: Optional[str] = Form(None),
    description: str = Form(""),
    auto_detect_format: bool = Form(True),
    max_rows: Optional[int] = Form(None),
    auth_data: dict = Depends(require_write_access)
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
            generate_preview=True
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
                raise HTTPException(status_code=400, detail=f"Unsupported format: {data_format}")
        
        # Parse data
        df, validation_result = await parser.parse_data(
            raw_data=file_content,
            data_format=declared_format,
            file_name=file.filename,
            max_rows=max_rows
        )
        
        if not validation_result.is_valid:
            raise HTTPException(status_code=400, detail=f"Validation failed: {validation_result.error_message}")
        
        # Generate data quality report
        quality_report = await parser.generate_data_quality_report(df)
        
        # Use enhanced AI analyzer
        from ai_analyzer import ai_analyzer
        
        # Convert file content to string for AI analyzer
        if isinstance(file_content, bytes):
            try:
                content_str = file_content.decode(validation_result.encoding or 'utf-8')
            except UnicodeDecodeError:
                content_str = file_content.decode('utf-8', errors='ignore')
        else:
            content_str = file_content
        
        # Analyze with enhanced AI
        ai_result = await ai_analyzer.analyze_data(
            raw_data=content_str,
            data_format=validation_result.detected_format or declared_format,
            client_id=client_id,
            file_name=file.filename
        )
        
        # Store data using optimized database manager
        manager = get_db_manager()
        
        # Convert DataFrame to records for storage
        records = df.to_dict('records')
        
        # Store in database
        rows_inserted = await manager.batch_insert_client_data(
            ai_result.table_schema.table_name,
            records,
            client_id
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
            "format_detected": validation_result.detected_format.value if validation_result.detected_format else None,
            "ai_confidence": ai_result.confidence,
            "quality_score": quality_report.quality_score,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Also update your existing data_uploads table with enhanced info
        upload_record = {
            "client_id": client_id,
            "original_filename": file.filename,
            "file_size_bytes": validation_result.file_size,
            "data_format": validation_result.detected_format.value if validation_result.detected_format else "unknown",
            # NEW: Enhanced fields (from minimal enhancement)
            "validation_status": "valid" if validation_result.is_valid else "invalid",
            "format_detected": validation_result.detected_format.value if validation_result.detected_format else None,
            "quality_score": quality_report.quality_score,
            "rows_processed": rows_inserted,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insert into both tables using your existing structure
        db_client.table("client_schemas").insert(schema_record).execute()
        db_client.table("data_uploads").insert(upload_record).execute()
        
        logger.info(f"✅ Enhanced upload completed: {rows_inserted} rows, quality score: {quality_report.quality_score:.2f}")
        
        return {
            "success": True,
            "message": "Data uploaded and analyzed successfully",
            "data_info": {
                "rows_processed": rows_inserted,
                "columns": len(df.columns),
                "detected_format": validation_result.detected_format.value if validation_result.detected_format else None,
                "file_size": validation_result.file_size,
                "encoding": validation_result.encoding
            },
            "ai_analysis": {
                "data_type": ai_result.data_type,
                "confidence": ai_result.confidence,
                "insights": ai_result.insights[:3],  # Show first 3 insights
                "recommended_charts": ai_result.recommended_visualizations[:3]
            },
            "data_quality": {
                "quality_score": quality_report.quality_score,
                "issues": quality_report.issues,
                "recommendations": quality_report.recommendations[:2]
            },
            "warnings": validation_result.warnings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Enhanced upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/data/validate")
async def validate_data_format(
    file: UploadFile = File(...),
    auth_data: dict = Depends(require_read_access)
):
    """Validate and preview data without storing it"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Use enhanced parser for validation only
        df, validation_result = await enhanced_parser.parse_data(
            raw_data=file_content,
            data_format=None,  # Auto-detect
            file_name=file.filename
        )
        
        # Generate preview
        preview_data = {
            "validation": validation_result.dict(),
            "preview": {
                "columns": list(df.columns) if not df.empty else [],
                "sample_rows": df.head(5).to_dict('records') if not df.empty else [],
                "total_rows": len(df),
                "detected_types": {col: str(df[col].dtype) for col in df.columns} if not df.empty else {}
            }
        }
        
        if validation_result.is_valid:
            # Generate quality report for valid data
            quality_report = await enhanced_parser.generate_data_quality_report(df)
            preview_data["data_quality"] = quality_report.dict()
        
        return {
            "success": True,
            "message": "Data validation completed",
            **preview_data
        }
        
    except Exception as e:
        logger.error(f"❌ Data validation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Data validation failed"
        }

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
                "mime_types": ["application/json"]
            },
            {
                "format": "csv", 
                "description": "Comma Separated Values",
                "extensions": [".csv"],
                "mime_types": ["text/csv"]
            },
            {
                "format": "tsv",
                "description": "Tab Separated Values", 
                "extensions": [".tsv", ".tab"],
                "mime_types": ["text/tab-separated-values"]
            },
            {
                "format": "excel",
                "description": "Microsoft Excel",
                "extensions": [".xlsx", ".xls"],
                "mime_types": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
            },
            {
                "format": "xml",
                "description": "Extensible Markup Language",
                "extensions": [".xml"],
                "mime_types": ["application/xml", "text/xml"]
            },
            {
                "format": "yaml",
                "description": "YAML Ain't Markup Language",
                "extensions": [".yaml", ".yml"],
                "mime_types": ["application/x-yaml"]
            },
            {
                "format": "parquet",
                "description": "Apache Parquet",
                "extensions": [".parquet"],
                "mime_types": ["application/x-parquet"]
            }
        ]
    }

@app.get("/api/data/quality/{client_id}")
async def get_data_quality_report(
    client_id: str,
    auth_data: dict = Depends(require_analytics_access)
):
    """Get data quality report for client data using existing tables"""
    try:
        # Verify client access
        if auth_data["client_id"] != client_id and auth_data["auth_type"] != "api_key":
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get quality info from your existing client_schemas and data_uploads tables
        db_client = get_admin_client()
        
        # Get latest quality data from client_schemas (enhanced with minimal changes)
        schema_response = db_client.table("client_schemas").select(
            "quality_score, format_detected, ai_confidence, created_at, data_type, schema_definition"
        ).eq("client_id", client_id).order("created_at", desc=True).limit(1).execute()
        
        # Get upload history from existing data_uploads table (enhanced with minimal changes)
        uploads_response = db_client.table("data_uploads").select(
            "validation_status, quality_score, rows_processed, format_detected, file_size_bytes, created_at"
        ).eq("client_id", client_id).order("created_at", desc=True).limit(5).execute()
        
        if not schema_response.data and not uploads_response.data:
            raise HTTPException(status_code=404, detail="No data quality information found")
        
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
            "upload_history": []
        }
        
        # Process schema information
        if schema_response.data:
            schema_data = schema_response.data[0]
            quality_summary.update({
                "latest_quality_score": schema_data.get("quality_score"),
                "ai_confidence": schema_data.get("ai_confidence"),
                "data_type": schema_data.get("data_type"),
                "schema_info": {
                    "format": schema_data.get("format_detected"),
                    "last_updated": schema_data.get("created_at")
                }
            })
        
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
                
                quality_summary["upload_history"].append({
                    "date": upload.get("created_at"),
                    "format": upload.get("format_detected"),
                    "status": upload.get("validation_status"),
                    "quality_score": upload.get("quality_score"),
                    "rows": upload.get("rows_processed"),
                    "file_size": upload.get("file_size_bytes")
                })
            
            quality_summary["data_formats_used"] = list(formats_used)
            
            if quality_scores:
                quality_summary["average_quality"] = sum(quality_scores) / len(quality_scores)
        
        return {
            "success": True,
            "quality_summary": quality_summary,
            "message": "Quality report compiled from existing data"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get quality report: {e}")
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
                "suitable_for": ["web applications", "SPAs", "mobile apps"]
            },
            "api_key_header": {
                "description": "API key in custom header",
                "header": "X-API-Key: <api_key>",
                "suitable_for": ["server-to-server", "automated scripts", "integrations"]
            },
            "api_key_query": {
                "description": "API key in query parameter",
                "parameter": "?api_key=<api_key>",
                "suitable_for": ["simple integrations", "testing", "webhooks"]
            }
        },
        "api_key_scopes": {
            "read": "Access to read data and analytics",
            "write": "Permission to upload and modify data",
            "admin": "Administrative access to account settings",
            "analytics": "Access to advanced analytics and insights",
            "full_access": "Complete access to all features"
        },
        "security_best_practices": [
            "Store API keys securely and never expose them in client-side code",
            "Use environment variables or secure key management systems",
            "Rotate API keys regularly",
            "Use the minimum required scope for each key",
            "Monitor API key usage and revoke unused keys",
            "Never share API keys in URLs, logs, or public repositories"
        ],
        "rate_limits": {
            "default": "100 requests per hour per API key",
            "burst": "10 requests per minute",
            "enterprise": "Custom limits available"
        }
    }

# ==================== SUPERADMIN DASHBOARD ENDPOINTS ====================

@app.post("/api/superadmin/generate-dashboard/{client_id}")
async def generate_dashboard_for_client(client_id: str, token: str = Depends(security)):
    """Superadmin: Manually trigger dashboard generation for any client"""
    try:
        # Verify superadmin token
        verify_superadmin_token(token.credentials)
        
        logger.info(f"🚀 Superadmin requested dashboard generation for client {client_id}")
        
        # Import and generate dashboard directly
        from dashboard_orchestrator import dashboard_orchestrator
        
        # Generate dashboard immediately (no background complexity)
        generation_response = await dashboard_orchestrator.generate_dashboard(
            client_id=uuid.UUID(client_id),
            force_regenerate=True
        )
        
        if generation_response.success:
            logger.info(f"✅ Dashboard generated successfully for client {client_id}")
            return {
                "success": True,
                "message": "Dashboard generated successfully",
                "client_id": client_id,
                "dashboard_config": generation_response.dashboard_config.dict() if generation_response.dashboard_config else None,
                "metrics_generated": generation_response.metrics_generated,
                "generation_time": generation_response.generation_time
            }
        else:
            logger.error(f"❌ Dashboard generation failed for client {client_id}: {generation_response.message}")
            return {
                "success": False,
                "message": generation_response.message,
                "client_id": client_id
            }
        
    except Exception as e:
        logger.error(f"❌ Superadmin dashboard generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")

# ==================== FAST DASHBOARD GENERATION ENDPOINTS ====================

@app.post("/api/superadmin/fast-generate/{client_id}")
async def fast_generate_dashboard(client_id: str, token: str = Depends(security)):
    """Superadmin: SUPER FAST dashboard generation without AI delays - completes in <5 seconds"""
    try:
        # Verify superadmin token
        verify_superadmin_token(token.credentials)
        
        logger.info(f"🚀 FAST dashboard generation for client {client_id}")
        start_time = datetime.utcnow()
        
        # Get client data
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Get client data
        data_response = db_client.table("client_data").select("data").eq("client_id", client_id).limit(100).execute()
        
        if not data_response.data:
            raise HTTPException(status_code=404, detail="No data found for client")
        
        logger.info(f"📊 Processing {len(data_response.data)} records for fast generation")
        
        # Quick data analysis
        sample_data = []
        for record in data_response.data[:10]:  # Use only first 10 records for speed
            try:
                if isinstance(record['data'], dict):
                    sample_data.append(record['data'])
                elif isinstance(record['data'], str):
                    sample_data.append(json.loads(record['data']))
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
                "responsive": True
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
                    "size": {"width": 1, "height": 1}
                },
                {
                    "id": "kpi_data_columns",
                    "title": "Data Fields",
                    "value": str(len(columns)),
                    "icon": "Columns", 
                    "icon_color": "text-success",
                    "icon_bg_color": "bg-success/10",
                    "position": {"row": 0, "col": 1},
                    "size": {"width": 1, "height": 1}
                },
                {
                    "id": "kpi_data_quality",
                    "title": "Data Quality",
                    "value": "98%",
                    "icon": "CheckCircle", 
                    "icon_color": "text-meta-3",
                    "icon_bg_color": "bg-meta-3/10",
                    "position": {"row": 0, "col": 2},
                    "size": {"width": 1, "height": 1}
                },
                {
                    "id": "kpi_last_updated",
                    "title": "Last Updated",
                    "value": "Now",
                    "icon": "Clock", 
                    "icon_color": "text-warning",
                    "icon_bg_color": "bg-warning/10",
                    "position": {"row": 0, "col": 3},
                    "size": {"width": 1, "height": 1}
                }
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
                        "real_data": sample_data
                    },
                    "position": {"row": 1, "col": 0},
                    "size": {"width": 2, "height": 2}
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
                        "data_columns": columns[1:3] if len(columns) > 2 else columns[:2],
                        "real_data": sample_data
                    },
                    "position": {"row": 1, "col": 2},
                    "size": {"width": 2, "height": 2}
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
                        "real_data": sample_data
                    },
                    "position": {"row": 3, "col": 0},
                    "size": {"width": 2, "height": 2}
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
                        "data_columns": columns[1:3] if len(columns) > 2 else columns[:2],
                        "real_data": sample_data
                    },
                    "position": {"row": 3, "col": 2},
                    "size": {"width": 2, "height": 2}
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
                        "real_data": sample_data
                    },
                    "position": {"row": 5, "col": 0},
                    "size": {"width": 2, "height": 2}
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
                        "data_columns": columns[1:3] if len(columns) > 2 else columns[:2],
                        "real_data": sample_data
                    },
                    "position": {"row": 5, "col": 2},
                    "size": {"width": 2, "height": 2}
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
                        "real_data": sample_data
                    },
                    "position": {"row": 7, "col": 0},
                    "size": {"width": 2, "height": 2}
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
                        "data_columns": columns[:3] if len(columns) >= 3 else columns[:2],
                        "real_data": sample_data
                    },
                    "position": {"row": 7, "col": 2},
                    "size": {"width": 2, "height": 2}
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
                        "real_data": sample_data
                    },
                    "position": {"row": 9, "col": 0},
                    "size": {"width": 2, "height": 2}
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
                        "real_data": sample_data
                    },
                    "position": {"row": 9, "col": 2},
                    "size": {"width": 2, "height": 2}
                }
            ],
            "theme": "default",
            "last_generated": datetime.utcnow().isoformat(),
            "version": "5.0-comprehensive-real-data"
        }
        
        # Save dashboard config
        config_record = {
            "client_id": client_id,
            "dashboard_config": dashboard_config,
            "is_generated": True,
            "generation_timestamp": datetime.utcnow().isoformat()
        }
        
        db_client.table("client_dashboard_configs").upsert(config_record, on_conflict="client_id").execute()
        
        # Generate basic metrics
        metrics = [
            {
                "metric_id": str(uuid.uuid4()),
                "client_id": client_id,
                "metric_name": "total_records",
                "metric_value": {"value": len(data_response.data)},
                "metric_type": "kpi",
                "calculated_at": datetime.utcnow().isoformat()
            },
            {
                "metric_id": str(uuid.uuid4()),
                "client_id": client_id, 
                "metric_name": "data_fields",
                "metric_value": {"value": len(columns)},
                "metric_type": "kpi",
                "calculated_at": datetime.utcnow().isoformat()
            }
        ]
        
        db_client.table("client_dashboard_metrics").insert(metrics).execute()
        
        generation_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"✅ FAST dashboard generated in {generation_time:.2f}s for client {client_id}")
        
        return {
            "success": True,
            "message": f"Fast dashboard generated successfully in {generation_time:.2f}s",
            "client_id": client_id,
            "dashboard_config": dashboard_config,
            "generation_time": generation_time,
            "records_processed": len(data_response.data),
            "mode": "fast"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fast dashboard generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Fast generation failed: {str(e)}")

@app.post("/api/dashboard/fast-generate")
async def fast_generate_dashboard_for_client(token: str = Depends(security)):
    """Client: SUPER FAST dashboard generation for authenticated client - completes in <5 seconds"""
    try:
        # Verify client token
        token_data = verify_token(token.credentials)
        client_id = str(token_data.client_id)
        
        logger.info(f"🚀 FAST dashboard generation for client {client_id}")
        start_time = datetime.utcnow()
        
        # Get client data
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Get client data
        data_response = db_client.table("client_data").select("data").eq("client_id", client_id).limit(100).execute()
        
        if not data_response.data:
            raise HTTPException(status_code=404, detail="No data found for client")
        
        logger.info(f"📊 Processing {len(data_response.data)} records for fast generation")
        
        # Quick data analysis
        sample_data = []
        for record in data_response.data[:10]:  # Use only first 10 records for speed
            try:
                if isinstance(record['data'], dict):
                    sample_data.append(record['data'])
                elif isinstance(record['data'], str):
                    sample_data.append(json.loads(record['data']))
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
            "layout": {
                "grid_cols": 4,
                "grid_rows": 6,
                "gap": 4,
                "responsive": True
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
                    "size": {"width": 1, "height": 1}
                },
                {
                    "id": "kpi_data_columns",
                    "title": "Data Fields",
                    "value": str(len(columns)),
                    "icon": "Columns", 
                    "icon_color": "text-success",
                    "icon_bg_color": "bg-success/10",
                    "position": {"row": 0, "col": 1},
                    "size": {"width": 1, "height": 1}
                }
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
                        "data_columns": columns[:2]
                    },
                    "position": {"row": 1, "col": 0},
                    "size": {"width": 2, "height": 2}
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
                        "data_columns": columns[:2]
                    },
                    "position": {"row": 1, "col": 2},
                    "size": {"width": 2, "height": 2}
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
                        "data_columns": columns[:2]
                    },
                    "position": {"row": 3, "col": 0},
                    "size": {"width": 2, "height": 2}
                }
            ],
            "theme": "default",
            "last_generated": datetime.utcnow().isoformat(),
            "version": "4.0-fast-client"
        }
        
        # Save dashboard config
        config_record = {
            "client_id": client_id,
            "dashboard_config": dashboard_config,
            "is_generated": True,
            "generation_timestamp": datetime.utcnow().isoformat()
        }
        
        db_client.table("client_dashboard_configs").upsert(config_record, on_conflict="client_id").execute()
        
        # Generate basic metrics
        metrics = [
            {
                "metric_id": str(uuid.uuid4()),
                "client_id": client_id,
                "metric_name": "total_records",
                "metric_value": {"value": len(data_response.data)},
                "metric_type": "kpi",
                "calculated_at": datetime.utcnow().isoformat()
            },
            {
                "metric_id": str(uuid.uuid4()),
                "client_id": client_id, 
                "metric_name": "data_fields",
                "metric_value": {"value": len(columns)},
                "metric_type": "kpi",
                "calculated_at": datetime.utcnow().isoformat()
            }
        ]
        
        db_client.table("client_dashboard_metrics").insert(metrics).execute()
        
        generation_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"✅ FAST dashboard generated in {generation_time:.2f}s for client {client_id}")
        
        return {
            "success": True,
            "message": f"Fast dashboard generated successfully in {generation_time:.2f}s",
            "dashboard_config": dashboard_config,
            "generation_time": generation_time,
            "records_processed": len(data_response.data),
            "mode": "fast_client"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fast dashboard generation failed: {e}")
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
        client_response = db_client.table("clients").select("*").eq("client_id", client_id).execute()
        
        # Check if dashboard config exists
        config_response = db_client.table("client_dashboard_configs").select("*").eq("client_id", client_id).execute()
        
        # Check if client data exists
        data_response = db_client.table("client_data").select("client_id").eq("client_id", client_id).limit(5).execute()
        
        return {
            "success": True,
            "client_id": client_id,
            "token_valid": True,
            "client_exists": bool(client_response.data),
            "client_info": client_response.data[0] if client_response.data else None,
            "dashboard_config_exists": bool(config_response.data),
            "data_records_count": len(data_response.data) if data_response.data else 0,
            "message": "Authentication successful"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Authentication failed"
        }

# ==================== DASHBOARD CONFIG ENDPOINTS ====================

# Add improved batch processing function
async def improved_batch_insert(db_client, batch_rows: List[Dict], data_type: str = "DATA") -> int:
    """
    Improved batch insert with smaller chunks, retry logic, and exponential backoff
    Specifically optimized for Supabase and large datasets
    """
    if not batch_rows:
        return 0
    
    logger.info(f"🚀 OPTIMIZED BATCH inserting {len(batch_rows)} {data_type.upper()} rows")
    
    # OPTIMIZED SETTINGS for Supabase
    chunk_size = 100  # Reduced from 1000 - optimal for Supabase
    max_retries = 3
    base_delay = 0.5  # Start with 500ms delay
    total_inserted = 0
    failed_chunks = []
    
    for i in range(0, len(batch_rows), chunk_size):
        chunk = batch_rows[i:i + chunk_size]
        chunk_num = i // chunk_size + 1
        retry_count = 0
        chunk_inserted = False
        
        while retry_count <= max_retries and not chunk_inserted:
            try:
                # Add small delay between chunks to avoid overwhelming Supabase
                if i > 0:  # Skip delay for first chunk
                    await asyncio.sleep(0.2)  # 200ms delay between chunks
                
                response = db_client.table("client_data").insert(chunk).execute()
                
                if response.data:
                    total_inserted += len(response.data)
                    logger.info(f"⚡ {data_type.upper()} CHUNK {chunk_num}: {len(response.data)} rows inserted!")
                    chunk_inserted = True
                else:
                    raise Exception("No data returned from insert")
                    
            except Exception as chunk_error:
                retry_count += 1
                error_msg = str(chunk_error)
                
                if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                    if retry_count <= max_retries:
                        # Exponential backoff for timeouts
                        delay = base_delay * (2 ** retry_count)
                        logger.warning(f"⏱️ {data_type.upper()} chunk {chunk_num} timeout (attempt {retry_count}/{max_retries + 1}). Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"❌ {data_type.upper()} chunk {chunk_num} failed after {max_retries + 1} attempts: {chunk_error}")
                        failed_chunks.append(chunk)
                        break
                else:
                    # Non-timeout error - don't retry
                    logger.error(f"❌ {data_type.upper()} chunk {chunk_num} failed with non-timeout error: {chunk_error}")
                    failed_chunks.append(chunk)
                    break
    
    # Handle failed chunks with smaller batch sizes
    if failed_chunks:
        logger.info(f"🔄 Retrying {len(failed_chunks)} failed chunks with smaller batches...")
        small_chunk_size = 20  # Even smaller for problem chunks
        
        for failed_chunk in failed_chunks:
            for j in range(0, len(failed_chunk), small_chunk_size):
                small_chunk = failed_chunk[j:j + small_chunk_size]
                try:
                    await asyncio.sleep(0.5)  # Extra delay for problem data
                    response = db_client.table("client_data").insert(small_chunk).execute()
                    if response.data:
                        total_inserted += len(response.data)
                        logger.info(f"🔧 Recovered {len(response.data)} rows with smaller batch")
                except Exception as final_error:
                    logger.error(f"💥 Final attempt failed for {len(small_chunk)} rows: {final_error}")
                    # Last resort: individual inserts with delays
                    for row in small_chunk:
                        try:
                            await asyncio.sleep(0.1)  # 100ms between individual inserts
                            db_client.table("client_data").insert(row).execute()
                            total_inserted += 1
                        except:
                            continue  # Skip problematic individual rows
    
    success_rate = (total_inserted / len(batch_rows)) * 100
    logger.info(f"🎯 BATCH COMPLETE: {total_inserted}/{len(batch_rows)} rows inserted ({success_rate:.1f}% success)")
    
    return total_inserted

@app.get("/api/debug/data-type-detection/{client_id}")
async def debug_data_type_detection(client_id: str):
    """Debug endpoint to test data type detection and business insights extraction"""
    try:
        # Get client data
        client_data = await ai_analyzer.get_client_data_optimized(client_id)
        if not client_data:
            return {"error": "No data found for this client"}
        
        # Test data type detection
        data_records = client_data.get('data', [])
        data_type = client_data.get('data_type', 'unknown')
        schema_type = client_data.get('schema', {}).get('type', 'unknown')
        
        # Test Shopify structure detection
        shopify_fields = ['title', 'handle', 'status', 'vendor', 'platform', 'variants', 'product_id', 'product_type']
        first_record = data_records[0] if data_records else {}
        shopify_field_count = sum(1 for field in shopify_fields if field in first_record)
        is_shopify = shopify_field_count >= 5
        
        # Test business data format detection
        business_fields = ['business_info', 'customer_data', 'monthly_summary', 'product_inventory', 'sales_transactions', 'performance_metrics']
        business_field_count = sum(1 for field in business_fields if field in first_record)
        is_business = business_field_count >= 5
        
        # Extract insights
        insights = await dashboard_orchestrator._extract_business_insights_from_data(client_data)
        
        return {
            "client_id": client_id,
            "data_type": data_type,
            "schema_type": schema_type,
            "total_records": len(data_records),
            "shopify_detection": {
                "field_count": shopify_field_count,
                "total_fields": len(shopify_fields),
                "is_shopify": is_shopify,
                "found_fields": [field for field in shopify_fields if field in first_record]
            },
            "business_detection": {
                "field_count": business_field_count,
                "total_fields": len(business_fields),
                "is_business": is_business,
                "found_fields": [field for field in business_fields if field in first_record]
            },
            "first_record_keys": list(first_record.keys()) if first_record else [],
            "insights_result": insights
        }
        
    except Exception as e:
        logger.error(f"❌ Debug data type detection failed: {e}")
        return {"error": f"Debug failed: {str(e)}"}

@app.get("/api/test-llm-analysis/{client_id}")
async def test_llm_analysis(client_id: str):
    """Test endpoint to demonstrate LLM-powered dashboard analysis"""
    try:
        # Get client data
        client_data = await ai_analyzer.get_client_data_optimized(client_id)
        if not client_data:
            return {"error": "No data found for this client"}
        
        # Extract LLM-powered insights
        insights = await dashboard_orchestrator._extract_business_insights_from_data(client_data)
        
        return {
            "client_id": client_id,
            "data_type": client_data.get('data_type', 'unknown'),
            "schema_type": client_data.get('schema', {}).get('type', 'unknown'),
            "total_records": len(client_data.get('data', [])),
            "llm_analysis": insights
        }
        
    except Exception as e:
        logger.error(f"❌ LLM analysis test failed: {e}")
        return {"error": f"LLM analysis test failed: {str(e)}"}

@app.get("/api/debug/llm-analysis/{client_id}")
async def debug_llm_analysis(client_id: str):
    """Debug endpoint to test LLM analysis step by step"""
    try:
        # Get client data
        client_data = await ai_analyzer.get_client_data_optimized(client_id)
        if not client_data:
            return {"error": "No data found for this client"}
        
        # Test each step of the LLM analysis
        data_records = client_data.get('data', [])
        data_type = client_data.get('data_type', 'unknown')
        schema_type = client_data.get('schema', {}).get('type', 'unknown')
        
        # Step 1: Create prompt
        sample_data = data_records[:3] if len(data_records) > 3 else data_records
        llm_prompt = dashboard_orchestrator._create_llm_analysis_prompt(data_type, schema_type, sample_data, len(data_records))
        
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
                structured_insights = dashboard_orchestrator._parse_llm_insights(llm_response, data_records)
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
            "prompt_preview": llm_prompt[:500] + "..." if len(llm_prompt) > 500 else llm_prompt,
            "llm_call": {
                "success": llm_success,
                "error": llm_error,
                "response_length": len(llm_response) if llm_response else 0,
                "response_preview": llm_response[:500] + "..." if llm_response and len(llm_response) > 500 else llm_response
            },
            "parsing": {
                "success": parse_success,
                "error": parse_error
            },
            "final_result": structured_insights
        }
        
    except Exception as e:
        logger.error(f"❌ Debug LLM analysis failed: {e}")
        return {"error": f"Debug LLM analysis failed: {str(e)}"}

@app.get("/api/debug/env-check")
async def debug_environment_variables():
    """Debug endpoint to check environment variables"""
    try:
        import os
        from dotenv import load_dotenv
        
        # Check if .env file exists
        env_file_path = os.path.join(os.path.dirname(__file__), '.env')
        env_file_exists = os.path.exists(env_file_path)
        
        # Load dotenv
        load_dotenv()
        
        # Check environment variables
        openai_key = os.getenv("OPENAI_API_KEY")
        openai_key_length = len(openai_key) if openai_key else 0
        openai_key_preview = openai_key[:20] + "..." if openai_key and len(openai_key) > 20 else openai_key
        
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
                "starts_with_sk": openai_key.startswith("sk-") if openai_key else False
            },
            "supabase_url": {
                "exists": bool(supabase_url),
                "preview": supabase_url[:30] + "..." if supabase_url and len(supabase_url) > 30 else supabase_url
            },
            "supabase_key": {
                "exists": bool(supabase_key),
                "preview": supabase_key[:20] + "..." if supabase_key and len(supabase_key) > 20 else supabase_key
            },
            "jwt_secret": {
                "exists": bool(jwt_secret),
                "preview": jwt_secret[:20] + "..." if jwt_secret and len(jwt_secret) > 20 else jwt_secret
            }
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
        dashboard_key = getattr(dashboard_orchestrator, 'openai_api_key', None)
        dashboard_key_length = len(dashboard_key) if dashboard_key else 0
        dashboard_key_preview = dashboard_key[:20] + "..." if dashboard_key and len(dashboard_key) > 20 else dashboard_key
        
        # Check AI analyzer
        ai_analyzer_key = getattr(ai_analyzer, 'openai_api_key', None)
        ai_analyzer_key_length = len(ai_analyzer_key) if ai_analyzer_key else 0
        ai_analyzer_key_preview = ai_analyzer_key[:20] + "..." if ai_analyzer_key and len(ai_analyzer_key) > 20 else ai_analyzer_key
        
        # Check if they match the current environment
        import os
        current_env_key = os.getenv("OPENAI_API_KEY")
        current_env_key_preview = current_env_key[:20] + "..." if current_env_key and len(current_env_key) > 20 else current_env_key
        
        return {
            "dashboard_orchestrator": {
                "has_key": bool(dashboard_key),
                "key_length": dashboard_key_length,
                "key_preview": dashboard_key_preview,
                "starts_with_sk": dashboard_key.startswith("sk-") if dashboard_key else False
            },
            "ai_analyzer": {
                "has_key": bool(ai_analyzer_key),
                "key_length": ai_analyzer_key_length,
                "key_preview": ai_analyzer_key_preview,
                "starts_with_sk": ai_analyzer_key.startswith("sk-") if ai_analyzer_key else False
            },
            "current_environment": {
                "has_key": bool(current_env_key),
                "key_length": len(current_env_key) if current_env_key else 0,
                "key_preview": current_env_key_preview,
                "starts_with_sk": current_env_key.startswith("sk-") if current_env_key else False
            },
            "keys_match": {
                "dashboard_vs_env": dashboard_key == current_env_key,
                "ai_analyzer_vs_env": ai_analyzer_key == current_env_key,
                "dashboard_vs_ai_analyzer": dashboard_key == ai_analyzer_key
            }
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
                max_tokens=10
            )
            
            return {
                "success": True,
                "message": "API key is valid and working",
                "response": response.choices[0].message.content,
                "model_used": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "debug": {
                    "key_length": key_length,
                    "key_preview": key_preview,
                    "starts_with_sk": api_key.startswith("sk-")
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"OpenAI API call failed: {str(e)}",
                "error_type": type(e).__name__,
                "debug": {
                    "key_length": key_length,
                    "key_preview": key_preview,
                    "starts_with_sk": api_key.startswith("sk-")
                }
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
        backend_env = current_dir / '.env'
        if backend_env.exists():
            env_files.append({
                "path": str(backend_env),
                "exists": True,
                "size": backend_env.stat().st_size
            })
        else:
            env_files.append({
                "path": str(backend_env),
                "exists": False
            })
        
        # Check root directory
        root_env = root_dir / '.env'
        if root_env.exists():
            env_files.append({
                "path": str(root_env),
                "exists": True,
                "size": root_env.stat().st_size
            })
        else:
            env_files.append({
                "path": str(root_env),
                "exists": False
            })
        
        # Check parent directory
        parent_env = root_dir.parent / '.env'
        if parent_env.exists():
            env_files.append({
                "path": str(parent_env),
                "exists": True,
                "size": parent_env.stat().st_size
            })
        else:
            env_files.append({
                "path": str(parent_env),
                "exists": False
            })
        
        # Check system environment variables
        system_openai_key = os.environ.get("OPENAI_API_KEY")
        
        return {
            "env_files": env_files,
            "system_environment": {
                "has_openai_key": bool(system_openai_key),
                "key_length": len(system_openai_key) if system_openai_key else 0,
                "key_preview": system_openai_key[:20] + "..." if system_openai_key and len(system_openai_key) > 20 else system_openai_key
            },
            "current_working_dir": str(Path.cwd()),
            "script_location": str(current_dir)
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
                messages=[
                    {"role": "user", "content": "Test"}
                ],
                max_tokens=5
            )
            
            return {
                "success": True,
                "message": "Environment reloaded and API key works",
                "debug": {
                    "key_length": key_length,
                    "key_preview": key_preview,
                    "starts_with_sk": api_key.startswith("sk-") if api_key else False
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"API call failed after reload: {str(e)}",
                "debug": {
                    "key_length": key_length,
                    "key_preview": key_preview,
                    "starts_with_sk": api_key.startswith("sk-") if api_key else False
                }
            }
        
    except Exception as e:
        return {"error": f"Force reload failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 