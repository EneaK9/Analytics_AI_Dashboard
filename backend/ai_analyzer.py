import json
import pandas as pd
import openai
import os
from typing import Dict, List, Any, Tuple
from models import ColumnAnalysis, TableSchema, AIAnalysisResult, DataFormat
import re
import logging
from datetime import datetime
from database import get_admin_client
import uuid

logger = logging.getLogger(__name__)

class AIDataAnalyzer:
    """AI-powered data analyzer that automatically detects data structures"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            logger.info("✅ OpenAI API key configured")
        else:
            logger.warning("⚠️  OpenAI API key not configured - AI analysis disabled")
    
    async def analyze_data(self, raw_data: str, data_format: DataFormat, client_id: str) -> AIAnalysisResult:
        """
        Analyze raw data and generate schema + insights
        """
        try:
            logger.info(f"🔄 Analyzing {data_format} data for client {client_id}")
            
            # Step 1: Parse the data into a structured format
            parsed_data = self._parse_data(raw_data, data_format)
            
            # Step 2: Analyze data structure
            columns = self._analyze_columns(parsed_data)
            
            # Step 3: Generate table name using hybrid approach
            # Format: client_{uuid}_data (or client_{uuid}_{data_type} if AI detects specific type)
            clean_client_id = client_id.replace('-', '_')
            table_name = f"client_{clean_client_id}_data"
            
            # Step 4: Create schema
            schema = TableSchema(
                table_name=table_name,
                columns=columns
            )
            
            # Step 5: AI analysis for insights and recommendations
            ai_insights = await self._get_ai_insights(parsed_data, schema)
            
            # Step 6: Update table name based on AI detection
            if ai_insights.get("data_type") and ai_insights.get("data_type") != "general":
                table_name = f"client_{clean_client_id}_{ai_insights.get('data_type')}"
                schema.table_name = table_name
            
            # Step 7: Combine everything
            result = AIAnalysisResult(
                data_type=ai_insights.get("data_type", "general"),
                confidence=ai_insights.get("confidence", 0.8),
                table_schema=schema,
                insights=ai_insights.get("insights", []),
                recommended_visualizations=ai_insights.get("visualizations", []),
                sample_queries=ai_insights.get("queries", [])
            )
            
            logger.info(f"✅ Analysis completed - detected {result.data_type} data")
            return result
            
        except Exception as e:
            logger.error(f"❌ Data analysis failed: {e}")
            raise Exception(f"Failed to analyze data: {str(e)}")
    
    async def create_table_and_insert_data(self, ai_result: AIAnalysisResult, raw_data: str, data_format: DataFormat, client_id: str) -> int:
        """
        Create individual client table and insert data (Hybrid Approach)
        """
        try:
            logger.info(f"🔧 Creating client-specific table and inserting data for client {client_id}")
            
            db_client = get_admin_client()
            if not db_client:
                raise Exception("Database client not available")
            
            # Step 1: Parse the data to get DataFrame
            parsed_data = self._parse_data(raw_data, data_format)
            
            # Step 2: Create the client-specific table
            table_name = ai_result.table_schema.table_name
            await self._create_client_table(db_client, ai_result.table_schema)
            
            # Step 3: Clean and prepare data for insertion
            clean_records = self._prepare_data_for_insertion(parsed_data)
            
            if not clean_records:
                logger.warning(f"⚠️  No records to insert for client {client_id}")
                return 0
            
            # Step 4: Insert data into client-specific table
            rows_inserted = await self._insert_data_into_client_table(
                db_client, table_name, clean_records
            )
            
            # Step 5: Update data_uploads table with status
            await self._update_data_uploads_status(
                db_client, client_id, data_format, len(raw_data), rows_inserted
            )
            
            logger.info(f"✅ Successfully created table {table_name} and inserted {rows_inserted} rows")
            return rows_inserted
                
        except Exception as e:
            logger.error(f"❌ Table creation/data insertion failed: {e}")
            raise Exception(f"Failed to create table and insert data: {str(e)}")
    
    async def _create_client_table(self, db_client, schema: TableSchema):
        """Create individual client table using database manager"""
        try:
            create_table_sql = self._generate_create_table_sql(schema)
            
            logger.info(f"📊 Creating table: {schema.table_name}")
            
            # Use the database manager to create the table
            from database import db_manager
            success = await db_manager.create_client_table(schema.table_name, create_table_sql)
            
            if success:
                logger.info(f"✅ Table {schema.table_name} created successfully")
            else:
                logger.warning(f"⚠️  Table creation simulated for {schema.table_name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to create table {schema.table_name}: {e}")
            raise Exception(f"Failed to create client table: {str(e)}")
    
    def _prepare_data_for_insertion(self, parsed_data: pd.DataFrame) -> List[Dict]:
        """Clean and prepare data for database insertion"""
        clean_records = []
        
        # Convert DataFrame to list of dictionaries
        records = parsed_data.to_dict('records')
        
        for record in records:
            clean_record = {}
            for key, value in record.items():
                # Clean column names (remove spaces, special characters)
                clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', str(key)).lower()
                clean_key = re.sub(r'^_+|_+$', '', clean_key)  # Remove leading/trailing underscores
                clean_key = re.sub(r'_+', '_', clean_key)  # Remove multiple underscores
                
                # Handle NaN values
                if pd.isna(value):
                    clean_record[clean_key] = None
                else:
                    clean_record[clean_key] = value
            
            clean_records.append(clean_record)
        
        return clean_records
    
    async def _insert_data_into_client_table(self, db_client, table_name: str, records: List[Dict]) -> int:
        """Insert data into client-specific table using database manager"""
        try:
            logger.info(f"📥 Inserting {len(records)} records into {table_name}")
            
            # Extract client_id from table name
            # Format: client_{uuid}_{data_type} or client_{uuid}_data
            client_id = None
            if table_name.startswith("client_"):
                parts = table_name.split("_")
                if len(parts) >= 6:  # client_uuid_with_dashes_data
                    # Reconstruct the UUID (it has underscores instead of dashes)
                    uuid_parts = parts[1:6]  # Take 5 parts for UUID
                    client_id = "-".join(uuid_parts)
                elif len(parts) >= 2:
                    # Try to extract from first part after "client_"
                    uuid_part = "_".join(parts[1:-1])  # Everything except first and last
                    client_id = uuid_part.replace("_", "-")
            
            if not client_id:
                logger.error(f"❌ Could not extract client_id from table name: {table_name}")
                return 0
            
            # Use the database manager to insert data
            from database import db_manager
            rows_inserted = await db_manager.insert_client_data(table_name, records, client_id)
            
            logger.info(f"✅ Successfully inserted {rows_inserted} records into {table_name}")
            return rows_inserted
            
        except Exception as e:
            logger.error(f"❌ Failed to insert data into {table_name}: {e}")
            raise Exception(f"Failed to insert data: {str(e)}")
    
    async def _update_data_uploads_status(self, db_client, client_id: str, data_format: DataFormat, 
                                        file_size: int, rows_processed: int):
        """Update data_uploads table with processing status"""
        try:
            upload_record = {
                "client_id": client_id,
                "original_filename": f"processed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{data_format}",
                "data_format": data_format,
                "file_size_bytes": file_size,
                "rows_processed": rows_processed,
                "status": "completed"
            }
            
            response = db_client.table("data_uploads").insert(upload_record).execute()
            
            if response.data:
                logger.info(f"✅ Data upload record updated: {rows_processed} rows processed")
            else:
                logger.warning("⚠️  Failed to update data upload record")
                
        except Exception as e:
            logger.error(f"❌ Failed to update data uploads status: {e}")
    
    async def get_client_data(self, client_id: str, table_name: str = None, limit: int = 100) -> Dict:
        """Retrieve data from client-specific table using database manager"""
        try:
            # If no table name provided, get from schema
            if not table_name:
                db_client = get_admin_client()
                if not db_client:
                    raise Exception("Database client not available")
                
                schema_response = db_client.table("client_schemas").select("table_name").eq("client_id", client_id).execute()
                if not schema_response.data:
                    raise Exception(f"No schema found for client {client_id}")
                table_name = schema_response.data[0]["table_name"]
            
            logger.info(f"📊 Retrieving data from {table_name} for client {client_id}")
            
            # Use the database manager to retrieve data
            from database import db_manager
            result = await db_manager.get_client_data(client_id, table_name, limit)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve client data: {e}")
            raise Exception(f"Failed to retrieve data: {str(e)}")
    
    def _generate_create_table_sql(self, schema: TableSchema) -> str:
        """Generate CREATE TABLE SQL statement for client-specific table"""
        columns_sql = []
        
        # Add an auto-incrementing ID as primary key
        columns_sql.append("id SERIAL PRIMARY KEY")
        
        for col in schema.columns:
            clean_col_name = re.sub(r'[^a-zA-Z0-9_]', '_', str(col.name)).lower()
            clean_col_name = re.sub(r'^_+|_+$', '', clean_col_name)
            clean_col_name = re.sub(r'_+', '_', clean_col_name)
            
            col_sql = f'"{clean_col_name}" {col.data_type}'
            if col.primary_key and clean_col_name != "id":
                col_sql += " UNIQUE"
            elif not col.nullable:
                col_sql += " NOT NULL"
            columns_sql.append(col_sql)
        
        # Add client_id for reference
        columns_sql.append("client_id UUID NOT NULL")
        
        # Add metadata columns
        columns_sql.append("created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
        columns_sql.append("updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
        
        return f'''
        CREATE TABLE IF NOT EXISTS "{schema.table_name}" (
            {', '.join(columns_sql)}
        );
        
        -- Create index on client_id for better performance
        CREATE INDEX IF NOT EXISTS "idx_{schema.table_name}_client_id" ON "{schema.table_name}" (client_id);
        '''

    def _parse_data(self, raw_data: str, data_format: DataFormat) -> pd.DataFrame:
        """Parse raw data into pandas DataFrame"""
        try:
            if data_format == DataFormat.JSON:
                # Handle both JSON array and single JSON object
                data = json.loads(raw_data)
                if isinstance(data, dict):
                    data = [data]  # Convert single object to array
                return pd.DataFrame(data)
            
            elif data_format == DataFormat.CSV:
                from io import StringIO
                return pd.read_csv(StringIO(raw_data))
            
            elif data_format == DataFormat.EXCEL:
                # For Excel, we'd need the raw file bytes, not string
                # This is a placeholder - in reality you'd handle file upload differently
                raise Exception("Excel format requires file upload - not implemented yet")
            
            else:
                raise Exception(f"Unsupported data format: {data_format}")
                
        except Exception as e:
            raise Exception(f"Failed to parse {data_format} data: {str(e)}")
    
    def _analyze_columns(self, df: pd.DataFrame) -> List[ColumnAnalysis]:
        """Analyze DataFrame columns and generate column definitions"""
        columns = []
        
        for col_name, col_data in df.items():
            # Determine data type
            sql_type = self._infer_sql_type(col_data)
            
            # Check for potential primary key
            is_primary_key = (
                col_name.lower() in ['id', 'uuid', 'pk'] or 
                col_name.lower().endswith('_id') or
                (col_data.nunique() == len(col_data) and col_data.nunique() > 0)
            )
            
            # Check for unique values
            is_unique = col_data.nunique() == len(col_data) and len(col_data) > 1
            
            # Check for nulls
            has_nulls = col_data.isnull().any()
            
            # Get sample values (first 3 non-null values)
            sample_values = col_data.dropna().head(3).tolist()
            
            column = ColumnAnalysis(
                name=col_name,
                data_type=sql_type,
                nullable=has_nulls,
                primary_key=is_primary_key,
                unique=is_unique,
                sample_values=sample_values,
                description=f"Auto-detected {sql_type} column"
            )
            
            columns.append(column)
        
        return columns
    
    def _infer_sql_type(self, series: pd.Series) -> str:
        """Infer SQL data type from pandas Series"""
        # Remove null values for type inference
        non_null_series = series.dropna()
        
        if len(non_null_series) == 0:
            return "TEXT"
        
        # Check if it's numeric
        if pd.api.types.is_integer_dtype(non_null_series):
            max_val = non_null_series.max()
            if max_val <= 2147483647:  # 32-bit int
                return "INTEGER"
            else:
                return "BIGINT"
        
        elif pd.api.types.is_float_dtype(non_null_series):
            return "DECIMAL(10,2)"
        
        # Check if it's boolean
        elif pd.api.types.is_bool_dtype(non_null_series):
            return "BOOLEAN"
        
        # Check if it's datetime
        elif pd.api.types.is_datetime64_any_dtype(non_null_series):
            return "TIMESTAMP"
        
        # For string data, check length
        elif pd.api.types.is_string_dtype(non_null_series) or pd.api.types.is_object_dtype(non_null_series):
            max_length = non_null_series.astype(str).str.len().max()
            if max_length <= 50:
                return "VARCHAR(50)"
            elif max_length <= 255:
                return "VARCHAR(255)"
            elif max_length <= 1000:
                return "VARCHAR(1000)"
            else:
                return "TEXT"
        
        else:
            return "TEXT"
    
    async def _get_ai_insights(self, df: pd.DataFrame, schema: TableSchema) -> Dict[str, Any]:
        """Use OpenAI to generate insights about the data"""
        if not self.openai_api_key:
            return self._generate_basic_insights(df, schema)
        
        try:
            # Prepare data summary for AI
            data_summary = {
                "row_count": len(df),
                "columns": [
                    {
                        "name": col.name,
                        "type": col.data_type,
                        "sample_values": col.sample_values[:3]
                    }
                    for col in schema.columns
                ],
                "sample_rows": df.head(3).to_dict('records')
            }
            
            prompt = f"""
            Analyze this dataset and provide insights:
            
            Data Summary:
            {json.dumps(data_summary, indent=2, default=str)}
            
            Please provide:
            1. data_type: What type of business data is this? (e.g., "ecommerce", "inventory", "hr", "financial", "iot", "marketing", etc.)
            2. confidence: How confident are you in this classification? (0.0 to 1.0)
            3. insights: List of 3-5 key insights about this data
            4. visualizations: List of 3-5 recommended chart types for this data
            5. queries: List of 3-5 useful SQL queries for this data
            
            Format your response as JSON:
            {{
                "data_type": "string",
                "confidence": 0.9,
                "insights": ["insight1", "insight2", ...],
                "visualizations": ["chart_type1", "chart_type2", ...],
                "queries": ["SELECT ...", "SELECT ...", ...]
            }}
            """
            
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            ai_response = json.loads(response.choices[0].message.content)
            logger.info(f"✅ AI analysis completed - detected {ai_response.get('data_type', 'unknown')} data")
            return ai_response
            
        except Exception as e:
            logger.warning(f"⚠️  AI analysis failed, using basic insights: {e}")
            return self._generate_basic_insights(df, schema)
    
    def _generate_basic_insights(self, df: pd.DataFrame, schema: TableSchema) -> Dict[str, Any]:
        """Generate basic insights without AI"""
        
        # Basic data type detection
        column_names = [col.name.lower() for col in schema.columns]
        
        if any(name in column_names for name in ['price', 'amount', 'revenue', 'cost']):
            data_type = "financial"
        elif any(name in column_names for name in ['product', 'order', 'customer']):
            data_type = "ecommerce"
        elif any(name in column_names for name in ['employee', 'salary', 'department']):
            data_type = "hr"
        elif any(name in column_names for name in ['inventory', 'stock', 'quantity']):
            data_type = "inventory"
        else:
            data_type = "general"
        
        return {
            "data_type": data_type,
            "confidence": 0.7,
            "insights": [
                f"Dataset contains {len(df)} rows and {len(schema.columns)} columns",
                f"Detected as {data_type} data based on column names",
                "Data structure automatically analyzed and optimized"
            ],
            "visualizations": [
                "Bar Chart",
                "Line Chart", 
                "Pie Chart",
                "Data Table"
            ],
            "queries": [
                f"SELECT * FROM {schema.table_name} LIMIT 10",
                f"SELECT COUNT(*) as total_rows FROM {schema.table_name}",
                f"SELECT * FROM {schema.table_name} ORDER BY created_at DESC"
            ]
        }

# Global analyzer instance
ai_analyzer = AIDataAnalyzer() 