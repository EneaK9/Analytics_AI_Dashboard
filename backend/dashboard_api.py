"""
Dashboard API - RESTful endpoints for AI-powered dashboard generation

This module provides API endpoints for:
- Data analysis and insights generation
- Dynamic dashboard configuration
- Real-time analytics
- AI-powered recommendations
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import pandas as pd
import json
import numpy as np
from datetime import datetime
import traceback
import logging
from typing import Dict, Any, List
import io
import base64

# Import our AI orchestrator
from ai_orchestrator import orchestrator, DashboardLayout, DashboardWidget

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Custom JSON encoder for handling numpy types and datetime
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

app.json_encoder = CustomJSONEncoder

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AI Dashboard API",
        "version": "1.0.0"
    })

@app.route('/api/analyze-data', methods=['POST'])
def analyze_data():
    """
    Analyze uploaded data and generate insights
    Expects: CSV data or JSON data
    Returns: Analysis results with trends, anomalies, recommendations
    """
    try:
        # Handle different data input formats
        if request.is_json:
            data_dict = request.get_json()
            if 'data' in data_dict:
                df = pd.DataFrame(data_dict['data'])
            else:
                df = pd.DataFrame(data_dict)
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith('.json'):
                df = pd.read_json(file)
            else:
                return jsonify({"error": "Unsupported file format. Use CSV or JSON."}), 400
        else:
            # Try to parse CSV from raw text
            csv_data = request.get_data(as_text=True)
            df = pd.read_csv(io.StringIO(csv_data))
        
        if df.empty:
            return jsonify({"error": "No data provided or data is empty"}), 400
        
        # Perform AI analysis
        analysis = orchestrator.analyze_data_pattern(df)
        
        # Generate insights summary
        insights_summary = orchestrator.generate_insights_summary(analysis)
        
        # Add data overview
        data_overview = {
            "total_records": len(df),
            "total_columns": len(df.columns),
            "numeric_columns": len(df.select_dtypes(include=[np.number]).columns),
            "categorical_columns": len(df.select_dtypes(include=['object']).columns),
            "missing_values": df.isnull().sum().sum(),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "column_info": [
                {
                    "name": col,
                    "type": str(df[col].dtype),
                    "non_null_count": df[col].count(),
                    "unique_values": df[col].nunique() if df[col].dtype == 'object' else None
                } for col in df.columns
            ]
        }
        
        return jsonify({
            "success": True,
            "analysis": analysis,
            "insights_summary": insights_summary,
            "data_overview": data_overview,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in data analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/generate-dashboard', methods=['POST'])
def generate_dashboard():
    """
    Generate dynamic dashboard configuration based on data analysis
    Expects: Data + optional preferences
    Returns: Complete dashboard configuration with widgets
    """
    try:
        request_data = request.get_json()
        
        # Extract data
        if 'data' not in request_data:
            return jsonify({"error": "No data provided"}), 400
        
        df = pd.DataFrame(request_data['data'])
        if df.empty:
            return jsonify({"error": "Data is empty"}), 400
        
        # Extract preferences
        user_preferences = request_data.get('preferences', {})
        dashboard_type = request_data.get('type', 'auto')
        
        # Generate dashboard configuration
        dashboard_config = orchestrator.generate_dashboard_config(
            data=df,
            user_preferences=user_preferences,
            dashboard_type=dashboard_type
        )
        
        # Convert to dict for JSON serialization
        dashboard_dict = {
            "id": dashboard_config.id,
            "title": dashboard_config.title,
            "widgets": [
                {
                    "id": widget.id,
                    "type": widget.type,
                    "title": widget.title,
                    "data": widget.data,
                    "config": widget.config,
                    "position": widget.position,
                    "size": widget.size,
                    "priority": widget.priority,
                    "insights": widget.insights
                } for widget in dashboard_config.widgets
            ],
            "theme": dashboard_config.theme,
            "refresh_interval": dashboard_config.refresh_interval,
            "filters": dashboard_config.filters,
            "created_at": dashboard_config.created_at.isoformat(),
            "ai_recommendations": dashboard_config.ai_recommendations
        }
        
        return jsonify({
            "success": True,
            "dashboard": dashboard_dict,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/optimize-dashboard', methods=['POST'])
def optimize_dashboard():
    """
    Optimize existing dashboard based on performance metrics and usage patterns
    """
    try:
        request_data = request.get_json()
        
        # Extract dashboard configuration
        dashboard_dict = request_data.get('dashboard')
        performance_metrics = request_data.get('performance_metrics', {})
        
        if not dashboard_dict:
            return jsonify({"error": "No dashboard configuration provided"}), 400
        
        # Convert dict back to DashboardLayout object
        widgets = []
        for widget_dict in dashboard_dict.get('widgets', []):
            widget = DashboardWidget(
                id=widget_dict['id'],
                type=widget_dict['type'],
                title=widget_dict['title'],
                data=widget_dict['data'],
                config=widget_dict['config'],
                position=widget_dict['position'],
                size=widget_dict['size'],
                priority=widget_dict['priority'],
                insights=widget_dict['insights']
            )
            widgets.append(widget)
        
        dashboard = DashboardLayout(
            id=dashboard_dict['id'],
            title=dashboard_dict['title'],
            widgets=widgets,
            theme=dashboard_dict['theme'],
            refresh_interval=dashboard_dict['refresh_interval'],
            filters=dashboard_dict['filters'],
            created_at=datetime.fromisoformat(dashboard_dict['created_at'].replace('Z', '+00:00')),
            ai_recommendations=dashboard_dict['ai_recommendations']
        )
        
        # Optimize the dashboard
        optimized_dashboard = orchestrator.optimize_dashboard_performance(dashboard, performance_metrics)
        
        # Convert back to dict
        optimized_dict = {
            "id": optimized_dashboard.id,
            "title": optimized_dashboard.title,
            "widgets": [
                {
                    "id": widget.id,
                    "type": widget.type,
                    "title": widget.title,
                    "data": widget.data,
                    "config": widget.config,
                    "position": widget.position,
                    "size": widget.size,
                    "priority": widget.priority,
                    "insights": widget.insights
                } for widget in optimized_dashboard.widgets
            ],
            "theme": optimized_dashboard.theme,
            "refresh_interval": optimized_dashboard.refresh_interval,
            "filters": optimized_dashboard.filters,
            "created_at": optimized_dashboard.created_at.isoformat(),
            "ai_recommendations": optimized_dashboard.ai_recommendations
        }
        
        return jsonify({
            "success": True,
            "optimized_dashboard": optimized_dict,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error optimizing dashboard: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/sample-data', methods=['GET'])
def get_sample_data():
    """
    Generate sample data for demonstration purposes
    """
    try:
        # Generate sample ecommerce data
        np.random.seed(42)  # For reproducible results
        
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        n_days = len(dates)
        
        # Create realistic sample data with trends and seasonality
        base_revenue = 1000
        trend = np.linspace(0, 500, n_days)  # Upward trend
        seasonality = 200 * np.sin(2 * np.pi * np.arange(n_days) / 365.25)  # Yearly seasonality
        noise = np.random.normal(0, 100, n_days)
        
        sample_data = {
            'date': dates.strftime('%Y-%m-%d').tolist(),
            'revenue': (base_revenue + trend + seasonality + noise).round(2).tolist(),
            'orders': np.random.poisson(50, n_days).tolist(),
            'customers': np.random.poisson(30, n_days).tolist(),
            'conversion_rate': (np.random.beta(2, 8, n_days) * 100).round(2).tolist(),
            'avg_order_value': (20 + np.random.gamma(2, 10, n_days)).round(2).tolist(),
            'customer_satisfaction': (4 + np.random.beta(5, 2, n_days)).round(1).tolist(),
            'marketing_spend': (500 + np.random.gamma(2, 50, n_days)).round(2).tolist(),
            'category': np.random.choice(['Electronics', 'Clothing', 'Books', 'Home'], n_days).tolist(),
            'region': np.random.choice(['North', 'South', 'East', 'West'], n_days).tolist()
        }
        
        return jsonify({
            "success": True,
            "data": sample_data,
            "description": "Sample ecommerce data with trends, seasonality, and realistic business metrics",
            "record_count": n_days,
            "date_range": {
                "start": dates[0].strftime('%Y-%m-%d'),
                "end": dates[-1].strftime('%Y-%m-%d')
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating sample data: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/insights/<insight_type>', methods=['POST'])
def get_specific_insights(insight_type):
    """
    Get specific type of insights (trends, anomalies, correlations, etc.)
    """
    try:
        request_data = request.get_json()
        
        if 'data' not in request_data:
            return jsonify({"error": "No data provided"}), 400
        
        df = pd.DataFrame(request_data['data'])
        if df.empty:
            return jsonify({"error": "Data is empty"}), 400
        
        # Perform full analysis first
        analysis = orchestrator.analyze_data_pattern(df)
        
        # Extract specific insight type
        if insight_type == 'trends':
            insights = analysis.get('trends', {})
        elif insight_type == 'anomalies':
            insights = analysis.get('anomalies', {})
        elif insight_type == 'correlations':
            insights = analysis.get('correlations', {})
        elif insight_type == 'seasonality':
            insights = analysis.get('seasonality', {})
        elif insight_type == 'growth':
            insights = analysis.get('growth_metrics', {})
        elif insight_type == 'quality':
            insights = analysis.get('data_quality', {})
        elif insight_type == 'recommendations':
            insights = analysis.get('recommendations', [])
        else:
            return jsonify({"error": f"Unknown insight type: {insight_type}"}), 400
        
        return jsonify({
            "success": True,
            "insight_type": insight_type,
            "insights": insights,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting {insight_type} insights: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/dashboard-templates', methods=['GET'])
def get_dashboard_templates():
    """
    Get available dashboard templates
    """
    try:
        templates = orchestrator.dashboard_templates
        
        # Add more details to templates
        enhanced_templates = {}
        for template_name, template_config in templates.items():
            enhanced_templates[template_name] = {
                **template_config,
                "name": template_name.title(),
                "description": f"Optimized dashboard for {template_name} analytics",
                "use_cases": _get_template_use_cases(template_name),
                "recommended_for": _get_template_recommendations(template_name)
            }
        
        return jsonify({
            "success": True,
            "templates": enhanced_templates,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard templates: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

def _get_template_use_cases(template_name: str) -> List[str]:
    """Get use cases for a specific template"""
    use_cases = {
        "ecommerce": [
            "Online store performance tracking",
            "Customer behavior analysis",
            "Sales trend monitoring",
            "Inventory management insights"
        ],
        "sales": [
            "Sales team performance",
            "Pipeline health monitoring",
            "Lead conversion tracking",
            "Revenue forecasting"
        ],
        "financial": [
            "Financial health monitoring",
            "Budget vs actual analysis",
            "Cash flow management",
            "Profitability insights"
        ],
        "operations": [
            "Operational efficiency tracking",
            "Resource utilization analysis",
            "Quality metrics monitoring",
            "Process optimization"
        ]
    }
    return use_cases.get(template_name, [])

def _get_template_recommendations(template_name: str) -> List[str]:
    """Get recommendations for when to use a specific template"""
    recommendations = {
        "ecommerce": [
            "E-commerce businesses",
            "Online marketplaces",
            "Retail analytics teams",
            "Digital marketing managers"
        ],
        "sales": [
            "Sales teams and managers",
            "Business development",
            "CRM administrators",
            "Revenue operations"
        ],
        "financial": [
            "Finance teams",
            "CFOs and controllers",
            "Investment analysts",
            "Budget planners"
        ],
        "operations": [
            "Operations managers",
            "Process improvement teams",
            "Manufacturing analytics",
            "Supply chain managers"
        ]
    }
    return recommendations.get(template_name, [])

@app.route('/api/data-preview', methods=['POST'])
def preview_data():
    """
    Preview uploaded data before analysis
    """
    try:
        # Handle file upload or JSON data
        if 'file' in request.files:
            file = request.files['file']
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file, nrows=100)  # Limit preview to first 100 rows
            elif file.filename.endswith('.json'):
                df = pd.read_json(file)
                df = df.head(100)
            else:
                return jsonify({"error": "Unsupported file format"}), 400
        else:
            request_data = request.get_json()
            if 'data' not in request_data:
                return jsonify({"error": "No data provided"}), 400
            
            data = request_data['data']
            df = pd.DataFrame(data)
            df = df.head(100)  # Limit preview
        
        # Generate preview information
        preview_info = {
            "sample_rows": df.head(10).to_dict('records'),
            "total_rows": len(df),
            "columns": [
                {
                    "name": col,
                    "type": str(df[col].dtype),
                    "sample_values": df[col].dropna().head(5).tolist(),
                    "null_count": df[col].isnull().sum(),
                    "unique_count": df[col].nunique()
                } for col in df.columns
            ],
            "data_types": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "basic_stats": df.describe().round(2).to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else {}
        }
        
        return jsonify({
            "success": True,
            "preview": preview_info,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error previewing data: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    logger.info("Starting AI Dashboard API server...")
    app.run(debug=True, host='0.0.0.0', port=5000) 