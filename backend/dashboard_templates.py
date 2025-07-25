from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from models import ChartType

class DashboardTemplateType(Enum):
    INVENTORY = "inventory"
    SALES = "sales"
    FINANCIAL = "financial"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    GENERAL = "general"

class ComponentType(Enum):
    KPI_CARD = "kpi_card"
    DATA_TABLE = "data_table"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    AREA_CHART = "area_chart"
    RADAR_CHART = "radar_chart"
    ALERT_SUMMARY = "alert_summary"
    DATE_RANGE_PICKER = "date_range_picker"
    TREND_INDICATOR = "trend_indicator"

@dataclass
class ComponentConfig:
    component_type: ComponentType
    title: str
    subtitle: Optional[str] = None
    data_source: str = "client_data"
    chart_type: Optional[str] = None
    position: Dict[str, int] = None
    size: Dict[str, int] = None
    config: Dict[str, Any] = None
    priority: int = 1
    required_columns: List[str] = None

@dataclass
class DashboardTemplate:
    template_type: DashboardTemplateType
    title: str
    description: str
    components: List[ComponentConfig]
    required_data_types: List[str]
    recommended_columns: List[str]
    layout_config: Dict[str, Any]
    color_scheme: Dict[str, str]

class DashboardTemplateManager:
    """Manages dashboard templates and their configurations"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[DashboardTemplateType, DashboardTemplate]:
        """Initialize all dashboard templates"""
        return {
            DashboardTemplateType.INVENTORY: self._create_inventory_template(),
            DashboardTemplateType.SALES: self._create_sales_template(),
            DashboardTemplateType.FINANCIAL: self._create_financial_template(),
            DashboardTemplateType.MARKETING: self._create_marketing_template(),
            DashboardTemplateType.OPERATIONS: self._create_operations_template(),
            DashboardTemplateType.ECOMMERCE: self._create_ecommerce_template(),
            DashboardTemplateType.SAAS: self._create_saas_template(),
            DashboardTemplateType.GENERAL: self._create_general_template()
        }
    
    def _create_inventory_template(self) -> DashboardTemplate:
        """Create inventory management dashboard template"""
        components = [
            # KPI Cards Row
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Total SKUs",
                data_source="inventory_count",
                position={"row": 0, "col": 0},
                size={"width": 1, "height": 1},
                required_columns=["sku", "product_name"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Low Stock Items",
                data_source="low_stock_count",
                position={"row": 0, "col": 1},
                size={"width": 1, "height": 1},
                required_columns=["stock_level", "reorder_point"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Total Inventory Value",
                data_source="inventory_value",
                position={"row": 0, "col": 2},
                size={"width": 1, "height": 1},
                required_columns=["unit_price", "quantity"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Turnover Rate",
                data_source="turnover_rate",
                position={"row": 0, "col": 3},
                size={"width": 1, "height": 1},
                required_columns=["units_sold", "average_inventory"]
            ),
            
            # SKU Data Table
            ComponentConfig(
                component_type=ComponentType.DATA_TABLE,
                title="SKU Inventory Overview",
                subtitle="Complete inventory status by SKU",
                position={"row": 1, "col": 0},
                size={"width": 4, "height": 2},
                required_columns=["sku", "product_name", "stock_level", "reorder_point", "unit_price"],
                config={
                    "columns": [
                        {"key": "sku", "title": "SKU Code", "sortable": True},
                        {"key": "product_name", "title": "Product Name", "sortable": True},
                        {"key": "stock_level", "title": "On Hand", "sortable": True, "type": "number"},
                        {"key": "incoming_inventory", "title": "Incoming", "sortable": True, "type": "number"},
                        {"key": "outgoing_inventory", "title": "Outgoing", "sortable": True, "type": "number"},
                        {"key": "availability", "title": "Available", "sortable": True, "type": "number"},
                        {"key": "reorder_point", "title": "Reorder Point", "sortable": True, "type": "number"}
                    ],
                    "pagination": True,
                    "search": True,
                    "export": True
                }
            ),
            
            # Inventory Level Trends
            ComponentConfig(
                component_type=ComponentType.LINE_CHART,
                title="Inventory Levels Trend",
                subtitle="7/30/90-day inventory tracking",
                chart_type="ShadcnAreaInteractive",
                position={"row": 3, "col": 0},
                size={"width": 2, "height": 2},
                required_columns=["date", "stock_level"],
                config={
                    "date_range_selector": True,
                    "show_legend": True,
                    "interactive": True
                }
            ),
            
            # Sales vs Inventory
            ComponentConfig(
                component_type=ComponentType.BAR_CHART,
                title="Sales Performance",
                subtitle="Current vs historical average",
                chart_type="ShadcnBarMultiple",
                position={"row": 3, "col": 2},
                size={"width": 2, "height": 2},
                required_columns=["product_name", "units_sold", "historical_average"],
                config={
                    "comparison_mode": True,
                    "show_values": True
                }
            ),
            
            # Alert Summary
            ComponentConfig(
                component_type=ComponentType.ALERT_SUMMARY,
                title="Inventory Alerts",
                subtitle="Active alerts and notifications",
                position={"row": 1, "col": 4},
                size={"width": 2, "height": 1},
                config={
                    "alert_types": ["low_stock", "overstock", "sales_spike", "sales_slowdown"],
                    "show_counts": True,
                    "quick_actions": True
                }
            )
        ]
        
        return DashboardTemplate(
            template_type=DashboardTemplateType.INVENTORY,
            title="Inventory Management Dashboard",
            description="Comprehensive inventory tracking, stock levels, and turnover analytics",
            components=components,
            required_data_types=["inventory", "sales", "procurement"],
            recommended_columns=["sku", "product_name", "stock_level", "unit_price", "reorder_point", "units_sold"],
            layout_config={
                "grid_cols": 4,
                "grid_rows": 5,
                "gap": 4,
                "responsive": True
            },
            color_scheme={
                "primary": "#2563eb",
                "secondary": "#f97316", 
                "success": "#16a34a",
                "warning": "#eab308",
                "danger": "#dc2626"
            }
        )
    
    def _create_sales_template(self) -> DashboardTemplate:
        """Create sales performance dashboard template"""
        components = [
            # Sales KPIs
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Total Revenue",
                position={"row": 0, "col": 0},
                size={"width": 1, "height": 1},
                required_columns=["revenue", "sales_amount", "total"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Orders Count",
                position={"row": 0, "col": 1}, 
                size={"width": 1, "height": 1},
                required_columns=["order_count", "transactions", "orders"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Average Order Value",
                position={"row": 0, "col": 2},
                size={"width": 1, "height": 1},
                required_columns=["order_value", "average_sale"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Conversion Rate",
                position={"row": 0, "col": 3},
                size={"width": 1, "height": 1},
                required_columns=["conversions", "visitors", "conversion_rate"]
            ),
            
            # Sales Trends
            ComponentConfig(
                component_type=ComponentType.LINE_CHART,
                title="Revenue Trends",
                subtitle="Sales performance over time",
                chart_type="ShadcnAreaStacked",
                position={"row": 1, "col": 0},
                size={"width": 3, "height": 2},
                required_columns=["date", "revenue"]
            ),
            
            # Top Products
            ComponentConfig(
                component_type=ComponentType.BAR_CHART,
                title="Top Selling Products",
                chart_type="ShadcnBarHorizontal",
                position={"row": 1, "col": 3},
                size={"width": 1, "height": 2},
                required_columns=["product_name", "units_sold"]
            ),
            
            # Sales by Category
            ComponentConfig(
                component_type=ComponentType.PIE_CHART,
                title="Sales by Category",
                chart_type="ShadcnPieInteractive",
                position={"row": 3, "col": 0},
                size={"width": 2, "height": 2},
                required_columns=["category", "sales_amount"]
            ),
            
            # Customer Regions
            ComponentConfig(
                component_type=ComponentType.BAR_CHART,
                title="Sales by Region",
                chart_type="ShadcnBarMultiple",
                position={"row": 3, "col": 2},
                size={"width": 2, "height": 2},
                required_columns=["region", "sales_amount", "order_count"]
            )
        ]
        
        return DashboardTemplate(
            template_type=DashboardTemplateType.SALES,
            title="Sales Performance Dashboard",  
            description="Comprehensive sales analytics, revenue tracking, and performance metrics",
            components=components,
            required_data_types=["sales", "products", "customers"],
            recommended_columns=["date", "revenue", "product_name", "category", "region", "order_count"],
            layout_config={
                "grid_cols": 4,
                "grid_rows": 5,
                "gap": 4,
                "responsive": True
            },
            color_scheme={
                "primary": "#16a34a",
                "secondary": "#2563eb",
                "success": "#16a34a", 
                "warning": "#eab308",
                "danger": "#dc2626"
            }
        )
    
    def _create_financial_template(self) -> DashboardTemplate:
        """Create financial dashboard template"""
        components = [
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Total Revenue",
                position={"row": 0, "col": 0},
                size={"width": 1, "height": 1},
                required_columns=["revenue", "income"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Total Expenses", 
                position={"row": 0, "col": 1},
                size={"width": 1, "height": 1},
                required_columns=["expenses", "costs"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Net Profit",
                position={"row": 0, "col": 2},
                size={"width": 1, "height": 1},
                required_columns=["profit", "net_income"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Profit Margin",
                position={"row": 0, "col": 3},
                size={"width": 1, "height": 1},
                required_columns=["profit_margin", "margin"]
            ),
            
            # Financial Trends
            ComponentConfig(
                component_type=ComponentType.LINE_CHART,
                title="Revenue vs Expenses",
                chart_type="ShadcnAreaLinear",
                position={"row": 1, "col": 0},
                size={"width": 4, "height": 2},
                required_columns=["date", "revenue", "expenses"]
            ),
            
            # Expense Breakdown
            ComponentConfig(
                component_type=ComponentType.PIE_CHART,
                title="Expense Categories",
                chart_type="ShadcnPieDonutText",
                position={"row": 3, "col": 0},
                size={"width": 2, "height": 2},
                required_columns=["expense_category", "amount"]
            ),
            
            # Cash Flow
            ComponentConfig(
                component_type=ComponentType.BAR_CHART,
                title="Monthly Cash Flow",
                chart_type="ShadcnBarNegative",
                position={"row": 3, "col": 2},
                size={"width": 2, "height": 2},
                required_columns=["month", "cash_flow"]
            )
        ]
        
        return DashboardTemplate(
            template_type=DashboardTemplateType.FINANCIAL,
            title="Financial Analytics Dashboard",
            description="Financial performance, cash flow, and profitability analysis", 
            components=components,
            required_data_types=["financial", "accounting", "revenue"],
            recommended_columns=["date", "revenue", "expenses", "profit", "cash_flow", "expense_category"],
            layout_config={
                "grid_cols": 4,
                "grid_rows": 5,
                "gap": 4,
                "responsive": True
            },
            color_scheme={
                "primary": "#059669",
                "secondary": "#dc2626",
                "success": "#16a34a",
                "warning": "#eab308", 
                "danger": "#dc2626"
            }
        )
    
    def _create_ecommerce_template(self) -> DashboardTemplate:
        """Create ecommerce dashboard template"""
        components = [
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Total Sales",
                position={"row": 0, "col": 0},
                size={"width": 1, "height": 1},
                required_columns=["sales", "revenue", "total_sales"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Orders",
                position={"row": 0, "col": 1},
                size={"width": 1, "height": 1},
                required_columns=["orders", "order_count"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Customers",
                position={"row": 0, "col": 2},
                size={"width": 1, "height": 1},
                required_columns=["customers", "users", "buyers"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Conversion Rate",
                position={"row": 0, "col": 3},
                size={"width": 1, "height": 1},
                required_columns=["conversion_rate", "conversions"]
            ),
            
            # Sales Trends
            ComponentConfig(
                component_type=ComponentType.AREA_CHART,
                title="Daily Sales Trends",
                chart_type="ShadcnAreaInteractive",
                position={"row": 1, "col": 0},
                size={"width": 3, "height": 2},
                required_columns=["date", "sales_amount"]
            ),
            
            # Top Products Table
            ComponentConfig(
                component_type=ComponentType.DATA_TABLE,
                title="Top Products",
                position={"row": 1, "col": 3},
                size={"width": 1, "height": 2},
                required_columns=["product_name", "units_sold", "revenue"],
                config={
                    "columns": [
                        {"key": "product_name", "title": "Product"},
                        {"key": "units_sold", "title": "Units Sold", "type": "number"},
                        {"key": "revenue", "title": "Revenue", "type": "currency"}
                    ],
                    "pagination": True,
                    "compact": True
                }
            )
        ]
        
        return DashboardTemplate(
            template_type=DashboardTemplateType.ECOMMERCE,
            title="E-commerce Dashboard",
            description="Complete ecommerce analytics including sales, products, and customers",
            components=components,
            required_data_types=["ecommerce", "sales", "products"],
            recommended_columns=["date", "sales", "orders", "customers", "product_name", "category"],
            layout_config={
                "grid_cols": 4,
                "grid_rows": 4,
                "gap": 4,
                "responsive": True
            },
            color_scheme={
                "primary": "#3b82f6",
                "secondary": "#8b5cf6",
                "success": "#10b981",
                "warning": "#f59e0b",
                "danger": "#ef4444"
            }
        )
    
    def _create_saas_template(self) -> DashboardTemplate:
        """Create SaaS metrics dashboard template"""
        components = [
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Monthly Recurring Revenue",
                position={"row": 0, "col": 0},
                size={"width": 1, "height": 1},
                required_columns=["mrr", "recurring_revenue"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Active Users",
                position={"row": 0, "col": 1},
                size={"width": 1, "height": 1},
                required_columns=["active_users", "users"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Churn Rate",
                position={"row": 0, "col": 2},
                size={"width": 1, "height": 1},
                required_columns=["churn_rate", "churn"]
            ),
            ComponentConfig(
                component_type=ComponentType.KPI_CARD,
                title="Customer LTV",
                position={"row": 0, "col": 3},
                size={"width": 1, "height": 1},
                required_columns=["ltv", "lifetime_value"]
            )
        ]
        
        return DashboardTemplate(
            template_type=DashboardTemplateType.SAAS,
            title="SaaS Metrics Dashboard",
            description="SaaS business metrics including MRR, churn, and user analytics",
            components=components,
            required_data_types=["saas", "subscriptions", "users"],
            recommended_columns=["date", "mrr", "active_users", "churn_rate", "ltv"],
            layout_config={
                "grid_cols": 4,
                "grid_rows": 4,
                "gap": 4,
                "responsive": True
            },
            color_scheme={
                "primary": "#6366f1",
                "secondary": "#ec4899",
                "success": "#10b981",
                "warning": "#f59e0b",
                "danger": "#ef4444"
            }
        )
    
    def _create_marketing_template(self) -> DashboardTemplate:
        """Create marketing dashboard template"""
        return DashboardTemplate(
            template_type=DashboardTemplateType.MARKETING,
            title="Marketing Analytics Dashboard",
            description="Campaign performance, leads, and marketing ROI analysis",
            components=[],  # Will be implemented later
            required_data_types=["marketing", "campaigns", "leads"],
            recommended_columns=["date", "campaign", "impressions", "clicks", "conversions", "cost"],
            layout_config={"grid_cols": 4, "grid_rows": 4, "gap": 4, "responsive": True},
            color_scheme={"primary": "#f59e0b", "secondary": "#3b82f6", "success": "#10b981", "warning": "#f59e0b", "danger": "#ef4444"}
        )
    
    def _create_operations_template(self) -> DashboardTemplate:
        """Create operations dashboard template"""
        return DashboardTemplate(
            template_type=DashboardTemplateType.OPERATIONS,
            title="Operations Dashboard",
            description="Operational efficiency, processes, and performance tracking",
            components=[],  # Will be implemented later
            required_data_types=["operations", "processes", "efficiency"],
            recommended_columns=["date", "process", "efficiency", "throughput", "quality"],
            layout_config={"grid_cols": 4, "grid_rows": 4, "gap": 4, "responsive": True},
            color_scheme={"primary": "#8b5cf6", "secondary": "#06b6d4", "success": "#10b981", "warning": "#f59e0b", "danger": "#ef4444"}
        )
    
    def _create_general_template(self) -> DashboardTemplate:
        """Create general purpose dashboard template"""
        return DashboardTemplate(
            template_type=DashboardTemplateType.GENERAL,
            title="General Analytics Dashboard",
            description="Flexible dashboard for any type of data analysis",
            components=[],  # Will be implemented later
            required_data_types=["general"],
            recommended_columns=[],
            layout_config={"grid_cols": 4, "grid_rows": 4, "gap": 4, "responsive": True},
            color_scheme={"primary": "#64748b", "secondary": "#475569", "success": "#10b981", "warning": "#f59e0b", "danger": "#ef4444"}
        )
    
    def get_template(self, template_type: DashboardTemplateType) -> DashboardTemplate:
        """Get a specific dashboard template"""
        return self.templates.get(template_type)
    
    def get_all_templates(self) -> Dict[DashboardTemplateType, DashboardTemplate]:
        """Get all available dashboard templates"""
        return self.templates
    
    def get_templates_by_data_type(self, data_types: List[str]) -> List[DashboardTemplate]:
        """Get templates that match the given data types"""
        matching_templates = []
        for template in self.templates.values():
            if any(dt in template.required_data_types for dt in data_types):
                matching_templates.append(template)
        return matching_templates
    
    def detect_best_template(self, data_columns: List[str], business_context: str = None) -> DashboardTemplateType:
        """Auto-detect best template based on data columns and business context"""
        # Inventory indicators
        inventory_indicators = ['sku', 'stock', 'inventory', 'quantity', 'reorder', 'warehouse']
        if any(indicator in col.lower() for col in data_columns for indicator in inventory_indicators):
            return DashboardTemplateType.INVENTORY
        
        # Sales indicators  
        sales_indicators = ['sales', 'revenue', 'order', 'customer', 'purchase']
        if any(indicator in col.lower() for col in data_columns for indicator in sales_indicators):
            return DashboardTemplateType.SALES
        
        # Financial indicators
        financial_indicators = ['profit', 'expense', 'cost', 'cash', 'financial', 'accounting']
        if any(indicator in col.lower() for col in data_columns for indicator in financial_indicators):
            return DashboardTemplateType.FINANCIAL
        
        # SaaS indicators
        saas_indicators = ['mrr', 'churn', 'subscription', 'ltv', 'user', 'trial']
        if any(indicator in col.lower() for col in data_columns for indicator in saas_indicators):
            return DashboardTemplateType.SAAS
        
        # Ecommerce indicators
        ecommerce_indicators = ['product', 'category', 'cart', 'checkout', 'shipping']
        if any(indicator in col.lower() for col in data_columns for indicator in ecommerce_indicators):
            return DashboardTemplateType.ECOMMERCE
        
        # Business context override
        if business_context:
            context_lower = business_context.lower()
            if 'inventory' in context_lower or 'warehouse' in context_lower:
                return DashboardTemplateType.INVENTORY
            elif 'sales' in context_lower or 'revenue' in context_lower:
                return DashboardTemplateType.SALES
            elif 'financial' in context_lower or 'accounting' in context_lower:
                return DashboardTemplateType.FINANCIAL
            elif 'saas' in context_lower or 'subscription' in context_lower:
                return DashboardTemplateType.SAAS
            elif 'ecommerce' in context_lower or 'shop' in context_lower:
                return DashboardTemplateType.ECOMMERCE
        
        # Default to general
        return DashboardTemplateType.GENERAL 