import json
import pandas as pd
import os
from typing import Dict, List, Any, Optional, Tuple
from models import (
    DashboardConfig, DashboardLayout, KPIWidget, ChartWidget, ChartType,
    DashboardMetric, BusinessContext, AIInsight, DataAnalysisResult,
    DashboardGenerationRequest, DashboardGenerationResponse,
    DashboardGenerationTracking, GenerationStatus, GenerationType, ErrorType,
    RetryInfo, GenerationResult, AutoGenerationRequest
)
import re
import logging
from datetime import datetime, timedelta
from database import get_admin_client
import uuid
import asyncio
from ai_analyzer import AIDataAnalyzer
import numpy as np
from collections import Counter

logger = logging.getLogger(__name__)

class DashboardOrchestrator:
    """AI-powered dashboard orchestrator that generates personalized dashboards"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.ai_analyzer = AIDataAnalyzer()
        
        if self.openai_api_key:
            logger.info("✅ OpenAI API key configured for Dashboard Orchestrator")
        else:
            logger.warning("⚠️  OpenAI API key not configured - using heuristic analysis")
        
        # Chart type mapping based on data characteristics
        self.chart_type_mapping = {
            'time_series': [ChartType.LINE, ChartType.AREA],
            'categorical': [ChartType.BAR, ChartType.PIE, ChartType.DOUGHNUT],
            'numerical': [ChartType.HISTOGRAM, ChartType.SCATTER],
            'correlation': [ChartType.SCATTER, ChartType.HEATMAP],
            'comparison': [ChartType.BAR, ChartType.LINE]
        }
        
        # Icon mapping for common business metrics
        self.kpi_icons = {
            'revenue': {'icon': 'DollarSign', 'color': 'text-meta-3', 'bg': 'bg-meta-3/10'},
            'sales': {'icon': 'TrendingUp', 'color': 'text-success', 'bg': 'bg-success/10'},
            'expenses': {'icon': 'TrendingDown', 'color': 'text-meta-1', 'bg': 'bg-meta-1/10'},
            'profit': {'icon': 'PieChart', 'color': 'text-primary', 'bg': 'bg-primary/10'},
            'users': {'icon': 'Users', 'color': 'text-meta-6', 'bg': 'bg-meta-6/10'},
            'orders': {'icon': 'ShoppingCart', 'color': 'text-warning', 'bg': 'bg-warning/10'},
            'inventory': {'icon': 'Package', 'color': 'text-info', 'bg': 'bg-info/10'},
            'performance': {'icon': 'BarChart', 'color': 'text-success', 'bg': 'bg-success/10'},
            'growth': {'icon': 'TrendingUp', 'color': 'text-meta-3', 'bg': 'bg-meta-3/10'},
            'conversion': {'icon': 'Target', 'color': 'text-primary', 'bg': 'bg-primary/10'}
        }
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error to determine if it should be retried"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # AI/OpenAI related errors (retryable)
        ai_error_indicators = [
            'openai', 'api', 'rate limit', 'timeout', 'connection',
            'service unavailable', 'internal server error', '429', '500', '502', '503', '504',
            'network', 'dns', 'ssl', 'certificate', 'authentication failed'
        ]
        
        # System errors (non-retryable)
        system_error_indicators = [
            'database', 'sql', 'table', 'column', 'foreign key', 'constraint',
            'permission', 'access denied', 'not found', 'invalid configuration'
        ]
        
        # Data errors (non-retryable)  
        data_error_indicators = [
            'no data', 'empty dataset', 'invalid data format', 'missing columns',
            'data validation', 'insufficient data', 'corrupt data'
        ]
        
        # Check for specific error patterns
        if any(indicator in error_str for indicator in ai_error_indicators):
            return ErrorType.AI_FAILURE
        elif any(indicator in error_str for indicator in system_error_indicators):
            return ErrorType.SYSTEM_ERROR
        elif any(indicator in error_str for indicator in data_error_indicators):
            return ErrorType.DATA_ERROR
        else:
            # Default to AI failure for unknown errors (safer to retry)
            logger.warning(f"🤔 Unknown error type, defaulting to AI_FAILURE: {error}")
            return ErrorType.AI_FAILURE
    
    def _calculate_retry_info(self, attempt_count: int, error_type: ErrorType) -> RetryInfo:
        """Calculate retry information with exponential backoff"""
        max_attempts = 5
        
        # Only retry AI failures
        should_retry = (
            error_type == ErrorType.AI_FAILURE and 
            attempt_count < max_attempts
        )
        
        if not should_retry:
            if error_type != ErrorType.AI_FAILURE:
                reason = f"Error type {error_type.value} is not retryable"
            else:
                reason = f"Maximum attempts ({max_attempts}) reached"
            
            return RetryInfo(
                should_retry=False,
                error_type=error_type,
                retry_delay_seconds=0,
                next_attempt=attempt_count + 1,
                max_attempts=max_attempts,
                reason=reason
            )
        
        # Exponential backoff: 1min, 5min, 15min, 30min, 30min...
        delay_map = {
            1: 60,      # 1 minute
            2: 300,     # 5 minutes
            3: 900,     # 15 minutes
            4: 1800,    # 30 minutes
            5: 1800     # 30 minutes
        }
        
        delay_seconds = delay_map.get(attempt_count + 1, 1800)
        
        return RetryInfo(
            should_retry=True,
            error_type=error_type,
            retry_delay_seconds=delay_seconds,
            next_attempt=attempt_count + 1,
            max_attempts=max_attempts,
            reason=f"AI failure, will retry in {delay_seconds//60} minutes"
        )
    
    async def _init_generation_tracking(self, client_id: uuid.UUID, generation_type: GenerationType) -> uuid.UUID:
        """Initialize generation tracking in database"""
        try:
            db_client = get_admin_client()
            if not db_client:
                raise Exception("Database client not available")
            
            tracking_data = {
                'client_id': str(client_id),
                'status': GenerationStatus.PENDING.value,
                'generation_type': generation_type.value,
                'attempt_count': 0,
                'max_attempts': 5,
                'started_at': datetime.now().isoformat()
            }
            
            response = db_client.table('client_dashboard_generation').upsert(
                tracking_data,
                on_conflict='client_id'
            ).execute()
            
            if response.data:
                generation_id = response.data[0]['generation_id']
                logger.info(f"✅ Generation tracking initialized for client {client_id}: {generation_id}")
                return uuid.UUID(generation_id)
            else:
                raise Exception("Failed to initialize generation tracking")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize generation tracking: {e}")
            # Return a dummy ID if tracking fails
            return uuid.uuid4()
    
    async def _update_generation_tracking(self, generation_id: uuid.UUID, status: GenerationStatus, 
                                        attempt_count: int = None, error_type: ErrorType = None,
                                        error_message: str = None, next_retry_at: datetime = None):
        """Update generation tracking status"""
        try:
            db_client = get_admin_client()
            if not db_client:
                return
            
            update_data = {
                'status': status.value,
                'last_attempt_at': datetime.now().isoformat()
            }
            
            if attempt_count is not None:
                update_data['attempt_count'] = attempt_count
            
            if error_type:
                update_data['error_type'] = error_type.value
                update_data['error_message'] = error_message
            
            if next_retry_at:
                update_data['next_retry_at'] = next_retry_at.isoformat()
            
            if status == GenerationStatus.COMPLETED:
                update_data['completed_at'] = datetime.now().isoformat()
            
            response = db_client.table('client_dashboard_generation').update(
                update_data
            ).eq('generation_id', str(generation_id)).execute()
            
            logger.info(f"📊 Generation tracking updated: {generation_id} -> {status.value}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update generation tracking: {e}")
    
    async def generate_dashboard_with_retry(self, request: AutoGenerationRequest) -> GenerationResult:
        """Generate a personalized dashboard with intelligent retry logic"""
        start_time = datetime.now()
        generation_id = None
        attempt_count = 1
        
        try:
            logger.info(f"🎨 Starting dashboard generation for client {request.client_id} (attempt {attempt_count})")
            
            # Initialize generation tracking
            generation_id = await self._init_generation_tracking(request.client_id, request.generation_type)
            
            # Update status to processing
            await self._update_generation_tracking(generation_id, GenerationStatus.PROCESSING, attempt_count)
            
            # Check if dashboard already exists (unless force retry)
            if not request.force_retry:
                existing_dashboard = await self._get_existing_dashboard(request.client_id)
                if existing_dashboard:
                    logger.info(f"📊 Dashboard already exists for client {request.client_id}")
                    await self._update_generation_tracking(generation_id, GenerationStatus.COMPLETED)
                    return GenerationResult(
                        success=True,
                        client_id=request.client_id,
                        generation_id=generation_id,
                        dashboard_config=existing_dashboard,
                        metrics_generated=0,
                        generation_time=(datetime.now() - start_time).total_seconds(),
                        attempt_number=attempt_count
                    )
            
            # Attempt dashboard generation
            result = await self._attempt_dashboard_generation(request.client_id, generation_id, attempt_count)
            
            if result.success:
                await self._update_generation_tracking(generation_id, GenerationStatus.COMPLETED)
                logger.info(f"✅ Dashboard generated successfully for client {request.client_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Dashboard generation failed for client {request.client_id}: {e}")
            
            # Classify the error
            error_type = self._classify_error(e)
            retry_info = self._calculate_retry_info(attempt_count, error_type)
            
            # Update tracking based on retry decision
            if retry_info.should_retry:
                next_retry_time = datetime.now() + timedelta(seconds=retry_info.retry_delay_seconds)
                await self._update_generation_tracking(
                    generation_id, 
                    GenerationStatus.RETRYING, 
                    attempt_count, 
                    error_type, 
                    str(e), 
                    next_retry_time
                )
                logger.warning(f"🔄 Will retry dashboard generation for client {request.client_id} in {retry_info.retry_delay_seconds//60} minutes")
            else:
                await self._update_generation_tracking(
                    generation_id, 
                    GenerationStatus.FAILED, 
                    attempt_count, 
                    error_type, 
                    str(e)
                )
                logger.error(f"❌ Dashboard generation permanently failed for client {request.client_id}: {retry_info.reason}")
            
            return GenerationResult(
                success=False,
                client_id=request.client_id,
                generation_id=generation_id or uuid.uuid4(),
                error_type=error_type,
                error_message=str(e),
                error_details={'exception_type': type(e).__name__},
                retry_info=retry_info,
                generation_time=(datetime.now() - start_time).total_seconds(),
                attempt_number=attempt_count
            )
    
    async def _attempt_dashboard_generation(self, client_id: uuid.UUID, generation_id: uuid.UUID, attempt_count: int) -> GenerationResult:
        """Single attempt at dashboard generation"""
        start_time = datetime.now()
        
        try:
            # Step 1: Analyze client data
            data_analysis = await self._analyze_client_data(client_id)
            
            # Step 2: Generate business context using AI
            business_context = await self._generate_business_context(client_id, data_analysis)
            
            # Step 3: Generate KPI widgets
            kpi_widgets = await self._generate_kpi_widgets(client_id, business_context, data_analysis)
            
            # Step 4: Generate chart widgets
            chart_widgets = await self._generate_chart_widgets(client_id, business_context, data_analysis)
            
            # Step 5: Create dashboard layout
            layout = DashboardLayout(
                grid_cols=4,
                grid_rows=max(6, len(kpi_widgets) // 4 + len(chart_widgets) // 2 + 2),
                gap=4,
                responsive=True
            )
            
            # Step 6: Create dashboard configuration
            dashboard_config = DashboardConfig(
                client_id=client_id,
                title=f"{business_context.business_type.title()} Analytics Dashboard",
                subtitle=f"AI-generated insights for {business_context.industry}",
                layout=layout,
                kpi_widgets=kpi_widgets,
                chart_widgets=chart_widgets,
                theme="default",
                last_generated=datetime.now(),
                version="1.0"
            )
            
            # Step 7: Save dashboard configuration
            await self._save_dashboard_config(dashboard_config)
            
            # Step 8: Generate and save metrics
            metrics_generated = await self._generate_and_save_metrics(client_id, dashboard_config, data_analysis)
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            return GenerationResult(
                success=True,
                client_id=client_id,
                generation_id=generation_id,
                dashboard_config=dashboard_config,
                metrics_generated=metrics_generated,
                generation_time=generation_time,
                attempt_number=attempt_count
            )
            
        except Exception as e:
            # Re-raise for the main handler to classify and handle retries
            raise e
    
    async def generate_dashboard(self, client_id: uuid.UUID, force_regenerate: bool = False) -> DashboardGenerationResponse:
        start_time = datetime.now()  # Add missing start_time variable
        
        try:
            logger.info(f"🎨 Starting dashboard generation for client {client_id}")
            
            # Step 1: Check if dashboard already exists
            if not force_regenerate:
                existing_dashboard = await self._get_existing_dashboard(client_id)
                if existing_dashboard:
                    logger.info(f"📊 Dashboard already exists for client {client_id}")
                    return DashboardGenerationResponse(
                        success=True,
                        client_id=client_id,
                        dashboard_config=existing_dashboard,
                        metrics_generated=0,
                        message="Dashboard already exists",
                        generation_time=(datetime.now() - start_time).total_seconds()
                    )
            
            # Step 2: Analyze client data
            data_analysis = await self._analyze_client_data(client_id)
            
            # Step 3: Generate business context using AI
            business_context = await self._generate_business_context(client_id, data_analysis)
            
            # Step 4: Generate KPI widgets
            kpi_widgets = await self._generate_kpi_widgets(client_id, business_context, data_analysis)
            
            # Step 5: Generate chart widgets
            chart_widgets = await self._generate_chart_widgets(client_id, business_context, data_analysis)
            
            # Step 6: Create dashboard layout
            layout = DashboardLayout(
                grid_cols=4,
                grid_rows=max(6, len(kpi_widgets) // 4 + len(chart_widgets) // 2 + 2),
                gap=4,
                responsive=True
            )
            
            # Step 7: Create dashboard configuration
            dashboard_config = DashboardConfig(
                client_id=client_id,
                title=f"{business_context.business_type.title()} Analytics Dashboard",
                subtitle=f"AI-generated insights for {business_context.industry}",
                layout=layout,
                kpi_widgets=kpi_widgets,
                chart_widgets=chart_widgets,
                theme="default",
                last_generated=datetime.now(),
                version="1.0"
            )
            
            # Step 8: Save dashboard configuration
            await self._save_dashboard_config(dashboard_config)
            
            # Step 9: Generate and save metrics
            metrics_generated = await self._generate_and_save_metrics(client_id, dashboard_config, data_analysis)
            
            generation_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Dashboard generated successfully for client {client_id} in {generation_time:.2f}s")
            
            return DashboardGenerationResponse(
                success=True,
                client_id=client_id,
                dashboard_config=dashboard_config,
                metrics_generated=metrics_generated,
                message="Dashboard generated successfully",
                generation_time=generation_time
            )
            
        except Exception as e:
            logger.error(f"❌ Dashboard generation failed for client {client_id}: {e}")
            return DashboardGenerationResponse(
                success=False,
                client_id=client_id,
                dashboard_config=None,
                metrics_generated=0,
                message=f"Dashboard generation failed: {str(e)}",
                generation_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _analyze_client_data(self, client_id: uuid.UUID) -> Dict[str, Any]:
        """Analyze client data to understand structure and characteristics"""
        try:
            # Get client data using AI analyzer
            client_data = await self.ai_analyzer.get_client_data(str(client_id))
            
            if not client_data.get('data'):
                logger.warning(f"⚠️  No data found for client {client_id}")
                return self._create_sample_analysis(client_id)
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(client_data['data'])
            
            # Analyze data characteristics
            analysis = {
                'total_records': len(df),
                'columns': list(df.columns),
                'column_types': df.dtypes.to_dict(),
                'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
                'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
                'date_columns': self._detect_date_columns(df),
                'missing_values': df.isnull().sum().to_dict(),
                'unique_values': {col: df[col].nunique() for col in df.columns},
                'sample_data': df.head().to_dict('records'),
                'data_quality_score': self._calculate_data_quality_score(df)
            }
            
            # Detect patterns and trends
            analysis['patterns'] = self._detect_data_patterns(df)
            analysis['trends'] = self._analyze_trends(df)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Data analysis failed for client {client_id}: {e}")
            return self._create_sample_analysis(client_id)
    
    async def _generate_business_context(self, client_id: uuid.UUID, data_analysis: Dict[str, Any]) -> BusinessContext:
        """Generate business context using AI analysis"""
        try:
            if self.openai_api_key:
                # Use OpenAI to analyze business context
                context = await self._ai_analyze_business_context(client_id, data_analysis)
            else:
                # Use heuristic analysis
                context = self._heuristic_business_context(data_analysis)
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Business context generation failed: {e}")
            return self._create_default_business_context(data_analysis)
    
    async def _ai_analyze_business_context(self, client_id: uuid.UUID, data_analysis: Dict[str, Any]) -> BusinessContext:
        """Use OpenAI to analyze business context"""
        try:
            # Prepare data summary for AI analysis
            data_summary = {
                'columns': data_analysis['columns'],
                'numeric_columns': data_analysis['numeric_columns'],
                'categorical_columns': data_analysis['categorical_columns'],
                'patterns': data_analysis['patterns'],
                'sample_data': data_analysis['sample_data'][:3]  # Limit sample size
            }
            
            prompt = f"""
            Analyze this business data and provide insights:
            
            Data Summary:
            {json.dumps(data_summary, indent=2)}
            
            Please provide:
            1. Industry classification
            2. Business type (ecommerce, saas, retail, service, etc.)
            3. Key business metrics that should be tracked
            4. Recommended chart types for this data
            5. Business insights and opportunities
            
            Respond in JSON format with the following structure:
            {{
                "industry": "string",
                "business_type": "string",
                "data_characteristics": ["list", "of", "characteristics"],
                "key_metrics": ["list", "of", "metrics"],
                "recommended_charts": ["line", "bar", "pie"],
                "insights": [
                    {{
                        "type": "opportunity/warning/trend/recommendation",
                        "title": "string",
                        "description": "string",
                        "impact": "high/medium/low",
                        "suggested_action": "string"
                    }}
                ],
                "confidence_score": 0.85
            }}
            """
            
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a business intelligence expert analyzing data to create personalized dashboards."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Get the response content and validate it
            response_content = response.choices[0].message.content
            if not response_content or not response_content.strip():
                logger.warning("⚠️  Empty response from OpenAI, falling back to heuristic analysis")
                return self._heuristic_business_context(data_analysis)
            
            # Strip markdown code blocks if present
            response_content = response_content.strip()
            if response_content.startswith('```json'):
                response_content = response_content[7:]  # Remove ```json
            if response_content.startswith('```'):
                response_content = response_content[3:]   # Remove ```
            if response_content.endswith('```'):
                response_content = response_content[:-3]  # Remove closing ```
            response_content = response_content.strip()
            
            # Try to parse JSON with better error handling
            try:
                ai_response = json.loads(response_content)
            except json.JSONDecodeError as json_error:
                logger.warning(f"⚠️  Invalid JSON from OpenAI: {json_error}. Response: {response_content[:200]}...")
                logger.warning("🔄 Falling back to heuristic analysis")
                return self._heuristic_business_context(data_analysis)
            
            # Validate that we have the expected structure
            if not isinstance(ai_response, dict):
                logger.warning("⚠️  OpenAI response is not a dictionary, falling back to heuristic analysis")
                return self._heuristic_business_context(data_analysis)
            
            # Convert to BusinessContext model
            insights = [
                AIInsight(
                    type=insight['type'],
                    title=insight['title'],
                    description=insight['description'],
                    impact=insight['impact'],
                    suggested_action=insight.get('suggested_action')
                ) for insight in ai_response.get('insights', [])
            ]
            
            return BusinessContext(
                industry=ai_response.get('industry', 'General'),
                business_type=ai_response.get('business_type', 'general'),
                data_characteristics=ai_response.get('data_characteristics', []),
                key_metrics=ai_response.get('key_metrics', []),
                recommended_charts=[ChartType(chart) for chart in ai_response.get('recommended_charts', ['bar', 'line'])],
                insights=insights,
                confidence_score=ai_response.get('confidence_score', 0.7)
            )
            
        except Exception as e:
            logger.error(f"❌ AI business context analysis failed: {e}")
            return self._heuristic_business_context(data_analysis)
    
    def _heuristic_business_context(self, data_analysis: Dict[str, Any]) -> BusinessContext:
        """Generate business context using heuristic analysis"""
        columns = [col.lower() for col in data_analysis['columns']]
        
        # Detect business type based on column names
        business_type = 'general'
        industry = 'General'
        
        if any(term in ' '.join(columns) for term in ['order', 'purchase', 'product', 'price', 'customer']):
            business_type = 'ecommerce'
            industry = 'E-commerce'
        elif any(term in ' '.join(columns) for term in ['user', 'subscription', 'plan', 'feature']):
            business_type = 'saas'
            industry = 'Software as a Service'
        elif any(term in ' '.join(columns) for term in ['sale', 'inventory', 'stock', 'item']):
            business_type = 'retail'
            industry = 'Retail'
        elif any(term in ' '.join(columns) for term in ['revenue', 'expense', 'profit', 'cost']):
            business_type = 'finance'
            industry = 'Financial Services'
        
        # Generate insights based on data patterns
        insights = []
        if data_analysis['patterns'].get('has_time_series'):
            insights.append(AIInsight(
                type='opportunity',
                title='Time Series Data Detected',
                description='Your data contains time-based patterns suitable for trend analysis',
                impact='high',
                suggested_action='Implement time-based forecasting and trend monitoring'
            ))
        
        if data_analysis['data_quality_score'] < 0.8:
            insights.append(AIInsight(
                type='warning',
                title='Data Quality Issues',
                description='Some data quality issues detected that may affect insights',
                impact='medium',
                suggested_action='Review and clean data sources for better accuracy'
            ))
        
        return BusinessContext(
            industry=industry,
            business_type=business_type,
            data_characteristics=self._extract_data_characteristics(data_analysis),
            key_metrics=self._extract_key_metrics(columns),
            recommended_charts=[ChartType.BAR, ChartType.LINE, ChartType.PIE],
            insights=insights,
            confidence_score=0.6
        )
    
    async def _generate_kpi_widgets(self, client_id: uuid.UUID, business_context: BusinessContext, data_analysis: Dict[str, Any]) -> List[KPIWidget]:
        """Generate KPI widgets based on business context and data"""
        kpi_widgets = []
        numeric_columns = data_analysis['numeric_columns']
        
        # Generate KPIs based on business context
        if business_context.business_type == 'ecommerce':
            kpi_suggestions = [
                {'key': 'revenue', 'title': 'Total Revenue', 'column': self._find_column(numeric_columns, ['revenue', 'sales', 'amount', 'total'])},
                {'key': 'orders', 'title': 'Total Orders', 'column': self._find_column(numeric_columns, ['orders', 'purchases', 'transactions'])},
                {'key': 'users', 'title': 'Active Customers', 'column': self._find_column(numeric_columns, ['customers', 'users', 'buyers'])},
                {'key': 'conversion', 'title': 'Conversion Rate', 'column': self._find_column(numeric_columns, ['conversion', 'rate', 'percentage'])}
            ]
        elif business_context.business_type == 'saas':
            kpi_suggestions = [
                {'key': 'revenue', 'title': 'Monthly Revenue', 'column': self._find_column(numeric_columns, ['revenue', 'mrr', 'income'])},
                {'key': 'users', 'title': 'Active Users', 'column': self._find_column(numeric_columns, ['users', 'subscribers', 'accounts'])},
                {'key': 'growth', 'title': 'Growth Rate', 'column': self._find_column(numeric_columns, ['growth', 'rate', 'change'])},
                {'key': 'performance', 'title': 'Performance Score', 'column': self._find_column(numeric_columns, ['score', 'performance', 'rating'])}
            ]
        else:
            # General business KPIs
            kpi_suggestions = [
                {'key': 'revenue', 'title': 'Total Revenue', 'column': numeric_columns[0] if numeric_columns else None},
                {'key': 'growth', 'title': 'Growth Rate', 'column': numeric_columns[1] if len(numeric_columns) > 1 else None},
                {'key': 'performance', 'title': 'Performance', 'column': numeric_columns[2] if len(numeric_columns) > 2 else None},
                {'key': 'users', 'title': 'Users/Clients', 'column': numeric_columns[3] if len(numeric_columns) > 3 else None}
            ]
        
        # Create KPI widgets
        for i, kpi in enumerate(kpi_suggestions):
            if kpi['column'] and i < 4:  # Limit to 4 KPIs
                icon_config = self.kpi_icons.get(kpi['key'], self.kpi_icons['performance'])
                
                kpi_widget = KPIWidget(
                    id=f"kpi_{kpi['key']}_{i}",
                    title=kpi['title'],
                    value=f"${data_analysis['sample_data'][0].get(kpi['column'], 0):,.0f}" if kpi['column'] in str(data_analysis['sample_data']) else "N/A",
                    icon=icon_config['icon'],
                    icon_color=icon_config['color'],
                    icon_bg_color=icon_config['bg'],
                    trend={"value": "12.5%", "isPositive": True},  # Will be calculated with real data
                    position={"row": 0, "col": i},
                    size={"width": 1, "height": 1}
                )
                kpi_widgets.append(kpi_widget)
        
        return kpi_widgets
    
    async def _generate_chart_widgets(self, client_id: uuid.UUID, business_context: BusinessContext, data_analysis: Dict[str, Any]) -> List[ChartWidget]:
        """Generate chart widgets based on business context and data"""
        chart_widgets = []
        
        # Generate charts based on data characteristics
        if data_analysis['patterns'].get('has_time_series'):
            # Time series chart
            chart_widgets.append(ChartWidget(
                id="chart_time_series",
                title="Trend Analysis",
                subtitle="Performance over time",
                chart_type=ChartType.LINE,
                data_source="time_series_data",
                config={"responsive": True, "showLegend": True},
                position={"row": 1, "col": 0},
                size={"width": 2, "height": 2}
            ))
        
        if len(data_analysis['categorical_columns']) > 0:
            # Categorical chart
            chart_widgets.append(ChartWidget(
                id="chart_categorical",
                title="Category Breakdown",
                subtitle="Distribution by category",
                chart_type=ChartType.BAR,
                data_source="categorical_data",
                config={"responsive": True, "showLegend": True},
                position={"row": 1, "col": 2},
                size={"width": 2, "height": 2}
            ))
        
        if len(data_analysis['numeric_columns']) >= 2:
            # Correlation/scatter chart
            chart_widgets.append(ChartWidget(
                id="chart_correlation",
                title="Performance Correlation",
                subtitle="Relationship between key metrics",
                chart_type=ChartType.SCATTER,
                data_source="correlation_data",
                config={"responsive": True, "showLegend": True},
                position={"row": 3, "col": 0},
                size={"width": 4, "height": 2}
            ))
        
        return chart_widgets
    
    def _convert_uuids_to_strings(self, obj):
        """Convert UUID and datetime objects to strings recursively"""
        if isinstance(obj, dict):
            return {k: self._convert_uuids_to_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_uuids_to_strings(item) for item in obj]
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    async def _save_dashboard_config(self, dashboard_config: DashboardConfig):
        """Save dashboard configuration to database"""
        try:
            db_client = get_admin_client()
            if not db_client:
                raise Exception("Database client not available")
            
            # Convert dashboard config to dict with proper UUID handling
            dashboard_dict = dashboard_config.dict()
            dashboard_dict = self._convert_uuids_to_strings(dashboard_dict)
            
            # Prepare data for insertion
            config_data = {
                'client_id': str(dashboard_config.client_id),
                'dashboard_config': dashboard_dict,
                'is_generated': True,
                'generation_timestamp': dashboard_config.last_generated.isoformat()
            }
            
            # Insert or update dashboard config
            response = db_client.table('client_dashboard_configs').upsert(
                config_data,
                on_conflict='client_id'
            ).execute()
            
            logger.info(f"✅ Dashboard config saved for client {dashboard_config.client_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save dashboard config: {e}")
            raise
    
    async def _generate_and_save_metrics(self, client_id: uuid.UUID, dashboard_config: DashboardConfig, data_analysis: Dict[str, Any]) -> int:
        """Generate and save dashboard metrics"""
        try:
            metrics_generated = 0
            db_client = get_admin_client()
            
            # Generate metrics for KPIs
            for kpi in dashboard_config.kpi_widgets:
                metric = DashboardMetric(
                    metric_id=uuid.uuid4(),  # Generate UUID for metric_id
                    client_id=client_id,
                    metric_name=kpi.id,
                    metric_value={
                        'value': kpi.value,
                        'title': kpi.title,
                        'trend': kpi.trend
                    },
                    metric_type='kpi',
                    calculated_at=datetime.now()
                )
                
                # Convert to dict with UUID handling
                metric_dict = self._convert_uuids_to_strings(metric.dict())
                
                # Save metric
                db_client.table('client_dashboard_metrics').insert(metric_dict).execute()
                metrics_generated += 1
            
            # Generate metrics for charts
            for chart in dashboard_config.chart_widgets:
                # Generate sample chart data (in real implementation, this would calculate from actual data)
                chart_data = self._generate_chart_data(chart.chart_type, data_analysis)
                
                metric = DashboardMetric(
                    metric_id=uuid.uuid4(),  # Generate UUID for metric_id
                    client_id=client_id,
                    metric_name=chart.data_source,
                    metric_value={
                        'data': chart_data,
                        'chart_type': chart.chart_type.value,  # Convert enum to string
                        'title': chart.title
                    },
                    metric_type='chart_data',
                    calculated_at=datetime.now()
                )
                
                # Convert to dict with UUID handling
                metric_dict = self._convert_uuids_to_strings(metric.dict())
                
                # Save metric
                db_client.table('client_dashboard_metrics').insert(metric_dict).execute()
                metrics_generated += 1
            
            return metrics_generated
            
        except Exception as e:
            logger.error(f"❌ Failed to generate and save metrics: {e}")
            return 0
    
    def _generate_chart_data(self, chart_type: ChartType, data_analysis: Dict[str, Any]) -> List[Dict]:
        """Generate sample chart data based on chart type"""
        if chart_type == ChartType.LINE:
            return [
                {'month': 'Jan', 'value': 45000},
                {'month': 'Feb', 'value': 52000},
                {'month': 'Mar', 'value': 48000},
                {'month': 'Apr', 'value': 61000},
                {'month': 'May', 'value': 55000},
                {'month': 'Jun', 'value': 67000}
            ]
        elif chart_type == ChartType.BAR:
            return [
                {'category': 'Category A', 'value': 25000},
                {'category': 'Category B', 'value': 15000},
                {'category': 'Category C', 'value': 12000},
                {'category': 'Category D', 'value': 18000}
            ]
        elif chart_type == ChartType.PIE:
            return [
                {'label': 'Segment 1', 'value': 40},
                {'label': 'Segment 2', 'value': 30},
                {'label': 'Segment 3', 'value': 20},
                {'label': 'Segment 4', 'value': 10}
            ]
        else:
            return []
    
    # Helper methods
    def _find_column(self, columns: List[str], search_terms: List[str]) -> Optional[str]:
        """Find column matching search terms"""
        for column in columns:
            for term in search_terms:
                if term.lower() in column.lower():
                    return column
        return None
    
    def _detect_date_columns(self, df: pd.DataFrame) -> List[str]:
        """Detect date columns in DataFrame"""
        date_columns = []
        for col in df.columns:
            if df[col].dtype == 'datetime64[ns]' or 'date' in col.lower():
                date_columns.append(col)
        return date_columns
    
    def _calculate_data_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate data quality score"""
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        return max(0, 1 - (missing_cells / total_cells))
    
    def _detect_data_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect patterns in data"""
        patterns = {
            'has_time_series': len(self._detect_date_columns(df)) > 0,
            'has_categorical': len(df.select_dtypes(include=['object']).columns) > 0,
            'has_numeric': len(df.select_dtypes(include=[np.number]).columns) > 0,
            'row_count': len(df),
            'column_count': len(df.columns)
        }
        return patterns
    
    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in data"""
        trends = {}
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if len(df[col].dropna()) > 1:
                # Simple trend analysis
                values = df[col].dropna().values
                if len(values) >= 2:
                    trend = 'increasing' if values[-1] > values[0] else 'decreasing'
                    trends[col] = {
                        'direction': trend,
                        'change': float(values[-1] - values[0]),
                        'percent_change': float((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
                    }
        
        return trends
    
    def _extract_data_characteristics(self, data_analysis: Dict[str, Any]) -> List[str]:
        """Extract data characteristics"""
        characteristics = []
        
        if data_analysis['patterns']['has_time_series']:
            characteristics.append('Time Series Data')
        if data_analysis['patterns']['has_categorical']:
            characteristics.append('Categorical Data')
        if data_analysis['patterns']['has_numeric']:
            characteristics.append('Numerical Data')
        if data_analysis['data_quality_score'] > 0.9:
            characteristics.append('High Quality Data')
        
        return characteristics
    
    def _extract_key_metrics(self, columns: List[str]) -> List[str]:
        """Extract key metrics from column names"""
        metrics = []
        metric_keywords = ['revenue', 'sales', 'profit', 'cost', 'price', 'amount', 'total', 'count', 'rate', 'percentage']
        
        for col in columns:
            for keyword in metric_keywords:
                if keyword in col.lower():
                    metrics.append(col)
                    break
        
        return metrics[:6]  # Limit to 6 key metrics
    
    def _create_sample_analysis(self, client_id: uuid.UUID) -> Dict[str, Any]:
        """Create sample analysis for clients without data"""
        return {
            'total_records': 0,
            'columns': ['revenue', 'date', 'category', 'amount'],
            'column_types': {'revenue': 'float64', 'date': 'datetime64[ns]', 'category': 'object', 'amount': 'float64'},
            'numeric_columns': ['revenue', 'amount'],
            'categorical_columns': ['category'],
            'date_columns': ['date'],
            'missing_values': {},
            'unique_values': {},
            'sample_data': [],
            'data_quality_score': 0.8,
            'patterns': {'has_time_series': True, 'has_categorical': True, 'has_numeric': True},
            'trends': {}
        }
    
    def _create_default_business_context(self, data_analysis: Dict[str, Any]) -> BusinessContext:
        """Create default business context"""
        return BusinessContext(
            industry='General',
            business_type='general',
            data_characteristics=['Mixed Data Types'],
            key_metrics=['Revenue', 'Growth', 'Performance'],
            recommended_charts=[ChartType.BAR, ChartType.LINE, ChartType.PIE],
            insights=[],
            confidence_score=0.5
        )
    
    async def _get_existing_dashboard(self, client_id: uuid.UUID) -> Optional[DashboardConfig]:
        """Get existing dashboard configuration"""
        try:
            db_client = get_admin_client()
            if not db_client:
                return None
            
            response = db_client.table('client_dashboard_configs').select('*').eq('client_id', str(client_id)).execute()
            
            if response.data:
                config_data = response.data[0]['dashboard_config']
                return DashboardConfig(**config_data)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get existing dashboard: {e}")
            return None
    
    async def process_pending_retries(self) -> List[GenerationResult]:
        """Process all pending dashboard generation retries"""
        results = []
        
        try:
            db_client = get_admin_client()
            if not db_client:
                return results
            
            # Get pending retries using the database function
            response = db_client.rpc('get_pending_dashboard_retries').execute()
            
            if not response.data:
                return results
            
            logger.info(f"🔄 Processing {len(response.data)} pending dashboard retries")
            
            for retry_data in response.data:
                client_id = uuid.UUID(retry_data['client_id'])
                generation_id = uuid.UUID(retry_data['generation_id'])
                attempt_count = retry_data['attempt_count'] + 1
                
                logger.info(f"🔄 Retrying dashboard generation for client {client_id} (attempt {attempt_count})")
                
                try:
                    # Update status to processing
                    await self._update_generation_tracking(generation_id, GenerationStatus.PROCESSING, attempt_count)
                    
                    # Attempt generation
                    result = await self._attempt_dashboard_generation(client_id, generation_id, attempt_count)
                    
                    if result.success:
                        await self._update_generation_tracking(generation_id, GenerationStatus.COMPLETED)
                        logger.info(f"✅ Retry successful for client {client_id}")
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"❌ Retry failed for client {client_id}: {e}")
                    
                    # Classify error and determine next action
                    error_type = self._classify_error(e)
                    retry_info = self._calculate_retry_info(attempt_count, error_type)
                    
                    if retry_info.should_retry:
                        next_retry_time = datetime.now() + timedelta(seconds=retry_info.retry_delay_seconds)
                        await self._update_generation_tracking(
                            generation_id, 
                            GenerationStatus.RETRYING, 
                            attempt_count, 
                            error_type, 
                            str(e), 
                            next_retry_time
                        )
                        logger.warning(f"🔄 Will retry again for client {client_id} in {retry_info.retry_delay_seconds//60} minutes")
                    else:
                        await self._update_generation_tracking(
                            generation_id, 
                            GenerationStatus.FAILED, 
                            attempt_count, 
                            error_type, 
                            str(e)
                        )
                        logger.error(f"❌ Giving up on client {client_id}: {retry_info.reason}")
                    
                    results.append(GenerationResult(
                        success=False,
                        client_id=client_id,
                        generation_id=generation_id,
                        error_type=error_type,
                        error_message=str(e),
                        retry_info=retry_info,
                        generation_time=0,
                        attempt_number=attempt_count
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to process pending retries: {e}")
            return results

# Create global instance
dashboard_orchestrator = DashboardOrchestrator() 