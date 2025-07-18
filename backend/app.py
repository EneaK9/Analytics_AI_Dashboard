from fastapi import FastAPI, HTTPException, Depends, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import os
from typing import Optional
import logging
import json
import asyncio
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid
import bcrypt
import jwt

# Import our custom modules
from models import *
from database import db_manager, get_db_client, get_admin_client
from ai_analyzer import ai_analyzer

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_TIME = 24  # hours

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
    """Health check endpoint"""
    try:
        # Test database connection
        db_healthy = await db_manager.test_connection() if db_manager.client else False
        
        return {
            "status": "healthy",
            "service": "Analytics AI Dashboard API",
            "version": "2.0.0",
            "database": "connected" if db_healthy else "disconnected", 
            "ai_analyzer": "enabled" if ai_analyzer.openai_api_key else "disabled",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/setup-schema")
async def setup_database_schema():
    """Setup base database schema (run once)"""
    try:
        schema_sql = await db_manager.create_base_schema()
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
    """Superadmin: Create a new client account with smart data processing"""
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
        logger.info(f"✅ Superadmin created client: {email}")
        
        # Smart data processing based on input method
        raw_data = ""
        if input_method == "paste" and data_content:
            raw_data = data_content
            logger.info(f"📝 Processing pasted {data_type.upper()} data ({len(data_content)} chars)")
        elif input_method == "upload" and uploaded_file:
            # Read uploaded file
            file_content = await uploaded_file.read()
            raw_data = file_content.decode('utf-8')
            logger.info(f"📁 Processing uploaded file: {uploaded_file.filename} ({len(raw_data)} chars)")
        
        # Use AI analyzer to process the data if we have content
        if raw_data:
            try:
                # Map data_type to DataFormat enum
                data_format_map = {
                    "json": "json",
                    "csv": "csv", 
                    "xml": "xml",
                    "api": "json"  # API responses are typically JSON
                }
                data_format = data_format_map.get(data_type, "json")
                
                # Analyze the data with AI
                ai_result = await ai_analyzer.analyze_data(
                    raw_data, 
                    data_format, 
                    client_id
                )
                
                # Store schema in client_schemas table
                schema_response = db_client.table("client_schemas").insert({
                    "client_id": client_id,
                    "schema_definition": ai_result.table_schema.dict(),
                    "table_name": ai_result.table_schema.table_name,
                    "data_type": ai_result.data_type,
                    "ai_analysis": json.dumps(ai_result.dict())
                }).execute()
                
                if schema_response.data:
                    logger.info(f"🤖 AI Analysis complete for {email}: {ai_result.data_type} data schema created")
                    logger.info(f"📊 Table: {ai_result.table_schema.table_name} with {len(ai_result.table_schema.columns)} columns")
                    
                    # Create the table and insert the data
                    try:
                        rows_inserted = await ai_analyzer.create_table_and_insert_data(
                            ai_result, 
                            raw_data, 
                            data_format, 
                            client_id
                        )
                        logger.info(f"✅ Data insertion complete for {email}: {rows_inserted} rows inserted")
                        
                        # 🎯 AUTOMATIC DASHBOARD GENERATION - This is the magic!
                        try:
                            from dashboard_orchestrator import dashboard_orchestrator
                            from models import AutoGenerationRequest, GenerationType
                            
                            # Trigger automatic dashboard generation in background
                            generation_request = AutoGenerationRequest(
                                client_id=uuid.UUID(client_id),
                                generation_type=GenerationType.AUTOMATIC
                            )
                            
                            # Start dashboard generation (fire and forget)
                            asyncio.create_task(
                                dashboard_orchestrator.generate_dashboard_with_retry(generation_request)
                            )
                            
                            logger.info(f"🎨 Automatic dashboard generation triggered for {email}")
                            
                        except Exception as dashboard_error:
                            logger.error(f"❌ Failed to trigger dashboard generation for {email}: {dashboard_error}")
                            # Don't fail client creation if dashboard trigger fails
                        
                    except Exception as insert_error:
                        logger.error(f"❌ Data insertion failed for {email}: {insert_error}")
                        
                else:
                    logger.warning(f"⚠️  Schema storage failed for {email}")
                    
            except Exception as ai_error:
                logger.error(f"❌ AI analysis failed for {email}: {ai_error}")
                # Don't fail the client creation if AI analysis fails
        else:
            logger.info(f"ℹ️  No data provided for {email} - client created without schema")
        
        return ClientResponse(**client)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Superadmin client creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Client creation failed: {str(e)}")

@app.get("/api/superadmin/clients")
async def list_clients_superadmin(token: str = Depends(security)):
    """Superadmin: List all clients with pagination"""
    try:
        logger.info(f"🔍 Superadmin clients request - token type: {type(token)}")
        logger.info(f"🔍 Token credentials: {token.credentials[:20] if token.credentials else 'None'}...")
        # Verify superadmin token
        verify_superadmin_token(token.credentials)
        
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        response = db_client.table("clients").select("*").order("created_at", desc=True).execute()
        
        clients = [ClientResponse(**client) for client in response.data]
        
        # Enhance clients with schema and data information (Hybrid Approach)
        enhanced_clients = []
        for client_data in response.data:
            # Check if client has schema and data
            schema_response = db_client.table("client_schemas").select("table_name, data_type, data_stored, row_count").eq("client_id", client_data['client_id']).execute()
            
            has_schema = len(schema_response.data) > 0
            schema_info = schema_response.data[0] if schema_response.data else None
            
            # Check actual data count from client_data table
            actual_data_count = 0
            if has_schema and schema_info:
                try:
                    data_response = db_client.table("client_data").select("id").eq("client_id", client_data['client_id']).execute()
                    actual_data_count = len(data_response.data) if data_response.data else 0
                    logger.info(f"📊 Client {client_data['client_id']} has {actual_data_count} data records")
                except Exception as e:
                    logger.warning(f"⚠️  Could not get data count for client {client_data['client_id']}: {e}")
            
            client_data['has_schema'] = has_schema
            client_data['schema_info'] = schema_info
            client_data['actual_data_count'] = actual_data_count
            client_data['data_stored'] = schema_info.get('data_stored', False) if schema_info else False
            
            # Debug logging
            logger.info(f"🔍 Client {client_data['client_id']} data: has_schema={has_schema}, actual_data_count={actual_data_count}, data_stored={client_data['data_stored']}")
            
            enhanced_clients.append(ClientResponse(**client_data))
        
        return ClientListResponse(
            clients=enhanced_clients,
            total=len(enhanced_clients),
            page=1,
            limit=len(enhanced_clients)
        )
        
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

# ==================== DATA UPLOAD & ANALYSIS ====================

@app.post("/api/admin/upload-data", response_model=CreateSchemaResponse)
async def upload_client_data(upload_data: CreateSchemaRequest):
    """Super Admin: Upload data for a client and create their schema"""
    try:
        logger.info(f"🔄 Processing data upload for client {upload_data.client_id}")
        
        # Step 1: Analyze the data with AI
        ai_result = await ai_analyzer.analyze_data(
            upload_data.raw_data, 
            upload_data.data_format, 
            str(upload_data.client_id)
        )
        
        # Step 2: Create the table in Supabase (for now, return SQL)
        # In a full implementation, this would create the actual table
        create_table_sql = f"""
        CREATE TABLE {ai_result.table_schema.table_name} (
            {', '.join([f"{col.name} {col.data_type}" + (" PRIMARY KEY" if col.primary_key else "") for col in ai_result.table_schema.columns])},
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Step 3: Store schema in client_schemas table
        db_client = get_admin_client()
        if db_client:
            schema_response = db_client.table("client_schemas").insert({
                "client_id": str(upload_data.client_id),
                "schema_definition": ai_result.table_schema.dict(),
                "table_name": ai_result.table_schema.table_name,
                "data_type": ai_result.data_type,
                "ai_analysis": json.dumps(ai_result.dict())
            }).execute()
        
        logger.info(f"✅ Schema created for client {upload_data.client_id}: {ai_result.data_type}")
        
        return CreateSchemaResponse(
            success=True,
            table_name=ai_result.table_schema.table_name,
            table_schema=ai_result.table_schema,
            ai_analysis=ai_result,
            rows_inserted=0,  # TODO: Actually insert data
            message=f"Schema analyzed and created successfully. SQL: {create_table_sql}"
        )
        
    except Exception as e:
        logger.error(f"❌ Data upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Data upload failed: {str(e)}")

@app.get("/api/data/{client_id}")
async def get_client_data(client_id: str, limit: int = 100):
    """Get client-specific data from their custom table (Hybrid Approach)"""
    try:
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Get client's schema first
        schema_response = db_client.table("client_schemas").select("*").eq("client_id", client_id).execute()
        
        if not schema_response.data:
            raise HTTPException(status_code=404, detail="Client schema not found")
        
        schema_info = schema_response.data[0]
        table_name = schema_info["table_name"]
        
        # Use AI analyzer to get the actual data
        try:
            data_result = await ai_analyzer.get_client_data(client_id, table_name, limit)
            
            return {
                "client_id": client_id,
                "table_name": table_name,
                "schema": schema_info["schema_definition"],
                "data_type": schema_info["data_type"],
                "data": data_result["data"],
                "row_count": data_result["row_count"],
                "message": data_result["message"]
            }
        except Exception as data_error:
            logger.error(f"❌ Failed to retrieve data for client {client_id}: {data_error}")
            return {
                "client_id": client_id,
                "table_name": table_name,
                "schema": schema_info["schema_definition"],
                "data_type": schema_info["data_type"],
                "data": [],
                "row_count": 0,
                "message": f"Data retrieval failed: {str(data_error)}"
            }
        
    except Exception as e:
        logger.error(f"❌ Failed to get client data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/api/dashboard/config", response_model=DashboardConfig)
async def get_dashboard_config(token: str = Depends(security)):
    """Get dashboard configuration for the authenticated client"""
    try:
        # Verify client token
        token_data = verify_token(token.credentials)
        
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Get dashboard config
        try:
            response = db_client.table("client_dashboard_configs").select("*").eq("client_id", str(token_data.client_id)).execute()
            
            if not response.data:
                raise HTTPException(status_code=404, detail="Dashboard not found. Please generate your dashboard first.")
            
            config_data = response.data[0]["dashboard_config"]
            return DashboardConfig(**config_data)
        except Exception as e:
            if "relation" in str(e) and "does not exist" in str(e):
                raise HTTPException(status_code=404, detail="Dashboard system not initialized. Please run the database setup script first.")
            raise
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get dashboard config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/metrics", response_model=List[DashboardMetric])
async def get_dashboard_metrics(token: str = Depends(security)):
    """Get dashboard metrics for the authenticated client"""
    try:
        # Verify client token
        token_data = verify_token(token.credentials)
        
        db_client = get_admin_client()
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Get dashboard metrics
        try:
            response = db_client.table("client_dashboard_metrics").select("*").eq("client_id", str(token_data.client_id)).order("calculated_at", desc=True).execute()
            
            metrics = []
            for metric_data in response.data:
                metric = DashboardMetric(
                    metric_id=metric_data["metric_id"],
                    client_id=metric_data["client_id"],
                    metric_name=metric_data["metric_name"],
                    metric_value=metric_data["metric_value"],
                    metric_type=metric_data["metric_type"],
                    calculated_at=metric_data["calculated_at"]
                )
                metrics.append(metric)
            
            return metrics
        except Exception as e:
            if "relation" in str(e) and "does not exist" in str(e):
                logger.warning(f"⚠️  Dashboard metrics table not found: {e}")
                return []
            raise
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
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
    
    # You can add startup tasks here, such as:
    # - Initial retry processing
    # - Database health checks
    # - Cache warming
    
    try:
        # Process any pending retries on startup
        from dashboard_orchestrator import dashboard_orchestrator
        results = await dashboard_orchestrator.process_pending_retries()
        if results:
            logger.info(f"🔄 Processed {len(results)} pending retries on startup")
    except Exception as e:
        logger.warning(f"⚠️  Failed to process pending retries on startup: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 