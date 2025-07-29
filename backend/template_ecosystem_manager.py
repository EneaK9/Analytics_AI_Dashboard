import json
import uuid
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from datetime import datetime
import hashlib
import colorsys

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from business_dna_analyzer import BusinessDNA, BusinessModel, BusinessMaturity
from dynamic_template_orchestrator import TemplateArchitecture, TemplateCategory, TemplatePersonality

logger = logging.getLogger(__name__)

class ThemeStyle(Enum):
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"
    MODERN = "modern"
    CLASSIC = "classic"
    MINIMALIST = "minimalist"
    VIBRANT = "vibrant"

class ColorPsychology(Enum):
    TRUST = "trust"           # Blues
    GROWTH = "growth"         # Greens
    ENERGY = "energy"         # Oranges, Reds
    INNOVATION = "innovation" # Purples
    STABILITY = "stability"   # Grays, Blues
    URGENCY = "urgency"       # Reds
    OPTIMISM = "optimism"     # Yellows
    PREMIUM = "premium"       # Black, Gold

@dataclass
class TemplateTheme:
    theme_id: str
    primary_color: str
    secondary_color: str
    accent_color: str
    success_color: str
    warning_color: str
    error_color: str
    neutral_color: str
    background_gradient: str
    typography: Dict[str, str]
    icon_style: str
    visual_personality: str
    color_psychology: ColorPsychology
    accessibility_score: float

@dataclass
class TemplateEcosystemRelationship:
    from_template: str
    to_template: str
    relationship_type: str
    navigation_label: str
    data_sharing: List[str]
    context_inheritance: Dict[str, Any]
    priority: int

@dataclass
class EcosystemNavigation:
    navigation_id: str
    template_hierarchy: Dict[str, List[str]]
    cross_references: List[TemplateEcosystemRelationship]
    shared_filters: List[str]
    synchronized_states: List[str]
    breadcrumb_structure: Dict[str, str]

@dataclass
class SmartTemplateName:
    template_id: str
    primary_name: str
    alternative_names: List[str]
    description: str
    target_audience: str
    business_context: str
    naming_confidence: float
    semantic_tags: List[str]

class TemplateEcosystemManager:
    """Advanced template ecosystem manager with intelligent relationships and theming"""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4o",
            temperature=0.6
        )
        
        self.color_psychology_mapping = self._initialize_color_psychology()
        self.business_theme_profiles = self._initialize_business_themes()
        self.naming_patterns = self._initialize_naming_patterns()
        self.ecosystem_templates = self._initialize_ecosystem_templates()
        
        logger.info("✅ Template Ecosystem Manager initialized")
    
    def _initialize_color_psychology(self) -> Dict[ColorPsychology, Dict[str, str]]:
        """Initialize color psychology mappings"""
        return {
            ColorPsychology.TRUST: {
                "primary": "#1e40af",    # Deep Blue
                "secondary": "#3b82f6",  # Blue
                "accent": "#60a5fa",     # Light Blue
                "personality": "trustworthy, reliable, professional"
            },
            ColorPsychology.GROWTH: {
                "primary": "#059669",    # Emerald
                "secondary": "#10b981",  # Green
                "accent": "#34d399",     # Light Green
                "personality": "growth-focused, sustainable, prosperous"
            },
            ColorPsychology.ENERGY: {
                "primary": "#dc2626",    # Red
                "secondary": "#f97316",  # Orange
                "accent": "#fb923c",     # Light Orange
                "personality": "energetic, urgent, action-oriented"
            },
            ColorPsychology.INNOVATION: {
                "primary": "#7c3aed",    # Purple
                "secondary": "#8b5cf6",  # Violet
                "accent": "#a78bfa",     # Light Purple
                "personality": "innovative, creative, forward-thinking"
            },
            ColorPsychology.STABILITY: {
                "primary": "#374151",    # Gray
                "secondary": "#6b7280",  # Medium Gray
                "accent": "#9ca3af",     # Light Gray
                "personality": "stable, established, dependable"
            },
            ColorPsychology.PREMIUM: {
                "primary": "#1f2937",    # Dark Gray
                "secondary": "#d97706",  # Gold
                "accent": "#f59e0b",     # Light Gold
                "personality": "premium, luxury, exclusive"
            }
        }
    
    def _initialize_business_themes(self) -> Dict[BusinessModel, Dict[str, Any]]:
        """Initialize business model specific theme profiles"""
        return {
            BusinessModel.B2B_SAAS: {
                "psychology": ColorPsychology.TRUST,
                "style": ThemeStyle.PROFESSIONAL,
                "emphasis": "reliability and growth",
                "visual_weight": "medium",
                "iconography": "clean and modern"
            },
            BusinessModel.B2C_ECOMMERCE: {
                "psychology": ColorPsychology.ENERGY,
                "style": ThemeStyle.VIBRANT,
                "emphasis": "conversion and engagement",
                "visual_weight": "high",
                "iconography": "friendly and approachable"
            },
            BusinessModel.FINANCIAL_SERVICES: {
                "psychology": ColorPsychology.TRUST,
                "style": ThemeStyle.EXECUTIVE,
                "emphasis": "security and stability",
                "visual_weight": "conservative",
                "iconography": "traditional and secure"
            },
            BusinessModel.MANUFACTURING: {
                "psychology": ColorPsychology.STABILITY,
                "style": ThemeStyle.TECHNICAL,
                "emphasis": "efficiency and precision",
                "visual_weight": "functional",
                "iconography": "industrial and precise"
            }
            # Note: STARTUP is a BusinessMaturity level, not a BusinessModel
            # Startup themes are handled through BusinessMaturity.STARTUP in other functions
        }
    
    def _initialize_naming_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize intelligent naming patterns"""
        return {
            "executive_patterns": {
                "command_center": ["Strategic Command Center", "Executive Command Bridge", "Leadership Control Hub"],
                "intelligence": ["Executive Intelligence Hub", "Strategic Intelligence Center", "Leadership Analytics"],
                "dashboard": ["Executive Dashboard", "Strategic Overview", "Leadership Portal"],
                "observatory": ["Performance Observatory", "Strategic Observatory", "Business Intelligence Center"]
            },
            "operational_patterns": {
                "control": ["Operations Control Center", "Process Control Hub", "Operational Command"],
                "management": ["Operations Management Center", "Process Management Hub", "Workflow Control"],
                "intelligence": ["Operational Intelligence", "Process Intelligence Hub", "Operations Analytics"],
                "monitor": ["Operations Monitor", "Process Monitor", "Performance Control Center"]
            },
            "analytical_patterns": {
                "analytics": ["Advanced Analytics Center", "Intelligence Analytics Hub", "Data Analytics Platform"],
                "insights": ["Performance Insights Center", "Business Insights Hub", "Analytics Intelligence"],
                "intelligence": ["Data Intelligence Center", "Analytics Intelligence Hub", "Insight Generation Center"],
                "laboratory": ["Analytics Laboratory", "Data Science Center", "Intelligence Lab"]
            },
            "industry_modifiers": {
                "saas": ["SaaS", "Cloud", "Platform", "Service"],
                "ecommerce": ["Commerce", "Retail", "Store", "Marketplace"],
                "manufacturing": ["Production", "Manufacturing", "Industrial", "Operations"],
                "financial": ["Financial", "Capital", "Investment", "Banking"]
            }
        }
    
    def _initialize_ecosystem_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize ecosystem relationship templates"""
        return {
            "strategic_to_operational": {
                "navigation_label": "Dive into Operations",
                "relationship_type": "drill_down",
                "data_sharing": ["date_range", "filters", "selected_metrics"],
                "context": "detailed operational view of strategic metrics"
            },
            "operational_to_analytical": {
                "navigation_label": "Advanced Analytics",
                "relationship_type": "deep_analysis",
                "data_sharing": ["process_data", "performance_metrics", "filters"],
                "context": "detailed analysis of operational processes"
            },
            "analytical_to_strategic": {
                "navigation_label": "Strategic Summary",
                "relationship_type": "roll_up",
                "data_sharing": ["insights", "trends", "recommendations"],
                "context": "strategic insights from analytical findings"
            },
            "cross_functional": {
                "navigation_label": "Related View",
                "relationship_type": "lateral",
                "data_sharing": ["shared_dimensions", "common_metrics"],
                "context": "complementary business perspective"
            }
        }
    
    async def generate_intelligent_themes(self, business_dna: BusinessDNA, template_architectures: List[TemplateArchitecture]) -> Dict[str, TemplateTheme]:
        """Generate intelligent themes based on business DNA and template personalities"""
        
        try:
            logger.info(f"🎨 Generating intelligent themes for {len(template_architectures)} templates")
            
            # Get business theme profile
            business_profile = self.business_theme_profiles.get(
                business_dna.business_model, 
                self.business_theme_profiles[BusinessModel.B2B_SAAS]
            )
            
            # Generate base theme from business DNA
            base_theme = await self._generate_base_theme(business_dna, business_profile)
            
            # Create personalized themes for each template
            themes = {}
            for i, architecture in enumerate(template_architectures):
                theme = await self._personalize_theme_for_template(
                    base_theme, 
                    architecture, 
                    business_dna,
                    variation_index=i
                )
                themes[architecture.template_id] = theme
            
            logger.info(f"🎨 Generated {len(themes)} personalized themes")
            return themes
            
        except Exception as e:
            logger.error(f"❌ Theme generation failed: {e}")
            return await self._generate_fallback_themes(template_architectures)
    
    async def _generate_base_theme(self, business_dna: BusinessDNA, business_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate base theme using AI and color psychology"""
        
        psychology = business_profile["psychology"]
        color_scheme = self.color_psychology_mapping[psychology]
        
        # AI-enhanced theme generation
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in UI/UX design and color psychology. 
            Generate sophisticated color themes for business dashboards that reflect the company's personality and industry.
            
            Consider:
            - Color psychology and business context
            - Accessibility and readability
            - Professional appearance
            - Brand personality alignment
            
            Return color values as hex codes."""),
            ("human", f"""Generate a sophisticated color theme for this business:
            
            Business Model: {business_dna.business_model.value}
            Industry: {business_dna.industry_sector}
            Maturity: {business_dna.maturity_level.value}
            Business Personality: {business_dna.business_personality}
            
            Base Color Psychology: {psychology.value}
            Style Direction: {business_profile['style'].value}
            
            Create a professional color palette with:
            1. Primary color (main brand color)
            2. Secondary color (supporting color)
            3. Accent color (highlights and CTAs)
            4. Success color (positive metrics)
            5. Warning color (attention items)
            6. Error color (negative metrics)
            7. Neutral color (text and backgrounds)
            
            Ensure colors work well together and maintain WCAG accessibility standards.
            """)
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        
        try:
            # Parse AI response for colors
            ai_colors = await self._parse_color_response(response.content)
            
            # Enhance with color psychology
            return {
                "primary": ai_colors.get("primary", color_scheme["primary"]),
                "secondary": ai_colors.get("secondary", color_scheme["secondary"]),
                "accent": ai_colors.get("accent", color_scheme["accent"]),
                "success": ai_colors.get("success", "#10b981"),
                "warning": ai_colors.get("warning", "#f59e0b"),
                "error": ai_colors.get("error", "#ef4444"),
                "neutral": ai_colors.get("neutral", "#6b7280"),
                "psychology": psychology,
                "style": business_profile["style"],
                "personality": color_scheme["personality"]
            }
            
        except Exception as e:
            logger.warning(f"AI color parsing failed, using color psychology fallback: {e}")
            return {
                "primary": color_scheme["primary"],
                "secondary": color_scheme["secondary"],
                "accent": color_scheme["accent"],
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "neutral": "#6b7280",
                "psychology": psychology,
                "style": business_profile["style"],
                "personality": color_scheme["personality"]
            }
    
    async def _personalize_theme_for_template(self, base_theme: Dict[str, Any], architecture: TemplateArchitecture, business_dna: BusinessDNA, variation_index: int) -> TemplateTheme:
        """Create personalized theme variations for each template personality"""
        
        # Create personality-specific color variations
        personality_adjustments = {
            TemplatePersonality.EXECUTIVE: {"saturation": -0.1, "lightness": -0.05, "formality": "high"},
            TemplatePersonality.OPERATIONAL: {"saturation": 0.0, "lightness": 0.0, "formality": "medium"},
            TemplatePersonality.ANALYTICAL: {"saturation": 0.1, "lightness": 0.05, "formality": "technical"},
            TemplatePersonality.STRATEGIC: {"saturation": -0.05, "lightness": -0.1, "formality": "high"},
            TemplatePersonality.TACTICAL: {"saturation": 0.05, "lightness": 0.1, "formality": "medium"}
        }
        
        adjustment = personality_adjustments.get(architecture.personality, {"saturation": 0, "lightness": 0, "formality": "medium"})
        
        # Apply personality-based color adjustments
        primary_color = self._adjust_color(base_theme["primary"], adjustment["saturation"], adjustment["lightness"])
        secondary_color = self._adjust_color(base_theme["secondary"], adjustment["saturation"] * 0.5, adjustment["lightness"] * 0.5)
        
        # Create unique variation for each template
        if variation_index > 0:
            hue_shift = variation_index * 15  # Slight hue variations
            primary_color = self._shift_hue(primary_color, hue_shift)
        
        # Generate background gradient
        background_gradient = self._generate_background_gradient(primary_color, architecture.personality)
        
        # Typography based on personality
        typography = self._select_typography(architecture.personality, adjustment["formality"])
        
        # Icon style
        icon_style = self._select_icon_style(architecture.personality, business_dna.business_model)
        
        return TemplateTheme(
            theme_id=f"theme_{architecture.template_id}",
            primary_color=primary_color,
            secondary_color=secondary_color,
            accent_color=base_theme["accent"],
            success_color=base_theme["success"],
            warning_color=base_theme["warning"],
            error_color=base_theme["error"],
            neutral_color=base_theme["neutral"],
            background_gradient=background_gradient,
            typography=typography,
            icon_style=icon_style,
            visual_personality=f"{architecture.personality.value}_{base_theme['style'].value}",
            color_psychology=base_theme["psychology"],
            accessibility_score=self._calculate_accessibility_score(primary_color, "#ffffff")
        )
    
    async def generate_smart_template_names(self, business_dna: BusinessDNA, template_architectures: List[TemplateArchitecture]) -> Dict[str, SmartTemplateName]:
        """Generate contextually intelligent template names"""
        
        try:
            logger.info(f"🏷️ Generating smart names for {len(template_architectures)} templates")
            
            smart_names = {}
            
            for architecture in template_architectures:
                smart_name = await self._generate_contextual_name(
                    architecture, 
                    business_dna
                )
                smart_names[architecture.template_id] = smart_name
            
            # Ensure name uniqueness across ecosystem
            smart_names = await self._ensure_name_uniqueness(smart_names)
            
            logger.info(f"🏷️ Generated {len(smart_names)} intelligent template names")
            return smart_names
            
        except Exception as e:
            logger.error(f"❌ Smart naming failed: {e}")
            return await self._generate_fallback_names(template_architectures)
    
    async def _generate_contextual_name(self, architecture: TemplateArchitecture, business_dna: BusinessDNA) -> SmartTemplateName:
        """Generate contextually appropriate name for template"""
        
        # AI-powered name generation
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in business intelligence and dashboard naming. 
            Create compelling, professional template names that:
            - Reflect the template's purpose and personality
            - Resonate with the target audience
            - Align with business context and industry
            - Are memorable and actionable
            - Avoid generic terms like "Dashboard 1, 2, 3"
            
            Generate names that sound like they were specifically designed for this business."""),
            ("human", f"""Create an intelligent name for this dashboard template:
            
            Template Details:
            - Category: {architecture.category.value}
            - Personality: {architecture.personality.value}
            - Target Audience: {architecture.target_audience}
            - Business Purpose: {architecture.description}
            
            Business Context:
            - Model: {business_dna.business_model.value}
            - Industry: {business_dna.industry_sector}
            - Maturity: {business_dna.maturity_level.value}
            - Key Workflows: {[w.name for w in business_dna.primary_workflows[:3]]}
            - Unique Characteristics: {business_dna.unique_characteristics}
            
            Generate:
            1. Primary name (2-4 words, professional, specific)
            2. 2-3 alternative names
            3. Brief description explaining the name choice
            4. Semantic tags for searchability
            
            Make it sound purpose-built for this specific business, not generic.
            """)
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        
        try:
            # Parse AI response
            name_data = await self._parse_naming_response(response.content)
            
            return SmartTemplateName(
                template_id=architecture.template_id,
                primary_name=name_data.get("primary_name", self._generate_fallback_name(architecture)),
                alternative_names=name_data.get("alternative_names", []),
                description=name_data.get("description", "Intelligent business dashboard"),
                target_audience=architecture.target_audience,
                business_context=f"{business_dna.business_model.value} {business_dna.industry_sector}",
                naming_confidence=name_data.get("confidence", 0.8),
                semantic_tags=name_data.get("semantic_tags", [])
            )
            
        except Exception as e:
            logger.warning(f"AI naming parsing failed, using pattern-based fallback: {e}")
            return self._generate_pattern_based_name(architecture, business_dna)
    
    async def build_ecosystem_relationships(self, template_architectures: List[TemplateArchitecture], business_dna: BusinessDNA) -> EcosystemNavigation:
        """Build intelligent relationships between templates"""
        
        logger.info("🌐 Building template ecosystem relationships")
        
        # Create template hierarchy
        hierarchy = self._build_template_hierarchy(template_architectures)
        
        # Generate cross-references
        cross_references = await self._generate_cross_references(template_architectures, business_dna)
        
        # Define shared elements
        shared_filters = self._define_shared_filters(business_dna)
        synchronized_states = self._define_synchronized_states(template_architectures)
        
        # Create breadcrumb structure
        breadcrumbs = self._create_breadcrumb_structure(hierarchy)
        
        return EcosystemNavigation(
            navigation_id=f"ecosystem_{uuid.uuid4().hex[:8]}",
            template_hierarchy=hierarchy,
            cross_references=cross_references,
            shared_filters=shared_filters,
            synchronized_states=synchronized_states,
            breadcrumb_structure=breadcrumbs
        )
    
    def _build_template_hierarchy(self, templates: List[TemplateArchitecture]) -> Dict[str, List[str]]:
        """Build logical hierarchy of templates"""
        
        hierarchy = {"root": []}
        
        # Group by personality/category
        executive_templates = [t for t in templates if t.personality == TemplatePersonality.EXECUTIVE]
        operational_templates = [t for t in templates if t.personality == TemplatePersonality.OPERATIONAL]
        analytical_templates = [t for t in templates if t.personality == TemplatePersonality.ANALYTICAL]
        
        # Executive templates are top-level
        for template in executive_templates:
            hierarchy["root"].append(template.template_id)
            hierarchy[template.template_id] = []
            
            # Operational and analytical templates are children of executive
            for child in operational_templates + analytical_templates:
                hierarchy[template.template_id].append(child.template_id)
        
        # If no executive templates, make operational top-level
        if not executive_templates:
            for template in operational_templates:
                hierarchy["root"].append(template.template_id)
                hierarchy[template.template_id] = [t.template_id for t in analytical_templates]
        
        return hierarchy
    
    async def _generate_cross_references(self, templates: List[TemplateArchitecture], business_dna: BusinessDNA) -> List[TemplateEcosystemRelationship]:
        """Generate intelligent cross-references between templates"""
        
        relationships = []
        
        for i, template_a in enumerate(templates):
            for j, template_b in enumerate(templates):
                if i != j:  # Don't relate template to itself
                    relationship = self._determine_relationship_type(template_a, template_b)
                    
                    if relationship:
                        eco_relationship = TemplateEcosystemRelationship(
                            from_template=template_a.template_id,
                            to_template=template_b.template_id,
                            relationship_type=relationship["type"],
                            navigation_label=relationship["label"],
                            data_sharing=relationship["data_sharing"],
                            context_inheritance=relationship.get("context", {}),
                            priority=relationship.get("priority", 3)
                        )
                        relationships.append(eco_relationship)
        
        return relationships
    
    def _determine_relationship_type(self, template_a: TemplateArchitecture, template_b: TemplateArchitecture) -> Optional[Dict[str, Any]]:
        """Determine the type of relationship between two templates"""
        
        # Executive to Operational
        if (template_a.personality == TemplatePersonality.EXECUTIVE and 
            template_b.personality == TemplatePersonality.OPERATIONAL):
            return {
                "type": "drill_down",
                "label": "View Operations Details",
                "data_sharing": ["date_range", "selected_metrics", "filters"],
                "priority": 1
            }
        
        # Operational to Analytical
        if (template_a.personality == TemplatePersonality.OPERATIONAL and 
            template_b.personality == TemplatePersonality.ANALYTICAL):
            return {
                "type": "deep_analysis",
                "label": "Advanced Analytics",
                "data_sharing": ["process_data", "performance_metrics"],
                "priority": 2
            }
        
        # Analytical to Executive (insights roll-up)
        if (template_a.personality == TemplatePersonality.ANALYTICAL and 
            template_b.personality == TemplatePersonality.EXECUTIVE):
            return {
                "type": "roll_up",
                "label": "Strategic Summary",
                "data_sharing": ["insights", "recommendations", "trends"],
                "priority": 2
            }
        
        # Same category (lateral relationships)
        if template_a.category == template_b.category:
            return {
                "type": "lateral",
                "label": "Related View",
                "data_sharing": ["common_filters", "shared_dimensions"],
                "priority": 3
            }
        
        return None
    
    def _define_shared_filters(self, business_dna: BusinessDNA) -> List[str]:
        """Define filters that should be shared across all templates in ecosystem"""
        
        shared_filters = ["date_range", "business_unit"]
        
        # Add business-specific shared filters
        if business_dna.business_model == BusinessModel.B2B_SAAS:
            shared_filters.extend(["subscription_plan", "customer_segment"])
        elif business_dna.business_model == BusinessModel.B2C_ECOMMERCE:
            shared_filters.extend(["product_category", "customer_type"])
        elif business_dna.business_model == BusinessModel.MANUFACTURING:
            shared_filters.extend(["production_line", "product_type"])
        
        return shared_filters
    
    def _define_synchronized_states(self, templates: List[TemplateArchitecture]) -> List[str]:
        """Define states that should be synchronized across templates"""
        
        return [
            "selected_time_period",
            "active_filters",
            "user_preferences",
            "view_mode",
            "data_refresh_status"
        ]
    
    def _create_breadcrumb_structure(self, hierarchy: Dict[str, List[str]]) -> Dict[str, str]:
        """Create breadcrumb navigation structure"""
        
        breadcrumbs = {}
        
        def build_breadcrumbs(template_id: str, path: List[str] = []):
            current_path = path + [template_id]
            breadcrumbs[template_id] = " > ".join(current_path)
            
            # Recursively build for children
            for child_id in hierarchy.get(template_id, []):
                build_breadcrumbs(child_id, current_path)
        
        # Start from root
        for root_template in hierarchy.get("root", []):
            build_breadcrumbs(root_template)
        
        return breadcrumbs
    
    # Color manipulation helper methods
    def _adjust_color(self, color_hex: str, saturation_delta: float, lightness_delta: float) -> str:
        """Adjust color saturation and lightness"""
        try:
            # Convert hex to RGB
            rgb = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))
            
            # Convert to HSL
            h, l, s = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
            
            # Adjust saturation and lightness
            s = max(0, min(1, s + saturation_delta))
            l = max(0, min(1, l + lightness_delta))
            
            # Convert back to RGB
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            
            # Convert to hex
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            
        except Exception:
            return color_hex  # Return original if adjustment fails
    
    def _shift_hue(self, color_hex: str, hue_shift: float) -> str:
        """Shift color hue by specified degrees"""
        try:
            rgb = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))
            h, l, s = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
            
            # Shift hue (0-360 degrees normalized to 0-1)
            h = (h + hue_shift/360) % 1
            
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            
        except Exception:
            return color_hex
    
    def _generate_background_gradient(self, primary_color: str, personality: TemplatePersonality) -> str:
        """Generate background gradient based on primary color and personality"""
        
        if personality == TemplatePersonality.EXECUTIVE:
            # Subtle, professional gradient
            lighter = self._adjust_color(primary_color, 0, 0.4)
            return f"linear-gradient(135deg, {lighter}15 0%, {primary_color}08 100%)"
        elif personality == TemplatePersonality.ANALYTICAL:
            # Technical, precise gradient
            darker = self._adjust_color(primary_color, -0.1, -0.1)
            return f"linear-gradient(180deg, {primary_color}10 0%, {darker}05 100%)"
        else:
            # Standard operational gradient
            return f"linear-gradient(45deg, {primary_color}12 0%, {primary_color}06 100%)"
    
    def _select_typography(self, personality: TemplatePersonality, formality: str) -> Dict[str, str]:
        """Select typography based on personality and formality"""
        
        typography_profiles = {
            TemplatePersonality.EXECUTIVE: {
                "font_family": "Inter, system-ui, sans-serif",
                "heading_weight": "600",
                "body_weight": "400",
                "letter_spacing": "-0.025em",
                "line_height": "1.5"
            },
            TemplatePersonality.ANALYTICAL: {
                "font_family": "JetBrains Mono, Consolas, monospace",
                "heading_weight": "500",
                "body_weight": "400",
                "letter_spacing": "0",
                "line_height": "1.6"
            },
            TemplatePersonality.OPERATIONAL: {
                "font_family": "system-ui, -apple-system, sans-serif",
                "heading_weight": "500",
                "body_weight": "400",
                "letter_spacing": "0",
                "line_height": "1.5"
            }
        }
        
        return typography_profiles.get(personality, typography_profiles[TemplatePersonality.OPERATIONAL])
    
    def _select_icon_style(self, personality: TemplatePersonality, business_model: BusinessModel) -> str:
        """Select icon style based on personality and business model"""
        
        if personality == TemplatePersonality.EXECUTIVE:
            return "outline-professional"
        elif personality == TemplatePersonality.ANALYTICAL:
            return "solid-technical"
        else:
            return "outline-friendly"
    
    def _calculate_accessibility_score(self, color1: str, color2: str) -> float:
        """Calculate WCAG accessibility score between two colors"""
        # Simplified accessibility calculation
        # In a real implementation, this would calculate actual contrast ratios
        return 0.85  # Placeholder
    
    # AI response parsing helpers
    async def _parse_color_response(self, response_content: str) -> Dict[str, str]:
        """Parse AI response for color values"""
        import re
        
        colors = {}
        
        # Extract hex colors from response
        hex_pattern = r'#[0-9a-fA-F]{6}'
        hex_matches = re.findall(hex_pattern, response_content)
        
        # Map to color roles (this is simplified - real implementation would be more sophisticated)
        color_roles = ['primary', 'secondary', 'accent', 'success', 'warning', 'error', 'neutral']
        
        for i, hex_color in enumerate(hex_matches[:len(color_roles)]):
            colors[color_roles[i]] = hex_color
        
        return colors
    
    async def _parse_naming_response(self, response_content: str) -> Dict[str, Any]:
        """Parse AI response for naming data"""
        # This would include sophisticated parsing of AI response
        # For now, return basic structure
        return {
            "primary_name": "Business Intelligence Center",
            "alternative_names": ["Analytics Hub", "Performance Center"],
            "description": "Comprehensive business analytics dashboard",
            "confidence": 0.8,
            "semantic_tags": ["analytics", "business", "performance"]
        }
    
    # Fallback methods
    def _generate_fallback_name(self, architecture: TemplateArchitecture) -> str:
        """Generate fallback name when AI fails"""
        personality_names = {
            TemplatePersonality.EXECUTIVE: "Strategic Overview",
            TemplatePersonality.OPERATIONAL: "Operations Center",
            TemplatePersonality.ANALYTICAL: "Analytics Hub"
        }
        
        return personality_names.get(architecture.personality, "Business Dashboard")
    
    def _generate_pattern_based_name(self, architecture: TemplateArchitecture, business_dna: BusinessDNA) -> SmartTemplateName:
        """Generate name using pattern-based approach"""
        
        personality_key = f"{architecture.personality.value}_patterns"
        patterns = self.naming_patterns.get(personality_key, {})
        
        # Select pattern based on architecture category
        if architecture.category == TemplateCategory.STRATEGIC:
            pattern_options = patterns.get("command_center", ["Strategic Center"])
        elif architecture.category == TemplateCategory.OPERATIONAL:
            pattern_options = patterns.get("control", ["Operations Hub"])
        else:
            pattern_options = patterns.get("analytics", ["Analytics Center"])
        
        primary_name = pattern_options[0] if pattern_options else "Business Dashboard"
        
        return SmartTemplateName(
            template_id=architecture.template_id,
            primary_name=primary_name,
            alternative_names=pattern_options[1:] if len(pattern_options) > 1 else [],
            description=f"Pattern-based {architecture.personality.value} dashboard",
            target_audience=architecture.target_audience,
            business_context=f"{business_dna.business_model.value}",
            naming_confidence=0.6,
            semantic_tags=[architecture.personality.value, architecture.category.value]
        )
    
    async def _ensure_name_uniqueness(self, smart_names: Dict[str, SmartTemplateName]) -> Dict[str, SmartTemplateName]:
        """Ensure all template names are unique within the ecosystem"""
        
        used_names = set()
        updated_names = {}
        
        for template_id, smart_name in smart_names.items():
            original_name = smart_name.primary_name
            
            # If name is already used, try alternatives
            if original_name in used_names:
                for alt_name in smart_name.alternative_names:
                    if alt_name not in used_names:
                        smart_name.primary_name = alt_name
                        break
                else:
                    # If no alternatives work, append a number
                    counter = 2
                    while f"{original_name} {counter}" in used_names:
                        counter += 1
                    smart_name.primary_name = f"{original_name} {counter}"
            
            used_names.add(smart_name.primary_name)
            updated_names[template_id] = smart_name
        
        return updated_names
    
    async def _generate_fallback_themes(self, templates: List[TemplateArchitecture]) -> Dict[str, TemplateTheme]:
        """Generate basic fallback themes"""
        
        fallback_themes = {}
        base_colors = ["#3b82f6", "#059669", "#7c3aed", "#f59e0b"]
        
        for i, template in enumerate(templates):
            color = base_colors[i % len(base_colors)]
            
            fallback_themes[template.template_id] = TemplateTheme(
                theme_id=f"fallback_{template.template_id}",
                primary_color=color,
                secondary_color=self._adjust_color(color, 0.1, 0.1),
                accent_color=self._adjust_color(color, -0.1, 0.2),
                success_color="#10b981",
                warning_color="#f59e0b",
                error_color="#ef4444",
                neutral_color="#6b7280",
                background_gradient=f"linear-gradient(135deg, {color}15 0%, {color}08 100%)",
                typography={"font_family": "system-ui, sans-serif"},
                icon_style="outline",
                visual_personality="professional",
                color_psychology=ColorPsychology.TRUST,
                accessibility_score=0.8
            )
        
        return fallback_themes
    
    async def _generate_fallback_names(self, templates: List[TemplateArchitecture]) -> Dict[str, SmartTemplateName]:
        """Generate fallback names when AI fails"""
        
        fallback_names = {}
        
        for i, template in enumerate(templates):
            fallback_names[template.template_id] = SmartTemplateName(
                template_id=template.template_id,
                primary_name=f"Analytics Dashboard {i+1}",
                alternative_names=[f"Business View {i+1}", f"Dashboard {i+1}"],
                description=f"Business analytics dashboard {i+1}",
                target_audience="Business Users",
                business_context="General Business",
                naming_confidence=0.5,
                semantic_tags=["dashboard", "analytics"]
            )
        
        return fallback_names 