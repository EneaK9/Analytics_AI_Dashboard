from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import uuid

# Enums
class SubscriptionTier(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class DataFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    XML = "xml"
    TSV = "tsv"
    PARQUET = "parquet"
    YAML = "yaml"
    AVRO = "avro"
    ORC = "orc"

class UploadStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ANALYZING = "analyzing"

# Client Management Models
class ClientCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)

class ClientLogin(BaseModel):
    email: EmailStr
    password: str

class ClientResponse(BaseModel):
    client_id: uuid.UUID
    company_name: str
    email: str
    subscription_tier: SubscriptionTier
    created_at: datetime
    updated_at: datetime
    
    # Optional fields for enhanced client info (hybrid approach)
    has_schema: Optional[bool] = None
    schema_info: Optional[Dict[str, Any]] = None
    actual_data_count: Optional[int] = None
    data_stored: Optional[bool] = None

class ClientUpdate(BaseModel):
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None
    subscription_tier: Optional[SubscriptionTier] = None

# Data Upload Models
class DataUpload(BaseModel):
    client_id: uuid.UUID
    raw_data: str  # JSON string, CSV content, etc.
    data_format: DataFormat
    description: str = ""
    original_filename: Optional[str] = None

class DataUploadResponse(BaseModel):
    upload_id: uuid.UUID
    client_id: uuid.UUID
    original_filename: Optional[str]
    data_format: DataFormat
    file_size_bytes: int
    rows_processed: Optional[int]
    status: UploadStatus
    error_message: Optional[str]
    created_at: datetime

# AI Analysis Models
class ColumnAnalysis(BaseModel):
    name: str
    data_type: str  # "INTEGER", "VARCHAR(255)", "DECIMAL(10,2)", etc.
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    sample_values: List[Any] = []
    description: str = ""

class TableSchema(BaseModel):
    table_name: str
    columns: List[ColumnAnalysis]
    relationships: List[Dict[str, Any]] = []
    indexes: List[str] = []
    constraints: List[str] = []

class AIAnalysisResult(BaseModel):
    data_type: str  # "ecommerce", "inventory", "hr", "financial", etc.
    confidence: float  # 0.0 to 1.0
    table_schema: TableSchema
    insights: List[str] = []
    recommended_visualizations: List[str] = []
    sample_queries: List[str] = []

class ClientSchemaResponse(BaseModel):
    schema_id: uuid.UUID
    client_id: uuid.UUID
    schema_definition: Dict[str, Any]
    table_name: str
    data_type: Optional[str]
    ai_analysis: Optional[str]
    created_at: datetime
    updated_at: datetime

# Authentication Models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    client_id: Optional[uuid.UUID] = None
    email: Optional[str] = None

# Dashboard Data Models (Dynamic)
class DynamicData(BaseModel):
    """Flexible data model for any client's custom data structure"""
    table_name: str
    table_schema: Dict[str, Any]
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}

class QueryRequest(BaseModel):
    client_id: uuid.UUID
    table_name: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 100
    offset: int = 0
    order_by: Optional[str] = None

class QueryResponse(BaseModel):
    data: List[Dict[str, Any]]
    total_count: int
    page: int
    limit: int
    has_more: bool

# Super Admin Models
class SuperAdminCreate(BaseModel):
    username: str
    password: str
    email: EmailStr

class SuperAdminLogin(BaseModel):
    username: str
    password: str

class SuperAdminResponse(BaseModel):
    admin_id: uuid.UUID
    username: str
    email: str
    created_at: datetime

# API Integration Models
class PlatformType(str, Enum):
    SHOPIFY = "shopify"
    AMAZON = "amazon"
    WOOCOMMERCE = "woocommerce"
    BIGCOMMERCE = "bigcommerce"
    ETSY = "etsy"
    MANUAL = "manual"

class APIConnectionStatus(str, Enum):
    PENDING = "pending"
    CONNECTED = "connected"
    ERROR = "error"
    EXPIRED = "expired"
    REVOKED = "revoked"

class ShopifyCredentials(BaseModel):
    shop_domain: str = Field(..., description="Store domain (e.g., mystore.myshopify.com)")
    access_token: str = Field(..., description="Admin API access token")
    scopes: List[str] = Field(default=["read_orders", "read_products", "read_customers", "read_analytics"])
    webhook_url: Optional[str] = None

class AmazonCredentials(BaseModel):
    seller_id: str = Field(..., description="Amazon Seller/Merchant ID")
    marketplace_ids: List[str] = Field(..., description="Marketplace IDs (US: ATVPDKIKX0DER)")
    access_key_id: str = Field(..., description="AWS Access Key ID for SP-API")
    secret_access_key: str = Field(..., description="AWS Secret Access Key")
    refresh_token: str = Field(..., description="SP-API Refresh Token")
    region: str = Field(default="us-east-1", description="AWS Region")

class WooCommerceCredentials(BaseModel):
    site_url: str = Field(..., description="WordPress site URL")
    consumer_key: str = Field(..., description="WooCommerce Consumer Key")
    consumer_secret: str = Field(..., description="WooCommerce Consumer Secret")
    version: str = Field(default="wc/v3", description="API Version")

class APICredentials(BaseModel):
    client_id: uuid.UUID
    platform_type: PlatformType
    connection_name: str = Field(..., description="User-friendly name for the connection")
    credentials: Union[ShopifyCredentials, AmazonCredentials, WooCommerceCredentials, Dict[str, Any]]
    status: APIConnectionStatus = APIConnectionStatus.PENDING
    last_sync_at: Optional[datetime] = None
    next_sync_at: Optional[datetime] = None
    sync_frequency_hours: int = Field(default=24, description="How often to sync data (hours)")
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class APIDataSyncResult(BaseModel):
    client_id: uuid.UUID
    platform_type: PlatformType
    connection_name: str
    records_fetched: int
    records_processed: int
    records_stored: int
    sync_duration_seconds: float
    success: bool
    error_message: Optional[str] = None
    data_types_synced: List[str] = Field(default=[], description="Types of data synced (orders, products, etc.)")
    sync_timestamp: datetime = Field(default_factory=datetime.now)

# Enhanced Client Management Models
class ClientCreateAdmin(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    # subscription_tier: SubscriptionTier = SubscriptionTier.BASIC
    data_type: Optional[str] = "json"
    input_method: Optional[str] = "paste"  # paste, upload, api
    data_content: Optional[str] = ""
    
    # API Integration fields
    platform_type: Optional[PlatformType] = None
    api_credentials: Optional[Dict[str, Any]] = None
    connection_name: Optional[str] = None
    sync_frequency_hours: Optional[int] = 24

class ClientListResponse(BaseModel):
    clients: List[ClientResponse]
    total: int
    page: int
    limit: int

# Schema Creation Request
class CreateSchemaRequest(BaseModel):
    client_id: uuid.UUID
    raw_data: str
    data_format: DataFormat
    force_recreate: bool = False

class CreateSchemaResponse(BaseModel):
    success: bool
    table_name: str
    table_schema: TableSchema
    ai_analysis: AIAnalysisResult
    rows_inserted: int
    message: str

# ==================== PERSONALIZED DASHBOARD MODELS ====================

from enum import Enum

# Chart Type Constants - MUI COMPONENTS ONLY
class ChartType(str, Enum):
	# Available MUI Charts
	BAR_CHART_ONE = "BarChartOne"
	LINE_CHART_ONE = "LineChartOne"
	
	# Legacy aliases for compatibility - all map to available MUI components
	line = "LineChartOne"
	bar = "BarChartOne"
	pie = "BarChartOne"  # Default to bar chart since no pie available

class KPIWidget(BaseModel):
    """Configuration for a KPI widget"""
    id: str
    title: str
    value: str
    icon: str
    icon_color: str
    icon_bg_color: str
    trend: Optional[Dict[str, Any]] = None  # {"value": "12.5%", "isPositive": True}
    position: Dict[str, int]  # {"row": 0, "col": 0}
    size: Dict[str, int]  # {"width": 1, "height": 1}

class ChartWidget(BaseModel):
    """Configuration for a chart widget"""
    id: str
    title: str
    subtitle: Optional[str] = None
    chart_type: ChartType
    data_source: str  # Reference to metric name
    config: Dict[str, Any]  # Chart-specific configuration
    position: Dict[str, int]  # {"row": 1, "col": 0}
    size: Dict[str, int]  # {"width": 2, "height": 2}

class DashboardLayout(BaseModel):
    """Dashboard layout configuration"""
    grid_cols: int = 4
    grid_rows: int = 6
    gap: int = 4
    responsive: bool = True

class DashboardConfig(BaseModel):
    """Complete dashboard configuration"""
    client_id: uuid.UUID
    title: str
    subtitle: Optional[str] = None
    layout: DashboardLayout
    kpi_widgets: List[KPIWidget]
    chart_widgets: List[ChartWidget]
    theme: str = "default"
    last_generated: datetime
    version: str = "1.0"

class DashboardMetric(BaseModel):
    """Dashboard metric data"""
    metric_id: Optional[uuid.UUID] = None
    client_id: uuid.UUID
    metric_name: str
    metric_value: Dict[str, Any]
    metric_type: str  # 'kpi', 'chart_data', 'trend'
    calculated_at: datetime

# NEW STANDARDIZED RESPONSE MODELS
class FieldMapping(BaseModel):
    """Field name mapping for clear display"""
    original_fields: Dict[str, str]  # "Monthly Sales" -> "monthly_sales"
    display_names: Dict[str, str]    # "monthly_sales" -> "Monthly Sales"
    
class MetadataInfo(BaseModel):
    """Dashboard metadata information"""
    source_type: str  # csv, json, api
    generated_at: datetime
    total_records: int
    version: str = "1.0"

class TrendInfo(BaseModel):
    """KPI trend information"""
    percentage: float
    direction: str  # up, down, neutral
    description: str = "vs last month"

class StandardizedKPI(BaseModel):
    """Standardized KPI structure"""
    id: str
    display_name: str
    technical_name: str
    value: str
    trend: TrendInfo
    format: str  # currency, number, percentage

class StandardizedChart(BaseModel):
    """Standardized chart structure"""
    id: str
    display_name: str
    technical_name: str
    chart_type: str
    data: List[Any]  # More flexible to handle complex chart data
    config: Dict[str, Any]  # Use simple dict instead of nested Pydantic models
    
    class Config:
        # Allow arbitrary types to handle complex chart data
        arbitrary_types_allowed = True
        # Use JSON serialization for complex objects
        json_encoders = {
            # Handle any datetime objects
            datetime: lambda dt: dt.isoformat(),
            # Handle numpy types if present
            type(None): lambda _: None
        }

class StandardizedTable(BaseModel):
    """Standardized table structure"""
    id: str
    display_name: str
    technical_name: str
    data: List[Any]  # Table rows - can be list or dict format
    columns: List[Any]  # Column definitions - can be string or dict format
    config: Dict[str, Any] = {}  # Table configuration (sorting, filtering, etc.)
    
    class Config:
        # Allow arbitrary types to handle both list and dict formats
        arbitrary_types_allowed = True

class StandardizedDashboardData(BaseModel):
    """Main dashboard data structure"""
    metadata: MetadataInfo
    kpis: List[StandardizedKPI]
    charts: List[StandardizedChart]
    tables: List[StandardizedTable] = []  # Add tables support
    field_mappings: FieldMapping

class StandardizedDashboardResponse(BaseModel):
    """Standardized response format for all dashboard endpoints"""
    success: bool
    client_id: uuid.UUID
    dashboard_data: StandardizedDashboardData
    message: Optional[str] = None
    
    class Config:
        # Allow arbitrary types for flexible data handling
        arbitrary_types_allowed = True
        # Custom JSON encoders for special types
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            uuid.UUID: lambda u: str(u)
        }

class DashboardGenerationRequest(BaseModel):
    """Request to generate a dashboard"""
    force_regenerate: bool = False
    include_sample_data: bool = True

class DashboardGenerationResponse(BaseModel):
    """Response from dashboard generation"""
    success: bool
    client_id: uuid.UUID
    dashboard_config: Optional[DashboardConfig]  # Make optional to allow None on errors
    metrics_generated: int
    message: str
    generation_time: float

class DashboardStatusResponse(BaseModel):
    """Dashboard status for a client"""
    client_id: uuid.UUID
    has_dashboard: bool
    is_generated: bool
    last_updated: Optional[datetime]
    metrics_count: int

class AIInsight(BaseModel):
    """AI-generated insight about client data"""
    type: str  # 'opportunity', 'warning', 'trend', 'recommendation'
    title: str
    description: str
    impact: str  # 'high', 'medium', 'low'
    suggested_action: Optional[str] = None
    data_source: Optional[str] = None

class BusinessContext(BaseModel):
    """AI-analyzed business context"""
    industry: str
    business_type: str  # 'ecommerce', 'saas', 'retail', 'service', etc.
    data_characteristics: List[str]
    key_metrics: List[str]
    recommended_charts: List[ChartType]
    insights: List[AIInsight]
    confidence_score: float

class DataAnalysisResult(BaseModel):
    """Result of AI data analysis for dashboard generation"""
    client_id: uuid.UUID
    business_context: BusinessContext
    suggested_kpis: List[Dict[str, Any]]
    suggested_charts: List[Dict[str, Any]]
    data_quality_score: float
    analysis_timestamp: datetime

# ==================== AUTOMATIC GENERATION & RETRY SYSTEM ====================

class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class GenerationType(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"

class ErrorType(str, Enum):
    AI_FAILURE = "ai_failure"        # Retryable - OpenAI API issues, timeouts
    SYSTEM_ERROR = "system_error"    # Non-retryable - Database issues, code bugs
    DATA_ERROR = "data_error"        # Non-retryable - Invalid/insufficient data

class DashboardGenerationTracking(BaseModel):
    """Tracks dashboard generation attempts and retries"""
    generation_id: Optional[uuid.UUID] = None
    client_id: uuid.UUID
    status: GenerationStatus
    generation_type: GenerationType
    attempt_count: int = 0
    max_attempts: int = 5
    last_attempt_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    error_type: Optional[ErrorType] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class RetryInfo(BaseModel):
    """Information about retry attempts"""
    should_retry: bool
    error_type: ErrorType
    retry_delay_seconds: int
    next_attempt: int
    max_attempts: int
    reason: str

class GenerationResult(BaseModel):
    """Result of dashboard generation attempt"""
    success: bool
    client_id: uuid.UUID
    generation_id: uuid.UUID
    dashboard_config: Optional[DashboardConfig] = None
    metrics_generated: int = 0
    error_type: Optional[ErrorType] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    retry_info: Optional[RetryInfo] = None
    generation_time: float
    attempt_number: int

class AutoGenerationRequest(BaseModel):
    """Request for automatic dashboard generation"""
    client_id: uuid.UUID
    generation_type: GenerationType = GenerationType.AUTOMATIC
    force_retry: bool = False

class GenerationStatusResponse(BaseModel):
    """Response showing generation status"""
    client_id: uuid.UUID
    status: GenerationStatus
    attempt_count: int
    max_attempts: int
    error_type: Optional[ErrorType] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None 

# ==================== API KEY AUTHENTICATION MODELS ====================

class APIKeyScope(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    ANALYTICS = "analytics"
    FULL_ACCESS = "full_access"

class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable name for the API key")
    scopes: List[APIKeyScope] = Field(..., min_items=1, description="List of permissions for this API key")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")
    rate_limit: Optional[int] = Field(100, ge=1, le=10000, description="Requests per hour limit")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")

class APIKeyResponse(BaseModel):
    key_id: uuid.UUID
    client_id: uuid.UUID
    name: str
    key_preview: str  # Show only first 8 characters for security
    scopes: List[APIKeyScope]
    status: APIKeyStatus
    rate_limit: int
    requests_made: int
    last_used: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    description: Optional[str] = None

class APIKeyUsage(BaseModel):
    key_id: uuid.UUID
    endpoint: str
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    response_status: int
    request_size: Optional[int]
    response_size: Optional[int]

# ==================== ENHANCED DATA UPLOAD MODELS ====================

class FileValidationResult(BaseModel):
    is_valid: bool
    file_size: int
    detected_format: Optional[DataFormat]
    error_message: Optional[str]
    warnings: List[str] = []
    encoding: Optional[str] = None
    rows_detected: Optional[int] = None
    columns_detected: Optional[int] = None

class EnhancedDataUpload(BaseModel):
    client_id: uuid.UUID
    raw_data: Optional[str] = None  # For pasted data
    file_name: Optional[str] = None  # For uploaded files
    data_format: DataFormat
    description: str = ""
    validation_result: Optional[FileValidationResult] = None
    auto_detect_format: bool = True
    encoding: str = "utf-8"
    delimiter: Optional[str] = None  # For CSV/TSV
    sheet_name: Optional[str] = None  # For Excel
    max_rows: Optional[int] = Field(None, ge=1, le=1000000)  # Limit for large files

class DataUploadConfig(BaseModel):
    """Configuration for data upload processing"""
    max_file_size_mb: int = 100
    allowed_formats: List[DataFormat] = [
        DataFormat.JSON, DataFormat.CSV, DataFormat.EXCEL, 
        DataFormat.XML, DataFormat.TSV, DataFormat.PARQUET
    ]
    auto_detect_encoding: bool = True
    validate_data_quality: bool = True
    generate_preview: bool = True
    chunk_size: int = 1000  # For large file processing

# ==================== SECURITY AND VALIDATION MODELS ====================

class SecurityValidation(BaseModel):
    """Security validation results for uploaded files"""
    passed_virus_scan: bool = True
    file_type_valid: bool = True
    content_safe: bool = True
    size_within_limits: bool = True
    security_warnings: List[str] = []
    scan_timestamp: datetime
    scan_engine: str = "internal"

class DataQualityReport(BaseModel):
    """Data quality assessment report"""
    total_rows: int
    total_columns: int
    complete_rows: int
    missing_values_count: int
    duplicate_rows: int
    data_types_detected: Dict[str, str]
    quality_score: float  # 0.0 to 1.0
    recommendations: List[str]
    issues: List[str]
    processing_time: float 