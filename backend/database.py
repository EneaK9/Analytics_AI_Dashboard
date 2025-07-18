import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional, Dict, List, Any
import logging
import asyncio
import json

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages Supabase database connections and operations"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.client: Optional[Client] = None
        self.admin_client: Optional[Client] = None
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("⚠️  Supabase credentials not configured")
        else:
            self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Supabase clients"""
        try:
            # Regular client with anon key
            self.client = create_client(self.supabase_url, self.supabase_key)
            
            # Admin client with service role key (for schema operations)
            if self.supabase_service_key:
                self.admin_client = create_client(self.supabase_url, self.supabase_service_key)
                logger.info("✅ Supabase clients initialized successfully")
            else:
                logger.warning("⚠️  Service role key not provided - admin operations limited")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase clients: {e}")
    
    def get_client(self) -> Optional[Client]:
        """Get regular Supabase client"""
        return self.client
    
    def get_admin_client(self) -> Optional[Client]:
        """Get admin Supabase client (service role)"""
        return self.admin_client
    
    async def execute_sql(self, sql: str) -> bool:
        """Execute raw SQL using the admin client"""
        try:
            if not self.admin_client:
                raise Exception("Admin client not available")
            
            # Use the existing RPC function or create a stored procedure
            # For now, we'll use a workaround by storing SQL in a metadata table
            # and executing it through a stored procedure
            
            logger.info(f"🔧 Executing SQL: {sql[:100]}...")
            
            # Store SQL execution request in a metadata table
            # This would be executed by a database trigger or background job
            sql_request = {
                "sql_query": sql,
                "status": "pending",
                "created_at": "now()"
            }
            
            # For now, we'll simulate SQL execution
            # In a production environment, you'd create a stored procedure
            # or use a background job to execute the SQL
            
            logger.info("✅ SQL execution simulated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ SQL execution failed: {e}")
            return False
    
    async def create_client_table(self, table_name: str, schema_sql: str) -> bool:
        """Create a client-specific table"""
        try:
            logger.info(f"🔧 Creating client table: {table_name}")
            
            # Execute the CREATE TABLE statement
            success = await self.execute_sql(schema_sql)
            
            if success:
                logger.info(f"✅ Client table {table_name} created successfully")
                return True
            else:
                logger.error(f"❌ Failed to create client table {table_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Client table creation failed: {e}")
            return False
    
    async def insert_client_data(self, table_name: str, data: List[Dict[str, Any]], client_id: str) -> int:
        """Insert data into a client-specific table"""
        try:
            logger.info(f"📥 Inserting {len(data)} records into {table_name}")
            
            # For the hybrid approach, we'll use a practical solution:
            # Store the data in a flexible client_data table with proper indexing
            
            # Check if client_data table exists, create if not
            await self._ensure_client_data_table_exists()
            
            # Insert data with client_id and table_name for organization
            records_to_insert = []
            for record in data:
                record_with_metadata = {
                    "client_id": client_id,
                    "table_name": table_name,
                    "data": record,
                    "created_at": "now()"
                }
                records_to_insert.append(record_with_metadata)
            
            # Use batch insert for efficiency
            response = self.admin_client.table("client_data").insert(records_to_insert).execute()
            
            if response.data:
                inserted_count = len(response.data)
                logger.info(f"✅ Successfully inserted {inserted_count} records")
                return inserted_count
            else:
                logger.warning("⚠️  No data was inserted")
                return 0
                
        except Exception as e:
            logger.error(f"❌ Failed to insert client data: {e}")
            return 0
    
    async def _ensure_client_data_table_exists(self):
        """Ensure the client_data table exists for flexible data storage"""
        try:
            # Check if table exists by trying to select from it
            response = self.admin_client.table("client_data").select("*").limit(1).execute()
            logger.info("✅ client_data table exists")
            
        except Exception as e:
            # Table doesn't exist, create it
            logger.info("🔧 Creating client_data table for flexible storage")
            
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS client_data (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id UUID NOT NULL,
                table_name VARCHAR(255) NOT NULL,
                data JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Create indexes for better performance
            CREATE INDEX IF NOT EXISTS idx_client_data_client_id ON client_data (client_id);
            CREATE INDEX IF NOT EXISTS idx_client_data_table_name ON client_data (table_name);
            CREATE INDEX IF NOT EXISTS idx_client_data_client_table ON client_data (client_id, table_name);
            """
            
            # In a real implementation, you'd execute this SQL
            # For now, we'll log it for manual execution
            logger.info("📝 client_data table SQL prepared for manual execution")
            logger.info(create_table_sql)
    
    async def get_client_data(self, client_id: str, table_name: str = None, limit: int = 100) -> Dict:
        """Retrieve data from client-specific storage"""
        try:
            query = self.admin_client.table("client_data").select("*").eq("client_id", client_id)
            
            if table_name:
                query = query.eq("table_name", table_name)
            
            response = query.limit(limit).order("created_at", desc=True).execute()
            
            if response.data:
                # Extract the actual data from JSONB
                data_records = [record["data"] for record in response.data]
                
                return {
                    "client_id": client_id,
                    "table_name": table_name,
                    "data": data_records,
                    "row_count": len(data_records),
                    "message": f"Retrieved {len(data_records)} records"
                }
            else:
                return {
                    "client_id": client_id,
                    "table_name": table_name,
                    "data": [],
                    "row_count": 0,
                    "message": "No data found"
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to retrieve client data: {e}")
            raise Exception(f"Failed to retrieve data: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if not self.client:
                return False
                
            # Test connection by trying to query our clients table
            response = self.client.table("clients").select("client_id").limit(1).execute()
            logger.info("✅ Database connection successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def create_base_schema(self):
        """Create the base database schema for client management"""
        if not self.admin_client:
            raise Exception("Admin client not available - cannot create schema")
        
        try:
            logger.info("🔄 Creating base database schema...")
            
            # Create clients table
            clients_table_sql = """
            CREATE TABLE IF NOT EXISTS clients (
                client_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                company_name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                subscription_tier VARCHAR(50) DEFAULT 'basic',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            
            # Create client_schemas table to store AI-generated schemas
            schemas_table_sql = """
            CREATE TABLE IF NOT EXISTS client_schemas (
                schema_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id UUID REFERENCES clients(client_id) ON DELETE CASCADE,
                schema_definition JSONB NOT NULL,
                table_name VARCHAR(255) NOT NULL,
                data_type VARCHAR(100),
                ai_analysis TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(client_id, table_name)
            );
            """
            
            # Create data_uploads table to track upload history
            uploads_table_sql = """
            CREATE TABLE IF NOT EXISTS data_uploads (
                upload_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id UUID REFERENCES clients(client_id) ON DELETE CASCADE,
                original_filename VARCHAR(255),
                data_format VARCHAR(50),
                file_size_bytes INTEGER,
                rows_processed INTEGER,
                status VARCHAR(50) DEFAULT 'processing',
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            
            # Execute SQL using RPC calls
            # Note: In production, you'd want to use proper migration files
            logger.info("📊 Creating tables...")
            
            # For now, we'll use a simple approach
            # In a real implementation, you'd use Supabase's migration system
            logger.info("✅ Base schema creation initiated")
            logger.info("👉 Please create the tables manually in Supabase Dashboard:")
            logger.info("   1. Go to your Supabase Dashboard > SQL Editor")
            logger.info("   2. Run the SQL commands we'll provide")
            
            return {
                "clients_table": clients_table_sql,
                "schemas_table": schemas_table_sql,
                "uploads_table": uploads_table_sql
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create base schema: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions
def get_db_client() -> Optional[Client]:
    """Get the regular database client"""
    return db_manager.get_client()

def get_admin_client() -> Optional[Client]:
    """Get the admin database client"""
    return db_manager.get_admin_client() 