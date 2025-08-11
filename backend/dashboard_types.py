from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import uuid
from dataclasses import dataclass, field

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
    BAK = "bak"

class UploadStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING = "pending"
    ANALYZING = "analyzing"

class AIModelVersion(str, Enum):
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo-preview"

class DashboardLayout(str, Enum):
    GRID = "grid"
    FLEXIBLE = "flexible"
    DASHBOARD = "dashboard"
    
class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    RADAR = "radar"
    DONUT = "donut"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    GAUGE = "gauge"
    FUNNEL = "funnel"

# Basic Widget Classes
@dataclass
class KPIWidget:
    title: str
    value: str
    change: Optional[str] = None
    trend: Optional[str] = None  # 'up', 'down', 'neutral'
    color: Optional[str] = None
    format_type: Optional[str] = "number"  # number, currency, percentage
    description: Optional[str] = None

@dataclass  
class ChartWidget:
    title: str
    type: ChartType
    data_keys: List[str]
    config: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None

# Basic Configuration Classes
@dataclass
class DashboardConfig:
    title: str
    description: str
    layout: DashboardLayout
    kpis: List[KPIWidget]
    charts: List[ChartWidget]
    color_scheme: Optional[Dict[str, str]] = None
    custom_css: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict) 