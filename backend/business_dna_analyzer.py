import json
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from collections import Counter
import re
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class BusinessModel(Enum):
    B2B_SAAS = "b2b_saas"
    B2C_ECOMMERCE = "b2c_ecommerce"
    MARKETPLACE = "marketplace"
    SUBSCRIPTION = "subscription"
    FREEMIUM = "freemium"
    MANUFACTURING = "manufacturing"
    SERVICES = "services"
    RETAIL = "retail"
    FINANCIAL_SERVICES = "financial_services"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    MEDIA = "media"
    NONPROFIT = "nonprofit"
    CONSULTING = "consulting"
    AGENCY = "agency"

class BusinessMaturity(Enum):
    STARTUP = "startup"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"
    MATURE = "mature"

class DataSophistication(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class BusinessProcessFlow:
    name: str
    stages: List[str]
    key_metrics: List[str]
    data_sources: List[str]
    business_logic: Dict[str, Any]

@dataclass
class BusinessDNA:
    business_model: BusinessModel
    industry_sector: str
    maturity_level: BusinessMaturity
    data_sophistication: DataSophistication
    primary_workflows: List[BusinessProcessFlow]
    success_metrics: List[str]
    key_relationships: Dict[str, List[str]]
    business_personality: Dict[str, Any]
    unique_characteristics: List[str]
    data_story: str
    confidence_score: float

class BusinessDNAAnalyzer:
    """Deep business intelligence analyzer that discovers unique business patterns and DNA"""
    
    def __init__(self):
        self.workflow_patterns = self._initialize_workflow_patterns()
        self.business_indicators = self._initialize_business_indicators()
        self.success_metric_patterns = self._initialize_success_metrics()
        
    def _initialize_workflow_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize common business workflow patterns"""
        return {
            "customer_acquisition": {
                "indicators": ["lead", "prospect", "signup", "registration", "trial", "demo"],
                "stages": ["Lead Generation", "Qualification", "Demo/Trial", "Conversion"],
                "metrics": ["conversion_rate", "cost_per_lead", "lead_quality_score"]
            },
            "subscription_lifecycle": {
                "indicators": ["subscription", "plan", "upgrade", "downgrade", "churn", "renewal"],
                "stages": ["Trial", "Onboarding", "Active", "At-Risk", "Renewal/Churn"],
                "metrics": ["mrr", "churn_rate", "ltv", "upgrade_rate"]
            },
            "inventory_management": {
                "indicators": ["stock", "inventory", "sku", "warehouse", "supplier", "reorder"],
                "stages": ["Procurement", "Storage", "Distribution", "Reorder"],
                "metrics": ["turnover_rate", "stock_levels", "carrying_costs"]
            },
            "sales_process": {
                "indicators": ["opportunity", "pipeline", "deal", "quota", "territory", "commission"],
                "stages": ["Prospecting", "Qualification", "Proposal", "Negotiation", "Close"],
                "metrics": ["win_rate", "sales_velocity", "quota_attainment"]
            },
            "customer_success": {
                "indicators": ["onboarding", "adoption", "health_score", "support", "satisfaction"],
                "stages": ["Onboarding", "Adoption", "Growth", "Advocacy"],
                "metrics": ["health_score", "product_adoption", "satisfaction_score"]
            },
            "financial_operations": {
                "indicators": ["revenue", "expense", "profit", "cash_flow", "budget", "forecast"],
                "stages": ["Planning", "Execution", "Monitoring", "Analysis"],
                "metrics": ["gross_margin", "operating_margin", "cash_flow"]
            },
            "product_development": {
                "indicators": ["feature", "release", "backlog", "sprint", "bug", "enhancement"],
                "stages": ["Planning", "Development", "Testing", "Release"],
                "metrics": ["velocity", "quality_score", "time_to_market"]
            },
            "marketing_campaigns": {
                "indicators": ["campaign", "channel", "attribution", "impression", "click", "conversion"],
                "stages": ["Planning", "Execution", "Optimization", "Analysis"],
                "metrics": ["roi", "cac", "roas", "attribution"]
            }
        }
    
    def _initialize_business_indicators(self) -> Dict[BusinessModel, Dict[str, Any]]:
        """Initialize business model indicators"""
        return {
            BusinessModel.B2B_SAAS: {
                "column_patterns": ["mrr", "arr", "churn", "ltv", "user", "subscription", "plan", "feature"],
                "relationships": ["user->subscription", "subscription->revenue", "feature->adoption"],
                "success_metrics": ["mrr_growth", "churn_rate", "expansion_revenue", "user_adoption"]
            },
            BusinessModel.B2C_ECOMMERCE: {
                "column_patterns": ["product", "order", "cart", "customer", "inventory", "shipping"],
                "relationships": ["customer->order", "order->product", "product->inventory"],
                "success_metrics": ["revenue", "conversion_rate", "aov", "repeat_purchase_rate"]
            },
            BusinessModel.MARKETPLACE: {
                "column_patterns": ["seller", "buyer", "transaction", "commission", "listing", "rating"],
                "relationships": ["seller->listing", "buyer->transaction", "transaction->commission"],
                "success_metrics": ["gmv", "take_rate", "active_sellers", "transaction_volume"]
            },
            BusinessModel.MANUFACTURING: {
                "column_patterns": ["production", "quality", "waste", "efficiency", "capacity", "downtime"],
                "relationships": ["production->quality", "capacity->efficiency", "raw_material->finished_goods"],
                "success_metrics": ["oee", "yield", "cycle_time", "defect_rate"]
            },
            BusinessModel.SERVICES: {
                "column_patterns": ["project", "client", "billable", "utilization", "resource", "delivery"],
                "relationships": ["client->project", "resource->utilization", "project->revenue"],
                "success_metrics": ["utilization_rate", "project_margin", "client_satisfaction"]
            }
        }
    
    def _initialize_success_metrics(self) -> Dict[str, List[str]]:
        """Initialize success metric patterns"""
        return {
            "revenue": ["revenue", "sales", "income", "earnings", "proceeds"],
            "growth": ["growth", "increase", "expansion", "scaling", "acceleration"],
            "efficiency": ["efficiency", "productivity", "optimization", "performance", "utilization"],
            "quality": ["quality", "satisfaction", "rating", "score", "feedback"],
            "cost": ["cost", "expense", "spend", "investment", "budget"],
            "engagement": ["engagement", "adoption", "usage", "activity", "interaction"],
            "retention": ["retention", "churn", "loyalty", "renewal", "lifetime"]
        }
    
    async def analyze_business_dna(self, client_id: str, data_analysis: Dict[str, Any]) -> BusinessDNA:
        """Perform comprehensive business DNA analysis"""
        try:
            logger.info(f"🧬 Starting comprehensive business DNA analysis for client {client_id}")
            
            # Extract data characteristics
            columns = data_analysis.get('columns', [])
            sample_data = data_analysis.get('sample_data', [])
            numeric_columns = data_analysis.get('numeric_columns', [])
            categorical_columns = data_analysis.get('categorical_columns', [])
            patterns = data_analysis.get('patterns', {})
            
            # Analyze business model
            business_model = await self._detect_business_model(columns, sample_data)
            
            # Analyze industry sector
            industry_sector = await self._detect_industry_sector(columns, sample_data)
            
            # Analyze maturity level
            maturity_level = await self._detect_maturity_level(data_analysis)
            
            # Analyze data sophistication
            data_sophistication = await self._analyze_data_sophistication(data_analysis)
            
            # Discover workflows
            workflows = await self._discover_business_workflows(columns, sample_data)
            
            # Identify success metrics
            success_metrics = await self._identify_success_metrics(columns, numeric_columns)
            
            # Map key relationships
            key_relationships = await self._map_key_relationships(columns, sample_data)
            
            # Analyze business personality
            business_personality = await self._analyze_business_personality(data_analysis)
            
            # Extract unique characteristics
            unique_characteristics = await self._extract_unique_characteristics(data_analysis)
            
            # Generate data story
            data_story = await self._generate_data_story(data_analysis, workflows, success_metrics)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(data_analysis, workflows)
            
            dna = BusinessDNA(
                business_model=business_model,
                industry_sector=industry_sector,
                maturity_level=maturity_level,
                data_sophistication=data_sophistication,
                primary_workflows=workflows,
                success_metrics=success_metrics,
                key_relationships=key_relationships,
                business_personality=business_personality,
                unique_characteristics=unique_characteristics,
                data_story=data_story,
                confidence_score=confidence_score
            )
            
            logger.info(f"🧬 Business DNA analysis complete: {business_model.value} | {industry_sector} | Confidence: {confidence_score:.2f}")
            return dna
            
        except Exception as e:
            logger.error(f"❌ Business DNA analysis failed: {e}")
            # Return basic DNA as fallback
            return self._create_fallback_dna(data_analysis)
    
    async def _detect_business_model(self, columns: List[str], sample_data: List[Dict]) -> BusinessModel:
        """Detect business model from data patterns"""
        column_text = ' '.join(columns).lower()
        
        # B2B SaaS indicators
        if any(indicator in column_text for indicator in ['mrr', 'arr', 'churn', 'subscription', 'plan', 'user', 'trial']):
            return BusinessModel.B2B_SAAS
        
        # E-commerce indicators
        if any(indicator in column_text for indicator in ['product', 'order', 'cart', 'inventory', 'shipping', 'customer']):
            return BusinessModel.B2C_ECOMMERCE
        
        # Marketplace indicators
        if any(indicator in column_text for indicator in ['seller', 'buyer', 'commission', 'listing', 'rating', 'marketplace']):
            return BusinessModel.MARKETPLACE
        
        # Manufacturing indicators
        if any(indicator in column_text for indicator in ['production', 'quality', 'waste', 'efficiency', 'capacity', 'manufacturing']):
            return BusinessModel.MANUFACTURING
        
        # Services indicators
        if any(indicator in column_text for indicator in ['project', 'client', 'billable', 'utilization', 'consulting', 'service']):
            return BusinessModel.SERVICES
        
        # Financial services indicators
        if any(indicator in column_text for indicator in ['account', 'transaction', 'balance', 'loan', 'credit', 'portfolio']):
            return BusinessModel.FINANCIAL_SERVICES
        
        # Default to services for unclassified
        return BusinessModel.SERVICES
    
    async def _detect_industry_sector(self, columns: List[str], sample_data: List[Dict]) -> str:
        """Detect industry sector from data characteristics"""
        column_text = ' '.join(columns).lower()
        
        industry_indicators = {
            "Technology": ["user", "feature", "api", "software", "platform", "cloud", "analytics"],
            "Retail": ["product", "inventory", "sku", "store", "customer", "sales", "merchandise"],
            "Financial Services": ["account", "transaction", "portfolio", "investment", "loan", "credit", "banking"],
            "Healthcare": ["patient", "treatment", "medical", "diagnosis", "prescription", "clinical"],
            "Education": ["student", "course", "enrollment", "grade", "curriculum", "learning"],
            "Manufacturing": ["production", "quality", "assembly", "materials", "factory", "manufacturing"],
            "Media": ["content", "audience", "engagement", "views", "subscribers", "publishing"],
            "Real Estate": ["property", "listing", "rent", "lease", "tenant", "mortgage"],
            "Transportation": ["route", "delivery", "vehicle", "logistics", "shipping", "fleet"],
            "Hospitality": ["guest", "booking", "reservation", "room", "hotel", "restaurant"]
        }
        
        for industry, indicators in industry_indicators.items():
            if sum(1 for indicator in indicators if indicator in column_text) >= 2:
                return industry
        
        return "Technology"  # Default
    
    async def _detect_maturity_level(self, data_analysis: Dict[str, Any]) -> BusinessMaturity:
        """Detect business maturity level from data sophistication"""
        total_records = data_analysis.get('total_records', 0)
        column_count = len(data_analysis.get('columns', []))
        data_quality = data_analysis.get('data_quality_score', 0)
        
        # Maturity scoring
        maturity_score = 0
        
        if total_records > 10000:
            maturity_score += 3
        elif total_records > 1000:
            maturity_score += 2
        elif total_records > 100:
            maturity_score += 1
        
        if column_count > 20:
            maturity_score += 3
        elif column_count > 10:
            maturity_score += 2
        elif column_count > 5:
            maturity_score += 1
        
        if data_quality > 0.9:
            maturity_score += 2
        elif data_quality > 0.7:
            maturity_score += 1
        
        if maturity_score >= 7:
            return BusinessMaturity.ENTERPRISE
        elif maturity_score >= 5:
            return BusinessMaturity.MATURE
        elif maturity_score >= 3:
            return BusinessMaturity.GROWTH
        else:
            return BusinessMaturity.STARTUP
    
    async def _analyze_data_sophistication(self, data_analysis: Dict[str, Any]) -> DataSophistication:
        """Analyze data sophistication level"""
        numeric_columns = len(data_analysis.get('numeric_columns', []))
        date_columns = len(data_analysis.get('date_columns', []))
        patterns = data_analysis.get('patterns', {})
        
        sophistication_score = 0
        
        # Complex data types
        if numeric_columns > 10:
            sophistication_score += 3
        elif numeric_columns > 5:
            sophistication_score += 2
        elif numeric_columns > 2:
            sophistication_score += 1
        
        # Time series data
        if date_columns > 0 and patterns.get('has_time_series'):
            sophistication_score += 2
        
        # Data relationships
        if patterns.get('has_categorical') and patterns.get('has_numeric'):
            sophistication_score += 1
        
        if sophistication_score >= 6:
            return DataSophistication.EXPERT
        elif sophistication_score >= 4:
            return DataSophistication.ADVANCED
        elif sophistication_score >= 2:
            return DataSophistication.INTERMEDIATE
        else:
            return DataSophistication.BASIC
    
    async def _discover_business_workflows(self, columns: List[str], sample_data: List[Dict]) -> List[BusinessProcessFlow]:
        """Discover business workflows from data patterns"""
        discovered_workflows = []
        column_text = ' '.join(columns).lower()
        
        for workflow_name, workflow_config in self.workflow_patterns.items():
            indicators = workflow_config['indicators']
            stages = workflow_config['stages']
            metrics = workflow_config['metrics']
            
            # Check if this workflow exists in the data
            indicator_matches = sum(1 for indicator in indicators if indicator in column_text)
            
            if indicator_matches >= 2:  # At least 2 indicators present
                # Find relevant columns for this workflow
                relevant_columns = [col for col in columns if any(indicator in col.lower() for indicator in indicators)]
                
                # Create workflow
                workflow = BusinessProcessFlow(
                    name=workflow_name.replace('_', ' ').title(),
                    stages=stages,
                    key_metrics=metrics,
                    data_sources=relevant_columns,
                    business_logic={
                        "indicators_found": indicator_matches,
                        "total_indicators": len(indicators),
                        "confidence": indicator_matches / len(indicators)
                    }
                )
                discovered_workflows.append(workflow)
        
        # Sort by confidence
        discovered_workflows.sort(key=lambda w: w.business_logic['confidence'], reverse=True)
        
        return discovered_workflows[:5]  # Return top 5 workflows
    
    async def _identify_success_metrics(self, columns: List[str], numeric_columns: List[str]) -> List[str]:
        """Identify key success metrics from data"""
        success_metrics = []
        
        for metric_category, patterns in self.success_metric_patterns.items():
            for column in numeric_columns:
                if any(pattern in column.lower() for pattern in patterns):
                    success_metrics.append(column)
                    break
        
        # Add any obviously important numeric columns
        priority_patterns = ['revenue', 'profit', 'growth', 'conversion', 'retention', 'satisfaction']
        for column in numeric_columns:
            if any(pattern in column.lower() for pattern in priority_patterns):
                if column not in success_metrics:
                    success_metrics.append(column)
        
        return success_metrics[:8]  # Return top 8 metrics
    
    async def _map_key_relationships(self, columns: List[str], sample_data: List[Dict]) -> Dict[str, List[str]]:
        """Map key data relationships"""
        relationships = {}
        
        # Common relationship patterns
        relationship_patterns = {
            "customer": ["order", "purchase", "transaction", "account", "subscription"],
            "product": ["inventory", "sales", "revenue", "category", "supplier"],
            "user": ["session", "engagement", "feature", "plan", "subscription"],
            "order": ["item", "payment", "shipping", "customer", "product"],
            "campaign": ["lead", "conversion", "cost", "revenue", "channel"]
        }
        
        for primary_entity, related_entities in relationship_patterns.items():
            primary_cols = [col for col in columns if primary_entity in col.lower()]
            related_cols = [col for col in columns if any(entity in col.lower() for entity in related_entities)]
            
            if primary_cols and related_cols:
                relationships[primary_entity] = related_cols[:5]  # Limit to 5 relationships
        
        return relationships
    
    async def _analyze_business_personality(self, data_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze business personality from data characteristics"""
        personality = {
            "data_driven": len(data_analysis.get('numeric_columns', [])) > 10,
            "customer_focused": any('customer' in col.lower() for col in data_analysis.get('columns', [])),
            "growth_oriented": any('growth' in col.lower() for col in data_analysis.get('columns', [])),
            "operational_focused": any(op in ' '.join(data_analysis.get('columns', [])).lower() 
                                    for op in ['efficiency', 'process', 'operation', 'performance']),
            "financial_focused": any(fin in ' '.join(data_analysis.get('columns', [])).lower() 
                                   for fin in ['revenue', 'profit', 'cost', 'budget', 'financial']),
            "innovation_focused": any(inn in ' '.join(data_analysis.get('columns', [])).lower() 
                                    for inn in ['feature', 'product', 'development', 'innovation']),
            "complexity_level": "high" if len(data_analysis.get('columns', [])) > 15 else "medium" if len(data_analysis.get('columns', [])) > 8 else "low"
        }
        
        return personality
    
    async def _extract_unique_characteristics(self, data_analysis: Dict[str, Any]) -> List[str]:
        """Extract unique business characteristics"""
        characteristics = []
        columns = data_analysis.get('columns', [])
        column_text = ' '.join(columns).lower()
        
        # Detect unique patterns
        unique_patterns = {
            "Multi-tenant SaaS": ["tenant", "organization", "workspace", "account"],
            "Subscription-based": ["subscription", "plan", "billing", "renewal"],
            "Marketplace model": ["seller", "buyer", "commission", "listing"],
            "B2B focused": ["account", "deal", "lead", "opportunity"],
            "Mobile-first": ["app", "mobile", "device", "notification"],
            "International": ["country", "currency", "timezone", "locale"],
            "Seasonal business": ["season", "holiday", "peak", "cycle"],
            "Enterprise sales": ["enterprise", "contract", "negotiation", "proposal"]
        }
        
        for characteristic, indicators in unique_patterns.items():
            if sum(1 for indicator in indicators if indicator in column_text) >= 2:
                characteristics.append(characteristic)
        
        return characteristics
    
    async def _generate_data_story(self, data_analysis: Dict[str, Any], workflows: List[BusinessProcessFlow], success_metrics: List[str]) -> str:
        """Generate a narrative data story"""
        total_records = data_analysis.get('total_records', 0)
        column_count = len(data_analysis.get('columns', []))
        primary_workflow = workflows[0].name if workflows else "Business Operations"
        top_metric = success_metrics[0] if success_metrics else "Performance"
        
        story = f"This business operates with {total_records:,} data points across {column_count} key dimensions. "
        story += f"The primary focus appears to be {primary_workflow}, with {top_metric} as a key success indicator. "
        
        if len(workflows) > 1:
            story += f"Secondary processes include {', '.join([w.name for w in workflows[1:3]])}. "
        
        if data_analysis.get('data_quality_score', 0) > 0.8:
            story += "The data quality is high, indicating mature data practices and reliable analytics foundation."
        else:
            story += "There are opportunities to improve data quality and standardization for better insights."
        
        return story
    
    def _calculate_confidence_score(self, data_analysis: Dict[str, Any], workflows: List[BusinessProcessFlow]) -> float:
        """Calculate confidence score for the analysis"""
        score = 0.0
        
        # Data completeness
        data_quality = data_analysis.get('data_quality_score', 0)
        score += data_quality * 0.3
        
        # Workflow discovery confidence
        if workflows:
            avg_workflow_confidence = sum(w.business_logic.get('confidence', 0) for w in workflows) / len(workflows)
            score += avg_workflow_confidence * 0.4
        
        # Data richness
        column_count = len(data_analysis.get('columns', []))
        numeric_count = len(data_analysis.get('numeric_columns', []))
        
        richness_score = min(1.0, (column_count / 20) * 0.7 + (numeric_count / 10) * 0.3)
        score += richness_score * 0.3
        
        return min(1.0, score)
    
    def _create_fallback_dna(self, data_analysis: Dict[str, Any]) -> BusinessDNA:
        """Create basic DNA when analysis fails"""
        return BusinessDNA(
            business_model=BusinessModel.SERVICES,
            industry_sector="Technology",
            maturity_level=BusinessMaturity.GROWTH,
            data_sophistication=DataSophistication.INTERMEDIATE,
            primary_workflows=[],
            success_metrics=data_analysis.get('numeric_columns', [])[:5],
            key_relationships={},
            business_personality={"data_driven": True},
            unique_characteristics=["Custom Business Model"],
            data_story="Business with custom data patterns requiring tailored analytics approach.",
            confidence_score=0.5
        ) 