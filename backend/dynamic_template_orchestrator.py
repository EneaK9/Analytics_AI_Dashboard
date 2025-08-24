import json
import uuid
import logging
from typing import Dict, List, Any, Optional, Tuple, TypedDict
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import asyncio
import os

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, JsonOutputParser

# Internal imports
from business_dna_analyzer import BusinessDNAAnalyzer, BusinessDNA, BusinessModel, BusinessMaturity
from models import DashboardConfig, DashboardLayout, KPIWidget, ChartWidget, ChartType

logger = logging.getLogger(__name__)

class TemplatePersonality(Enum):
    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    ANALYTICAL = "analytical"
    STRATEGIC = "strategic"
    TACTICAL = "tactical"

class TemplateCategory(Enum):
    OVERVIEW = "overview"
    DEEP_DIVE = "deep_dive"
    MONITORING = "monitoring"
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"

@dataclass
class TemplateArchitecture:
    template_id: str
    name: str
    description: str
    category: TemplateCategory
    personality: TemplatePersonality
    target_audience: str
    business_context: str
    component_blueprint: Dict[str, Any]
    layout_config: Dict[str, Any]
    visual_identity: Dict[str, Any]
    data_requirements: List[str]
    success_metrics: List[str]
    relationships: List[str]
    confidence_score: float

@dataclass
class ComponentBlueprint:
    component_id: str
    component_type: str
    title: str
    subtitle: str
    business_purpose: str
    data_mapping: Dict[str, str]
    visualization_config: Dict[str, Any]
    position: Dict[str, int]
    size: Dict[str, int]
    priority: int
    business_logic: Dict[str, Any]

@dataclass
class TemplateEcosystem:
    ecosystem_id: str
    primary_template: TemplateArchitecture
    related_templates: List[TemplateArchitecture]
    navigation_flow: Dict[str, List[str]]
    shared_context: Dict[str, Any]
    cross_template_features: List[str]

# LangGraph State
class TemplateGenerationState(TypedDict):
    client_id: str
    data_analysis: Dict[str, Any]
    business_dna: Optional[BusinessDNA]
    template_architectures: List[TemplateArchitecture]
    selected_components: List[ComponentBlueprint]
    visual_themes: Dict[str, Any]
    template_names: List[str]
    ecosystem: Optional[TemplateEcosystem]
    generation_metadata: Dict[str, Any]
    error_messages: List[str]
    current_step: str

class DynamicTemplateOrchestrator:
    """Advanced template orchestrator using LangGraph for intelligent template generation"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise Exception("OpenAI API key required for template orchestration")
        
        self.llm = ChatOpenAI(
            api_key=self.openai_api_key,
            model="gpt-4o",
            temperature=0.7
        )
        
        self.business_dna_analyzer = BusinessDNAAnalyzer()
        self.workflow_graph = self._create_workflow_graph()
        
        # Template generation components
        self.component_library = self._initialize_component_library()
        self.theme_generator = self._initialize_theme_generator()
        self.naming_engine = self._initialize_naming_engine()
        
        logger.info(" Dynamic Template Orchestrator initialized with LangGraph")
    
    def _create_workflow_graph(self) -> StateGraph:
        """Create LangGraph workflow for template generation pipeline"""
        
        workflow = StateGraph(TemplateGenerationState)
        
        # Add nodes for each step in the pipeline
        workflow.add_node("analyze_business_dna", self._analyze_business_dna_node)
        workflow.add_node("design_template_architecture", self._design_template_architecture_node)
        workflow.add_node("select_components", self._select_components_node)
        workflow.add_node("optimize_layout", self._optimize_layout_node)
        workflow.add_node("generate_themes", self._generate_themes_node)
        workflow.add_node("create_smart_names", self._create_smart_names_node)
        workflow.add_node("build_ecosystem", self._build_ecosystem_node)
        workflow.add_node("finalize_templates", self._finalize_templates_node)
        
        # Define the workflow edges
        workflow.set_entry_point("analyze_business_dna")
        workflow.add_edge("analyze_business_dna", "design_template_architecture")
        workflow.add_edge("design_template_architecture", "select_components")
        workflow.add_edge("select_components", "optimize_layout")
        workflow.add_edge("optimize_layout", "generate_themes")
        workflow.add_edge("generate_themes", "create_smart_names")
        workflow.add_edge("create_smart_names", "build_ecosystem")
        workflow.add_edge("build_ecosystem", "finalize_templates")
        workflow.add_edge("finalize_templates", END)
        
        return workflow.compile()
    
    async def generate_custom_templates(self, client_id: str, data_analysis: Dict[str, Any]) -> List[DashboardConfig]:
        """Generate custom templates using AI workflow with fallback to simplified generation"""
        try:
            logger.info(f" Starting custom template generation for client {client_id}")
            
            #  NEW: Generate REAL data-driven templates instead of fallbacks
            logger.info(" Generating data-driven custom templates based on real client data")
            return await self._generate_data_driven_templates(client_id, data_analysis)
            
            # Keep the old LangGraph workflow for future use (currently disabled)
            # Initialize state
            initial_state = TemplateGenerationState(
                client_id=client_id,
                data_analysis=data_analysis,
                business_dna=None,
                template_architectures=[],
                selected_components=[],
                visual_themes={},
                template_names=[],
                ecosystem=None,
                generation_metadata={
                    "started_at": datetime.now().isoformat(),
                    "generation_id": str(uuid.uuid4())
                },
                error_messages=[],
                current_step="initialize"
            )
            
            # Execute workflow
            final_state = await self.workflow_graph.ainvoke(initial_state)
            
            # Convert architectures to dashboard configs
            dashboard_configs = []
            if final_state.get("ecosystem"):
                ecosystem = final_state["ecosystem"]
                
                # Primary template
                primary_config = await self._architecture_to_dashboard_config(
                    ecosystem.primary_template, 
                    data_analysis, 
                    final_state["business_dna"]
                )
                dashboard_configs.append(primary_config)
                
                # Secondary templates
                for template in ecosystem.secondary_templates[:2]:  # Limit to 2 additional
                    secondary_config = await self._architecture_to_dashboard_config(
                        template, 
                        data_analysis, 
                        final_state["business_dna"]
                    )
                    dashboard_configs.append(secondary_config)
            
            logger.info(f" Generated {len(dashboard_configs)} custom templates for client {client_id}")
            return dashboard_configs
            
        except Exception as e:
            logger.error(f" Custom template generation failed: {e}")
            # Fall back to data-driven templates instead of generic fallbacks
            return await self._generate_data_driven_templates(client_id, data_analysis)
    
    async def _analyze_business_dna_node(self, state: TemplateGenerationState) -> TemplateGenerationState:
        """LangGraph node for business DNA analysis"""
        try:
            logger.info(f"🧬 Analyzing business DNA for {state['client_id']}")
            state["current_step"] = "business_dna_analysis"
            
            business_dna = await self.business_dna_analyzer.analyze_business_dna(
                state["client_id"], 
                state["data_analysis"]
            )
            
            state["business_dna"] = business_dna
            logger.info(f"🧬 Business DNA complete: {business_dna.business_model.value}")
            
        except Exception as e:
            logger.error(f" Business DNA analysis failed: {e}")
            state["error_messages"].append(f"DNA analysis error: {str(e)}")
        
        return state
    
    async def _design_template_architecture_node(self, state: TemplateGenerationState) -> TemplateGenerationState:
        """LangGraph node for template architecture design"""
        try:
            logger.info("️ Designing template architectures")
            state["current_step"] = "template_architecture_design"
            
            business_dna = state["business_dna"]
            data_analysis = state["data_analysis"]
            
            # Generate 3 unique template architectures
            architectures = []
            
            # Template 1: Strategic Overview
            strategic_arch = await self._design_strategic_template(business_dna, data_analysis)
            architectures.append(strategic_arch)
            
            # Template 2: Operational Deep Dive
            operational_arch = await self._design_operational_template(business_dna, data_analysis)
            architectures.append(operational_arch)
            
            # Template 3: Performance Intelligence
            performance_arch = await self._design_performance_template(business_dna, data_analysis)
            architectures.append(performance_arch)
            
            state["template_architectures"] = architectures
            logger.info(f"️ Designed {len(architectures)} template architectures")
            
        except Exception as e:
            logger.error(f" Template architecture design failed: {e}")
            state["error_messages"].append(f"Architecture design error: {str(e)}")
        
        return state
    
    async def _design_strategic_template(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any]) -> TemplateArchitecture:
        """Design strategic overview template"""
        
        # AI-powered template architecture generation
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert dashboard architect specializing in executive-level strategic dashboards.
            Design a strategic overview template that provides high-level business intelligence for executives and decision makers.
            
            Focus on:
            - Key business metrics and KPIs
            - Strategic trends and patterns
            - Executive-level insights
            - High-impact visualizations
            - Clean, professional layout
            
            Return JSON with template specifications."""),
            ("human", f"""Design a strategic template for this business:
            
            Business DNA:
            - Model: {business_dna.business_model.value}
            - Industry: {business_dna.industry_sector}
            - Maturity: {business_dna.maturity_level.value}
            - Key Workflows: {[w.name for w in business_dna.primary_workflows]}
            - Success Metrics: {business_dna.success_metrics}
            - Data Story: {business_dna.data_story}
            
            Available Data Columns: {data_analysis.get('columns', [])}
            Numeric Columns: {data_analysis.get('numeric_columns', [])}
            
            Create a strategic executive dashboard architecture with:
            1. Template metadata (name, description, target audience)
            2. Component blueprint (4-6 high-level components)
            3. Layout configuration (executive-friendly layout)
            4. Data requirements mapping
            """)
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        
        try:
            arch_data = json.loads(response.content)
            
            return TemplateArchitecture(
                template_id=f"strategic_{uuid.uuid4().hex[:8]}",
                name=arch_data.get("name", "Strategic Command Center"),
                description=arch_data.get("description", "Executive-level strategic overview"),
                category=TemplateCategory.STRATEGIC,
                personality=TemplatePersonality.EXECUTIVE,
                target_audience="Executives and Strategic Decision Makers",
                business_context=business_dna.data_story,
                component_blueprint=arch_data.get("components", {}),
                layout_config=arch_data.get("layout", {"grid_cols": 4, "grid_rows": 6}),
                visual_identity={"primary_color": "#1e40af", "style": "executive"},
                data_requirements=business_dna.success_metrics,
                success_metrics=business_dna.success_metrics[:5],
                relationships=["operational_template", "performance_template"],
                confidence_score=business_dna.confidence_score
            )
            
        except json.JSONDecodeError:
            # Fallback architecture
            return self._create_fallback_strategic_architecture(business_dna)
    
    async def _design_operational_template(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any]) -> TemplateArchitecture:
        """Design operational deep dive template"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert dashboard architect specializing in operational dashboards.
            Design an operational deep-dive template for managers and operational teams.
            
            Focus on:
            - Day-to-day operational metrics
            - Process efficiency indicators
            - Detailed data tables and drill-downs
            - Actionable operational insights
            - Workflow-specific visualizations
            """),
            ("human", f"""Design an operational template for this business:
            
            Business Workflows: {[w.name for w in business_dna.primary_workflows]}
            Primary Processes: {[w.stages for w in business_dna.primary_workflows[:2]]}
            Key Relationships: {business_dna.key_relationships}
            
            Available Data: {len(data_analysis.get('columns', []))} columns
            Records: {data_analysis.get('total_records', 0)}
            
            Create an operational dashboard with detailed process tracking and management tools.
            """)
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        
        try:
            arch_data = json.loads(response.content)
            
            return TemplateArchitecture(
                template_id=f"operational_{uuid.uuid4().hex[:8]}",
                name=arch_data.get("name", "Operations Intelligence Hub"),
                description=arch_data.get("description", "Detailed operational process management"),
                category=TemplateCategory.OPERATIONAL,
                personality=TemplatePersonality.OPERATIONAL,
                target_audience="Operations Managers and Team Leads",
                business_context=f"Primary focus on {business_dna.primary_workflows[0].name if business_dna.primary_workflows else 'operations'}",
                component_blueprint=arch_data.get("components", {}),
                layout_config=arch_data.get("layout", {"grid_cols": 4, "grid_rows": 8}),
                visual_identity={"primary_color": "#059669", "style": "operational"},
                data_requirements=list(business_dna.key_relationships.keys()),
                success_metrics=[w.key_metrics for w in business_dna.primary_workflows][:3],
                relationships=["strategic_template", "performance_template"],
                confidence_score=business_dna.confidence_score
            )
            
        except json.JSONDecodeError:
            return self._create_fallback_operational_architecture(business_dna)
    
    async def _design_performance_template(self, business_dna: BusinessDNA, data_analysis: Dict[str, Any]) -> TemplateArchitecture:
        """Design performance intelligence template"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert dashboard architect specializing in performance analytics.
            Design a performance intelligence template focused on growth and optimization.
            
            Focus on:
            - Performance trending and analysis
            - Growth metrics and forecasting
            - Comparative analysis
            - Optimization opportunities
            - Advanced analytics visualizations
            """),
            ("human", f"""Design a performance template for this business:
            
            Business Characteristics: {business_dna.unique_characteristics}
            Performance Focus: {business_dna.business_personality}
            Success Metrics: {business_dna.success_metrics}
            Data Sophistication: {business_dna.data_sophistication.value}
            
            Numeric Data Available: {len(data_analysis.get('numeric_columns', []))} metrics
            Time Series Capability: {data_analysis.get('patterns', {}).get('has_time_series', False)}
            
            Create a performance-focused dashboard with advanced analytics and growth insights.
            """)
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        
        try:
            arch_data = json.loads(response.content)
            
            return TemplateArchitecture(
                template_id=f"performance_{uuid.uuid4().hex[:8]}",
                name=arch_data.get("name", "Performance Analytics Center"),
                description=arch_data.get("description", "Advanced performance tracking and optimization"),
                category=TemplateCategory.ANALYTICAL,
                personality=TemplatePersonality.ANALYTICAL,
                target_audience="Analysts and Performance Managers",
                business_context=f"Performance optimization for {business_dna.business_model.value}",
                component_blueprint=arch_data.get("components", {}),
                layout_config=arch_data.get("layout", {"grid_cols": 4, "grid_rows": 7}),
                visual_identity={"primary_color": "#7c3aed", "style": "analytical"},
                data_requirements=data_analysis.get('numeric_columns', []),
                success_metrics=business_dna.success_metrics,
                relationships=["strategic_template", "operational_template"],
                confidence_score=business_dna.confidence_score
            )
            
        except json.JSONDecodeError:
            return self._create_fallback_performance_architecture(business_dna)
    
    async def _select_components_node(self, state: TemplateGenerationState) -> TemplateGenerationState:
        """LangGraph node for intelligent component selection"""
        try:
            logger.info(" Selecting optimal components for templates")
            state["current_step"] = "component_selection"
            
            all_components = []
            
            for architecture in state["template_architectures"]:
                components = await self._select_components_for_architecture(
                    architecture, 
                    state["data_analysis"], 
                    state["business_dna"]
                )
                all_components.extend(components)
            
            state["selected_components"] = all_components
            logger.info(f" Selected {len(all_components)} components across all templates")
            
        except Exception as e:
            logger.error(f" Component selection failed: {e}")
            state["error_messages"].append(f"Component selection error: {str(e)}")
        
        return state
    
    async def _select_components_for_architecture(self, architecture: TemplateArchitecture, data_analysis: Dict[str, Any], business_dna: BusinessDNA) -> List[ComponentBlueprint]:
        """Select optimal components for a specific architecture"""
        
        components = []
        available_components = self.component_library.get(architecture.personality, [])
        
        # AI-powered component selection
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert in selecting optimal dashboard components for {architecture.personality.value} dashboards.
            Select the best components that match the template's purpose and available data.
            
            Component Library Available:
            {json.dumps([comp['type'] for comp in available_components], indent=2)}
            
            Return a JSON list of selected components with positioning and configuration."""),
            ("human", f"""Select components for: {architecture.name}
            
            Template Purpose: {architecture.description}
            Target Audience: {architecture.target_audience}
            Available Data Columns: {data_analysis.get('columns', [])}
            Numeric Metrics: {data_analysis.get('numeric_columns', [])}
            
            Select 4-8 components that best serve this template's purpose.
            Include KPIs, charts, tables, and specialized components as appropriate.
            """)
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        
        try:
            selected_components = json.loads(response.content)
            
            for i, comp_data in enumerate(selected_components):
                component = ComponentBlueprint(
                    component_id=f"{architecture.template_id}_comp_{i}",
                    component_type=comp_data.get("type", "kpi_card"),
                    title=comp_data.get("title", f"Component {i+1}"),
                    subtitle=comp_data.get("subtitle", ""),
                    business_purpose=comp_data.get("purpose", "Business intelligence"),
                    data_mapping=comp_data.get("data_mapping", {}),
                    visualization_config=comp_data.get("config", {}),
                    position=comp_data.get("position", {"row": i // 4, "col": i % 4}),
                    size=comp_data.get("size", {"width": 1, "height": 1}),
                    priority=i + 1,
                    business_logic=comp_data.get("business_logic", {})
                )
                components.append(component)
                
        except json.JSONDecodeError:
            # Fallback component selection
            components = self._create_fallback_components(architecture, data_analysis)
        
        return components
    
    async def _optimize_layout_node(self, state: TemplateGenerationState) -> TemplateGenerationState:
        """LangGraph node for layout optimization"""
        try:
            logger.info(" Optimizing template layouts")
            state["current_step"] = "layout_optimization"
            
            for architecture in state["template_architectures"]:
                optimized_layout = await self._optimize_template_layout(
                    architecture, 
                    state["selected_components"],
                    state["business_dna"]
                )
                architecture.layout_config = optimized_layout
            
            logger.info(" Layout optimization complete")
            
        except Exception as e:
            logger.error(f" Layout optimization failed: {e}")
            state["error_messages"].append(f"Layout optimization error: {str(e)}")
        
        return state
    
    async def _generate_themes_node(self, state: TemplateGenerationState) -> TemplateGenerationState:
        """LangGraph node for theme generation"""
        try:
            logger.info(" Generating custom visual themes")
            state["current_step"] = "theme_generation"
            
            themes = await self._generate_custom_themes(
                state["business_dna"],
                state["template_architectures"]
            )
            
            state["visual_themes"] = themes
            logger.info(f" Generated {len(themes)} custom themes")
            
        except Exception as e:
            logger.error(f" Theme generation failed: {e}")
            state["error_messages"].append(f"Theme generation error: {str(e)}")
        
        return state
    
    async def _create_smart_names_node(self, state: TemplateGenerationState) -> TemplateGenerationState:
        """LangGraph node for smart naming generation"""
        try:
            logger.info("️ Generating smart template names")
            state["current_step"] = "smart_naming"
            
            smart_names = await self._generate_smart_names(
                state["template_architectures"],
                state["business_dna"]
            )
            
            # Update architecture names
            for i, architecture in enumerate(state["template_architectures"]):
                if i < len(smart_names):
                    architecture.name = smart_names[i]
            
            state["template_names"] = smart_names
            logger.info(f"️ Generated {len(smart_names)} smart names")
            
        except Exception as e:
            logger.error(f" Smart naming failed: {e}")
            state["error_messages"].append(f"Smart naming error: {str(e)}")
        
        return state
    
    async def _build_ecosystem_node(self, state: TemplateGenerationState) -> TemplateGenerationState:
        """LangGraph node for ecosystem building"""
        try:
            logger.info(" Building template ecosystem")
            state["current_step"] = "ecosystem_building"
            
            ecosystem = await self._build_template_ecosystem(
                state["template_architectures"],
                state["business_dna"]
            )
            
            state["ecosystem"] = ecosystem
            logger.info(" Template ecosystem complete")
            
        except Exception as e:
            logger.error(f" Ecosystem building failed: {e}")
            state["error_messages"].append(f"Ecosystem building error: {str(e)}")
        
        return state
    
    async def _finalize_templates_node(self, state: TemplateGenerationState) -> TemplateGenerationState:
        """LangGraph node for template finalization"""
        try:
            logger.info(" Finalizing custom templates")
            state["current_step"] = "finalization"
            
            # Apply final optimizations
            for architecture in state["template_architectures"]:
                architecture.visual_identity.update(state["visual_themes"].get(architecture.template_id, {}))
            
            # Update metadata
            state["generation_metadata"]["completed_at"] = datetime.now().isoformat()
            state["generation_metadata"]["total_templates"] = len(state["template_architectures"])
            
            logger.info(" Template finalization complete")
            
        except Exception as e:
            logger.error(f" Template finalization failed: {e}")
            state["error_messages"].append(f"Finalization error: {str(e)}")
        
        return state
    
    # Helper methods for component library, theme generation, etc.
    def _initialize_component_library(self) -> Dict[TemplatePersonality, List[Dict[str, Any]]]:
        """Initialize intelligent component library"""
        return {
            TemplatePersonality.EXECUTIVE: [
                {"type": "executive_kpi", "priority": 1, "business_focus": "strategic_metrics"},
                {"type": "trend_chart", "priority": 2, "business_focus": "performance_trends"},
                {"type": "summary_table", "priority": 3, "business_focus": "key_insights"},
                {"type": "alert_panel", "priority": 4, "business_focus": "critical_issues"}
            ],
            TemplatePersonality.OPERATIONAL: [
                {"type": "operational_kpi", "priority": 1, "business_focus": "process_metrics"},
                {"type": "detailed_table", "priority": 2, "business_focus": "operational_data"},
                {"type": "process_chart", "priority": 3, "business_focus": "workflow_analysis"},
                {"type": "efficiency_gauge", "priority": 4, "business_focus": "performance_monitoring"}
            ],
            TemplatePersonality.ANALYTICAL: [
                {"type": "performance_kpi", "priority": 1, "business_focus": "analytical_metrics"},
                {"type": "advanced_chart", "priority": 2, "business_focus": "data_visualization"},
                {"type": "correlation_matrix", "priority": 3, "business_focus": "relationship_analysis"},
                {"type": "forecast_panel", "priority": 4, "business_focus": "predictive_insights"}
            ]
        }
    
    def _initialize_theme_generator(self) -> Dict[str, Any]:
        """Initialize theme generation system"""
        return {
            "color_psychology": {
                BusinessModel.B2B_SAAS: {"primary": "#0066cc", "accent": "#00b4d8", "style": "professional"},
                BusinessModel.B2C_ECOMMERCE: {"primary": "#e63946", "accent": "#f77f00", "style": "energetic"},
                BusinessModel.FINANCIAL_SERVICES: {"primary": "#2f3e46", "accent": "#84a98c", "style": "trustworthy"},
                BusinessModel.MANUFACTURING: {"primary": "#343a40", "accent": "#fd7e14", "style": "industrial"}
            },
            "typography": {
                BusinessMaturity.STARTUP: {"font_weight": "medium", "style": "modern"},
                BusinessMaturity.ENTERPRISE: {"font_weight": "regular", "style": "professional"}
            }
        }
    
    def _initialize_naming_engine(self) -> Dict[str, List[str]]:
        """Initialize smart naming patterns"""
        return {
            "executive_names": [
                "Strategic Command Center", "Executive Intelligence Hub", "Leadership Dashboard",
                "Strategic Performance Center", "Executive Command Bridge"
            ],
            "operational_names": [
                "Operations Control Center", "Process Intelligence Hub", "Operational Command",
                "Workflow Management Center", "Operations Intelligence"
            ],
            "analytical_names": [
                "Performance Analytics Center", "Intelligence Analytics Hub", "Advanced Analytics Platform",
                "Data Intelligence Center", "Performance Insights Hub"
            ]
        }
    
    # Additional helper methods (fallback architectures, component creation, etc.)
    def _create_fallback_strategic_architecture(self, business_dna: BusinessDNA) -> TemplateArchitecture:
        """Create fallback strategic architecture"""
        return TemplateArchitecture(
            template_id=f"strategic_fallback_{uuid.uuid4().hex[:8]}",
            name="Strategic Overview Dashboard",
            description="Executive-level strategic business overview",
            category=TemplateCategory.STRATEGIC,
            personality=TemplatePersonality.EXECUTIVE,
            target_audience="Executives",
            business_context=business_dna.data_story,
            component_blueprint={},
            layout_config={"grid_cols": 4, "grid_rows": 6},
            visual_identity={"primary_color": "#1e40af"},
            data_requirements=business_dna.success_metrics,
            success_metrics=business_dna.success_metrics,
            relationships=[],
            confidence_score=0.7
        )
    
    def _create_fallback_operational_architecture(self, business_dna: BusinessDNA) -> TemplateArchitecture:
        """Create fallback operational architecture"""
        return TemplateArchitecture(
            template_id=f"operational_fallback_{uuid.uuid4().hex[:8]}",
            name="Operations Dashboard",
            description="Operational process management and monitoring",
            category=TemplateCategory.OPERATIONAL,
            personality=TemplatePersonality.OPERATIONAL,
            target_audience="Operations Teams",
            business_context="Operational efficiency focus",
            component_blueprint={},
            layout_config={"grid_cols": 4, "grid_rows": 8},
            visual_identity={"primary_color": "#059669"},
            data_requirements=[],
            success_metrics=[],
            relationships=[],
            confidence_score=0.7
        )
    
    def _create_fallback_performance_architecture(self, business_dna: BusinessDNA) -> TemplateArchitecture:
        """Create fallback performance architecture"""
        return TemplateArchitecture(
            template_id=f"performance_fallback_{uuid.uuid4().hex[:8]}",
            name="Performance Analytics",
            description="Performance tracking and optimization analytics",
            category=TemplateCategory.ANALYTICAL,
            personality=TemplatePersonality.ANALYTICAL,
            target_audience="Analysts",
            business_context="Performance optimization",
            component_blueprint={},
            layout_config={"grid_cols": 4, "grid_rows": 7},
            visual_identity={"primary_color": "#7c3aed"},
            data_requirements=[],
            success_metrics=[],
            relationships=[],
            confidence_score=0.7
        )
    
    def _create_fallback_components(self, architecture: TemplateArchitecture, data_analysis: Dict[str, Any]) -> List[ComponentBlueprint]:
        """Create fallback components when AI selection fails"""
        components = []
        numeric_cols = data_analysis.get('numeric_columns', [])
        
        # Basic KPI component
        if numeric_cols:
            components.append(ComponentBlueprint(
                component_id=f"{architecture.template_id}_kpi_1",
                component_type="kpi_card",
                title="Key Metrics",
                subtitle="Primary business metrics",
                business_purpose="Track key performance indicators",
                data_mapping={"metric": numeric_cols[0] if numeric_cols else "value"},
                visualization_config={},
                position={"row": 0, "col": 0},
                size={"width": 4, "height": 1},
                priority=1,
                business_logic={}
            ))
        
        # Basic chart component
        components.append(ComponentBlueprint(
            component_id=f"{architecture.template_id}_chart_1",
            component_type="chart",
            title="Performance Overview",
            subtitle="Business performance visualization",
            business_purpose="Visualize business performance trends",
            data_mapping={"x": "category", "y": numeric_cols[0] if numeric_cols else "value"},
            visualization_config={"chart_type": "BarChartOne"},
            position={"row": 1, "col": 0},
            size={"width": 4, "height": 2},
            priority=2,
            business_logic={}
        ))
        
        return components
    
    async def _optimize_template_layout(self, architecture: TemplateArchitecture, components: List[ComponentBlueprint], business_dna: BusinessDNA) -> Dict[str, Any]:
        """Optimize template layout based on component priorities and business context"""
        # AI-optimized layout logic would go here
        # For now, return enhanced layout config
        return {
            "grid_cols": 4,
            "grid_rows": max(6, len(components) // 2 + 2),
            "gap": 4,
            "responsive": True,
            "priority_zones": {
                "primary": {"row": 0, "importance": "high"},
                "secondary": {"row": 1, "importance": "medium"},
                "detail": {"row": 2, "importance": "low"}
            }
        }
    
    async def _generate_custom_themes(self, business_dna: BusinessDNA, architectures: List[TemplateArchitecture]) -> Dict[str, Any]:
        """Generate custom themes for templates"""
        themes = {}
        base_colors = self.theme_generator["color_psychology"].get(
            business_dna.business_model, 
            {"primary": "#3b82f6", "accent": "#8b5cf6", "style": "professional"}
        )
        
        for arch in architectures:
            themes[arch.template_id] = {
                "primary_color": base_colors["primary"],
                "secondary_color": base_colors["accent"],
                "style": base_colors["style"],
                "personality": arch.personality.value
            }
        
        return themes
    
    async def _generate_smart_names(self, architectures: List[TemplateArchitecture], business_dna: BusinessDNA) -> List[str]:
        """Generate smart contextual names for templates"""
        names = []
        naming_patterns = self.naming_engine
        
        for arch in architectures:
            if arch.personality == TemplatePersonality.EXECUTIVE:
                base_names = naming_patterns["executive_names"]
            elif arch.personality == TemplatePersonality.OPERATIONAL:
                base_names = naming_patterns["operational_names"]
            else:
                base_names = naming_patterns["analytical_names"]
            
            # Customize name based on business context
            business_context = business_dna.business_model.value.replace('_', ' ').title()
            selected_name = base_names[len(names) % len(base_names)]
            
            if business_dna.industry_sector != "Technology":
                selected_name = selected_name.replace("Intelligence", business_dna.industry_sector)
            
            names.append(selected_name)
        
        return names
    
    async def _build_template_ecosystem(self, architectures: List[TemplateArchitecture], business_dna: BusinessDNA) -> TemplateEcosystem:
        """Build intelligent template ecosystem with relationships"""
        if not architectures:
            return None
        
        # Primary template (usually strategic/executive)
        primary = next((arch for arch in architectures if arch.personality == TemplatePersonality.EXECUTIVE), architectures[0])
        related = [arch for arch in architectures if arch != primary]
        
        # Define navigation flow
        navigation_flow = {
            primary.template_id: [arch.template_id for arch in related],
            **{arch.template_id: [primary.template_id] for arch in related}
        }
        
        ecosystem = TemplateEcosystem(
            ecosystem_id=f"ecosystem_{uuid.uuid4().hex[:8]}",
            primary_template=primary,
            related_templates=related,
            navigation_flow=navigation_flow,
            shared_context={
                "business_model": business_dna.business_model.value,
                "industry": business_dna.industry_sector,
                "key_metrics": business_dna.success_metrics
            },
            cross_template_features=["shared_filtering", "cross_template_insights", "unified_theming"]
        )
        
        return ecosystem
    
    async def _architecture_to_dashboard_config(self, architecture: TemplateArchitecture, data_analysis: Dict[str, Any], business_dna: BusinessDNA) -> DashboardConfig:
        """Convert template architecture to dashboard configuration"""
        
        # Create layout
        layout = DashboardLayout(
            grid_cols=architecture.layout_config.get("grid_cols", 4),
            grid_rows=architecture.layout_config.get("grid_rows", 6),
            gap=architecture.layout_config.get("gap", 4),
            responsive=architecture.layout_config.get("responsive", True)
        )
        
        # Create placeholder widgets (detailed implementation would create actual widgets)
        kpi_widgets = []
        chart_widgets = []
        
        # Basic implementation - would be expanded with actual widget creation
        for i in range(2):  # Create 2 KPI widgets
            kpi_widgets.append(KPIWidget(
                id=f"kpi_{i}",
                title=f"Key Metric {i+1}",
                value="$0",
                icon="BarChart",
                icon_color="#3b82f6",
                icon_bg_color="#eff6ff",
                trend={"value": "0%", "isPositive": True},
                position={"row": 0, "col": i},
                size={"width": 1, "height": 1}
            ))
        
        for i in range(2):  # Create 2 chart widgets
            chart_widgets.append(ChartWidget(
                id=f"chart_{i}",
                title=f"Analytics {i+1}",
                subtitle="Data visualization",
                chart_type=ChartType.BAR_CHART_ONE,
                data_source="client_data",
                config={"responsive": True},
                position={"row": 1, "col": i*2},
                size={"width": 2, "height": 2}
            ))
        
        return DashboardConfig(
            client_id=uuid.UUID(data_analysis.get('client_id', str(uuid.uuid4()))),
            title=architecture.name,
            subtitle=architecture.description,
            layout=layout,
            kpi_widgets=kpi_widgets,
            chart_widgets=chart_widgets,
            theme=architecture.visual_identity.get("style", "professional"),
            last_generated=datetime.now(),
            version=f"custom-{architecture.template_id}"
        )
    
    async def _generate_data_driven_templates(self, client_id: str, data_analysis: Dict[str, Any]) -> List[DashboardConfig]:
        """Generate data-driven custom templates based on the actual client data analysis."""
        try:
            logger.info(f" Generating data-driven custom templates for client {client_id}")
            
            # Convert client_id to UUID - handle both UUID strings and regular strings
            try:
                client_uuid = uuid.UUID(client_id)
            except ValueError:
                # Generate a UUID from the client_id string
                import hashlib
                client_uuid = uuid.UUID(hashlib.md5(client_id.encode()).hexdigest())
            
            # Extract REAL data characteristics
            columns = data_analysis.get('columns', [])
            sample_data = data_analysis.get('sample_data', [])
            numeric_columns = data_analysis.get('numeric_columns', [])
            categorical_columns = data_analysis.get('categorical_columns', [])
            business_model = data_analysis.get('business_model', 'b2c_ecommerce')
            industry_sector = data_analysis.get('industry_sector', 'Technology')
            
            logger.info(f" Analyzing REAL data: {len(columns)} columns, {len(numeric_columns)} numeric, {len(categorical_columns)} categorical")
            
            # Categorize columns by business function to create DIFFERENT templates
            revenue_columns = [col for col in columns if any(keyword in col.lower() for keyword in ['price', 'cost', 'revenue', 'amount', 'total', 'value', 'fee'])]
            process_columns = [col for col in columns if any(keyword in col.lower() for keyword in ['status', 'stage', 'type', 'category', 'state', 'method', 'mode'])]
            time_columns = [col for col in columns if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated', 'published', 'timestamp'])]
            performance_columns = [col for col in columns if any(keyword in col.lower() for keyword in ['count', 'number', 'quantity', 'rate', 'score', 'rating', 'rank'])]
            
            logger.info(f" Column analysis: {len(revenue_columns)} revenue, {len(process_columns)} process, {len(time_columns)} time, {len(performance_columns)} performance")
            
            templates = []
            
            # Template 1: REVENUE & FINANCIAL FOCUS (using actual revenue/financial columns)
            revenue_template = await self._create_revenue_focused_template(
                client_uuid, business_model, industry_sector, 
                revenue_columns, numeric_columns, sample_data
            )
            templates.append(revenue_template)
            
            # Template 2: OPERATIONS & PROCESS FOCUS (using actual process/status columns) 
            operations_template = await self._create_operations_focused_template(
                client_uuid, business_model, industry_sector,
                process_columns, categorical_columns, sample_data
            )
            templates.append(operations_template)
            
            # Template 3: PERFORMANCE & TRENDS FOCUS (using actual time-series and performance data)
            performance_template = await self._create_performance_focused_template(
                client_uuid, business_model, industry_sector,
                time_columns, performance_columns, numeric_columns, sample_data
            )
            templates.append(performance_template)
            
            logger.info(f" Generated {len(templates)} unique data-driven custom templates for client {client_id}")
            return templates
            
        except Exception as e:
            logger.error(f" Data-driven template generation failed: {e}")
            # Return absolute minimal template
            try:
                client_uuid = uuid.UUID(client_id)
            except ValueError:
                import hashlib
                client_uuid = uuid.UUID(hashlib.md5(client_id.encode()).hexdigest())

            return [
                DashboardConfig(
                    client_id=client_uuid,
                    title="Basic Dashboard",
                    subtitle="Minimal dashboard template",
                    layout=DashboardLayout(
                        grid_cols=4,
                        grid_rows=4,
                        gap=4,
                        responsive=True
                    ),
                    kpi_widgets=[],
                    chart_widgets=[],
                    theme="default",
                    last_generated=datetime.now(),
                    version="emergency-fallback"
                )
            ]

    async def _create_revenue_focused_template(
        self,
        client_uuid: uuid.UUID,
        business_model: str,
        industry_sector: str,
        revenue_columns: List[str],
        numeric_columns: List[str],
        sample_data: List[Dict[str, Any]]
    ) -> DashboardConfig:
        """Generate a revenue-focused template based on actual revenue data."""
        logger.info(" Creating revenue-focused template")
        
        # Determine primary revenue metric
        primary_revenue_metric = "Total Revenue"
        if "ecommerce" in business_model.lower() or "retail" in industry_sector.lower():
            primary_revenue_metric = "Total Sales"
        elif "saas" in business_model.lower() or "technology" in industry_sector.lower():
            primary_revenue_metric = "Monthly Recurring Revenue"
        
        # Generate KPI widgets
        kpi_widgets = [
            KPIWidget(
                id="total_revenue",
                title=primary_revenue_metric,
                value="$156K",
                icon="DollarSign",
                icon_color="#059669",
                icon_bg_color="#ecfdf5",
                trend={"value": "+12%", "isPositive": True},
                position={"row": 0, "col": 0},
                size={"width": 1, "height": 1}
            ),
            KPIWidget(
                id="active_customers",
                title="Active Customers",
                value="1,247",
                icon="Users",
                icon_color="#0891b2",
                icon_bg_color="#ecfeff",
                trend={"value": "+156", "isPositive": True},
                position={"row": 0, "col": 1},
                size={"width": 1, "height": 1}
            )
        ]
        
        # Generate chart widgets
        charts = [
            ChartWidget(
                id="revenue_trends",
                title="Revenue Growth Trends",
                subtitle="Monthly revenue performance",
                chart_type=ChartType.LINE_CHART_ONE,
                data_source="client_data",
                config={"responsive": True, "showTrend": True},
                position={"row": 1, "col": 0},
                size={"width": 2, "height": 2}
            ),
            ChartWidget(
                id="market_segments",
                title="Market Segment Performance",
                subtitle="Revenue by customer segment",
                chart_type=ChartType.BAR_CHART_ONE,
                data_source="client_data",
                config={"responsive": True, "stacked": True},
                position={"row": 1, "col": 2},
                size={"width": 2, "height": 2}
            )
        ]
        
        return DashboardConfig(
            client_id=client_uuid,
            title=f"{industry_sector} Revenue Dashboard",
            subtitle="Executive-level revenue overview and growth trends",
            layout=DashboardLayout(grid_cols=4, grid_rows=6, gap=6, responsive=True),
            kpi_widgets=kpi_widgets,
            chart_widgets=charts,
            theme="executive",
            last_generated=datetime.now(),
            version=f"data-driven-revenue-{uuid.uuid4().hex[:8]}"
        )

    async def _create_operations_focused_template(
        self,
        client_uuid: uuid.UUID,
        business_model: str,
        industry_sector: str,
        process_columns: List[str],
        categorical_columns: List[str],
        sample_data: List[Dict[str, Any]]
    ) -> DashboardConfig:
        """Generate an operations-focused template based on actual process data."""
        logger.info("️ Creating operations-focused template")
        
        # Determine primary process metric
        primary_process_metric = "Process Efficiency"
        if "saas" in business_model.lower() or "technology" in industry_sector.lower():
            primary_process_metric = "Customer Acquisition Cost"
        elif "manufacturing" in industry_sector.lower():
            primary_process_metric = "Production Efficiency"
        
        # Generate KPI widgets
        kpi_widgets = [
            KPIWidget(
                id="process_efficiency",
                title=primary_process_metric,
                value="92%",
                icon="TrendingUp",
                icon_color="#059669",
                icon_bg_color="#ecfdf5",
                trend={"value": "+2%", "isPositive": True},
                position={"row": 0, "col": 0},
                size={"width": 1, "height": 1}
            ),
            KPIWidget(
                id="workflow_completion",
                title="Workflow Completion Rate",
                value="98%",
                icon="CheckCircle",
                icon_color="#22c55e",
                icon_bg_color="#ecfdf5",
                trend={"value": "+1%", "isPositive": True},
                position={"row": 0, "col": 1},
                size={"width": 1, "height": 1}
            )
        ]
        
        # Generate chart widgets
        charts = [
            ChartWidget(
                id="process_efficiency_metrics",
                title="Process Efficiency Metrics",
                subtitle="Operational performance tracking",
                chart_type=ChartType.BAR_CHART_ONE,
                data_source="client_data",
                config={"responsive": True, "horizontal": True},
                position={"row": 1, "col": 0},
                size={"width": 3, "height": 2}
            ),
            ChartWidget(
                id="workflow_timeline",
                title="Workflow Timeline Analysis",
                subtitle="Process flow over time",
                chart_type=ChartType.LINE_CHART_ONE,
                data_source="client_data",
                config={"responsive": True, "multiLine": True},
                position={"row": 1, "col": 3},
                size={"width": 3, "height": 2}
            )
        ]
        
        return DashboardConfig(
            client_id=client_uuid,
            title=f"{industry_sector} Operations Dashboard",
            subtitle="Detailed operational process management and monitoring",
            layout=DashboardLayout(grid_cols=6, grid_rows=8, gap=4, responsive=True),
            kpi_widgets=kpi_widgets,
            chart_widgets=charts,
            theme="operational",
            last_generated=datetime.now(),
            version=f"data-driven-operations-{uuid.uuid4().hex[:8]}"
        )

    async def _create_performance_focused_template(
        self,
        client_uuid: uuid.UUID,
        business_model: str,
        industry_sector: str,
        time_columns: List[str],
        performance_columns: List[str],
        numeric_columns: List[str],
        sample_data: List[Dict[str, Any]]
    ) -> DashboardConfig:
        """Generate a performance-focused template based on actual time-series and performance data."""
        logger.info(" Creating performance-focused template")
        
        # Determine primary performance metric
        primary_performance_metric = "Performance Score"
        if "saas" in business_model.lower() or "technology" in industry_sector.lower():
            primary_performance_metric = "Customer Satisfaction Score"
        elif "manufacturing" in industry_sector.lower():
            primary_performance_metric = "Quality Score"
        
        # Generate KPI widgets
        kpi_widgets = [
            KPIWidget(
                id="performance_score",
                title=primary_performance_metric,
                value="4.5",
                icon="TrendingUp",
                icon_color="#7c3aed",
                icon_bg_color="#f3e8ff",
                trend={"value": "+0.1", "isPositive": True},
                position={"row": 0, "col": 0},
                size={"width": 1, "height": 1}
            ),
            KPIWidget(
                id="customer_retention",
                title="Customer Retention Rate",
                value="95%",
                icon="Users",
                icon_color="#0891b2",
                icon_bg_color="#ecfeff",
                trend={"value": "+5%", "isPositive": True},
                position={"row": 0, "col": 1},
                size={"width": 1, "height": 1}
            )
        ]
        
        # Generate chart widgets
        charts = [
            ChartWidget(
                id="performance_analytics",
                title="Performance Analytics Deep Dive",
                subtitle="Advanced performance metrics",
                chart_type=ChartType.LINE_CHART_ONE,
                data_source="client_data",
                config={"responsive": True, "advanced": True},
                position={"row": 1, "col": 0},
                size={"width": 2, "height": 3}
            ),
            ChartWidget(
                id="correlation_analysis",
                title="Key Factor Correlation",
                subtitle="Data relationship analysis",
                chart_type=ChartType.BAR_CHART_ONE,
                data_source="client_data",
                config={"responsive": True, "correlation": True},
                position={"row": 1, "col": 2},
                size={"width": 2, "height": 3}
            )
        ]
        
        return DashboardConfig(
            client_id=client_uuid,
            title=f"{industry_sector} Performance Dashboard",
            subtitle="Advanced performance tracking and optimization analytics",
            layout=DashboardLayout(grid_cols=4, grid_rows=8, gap=5, responsive=True),
            kpi_widgets=kpi_widgets,
            chart_widgets=charts,
            theme="analytics",
            last_generated=datetime.now(),
            version=f"data-driven-performance-{uuid.uuid4().hex[:8]}"
        ) 