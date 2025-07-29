import json
import uuid
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from datetime import datetime

from business_dna_analyzer import BusinessDNA, BusinessModel, BusinessMaturity
from dashboard_types import KPIWidget, ChartWidget, ChartType

logger = logging.getLogger(__name__)

class ComponentAdaptability(Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    INTELLIGENT = "intelligent"
    SELF_OPTIMIZING = "self_optimizing"

class BusinessContext(Enum):
    EXECUTIVE_OVERVIEW = "executive_overview"
    OPERATIONAL_DETAILS = "operational_details"
    ANALYTICAL_DEEP_DIVE = "analytical_deep_dive"
    STRATEGIC_PLANNING = "strategic_planning"
    PERFORMANCE_MONITORING = "performance_monitoring"

@dataclass
class IntelligentComponentConfig:
    component_id: str
    base_type: str
    adaptability_level: ComponentAdaptability
    business_contexts: List[BusinessContext]
    data_requirements: Dict[str, Any]
    adaptation_rules: Dict[str, Any]
    performance_metrics: Dict[str, float]
    version: str

class IntelligentComponent(ABC):
    """Base class for intelligent, adaptive dashboard components"""
    
    def __init__(self, config: IntelligentComponentConfig):
        self.config = config
        self.adaptation_history = []
        self.performance_scores = {}
        
    @abstractmethod
    async def adapt_to_context(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any], context: BusinessContext) -> Dict[str, Any]:
        """Adapt component configuration based on business context"""
        pass
    
    @abstractmethod
    async def optimize_for_data(self, data_characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize component for specific data characteristics"""
        pass
    
    @abstractmethod
    def get_performance_score(self) -> float:
        """Calculate component performance score"""
        pass

class IntelligentKPIComponent(IntelligentComponent):
    """Intelligent KPI component that adapts based on business model and context"""
    
    def __init__(self):
        config = IntelligentComponentConfig(
            component_id=f"intelligent_kpi_{uuid.uuid4().hex[:8]}",
            base_type="kpi_widget",
            adaptability_level=ComponentAdaptability.INTELLIGENT,
            business_contexts=[BusinessContext.EXECUTIVE_OVERVIEW, BusinessContext.PERFORMANCE_MONITORING],
            data_requirements={"numeric_columns": 1, "min_data_points": 10},
            adaptation_rules={
                "b2b_saas": {"focus": "mrr_metrics", "format": "currency", "trend_emphasis": "high"},
                "ecommerce": {"focus": "revenue_metrics", "format": "currency", "comparison": "enabled"},
                "manufacturing": {"focus": "efficiency_metrics", "format": "percentage", "targets": "enabled"}
            },
            performance_metrics={"relevance": 0.0, "accuracy": 0.0, "engagement": 0.0},
            version="1.0"
        )
        super().__init__(config)
    
    async def adapt_to_context(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any], context: BusinessContext) -> Dict[str, Any]:
        """Adapt KPI component based on business DNA and context"""
        
        numeric_columns = data_analysis.get('numeric_columns', [])
        if not numeric_columns:
            return self._create_fallback_kpi_config()
        
        # Business model specific adaptations
        if business_dna.business_model == BusinessModel.B2B_SAAS:
            return await self._adapt_for_saas(business_dna, data_analysis, context)
        elif business_dna.business_model == BusinessModel.B2C_ECOMMERCE:
            return await self._adapt_for_ecommerce(business_dna, data_analysis, context)
        elif business_dna.business_model == BusinessModel.MANUFACTURING:
            return await self._adapt_for_manufacturing(business_dna, data_analysis, context)
        else:
            return await self._adapt_for_general_business(business_dna, data_analysis, context)
    
    async def _adapt_for_saas(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any], context: BusinessContext) -> Dict[str, Any]:
        """SaaS-specific KPI adaptations"""
        numeric_cols = data_analysis.get('numeric_columns', [])
        
        # Find SaaS-specific metrics
        mrr_col = self._find_best_column(numeric_cols, ['mrr', 'recurring_revenue', 'subscription_revenue'])
        churn_col = self._find_best_column(numeric_cols, ['churn', 'churn_rate', 'cancellation'])
        ltv_col = self._find_best_column(numeric_cols, ['ltv', 'lifetime_value', 'customer_value'])
        user_col = self._find_best_column(numeric_cols, ['users', 'active_users', 'subscribers'])
        
        kpis = []
        
        if mrr_col:
            kpis.append({
                "title": "Monthly Recurring Revenue",
                "column": mrr_col,
                "format": "currency",
                "icon": "DollarSign",
                "color": "#059669",
                "priority": 1,
                "context_specific": True
            })
        
        if user_col:
            kpis.append({
                "title": "Active Users",
                "column": user_col,
                "format": "number",
                "icon": "Users",
                "color": "#3b82f6",
                "priority": 2,
                "growth_focus": True
            })
        
        if churn_col:
            kpis.append({
                "title": "Churn Rate",
                "column": churn_col,
                "format": "percentage",
                "icon": "TrendingDown",
                "color": "#dc2626",
                "priority": 3,
                "inverse_good": True  # Lower is better
            })
        
        if ltv_col:
            kpis.append({
                "title": "Customer LTV",
                "column": ltv_col,
                "format": "currency",
                "icon": "Target",
                "color": "#7c3aed",
                "priority": 4
            })
        
        return {
            "kpis": kpis,
            "business_model": "saas",
            "context": context.value,
            "adaptation_confidence": 0.9
        }
    
    async def _adapt_for_ecommerce(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any], context: BusinessContext) -> Dict[str, Any]:
        """E-commerce specific KPI adaptations"""
        numeric_cols = data_analysis.get('numeric_columns', [])
        
        revenue_col = self._find_best_column(numeric_cols, ['revenue', 'sales', 'total_sales', 'amount'])
        orders_col = self._find_best_column(numeric_cols, ['orders', 'order_count', 'transactions'])
        customers_col = self._find_best_column(numeric_cols, ['customers', 'buyers', 'users'])
        conversion_col = self._find_best_column(numeric_cols, ['conversion', 'conversion_rate', 'cr'])
        
        kpis = []
        
        if revenue_col:
            kpis.append({
                "title": "Total Revenue",
                "column": revenue_col,
                "format": "currency",
                "icon": "DollarSign",
                "color": "#059669",
                "priority": 1,
                "comparison": "period_over_period"
            })
        
        if orders_col:
            kpis.append({
                "title": "Total Orders",
                "column": orders_col,
                "format": "number",
                "icon": "ShoppingCart",
                "color": "#f59e0b",
                "priority": 2,
                "trend_analysis": True
            })
        
        if customers_col:
            kpis.append({
                "title": "Active Customers",
                "column": customers_col,
                "format": "number",
                "icon": "Users",
                "color": "#3b82f6",
                "priority": 3
            })
        
        if conversion_col:
            kpis.append({
                "title": "Conversion Rate",
                "column": conversion_col,
                "format": "percentage",
                "icon": "Target",
                "color": "#7c3aed",
                "priority": 4,
                "optimization_focus": True
            })
        
        # Calculate AOV if we have both revenue and orders
        if revenue_col and orders_col:
            kpis.append({
                "title": "Average Order Value",
                "calculation": f"{revenue_col}/{orders_col}",
                "format": "currency",
                "icon": "Calculator",
                "color": "#06b6d4",
                "priority": 5,
                "calculated_metric": True
            })
        
        return {
            "kpis": kpis,
            "business_model": "ecommerce",
            "context": context.value,
            "adaptation_confidence": 0.85
        }
    
    async def _adapt_for_manufacturing(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any], context: BusinessContext) -> Dict[str, Any]:
        """Manufacturing specific KPI adaptations"""
        numeric_cols = data_analysis.get('numeric_columns', [])
        
        production_col = self._find_best_column(numeric_cols, ['production', 'units_produced', 'output'])
        efficiency_col = self._find_best_column(numeric_cols, ['efficiency', 'oee', 'utilization'])
        quality_col = self._find_best_column(numeric_cols, ['quality', 'defect_rate', 'yield'])
        downtime_col = self._find_best_column(numeric_cols, ['downtime', 'maintenance', 'stops'])
        
        kpis = []
        
        if production_col:
            kpis.append({
                "title": "Production Output",
                "column": production_col,
                "format": "number",
                "icon": "Package",
                "color": "#059669",
                "priority": 1,
                "target_comparison": True
            })
        
        if efficiency_col:
            kpis.append({
                "title": "Overall Equipment Effectiveness",
                "column": efficiency_col,
                "format": "percentage",
                "icon": "Activity",
                "color": "#3b82f6",
                "priority": 2,
                "benchmark": 85  # Industry standard OEE
            })
        
        if quality_col:
            kpis.append({
                "title": "Quality Score",
                "column": quality_col,
                "format": "percentage",
                "icon": "CheckCircle",
                "color": "#16a34a",
                "priority": 3,
                "quality_focus": True
            })
        
        if downtime_col:
            kpis.append({
                "title": "Downtime",
                "column": downtime_col,
                "format": "hours",
                "icon": "AlertTriangle",
                "color": "#dc2626",
                "priority": 4,
                "inverse_good": True,
                "alert_threshold": 8  # 8 hours downtime alert
            })
        
        return {
            "kpis": kpis,
            "business_model": "manufacturing",
            "context": context.value,
            "adaptation_confidence": 0.8
        }
    
    async def _adapt_for_general_business(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any], context: BusinessContext) -> Dict[str, Any]:
        """General business KPI adaptations"""
        numeric_cols = data_analysis.get('numeric_columns', [])
        success_metrics = business_dna.success_metrics[:4]  # Top 4 success metrics
        
        kpis = []
        
        for i, metric in enumerate(success_metrics):
            if metric in numeric_cols:
                kpis.append({
                    "title": self._humanize_column_name(metric),
                    "column": metric,
                    "format": self._detect_format(metric),
                    "icon": self._select_icon(metric),
                    "color": self._select_color(i),
                    "priority": i + 1,
                    "adaptive": True
                })
        
        # Fill remaining slots with top numeric columns
        remaining_slots = 4 - len(kpis)
        remaining_cols = [col for col in numeric_cols if col not in success_metrics][:remaining_slots]
        
        for i, col in enumerate(remaining_cols):
            kpis.append({
                "title": self._humanize_column_name(col),
                "column": col,
                "format": self._detect_format(col),
                "icon": "BarChart3",
                "color": self._select_color(len(kpis)),
                "priority": len(kpis) + 1,
                "general_metric": True
            })
        
        return {
            "kpis": kpis,
            "business_model": "general",
            "context": context.value,
            "adaptation_confidence": 0.7
        }
    
    async def optimize_for_data(self, data_characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize KPI component for specific data characteristics"""
        optimizations = {}
        
        # Data volume optimizations
        total_records = data_characteristics.get('total_records', 0)
        if total_records > 100000:
            optimizations['sampling'] = True
            optimizations['cache_strategy'] = 'aggressive'
        elif total_records > 10000:
            optimizations['cache_strategy'] = 'moderate'
        
        # Data quality optimizations
        data_quality = data_characteristics.get('data_quality_score', 1.0)
        if data_quality < 0.8:
            optimizations['data_validation'] = True
            optimizations['null_handling'] = 'intelligent'
        
        # Real-time requirements
        if data_characteristics.get('has_time_series'):
            optimizations['refresh_rate'] = 'high'
            optimizations['trend_calculation'] = 'enabled'
        
        return optimizations
    
    def get_performance_score(self) -> float:
        """Calculate KPI component performance score"""
        scores = self.performance_metrics
        
        # Weight different aspects
        relevance_weight = 0.4
        accuracy_weight = 0.35
        engagement_weight = 0.25
        
        total_score = (
            scores.get('relevance', 0) * relevance_weight +
            scores.get('accuracy', 0) * accuracy_weight +
            scores.get('engagement', 0) * engagement_weight
        )
        
        return min(1.0, total_score)
    
    # Helper methods
    def _find_best_column(self, columns: List[str], patterns: List[str]) -> Optional[str]:
        """Find the best matching column for given patterns"""
        for pattern in patterns:
            for column in columns:
                if pattern.lower() in column.lower():
                    return column
        return None
    
    def _humanize_column_name(self, column_name: str) -> str:
        """Convert column name to human-readable title"""
        # Replace underscores and hyphens with spaces
        title = column_name.replace('_', ' ').replace('-', ' ')
        
        # Handle camelCase
        import re
        title = re.sub(r'([a-z])([A-Z])', r'\1 \2', title)
        
        # Capitalize words
        title = ' '.join(word.capitalize() for word in title.split())
        
        # Common business term replacements
        replacements = {
            'Mrr': 'Monthly Recurring Revenue',
            'Ltv': 'Lifetime Value',
            'Cac': 'Customer Acquisition Cost',
            'Aov': 'Average Order Value',
            'Oee': 'Overall Equipment Effectiveness'
        }
        
        for abbrev, full_form in replacements.items():
            title = title.replace(abbrev, full_form)
        
        return title
    
    def _detect_format(self, column_name: str) -> str:
        """Detect appropriate format for column"""
        column_lower = column_name.lower()
        
        if any(term in column_lower for term in ['revenue', 'sales', 'amount', 'price', 'cost', 'value']):
            return 'currency'
        elif any(term in column_lower for term in ['rate', 'percentage', 'percent', '%']):
            return 'percentage'
        elif any(term in column_lower for term in ['time', 'duration', 'hours', 'minutes']):
            return 'time'
        else:
            return 'number'
    
    def _select_icon(self, column_name: str) -> str:
        """Select appropriate icon for column"""
        column_lower = column_name.lower()
        
        icon_mapping = {
            'revenue': 'DollarSign',
            'sales': 'TrendingUp',
            'users': 'Users',
            'customers': 'Users',
            'orders': 'ShoppingCart',
            'production': 'Package',
            'efficiency': 'Activity',
            'quality': 'CheckCircle',
            'performance': 'BarChart3',
            'growth': 'TrendingUp',
            'conversion': 'Target'
        }
        
        for keyword, icon in icon_mapping.items():
            if keyword in column_lower:
                return icon
        
        return 'BarChart3'  # Default icon
    
    def _select_color(self, index: int) -> str:
        """Select color based on index"""
        colors = ['#059669', '#3b82f6', '#7c3aed', '#f59e0b', '#dc2626', '#06b6d4']
        return colors[index % len(colors)]
    
    def _create_fallback_kpi_config(self) -> Dict[str, Any]:
        """Create fallback KPI configuration"""
        return {
            "kpis": [{
                "title": "Business Metric",
                "column": "value",
                "format": "number",
                "icon": "BarChart3",
                "color": "#3b82f6",
                "priority": 1,
                "fallback": True
            }],
            "business_model": "general",
            "context": "fallback",
            "adaptation_confidence": 0.5
        }

class IntelligentChartComponent(IntelligentComponent):
    """Intelligent chart component that adapts visualization based on data and context"""
    
    def __init__(self):
        config = IntelligentComponentConfig(
            component_id=f"intelligent_chart_{uuid.uuid4().hex[:8]}",
            base_type="chart_widget",
            adaptability_level=ComponentAdaptability.INTELLIGENT,
            business_contexts=[BusinessContext.ANALYTICAL_DEEP_DIVE, BusinessContext.PERFORMANCE_MONITORING],
            data_requirements={"min_data_points": 5, "columns": 2},
            adaptation_rules={
                "time_series": {"preferred_charts": ["LineChartOne"], "features": ["trend_analysis"]},
                "categorical": {"preferred_charts": ["BarChartOne"], "features": ["comparison"]},
                "correlation": {"preferred_charts": ["LineChartOne"], "features": ["relationship_analysis"]}
            },
            performance_metrics={"clarity": 0.0, "insight_value": 0.0, "user_engagement": 0.0},
            version="1.0"
        )
        super().__init__(config)
    
    async def adapt_to_context(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any], context: BusinessContext) -> Dict[str, Any]:
        """Adapt chart component based on business context and data characteristics"""
        
        charts = []
        numeric_cols = data_analysis.get('numeric_columns', [])
        categorical_cols = data_analysis.get('categorical_columns', [])
        date_cols = data_analysis.get('date_columns', [])
        
        if context == BusinessContext.EXECUTIVE_OVERVIEW:
            charts = await self._create_executive_charts(business_dna, data_analysis)
        elif context == BusinessContext.OPERATIONAL_DETAILS:
            charts = await self._create_operational_charts(business_dna, data_analysis)
        elif context == BusinessContext.ANALYTICAL_DEEP_DIVE:
            charts = await self._create_analytical_charts(business_dna, data_analysis)
        else:
            charts = await self._create_general_charts(business_dna, data_analysis)
        
        return {
            "charts": charts,
            "context": context.value,
            "data_characteristics": {
                "numeric_columns": len(numeric_cols),
                "categorical_columns": len(categorical_cols),
                "has_time_series": len(date_cols) > 0
            },
            "adaptation_confidence": 0.8
        }
    
    async def _create_executive_charts(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create executive-level charts focused on high-level trends and KPIs"""
        charts = []
        numeric_cols = data_analysis.get('numeric_columns', [])
        date_cols = data_analysis.get('date_columns', [])
        
        # Revenue/Performance trend chart
        if date_cols and numeric_cols:
            primary_metric = self._find_primary_metric(numeric_cols, business_dna)
            charts.append({
                "title": f"{self._humanize_column_name(primary_metric)} Trends",
                "subtitle": "Performance over time",
                "chart_type": "LineChartOne",
                "data_mapping": {
                    "x_axis": date_cols[0],
                    "y_axis": primary_metric
                },
                "config": {
                    "trend_line": True,
                    "executive_style": True,
                    "clean_layout": True
                },
                "business_purpose": "Track primary business performance trends",
                "priority": 1
            })
        
        # Key metrics comparison
        if len(numeric_cols) >= 2:
            top_metrics = numeric_cols[:4]  # Top 4 metrics
            charts.append({
                "title": "Key Performance Indicators",
                "subtitle": "Comparative business metrics",
                "chart_type": "BarChartOne",
                "data_mapping": {
                    "categories": "metrics",
                    "values": "performance"
                },
                "config": {
                    "comparison_mode": True,
                    "executive_colors": True,
                    "simplified_labels": True
                },
                "business_purpose": "Compare key business metrics at a glance",
                "priority": 2
            })
        
        return charts
    
    async def _create_operational_charts(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create operational charts focused on process details and workflows"""
        charts = []
        numeric_cols = data_analysis.get('numeric_columns', [])
        categorical_cols = data_analysis.get('categorical_columns', [])
        
        # Process efficiency charts
        if categorical_cols and numeric_cols:
            process_col = categorical_cols[0]  # Assume first categorical is process-related
            efficiency_col = self._find_best_metric(numeric_cols, ['efficiency', 'performance', 'utilization'])
            
            charts.append({
                "title": "Process Performance Analysis",
                "subtitle": "Efficiency by process stage",
                "chart_type": "BarChartOne",
                "data_mapping": {
                    "x_axis": process_col,
                    "y_axis": efficiency_col or numeric_cols[0]
                },
                "config": {
                    "detailed_labels": True,
                    "threshold_lines": True,
                    "operational_colors": True
                },
                "business_purpose": "Monitor operational process performance",
                "priority": 1
            })
        
        # Detailed data table for operational drill-down
        charts.append({
            "title": "Operational Data Details",
            "subtitle": "Comprehensive operational metrics",
            "chart_type": "DataTable",
            "data_mapping": {
                "columns": numeric_cols[:6] + categorical_cols[:3]  # Mix of numeric and categorical
            },
            "config": {
                "pagination": True,
                "sorting": True,
                "filtering": True,
                "export": True
            },
            "business_purpose": "Detailed operational data analysis",
            "priority": 2
        })
        
        return charts
    
    async def _create_analytical_charts(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create analytical charts for deep-dive analysis"""
        charts = []
        numeric_cols = data_analysis.get('numeric_columns', [])
        categorical_cols = data_analysis.get('categorical_columns', [])
        
        # Correlation analysis
        if len(numeric_cols) >= 2:
            charts.append({
                "title": "Performance Correlation Analysis",
                "subtitle": "Relationship between key metrics",
                "chart_type": "LineChartOne",  # Using line chart for correlation visualization
                "data_mapping": {
                    "x_axis": numeric_cols[0],
                    "y_axis": numeric_cols[1]
                },
                "config": {
                    "correlation_mode": True,
                    "regression_line": True,
                    "advanced_tooltips": True
                },
                "business_purpose": "Identify relationships between business metrics",
                "priority": 1
            })
        
        # Distribution analysis
        if categorical_cols and numeric_cols:
            charts.append({
                "title": "Performance Distribution",
                "subtitle": "Metric distribution across categories",
                "chart_type": "BarChartOne",
                "data_mapping": {
                    "x_axis": categorical_cols[0],
                    "y_axis": numeric_cols[0]
                },
                "config": {
                    "distribution_mode": True,
                    "statistical_overlay": True,
                    "analytical_colors": True
                },
                "business_purpose": "Analyze performance distribution patterns",
                "priority": 2
            })
        
        # Advanced time series analysis if available
        date_cols = data_analysis.get('date_columns', [])
        if date_cols and len(numeric_cols) >= 2:
            charts.append({
                "title": "Multi-Metric Trend Analysis",
                "subtitle": "Advanced time series analysis",
                "chart_type": "LineChartOne",
                "data_mapping": {
                    "x_axis": date_cols[0],
                    "y_axes": numeric_cols[:3]  # Multiple metrics
                },
                "config": {
                    "multi_series": True,
                    "trend_analysis": True,
                    "forecasting": True,
                    "seasonal_detection": True
                },
                "business_purpose": "Advanced trend and pattern analysis",
                "priority": 3
            })
        
        return charts
    
    async def _create_general_charts(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create general purpose charts"""
        charts = []
        numeric_cols = data_analysis.get('numeric_columns', [])
        categorical_cols = data_analysis.get('categorical_columns', [])
        
        # Basic bar chart for categorical vs numeric
        if categorical_cols and numeric_cols:
            charts.append({
                "title": "Performance Overview",
                "subtitle": "Key metrics by category",
                "chart_type": "BarChartOne",
                "data_mapping": {
                    "x_axis": categorical_cols[0],
                    "y_axis": numeric_cols[0]
                },
                "config": {
                    "standard_layout": True,
                    "responsive": True
                },
                "business_purpose": "General performance visualization",
                "priority": 1
            })
        
        # Line chart for trends if time data available
        date_cols = data_analysis.get('date_columns', [])
        if date_cols and numeric_cols:
            charts.append({
                "title": "Trend Analysis",
                "subtitle": "Performance trends over time",
                "chart_type": "LineChartOne",
                "data_mapping": {
                    "x_axis": date_cols[0],
                    "y_axis": numeric_cols[0]
                },
                "config": {
                    "trend_indicators": True,
                    "responsive": True
                },
                "business_purpose": "Track performance trends",
                "priority": 2
            })
        
        return charts
    
    async def optimize_for_data(self, data_characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize chart component for data characteristics"""
        optimizations = {}
        
        # Performance optimizations based on data size
        total_records = data_characteristics.get('total_records', 0)
        if total_records > 10000:
            optimizations['data_sampling'] = True
            optimizations['lazy_loading'] = True
            optimizations['virtualization'] = True
        
        # Chart type optimizations based on data shape
        column_count = len(data_characteristics.get('columns', []))
        if column_count > 20:
            optimizations['column_selection'] = 'intelligent'
            optimizations['progressive_disclosure'] = True
        
        # Interactivity optimizations
        if data_characteristics.get('has_time_series'):
            optimizations['zoom_enabled'] = True
            optimizations['brush_selection'] = True
        
        return optimizations
    
    def get_performance_score(self) -> float:
        """Calculate chart component performance score"""
        scores = self.performance_metrics
        
        clarity_weight = 0.4
        insight_weight = 0.4
        engagement_weight = 0.2
        
        total_score = (
            scores.get('clarity', 0) * clarity_weight +
            scores.get('insight_value', 0) * insight_weight +
            scores.get('user_engagement', 0) * engagement_weight
        )
        
        return min(1.0, total_score)
    
    # Helper methods
    def _find_primary_metric(self, numeric_cols: List[str], business_dna: BusinessDNA) -> str:
        """Find the primary metric for the business"""
        success_metrics = business_dna.success_metrics
        
        for metric in success_metrics:
            if metric in numeric_cols:
                return metric
        
        # Fallback to first numeric column
        return numeric_cols[0] if numeric_cols else "value"
    
    def _find_best_metric(self, numeric_cols: List[str], patterns: List[str]) -> Optional[str]:
        """Find best matching metric for given patterns"""
        for pattern in patterns:
            for col in numeric_cols:
                if pattern.lower() in col.lower():
                    return col
        return None
    
    def _humanize_column_name(self, column_name: str) -> str:
        """Convert column name to human-readable format"""
        # Same implementation as in KPI component
        title = column_name.replace('_', ' ').replace('-', ' ')
        import re
        title = re.sub(r'([a-z])([A-Z])', r'\1 \2', title)
        return ' '.join(word.capitalize() for word in title.split())

class IntelligentComponentFactory:
    """Factory for creating intelligent components based on requirements"""
    
    def __init__(self):
        self.component_registry = {
            'kpi_widget': IntelligentKPIComponent,
            'chart_widget': IntelligentChartComponent,
            # Add more component types as needed
        }
    
    async def create_component(self, component_type: str, business_dna: BusinessDNA, data_analysis: Dict[str, Any], context: BusinessContext) -> IntelligentComponent:
        """Create and configure an intelligent component"""
        
        if component_type not in self.component_registry:
            raise ValueError(f"Unknown component type: {component_type}")
        
        component_class = self.component_registry[component_type]
        component = component_class()
        
        # Adapt component to context
        await component.adapt_to_context(business_dna, data_analysis, context)
        
        # Optimize for data characteristics
        await component.optimize_for_data({
            'total_records': data_analysis.get('total_records', 0),
            'columns': data_analysis.get('columns', []),
            'data_quality_score': data_analysis.get('data_quality_score', 1.0),
            'has_time_series': len(data_analysis.get('date_columns', [])) > 0
        })
        
        return component
    
    def register_component(self, component_type: str, component_class: type):
        """Register a new component type"""
        self.component_registry[component_type] = component_class
    
    def get_available_components(self) -> List[str]:
        """Get list of available component types"""
        return list(self.component_registry.keys())

class ComponentPerformanceAnalyzer:
    """Analyzes and optimizes component performance"""
    
    def __init__(self):
        self.performance_history = {}
        self.optimization_rules = {}
    
    async def analyze_component_performance(self, component: IntelligentComponent, usage_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze component performance metrics"""
        
        # Calculate relevance score
        relevance_score = self._calculate_relevance_score(component, usage_data)
        
        # Calculate accuracy score
        accuracy_score = self._calculate_accuracy_score(component, usage_data)
        
        # Calculate engagement score
        engagement_score = self._calculate_engagement_score(component, usage_data)
        
        performance_metrics = {
            'relevance': relevance_score,
            'accuracy': accuracy_score,
            'engagement': engagement_score,
            'overall': (relevance_score + accuracy_score + engagement_score) / 3
        }
        
        # Update component performance metrics
        component.performance_metrics.update(performance_metrics)
        
        return performance_metrics
    
    def _calculate_relevance_score(self, component: IntelligentComponent, usage_data: Dict[str, Any]) -> float:
        """Calculate how relevant the component is to the business context"""
        # Implement relevance scoring logic
        return 0.8  # Placeholder
    
    def _calculate_accuracy_score(self, component: IntelligentComponent, usage_data: Dict[str, Any]) -> float:
        """Calculate accuracy of component data and calculations"""
        # Implement accuracy scoring logic
        return 0.85  # Placeholder
    
    def _calculate_engagement_score(self, component: IntelligentComponent, usage_data: Dict[str, Any]) -> float:
        """Calculate user engagement with the component"""
        # Implement engagement scoring logic
        return 0.75  # Placeholder
    
    async def suggest_optimizations(self, component: IntelligentComponent) -> List[str]:
        """Suggest optimizations for component performance"""
        suggestions = []
        
        performance_score = component.get_performance_score()
        
        if performance_score < 0.7:
            suggestions.append("Consider adapting component configuration for better business relevance")
        
        if component.performance_metrics.get('engagement', 0) < 0.6:
            suggestions.append("Enhance visual design or interactivity to improve user engagement")
        
        if component.performance_metrics.get('accuracy', 0) < 0.8:
            suggestions.append("Review data quality and calculation accuracy")
        
        return suggestions 