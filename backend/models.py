from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
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

# Enhanced Client Management Models
class ClientCreateAdmin(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    # subscription_tier: SubscriptionTier = SubscriptionTier.BASIC
    data_type: Optional[str] = "json"
    input_method: Optional[str] = "paste"
    data_content: Optional[str] = ""

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

class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"

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