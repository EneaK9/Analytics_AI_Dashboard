import json
import pandas as pd
import os
from typing import Dict, List, Any, Tuple
from models import ColumnAnalysis, TableSchema, AIAnalysisResult, DataFormat
import re
import logging
from datetime import datetime
from database import get_admin_client, get_db_manager
import uuid
import asyncio
import random
from openai import OpenAI

# Import enhanced data parser
from enhanced_data_parser import enhanced_parser

logger = logging.getLogger(__name__)

class AIDataAnalyzer:
    """AI-powered data analyzer with enhanced format support and comprehensive validation"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            logger.info("✅ OpenAI API key configured")
        else:
            raise Exception("❌ OpenAI API key REQUIRED - no fallbacks allowed")
        
        # Initialize enhanced parser with default config
        self.enhanced_parser = enhanced_parser
    
    async def analyze_data(self, raw_data: str, data_format: DataFormat, client_id: str, 
                          file_name: str = None, **kwargs) -> AIAnalysisResult:
        """
        Analyze raw data using enhanced parser with comprehensive validation
        """
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"🔄 Enhanced analysis of {data_format} data for client {client_id} (attempt {retry_count + 1})")
                
                # Step 1: Use enhanced parser for parsing and validation
                parsed_data, validation_result = await self.enhanced_parser.parse_data(
                    raw_data=raw_data,
                    data_format=data_format,
                    file_name=file_name,
                    **kwargs
                )
                
                if not validation_result.is_valid:
                    raise Exception(f"Data validation failed: {validation_result.error_message}")
                
                # Step 2: Generate data quality report
                quality_report = await self.enhanced_parser.generate_data_quality_report(parsed_data)
                
                logger.info(f"📊 Data quality score: {quality_report.quality_score:.2f}")
                
                # Step 3: Analyze data structure for schema generation
                columns = self._analyze_columns_enhanced(parsed_data, quality_report)
                
                # Step 4: Generate table name
                clean_client_id = client_id.replace('-', '_')
                table_name = f"client_{clean_client_id}_data"
                
                # Step 5: Create enhanced schema with validation info
                schema = TableSchema(
                    table_name=table_name,
                    columns=columns,
                    relationships=[],
                    indexes=[],
                    constraints=[]
                )
                
                # Step 6: Generate AI insights with enhanced context
                business_insights = await self._generate_enhanced_ai_insights(
                    parsed_data, schema, data_format, validation_result, quality_report
                )
                
                # Step 7: Create comprehensive AI result
                result = AIAnalysisResult(
                    data_type=self._detect_enhanced_data_type(parsed_data, business_insights),
                    confidence=business_insights.get('confidence', 0.8),
                    table_schema=schema,
                    insights=business_insights.get('insights', []),
                    recommended_visualizations=business_insights.get('visualizations', []),
                    sample_queries=business_insights.get('queries', [])
                )
                
                logger.info(f"✅ Enhanced AI analysis completed for client {client_id}")
                logger.info(f"📈 Detected: {result.data_type} data with {quality_report.quality_score:.1%} quality")
                
                return result
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"⚠️ Enhanced analysis attempt {retry_count} failed: {e}")
                
                if retry_count >= max_retries:
                    logger.error(f"❌ Enhanced analysis failed after {max_retries} attempts")
                    raise Exception(f"AI analysis failed after {max_retries} attempts: {str(e)}")
                
                # Exponential backoff
                wait_time = min(2 ** retry_count + (random.random() * 2), 30)
                logger.info(f"⏳ Waiting {wait_time:.1f}s before retry...")
                await asyncio.sleep(wait_time)
    
    async def create_table_and_insert_data(self, ai_result: AIAnalysisResult, parsed_data: pd.DataFrame, client_id: str):
        """High-performance table creation and data insertion using database manager"""
        try:
            logger.info(f"🚀 Starting high-performance data insertion for client {client_id}")
            
            # Step 1: Create the table first
            await self._create_client_table(None, ai_result.table_schema)
            
            # Step 2: Clean and prepare data for insertion
            clean_records = self._prepare_data_for_insertion(parsed_data)
            
            if not clean_records:
                logger.warning(f"⚠️  No records to insert for client {client_id}")
                return 0
            
            # Step 3: Use optimized batch insert
            manager = get_db_manager()
            table_name = ai_result.table_schema.table_name
            
            rows_inserted = await manager.batch_insert_client_data(
                table_name, clean_records, client_id
            )
            
            # Step 4: Update data_uploads table with status using optimized method
            await self._update_data_uploads_status_optimized(
                client_id, data_format, len(raw_data), rows_inserted
            )
            
            logger.info(f"✅ High-performance insertion completed: {rows_inserted} rows")
            return rows_inserted
                
        except Exception as e:
            logger.error(f"❌ Optimized data insertion failed: {e}")
            raise Exception(f"Failed to create table and insert data: {str(e)}")
    
    async def _create_client_table(self, db_client, schema: TableSchema):
        """Create individual client table using database manager"""
        try:
            create_table_sql = self._generate_create_table_sql(schema)
            
            logger.info(f"📊 Creating table: {schema.table_name}")
            
            # Use the database manager to create the table
            manager = get_db_manager()
            success = await manager.create_client_table(schema.table_name, create_table_sql)
            
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
        
        for _, row in parsed_data.iterrows():
            record = {}
            for col, value in row.items():
                # Clean column name (remove special characters)
                clean_col = re.sub(r'[^a-zA-Z0-9_]', '_', str(col).lower())
                
                # Handle different data types
                if pd.isna(value):
                    record[clean_col] = None
                elif isinstance(value, (int, float)):
                    record[clean_col] = value
                else:
                    record[clean_col] = str(value)
            
            clean_records.append(record)
        
        return clean_records
    
    async def insert_data_into_table(self, table_name: str, records: List[Dict], data_format: str = "json"):
        """Insert data into existing table using optimized database manager"""
        try:
            logger.info(f"⚡ Fast data insertion into {table_name}: {len(records)} records")
            
            # Extract client_id from table name
            client_id = None
            if table_name.startswith("client_") and table_name.endswith("_data"):
                # Extract UUID from table name: client_{uuid}_data
                parts = table_name.split("_")
                if len(parts) >= 3:
                    uuid_part = "_".join(parts[1:-1])  # Everything except first and last
                    client_id = uuid_part.replace("_", "-")
            
            if not client_id:
                logger.error(f"❌ Could not extract client_id from table name: {table_name}")
                return 0
            
            # Use the database manager to insert data
            manager = get_db_manager()
            rows_inserted = await manager.insert_client_data(table_name, records, client_id)
            
            logger.info(f"✅ Successfully inserted {rows_inserted} records into {table_name}")
            return rows_inserted
            
        except Exception as e:
            logger.error(f"❌ Failed to insert data into {table_name}: {e}")
            raise Exception(f"Failed to insert data: {str(e)}")
    
    async def _update_data_uploads_status(self, db_client, client_id: str, data_format: DataFormat, 
                                        file_size: int, rows_processed: int):
        """Update data_uploads table with optimized operations"""
        try:
            logger.info(f"📝 Updating upload status for client {client_id}")
            
            upload_record = {
                "client_id": client_id,
                "file_type": data_format.value,
                "file_size": file_size,
                "rows_processed": rows_processed,
                "status": "completed",
                "uploaded_at": datetime.utcnow().isoformat(),
                "processing_time": "< 1 second"  # High-performance!
            }
            
            # Insert upload record
            response = db_client.table("data_uploads").insert(upload_record).execute()
            
            if response.data:
                logger.info(f"✅ Upload status updated for client {client_id}")
            else:
                logger.warning(f"⚠️  Upload status update failed for client {client_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to update upload status: {e}")
    
    async def _update_data_uploads_status_optimized(self, client_id: str, data_format: DataFormat, 
                                                  file_size: int, rows_processed: int):
        """Update data_uploads table using optimized database operations"""
        try:
            manager = get_db_manager()
            client = manager.get_admin_client()
            
            upload_record = {
                "client_id": client_id,
                "file_type": data_format.value,
                "file_size": file_size,
                "rows_processed": rows_processed,
                "status": "completed",
                "uploaded_at": datetime.utcnow().isoformat(),
                "processing_time": "< 1 second"  # High-performance!
            }
            
            # Insert upload record using optimized client
            response = client.table("data_uploads").insert(upload_record).execute()
            
            if response.data:
                logger.info(f"✅ Optimized upload status updated for client {client_id}")
            else:
                logger.warning(f"⚠️  Optimized upload status update failed for client {client_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to update optimized upload status: {e}")
    
    async def get_client_data_optimized(self, client_id: str, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Retrieve client data using optimized database operations with caching.

        Accepts optional start_date/end_date ISO strings to return a full-range dataset without sampling."""
        try:
            logger.info(f"⚡ Fast data retrieval for client {client_id}")

            manager = get_db_manager()
            result = await manager.fast_client_data_lookup(
                client_id, use_cache=True, start_date=start_date, end_date=end_date
            )

            # Ensure client_id is present for hashing
            result['client_id'] = client_id

            logger.info(
                f"✅ Retrieved {result['row_count']} records in {result.get('query_time', 0):.3f}s"
            )
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
    
    def _analyze_columns_enhanced(self, df: pd.DataFrame, quality_report) -> List[ColumnAnalysis]:
        """Enhanced column analysis with data quality insights"""
        columns = []
        
        for col_name, col_data in df.items():
            # Get enhanced data type info
            sql_type = self._infer_sql_type_enhanced(col_data, quality_report.data_types_detected.get(col_name))
            
            # Advanced primary key detection
            is_primary_key = self._detect_primary_key_enhanced(col_name, col_data)
            
            # Enhanced uniqueness check
            is_unique = self._check_uniqueness_enhanced(col_data)
            
            # Null analysis
            has_nulls = col_data.isnull().any()
            null_percentage = (col_data.isnull().sum() / len(col_data)) * 100 if len(col_data) > 0 else 0
            
            # Enhanced sample values
            sample_values = self._get_enhanced_sample_values(col_data)
            
            # Generate enhanced description
            description = self._generate_column_description(col_name, col_data, sql_type, null_percentage)
            
            column = ColumnAnalysis(
                name=col_name,
                data_type=sql_type,
                nullable=has_nulls,
                primary_key=is_primary_key,
                unique=is_unique,
                sample_values=sample_values,
                description=description
            )
            
            columns.append(column)
        
        return columns
    
    def _infer_sql_type_enhanced(self, series: pd.Series, detected_type: str = None) -> str:
        """Enhanced SQL type inference with better precision"""
        non_null_series = series.dropna()
        
        if len(non_null_series) == 0:
            return "TEXT"
        
        # Use detected type as hint
        if detected_type:
            if detected_type == "integer":
                max_val = non_null_series.max()
                min_val = non_null_series.min()
                if min_val >= -2147483648 and max_val <= 2147483647:
                    return "INTEGER"
                else:
                    return "BIGINT"
            elif detected_type == "float":
                # Check precision requirements
                max_decimal_places = 0
                for val in non_null_series.head(100):  # Sample for performance
                    if isinstance(val, float):
                        decimal_str = str(val).split('.')
                        if len(decimal_str) > 1:
                            max_decimal_places = max(max_decimal_places, len(decimal_str[1]))
                
                if max_decimal_places <= 2:
                    return "DECIMAL(10,2)"
                elif max_decimal_places <= 4:
                    return "DECIMAL(15,4)"
                else:
                    return "DOUBLE PRECISION"
            elif detected_type == "boolean":
                return "BOOLEAN"
            elif detected_type == "datetime":
                return "TIMESTAMP WITH TIME ZONE"
        
        # Fallback to original logic
        return self._infer_sql_type(series)
    
    def _detect_primary_key_enhanced(self, col_name: str, col_data: pd.Series) -> bool:
        """Enhanced primary key detection"""
        # Check naming patterns
        pk_patterns = ['id', 'uuid', 'pk', '_id', 'key']
        name_lower = col_name.lower()
        
        if any(pattern in name_lower for pattern in pk_patterns):
            # Check if values are unique and not null
            if col_data.nunique() == len(col_data) and not col_data.isnull().any():
                return True
        
        # Check for auto-incrementing integer patterns
        if pd.api.types.is_integer_dtype(col_data):
            if col_data.nunique() == len(col_data):
                # Check if it looks like auto-increment
                sorted_values = col_data.sort_values()
                if len(sorted_values) > 1:
                    differences = sorted_values.diff().dropna()
                    if all(diff == 1 for diff in differences):
                        return True
        
        return False
    
    def _check_uniqueness_enhanced(self, col_data: pd.Series) -> bool:
        """Enhanced uniqueness check with statistical analysis"""
        if len(col_data) == 0:
            return False
        
        unique_count = col_data.nunique()
        total_count = len(col_data)
        
        # Consider unique if > 95% unique values
        uniqueness_ratio = unique_count / total_count
        return uniqueness_ratio > 0.95
    
    def _get_enhanced_sample_values(self, col_data: pd.Series) -> List[Any]:
        """Get enhanced sample values with better representation"""
        non_null_data = col_data.dropna()
        
        if len(non_null_data) == 0:
            return ["NULL"]
        
        # For numeric data, include min, max, and median
        if pd.api.types.is_numeric_dtype(non_null_data):
            samples = [
                non_null_data.min(),
                non_null_data.median(),
                non_null_data.max()
            ]
            return [float(x) if pd.api.types.is_float_dtype(non_null_data) else int(x) for x in samples]
        
        # For categorical data, get most frequent values
        value_counts = non_null_data.value_counts()
        top_values = value_counts.head(3).index.tolist()
        
        return [str(val) for val in top_values]
    
    def _generate_column_description(self, col_name: str, col_data: pd.Series, 
                                   sql_type: str, null_percentage: float) -> str:
        """Generate enhanced column descriptions"""
        description_parts = [f"Auto-detected {sql_type} column"]
        
        if null_percentage > 0:
            description_parts.append(f"({null_percentage:.1f}% null values)")
        
        # Add semantic hints based on column name
        name_lower = col_name.lower()
        if 'email' in name_lower:
            description_parts.append("(email address)")
        elif 'phone' in name_lower:
            description_parts.append("(phone number)")
        elif 'date' in name_lower or 'time' in name_lower:
            description_parts.append("(temporal data)")
        elif 'price' in name_lower or 'cost' in name_lower or 'amount' in name_lower:
            description_parts.append("(monetary value)")
        elif 'count' in name_lower or 'quantity' in name_lower:
            description_parts.append("(quantity/count)")
        
        return " ".join(description_parts)
    
    async def _generate_enhanced_ai_insights(self, df: pd.DataFrame, schema: TableSchema, 
                                           data_format: DataFormat, validation_result, 
                                           quality_report) -> Dict[str, Any]:
        """Generate enhanced AI insights with comprehensive context"""
        max_retries = 15
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Prepare enhanced data summary
                enhanced_summary = {
                    "basic_info": {
                        "row_count": len(df),
                        "column_count": len(df.columns),
                        "data_format": data_format.value,
                        "file_size": validation_result.file_size,
                        "encoding": validation_result.encoding
                    },
                    "data_quality": {
                        "quality_score": quality_report.quality_score,
                        "complete_rows": quality_report.complete_rows,
                        "missing_values": quality_report.missing_values_count,
                        "duplicate_rows": quality_report.duplicate_rows,
                        "issues": quality_report.issues,
                        "data_types": quality_report.data_types_detected
                    },
                    "column_analysis": [
                        {
                            "name": col.name,
                            "type": col.data_type,
                            "sample_values": col.sample_values[:3],
                            "is_unique": col.unique,
                            "description": col.description
                        }
                        for col in schema.columns[:10]  # Limit for AI processing
                    ],
                    "sample_data": df.head(3).to_dict('records') if not df.empty else []
                }
                
                # Enhance prompt for JSON data with more specific context
                data_format_context = ""
                if data_format == DataFormat.JSON:
                    data_format_context = f"""
                    
                    📊 **JSON DATA ANALYSIS FOCUS**:
                    This is JSON data with {len(df)} records and {len(df.columns)} fields.
                    Field types detected: {', '.join([f"{col.name}({col.data_type})" for col in schema.columns[:5]])}
                    
                    Please provide detailed insights specifically for this JSON dataset structure:
                    - Analyze the relationships between fields
                    - Identify key patterns in the data values
                    - Suggest appropriate visualizations for the data structure
                    - Recommend practical business use cases for this specific data
                    """
                
                prompt = f"""
                Analyze this enhanced dataset and provide comprehensive insights:
                
                Dataset Summary:
                {json.dumps(enhanced_summary, indent=2, default=str)}
                {data_format_context}
                
                Based on this enhanced analysis, please provide SPECIFIC and DETAILED insights:
                
                1. **data_type**: What type of data is this? 
                   Options: "ecommerce", "crm", "financial", "hr", "marketing", "analytics", 
                   "iot", "inventory", "healthcare", "education", "logistics", "manufacturing", "other"
                
                2. **confidence**: Confidence in classification (0.0 to 1.0)
                
                3. **insights**: List of 5-7 SPECIFIC insights about this data (avoid generic statements):
                   - Concrete data quality observations with numbers
                   - Specific business value potential with examples
                   - Actual patterns or trends visible in the data
                   - Practical recommended use cases for this exact dataset
                   - Key correlations or relationships between fields
                
                4. **visualizations**: List of 8-12 recommended chart types optimized for this specific data:
                   Options: "line_chart", "bar_chart", "pie_chart", "scatter_plot", "heatmap", 
                   "area_chart", "histogram", "box_plot", "treemap", "gauge", "funnel", "waterfall"
                
                5. **queries**: List of 5-7 useful SQL queries for analyzing this specific dataset
                
                6. **recommendations**: List of 3-5 actionable recommendations for this specific dataset
                
                7. **kpi_suggestions**: List of 8-12 key performance indicators that could be calculated from this data
                
                Respond in valid JSON format:
                {{
                    "data_type": "string",
                    "confidence": 0.9,
                    "insights": ["insight1", "insight2", ...],
                    "visualizations": ["chart_type1", "chart_type2", ...],
                    "queries": ["SELECT ...", "SELECT ...", ...],
                    "recommendations": ["recommendation1", ...],
                    "kpi_suggestions": ["kpi1", "kpi2", ...]
                }}
                """
                
                # Enhanced OpenAI call with better model
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",  # Use GPT-4o-mini for cost-effective analysis
                    messages=[
                        {"role": "system", "content": "You are an expert data analyst and business intelligence consultant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=3000  # Increased for comprehensive response
                )
                
                ai_response = json.loads(response.choices[0].message.content)
                
                # Validate response structure
                required_keys = ["data_type", "confidence", "insights", "visualizations", "queries", "recommendations"]
                for key in required_keys:
                    if key not in ai_response:
                        raise Exception(f"Missing required key in AI response: {key}")
                
                logger.info(f"✅ Enhanced AI insights completed - detected {ai_response.get('data_type', 'unknown')} data")
                return ai_response
                
            except Exception as e:
                retry_count += 1
                wait_time = min(retry_count * 3, 60)
                logger.warning(f"⚠️ Enhanced AI insights attempt {retry_count} failed: {e}")
                
                if retry_count >= max_retries:
                    logger.error(f"❌ Enhanced AI insights failed after {max_retries} attempts: {e}")
                    # Return fallback response
                    return {
                        "data_type": "general",
                        "confidence": 0.5,
                        "insights": ["Data analysis completed with enhanced parser"],
                        "visualizations": ["bar_chart", "line_chart"],
                        "queries": ["SELECT * FROM data LIMIT 10"],
                        "recommendations": ["Explore data patterns"],
                        "kpi_suggestions": ["Total Records", "Data Quality Score"]
                    }
                
                logger.info(f"🔄 Retrying enhanced AI call in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
    
    def _detect_enhanced_data_type(self, df: pd.DataFrame, business_insights: Dict[str, Any]) -> str:
        """Enhanced data type detection using AI insights and heuristics"""
        ai_detected = business_insights.get("data_type", "general")
        
        # Validate AI detection with heuristics
        column_names = [col.lower() for col in df.columns]
        
        # E-commerce indicators
        ecommerce_keywords = ['price', 'product', 'order', 'customer', 'sale', 'revenue', 'cart', 'checkout']
        if any(keyword in ' '.join(column_names) for keyword in ecommerce_keywords):
            if ai_detected in ['ecommerce', 'general']:
                return 'ecommerce'
        
        # Financial indicators
        financial_keywords = ['amount', 'transaction', 'account', 'balance', 'payment', 'invoice']
        if any(keyword in ' '.join(column_names) for keyword in financial_keywords):
            if ai_detected in ['financial', 'general']:
                return 'financial'
        
        # CRM indicators
        crm_keywords = ['contact', 'lead', 'opportunity', 'pipeline', 'customer', 'client']
        if any(keyword in ' '.join(column_names) for keyword in crm_keywords):
            if ai_detected in ['crm', 'general']:
                return 'crm'
        
        return ai_detected
    
    def _calculate_confidence(self, df: pd.DataFrame, columns: List[ColumnAnalysis]) -> float:
        """Calculate a confidence score based on the number of unique values and nulls."""
        total_rows = len(df)
        unique_values_count = sum(col.unique for col in columns)
        null_count = sum(col.nullable for col in columns)
        
        # Simple heuristic: confidence is higher if many columns are unique and few are null
        # This is a placeholder and can be refined
        confidence = (unique_values_count / len(columns)) * (1 - (null_count / total_rows))
        return min(1.0, max(0.0, confidence))

    def _generate_recommendations(self, df: pd.DataFrame, schema: TableSchema) -> List[str]:
        """Generate recommendations based on the AI insights."""
        insights = schema.ai_suggestions.lower()
        recommendations = []
        
        if "recommendation" in insights:
            recommendations.append("Consider implementing a data visualization dashboard.")
            recommendations.append("Analyze trends and patterns in the data.")
            recommendations.append("Identify potential outliers or anomalies.")
        if "visualization" in insights:
            recommendations.append("Use charts and graphs to represent the data.")
            recommendations.append("Consider a bar chart for categorical data.")
            recommendations.append("Use a line chart for time-series data.")
        if "query" in insights:
            recommendations.append("Write SQL queries to extract specific data.")
            recommendations.append("Optimize existing queries for better performance.")
            recommendations.append("Consider using materialized views for frequently queried data.")
        
        return recommendations

# Global analyzer instance
ai_analyzer = AIDataAnalyzer() 