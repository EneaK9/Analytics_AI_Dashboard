"use client";

import React, { useState } from "react";
import {
	Package,
	TrendingUp,
	DollarSign,
	BarChart3,
	Users,
	Megaphone,
	Settings,
	CheckCircle,
	ArrowRight,
	Sparkles,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export enum DashboardTemplateType {
	INVENTORY = "inventory",
	SALES = "sales",
	FINANCIAL = "financial",
	MARKETING = "marketing",
	OPERATIONS = "operations",
	ECOMMERCE = "ecommerce",
	GENERAL = "general",
}

interface DashboardTemplate {
	type: DashboardTemplateType;
	title: string;
	description: string;
	icon: React.ReactNode;
	features: string[];
	recommended: boolean;
	colorScheme: {
		primary: string;
		secondary: string;
		background: string;
	};
	requiredDataTypes: string[];
}

interface DashboardTemplateSelectorProps {
	selectedTemplate?: DashboardTemplateType;
	onTemplateSelect: (template: DashboardTemplateType) => void;
	onContinue?: () => void;
	showContinue?: boolean;
	className?: string;
	userDataColumns?: string[];
}

const templates: DashboardTemplate[] = [
	{
		type: DashboardTemplateType.INVENTORY,
		title: "Inventory Management",
		description:
			"Track stock levels, manage SKUs, monitor turnover rates, and receive low-stock alerts",
		icon: <Package className="h-8 w-8" />,
		features: [
			"SKU tracking and management",
			"Low stock and overstock alerts",
			"Inventory turnover analysis",
			"Stock level trends",
			"Reorder point monitoring",
		],
		recommended: false,
		colorScheme: {
			primary: "#2563eb",
			secondary: "#f97316",
			background: "from-blue-50 to-indigo-50",
		},
		requiredDataTypes: ["sku", "stock", "inventory", "quantity", "product"],
	},
	{
		type: DashboardTemplateType.SALES,
		title: "Sales Performance",
		description:
			"Monitor revenue, track sales trends, analyze customer behavior, and measure conversion rates",
		icon: <TrendingUp className="h-8 w-8" />,
		features: [
			"Revenue and sales tracking",
			"Customer acquisition metrics",
			"Product performance analysis",
			"Sales trend visualization",
			"Conversion rate optimization",
		],
		recommended: true,
		colorScheme: {
			primary: "#16a34a",
			secondary: "#2563eb",
			background: "from-green-50 to-emerald-50",
		},
		requiredDataTypes: ["sales", "revenue", "customer", "order", "conversion"],
	},
	{
		type: DashboardTemplateType.FINANCIAL,
		title: "Financial Analytics",
		description:
			"Track revenue, expenses, profit margins, cash flow, and financial KPIs for business health",
		icon: <DollarSign className="h-8 w-8" />,
		features: [
			"Profit & loss analysis",
			"Cash flow monitoring",
			"Expense categorization",
			"Financial ratios",
			"Budget vs actual tracking",
		],
		recommended: false,
		colorScheme: {
			primary: "#059669",
			secondary: "#dc2626",
			background: "from-emerald-50 to-teal-50",
		},
		requiredDataTypes: ["revenue", "expenses", "profit", "cash", "financial"],
	},
	{
		type: DashboardTemplateType.ECOMMERCE,
		title: "E-commerce Dashboard",
		description:
			"Monitor online store performance, product analytics, customer journey, and order fulfillment",
		icon: <BarChart3 className="h-8 w-8" />,
		features: [
			"Product performance tracking",
			"Order fulfillment analytics",
			"Customer behavior insights",
			"Shopping cart analysis",
			"Revenue optimization",
		],
		recommended: false,
		colorScheme: {
			primary: "#3b82f6",
			secondary: "#8b5cf6",
			background: "from-blue-50 to-purple-50",
		},
		requiredDataTypes: ["product", "order", "customer", "cart", "ecommerce"],
	},
	{
		type: DashboardTemplateType.MARKETING,
		title: "Marketing Analytics",
		description:
			"Track campaign performance, lead generation, customer acquisition cost, and marketing ROI",
		icon: <Megaphone className="h-8 w-8" />,
		features: [
			"Campaign performance tracking",
			"Lead generation analytics",
			"Customer acquisition cost",
			"Marketing ROI analysis",
			"Channel attribution",
		],
		recommended: false,
		colorScheme: {
			primary: "#f59e0b",
			secondary: "#3b82f6",
			background: "from-amber-50 to-yellow-50",
		},
		requiredDataTypes: ["campaign", "leads", "marketing", "acquisition", "roi"],
	},
	{
		type: DashboardTemplateType.OPERATIONS,
		title: "Operations Dashboard",
		description:
			"Monitor operational efficiency, process performance, resource utilization, and productivity metrics",
		icon: <Settings className="h-8 w-8" />,
		features: [
			"Process efficiency tracking",
			"Resource utilization",
			"Productivity metrics",
			"Quality control",
			"Operational KPIs",
		],
		recommended: false,
		colorScheme: {
			primary: "#8b5cf6",
			secondary: "#06b6d4",
			background: "from-purple-50 to-indigo-50",
		},
		requiredDataTypes: [
			"process",
			"efficiency",
			"productivity",
			"operations",
			"quality",
		],
	},
	{
		type: DashboardTemplateType.GENERAL,
		title: "General Analytics",
		description:
			"Flexible dashboard for any type of data analysis with customizable charts and metrics",
		icon: <BarChart3 className="h-8 w-8" />,
		features: [
			"Flexible data visualization",
			"Customizable metrics",
			"Multi-purpose analytics",
			"Adaptable layouts",
			"General business insights",
		],
		recommended: false,
		colorScheme: {
			primary: "#64748b",
			secondary: "#475569",
			background: "from-slate-50 to-gray-50",
		},
		requiredDataTypes: ["general", "data", "analytics"],
	},
];

export default function DashboardTemplateSelector({
	selectedTemplate,
	onTemplateSelect,
	onContinue,
	showContinue = true,
	className = "",
	userDataColumns = [],
}: DashboardTemplateSelectorProps) {
	const [hoveredTemplate, setHoveredTemplate] =
		useState<DashboardTemplateType | null>(null);

	// Auto-recommend template based on user data columns
	const getRecommendedTemplate = () => {
		if (userDataColumns.length === 0) return DashboardTemplateType.GENERAL;

		const columnText = userDataColumns.join(" ").toLowerCase();

		// Check for inventory indicators
		if (
			userDataColumns.some((col) =>
				["sku", "stock", "inventory", "quantity", "warehouse"].some(
					(indicator) => col.toLowerCase().includes(indicator)
				)
			)
		) {
			return DashboardTemplateType.INVENTORY;
		}

		// Check for sales indicators
		if (
			userDataColumns.some((col) =>
				["sales", "revenue", "order", "customer", "purchase"].some(
					(indicator) => col.toLowerCase().includes(indicator)
				)
			)
		) {
			return DashboardTemplateType.SALES;
		}

		// Check for financial indicators
		if (
			userDataColumns.some((col) =>
				["profit", "expense", "cost", "cash", "financial"].some((indicator) =>
					col.toLowerCase().includes(indicator)
				)
			)
		) {
			return DashboardTemplateType.FINANCIAL;
		}

		// Check for ecommerce indicators
		if (
			userDataColumns.some((col) =>
				["product", "category", "cart", "checkout", "shipping"].some(
					(indicator) => col.toLowerCase().includes(indicator)
				)
			)
		) {
			return DashboardTemplateType.ECOMMERCE;
		}

		return DashboardTemplateType.GENERAL;
	};

	const recommendedTemplate = getRecommendedTemplate();

	const handleTemplateSelect = (templateType: DashboardTemplateType) => {
		onTemplateSelect(templateType);
	};

	const isTemplateRecommended = (template: DashboardTemplate) => {
		return template.type === recommendedTemplate || template.recommended;
	};

	return (
		<div className={`space-y-8 ${className}`}>
			{/* Header */}
			<div className="text-center">
				<h2 className="text-3xl font-bold text-gray-900 mb-4">
					Choose Your Dashboard Template
				</h2>
				<p className="text-lg text-gray-600 max-w-2xl mx-auto">
					Select a pre-built dashboard template that matches your business
					needs. Each template includes relevant KPIs, charts, and analytics
					tailored to your industry.
				</p>
				{userDataColumns.length > 0 && (
					<div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg">
						<Sparkles className="h-4 w-4" />
						<span className="text-sm font-medium">
							Based on your data, we recommend the{" "}
							{templates.find((t) => t.type === recommendedTemplate)?.title}{" "}
							template
						</span>
					</div>
				)}
			</div>

			{/* Template Grid */}
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
				{templates.map((template) => {
					const isSelected = selectedTemplate === template.type;
					const isRecommended = isTemplateRecommended(template);
					const isHovered = hoveredTemplate === template.type;

					return (
						<Card
							key={template.type}
							className={`relative cursor-pointer transition-all duration-300 transform hover:-translate-y-2 hover:shadow-xl border-2 ${
								isSelected
									? "border-blue-500 shadow-lg ring-2 ring-blue-200"
									: "border-gray-200 hover:border-gray-300"
							} ${
								isRecommended ? "ring-2 ring-green-200 border-green-300" : ""
							}`}
							onClick={() => handleTemplateSelect(template.type)}
							onMouseEnter={() => setHoveredTemplate(template.type)}
							onMouseLeave={() => setHoveredTemplate(null)}>
							{/* Recommended Badge */}
							{isRecommended && (
								<div className="absolute -top-3 -right-3 z-10">
									<div className="bg-green-500 text-white px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
										<Sparkles className="h-3 w-3" />
										Recommended
									</div>
								</div>
							)}

							{/* Selected Badge */}
							{isSelected && (
								<div className="absolute -top-3 -left-3 z-10">
									<div className="bg-blue-500 text-white p-2 rounded-full">
										<CheckCircle className="h-4 w-4" />
									</div>
								</div>
							)}

							<CardHeader
								className={`pb-4 bg-gradient-to-br ${template.colorScheme.background} rounded-t-lg`}>
								<div className="flex items-center gap-4 mb-4">
									<div
										className="p-3 rounded-xl shadow-sm"
										style={{
											backgroundColor: template.colorScheme.primary + "20",
											color: template.colorScheme.primary,
										}}>
										{template.icon}
									</div>
									<div className="flex-1">
										<CardTitle className="text-xl font-bold text-gray-900">
											{template.title}
										</CardTitle>
									</div>
								</div>
								<p className="text-gray-700 leading-relaxed">
									{template.description}
								</p>
							</CardHeader>

							<CardContent className="pt-4">
								{/* Features List */}
								<div className="space-y-3">
									<h4 className="font-semibold text-gray-900 text-sm">
										Key Features:
									</h4>
									<ul className="space-y-2">
										{template.features
											.slice(0, isHovered ? template.features.length : 3)
											.map((feature, index) => (
												<li
													key={index}
													className="flex items-start gap-2 text-sm text-gray-600">
													<CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
													<span>{feature}</span>
												</li>
											))}
										{!isHovered && template.features.length > 3 && (
											<li className="text-sm text-gray-500 font-medium">
												+{template.features.length - 3} more features...
											</li>
										)}
									</ul>
								</div>

								{/* Data Requirements */}
								<div className="mt-4 pt-4 border-t border-gray-100">
									<h4 className="font-semibold text-gray-900 text-sm mb-2">
										Works best with:
									</h4>
									<div className="flex flex-wrap gap-1">
										{template.requiredDataTypes.slice(0, 3).map((dataType) => (
											<span
												key={dataType}
												className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
												{dataType}
											</span>
										))}
										{template.requiredDataTypes.length > 3 && (
											<span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
												+{template.requiredDataTypes.length - 3} more
											</span>
										)}
									</div>
								</div>

								{/* Action Button */}
								<div className="mt-6">
									<button
										onClick={(e) => {
											e.stopPropagation();
											handleTemplateSelect(template.type);
										}}
										className={`w-full py-3 px-4 rounded-lg font-semibold transition-all duration-200 flex items-center justify-center gap-2 ${
											isSelected
												? "bg-blue-600 text-white shadow-lg hover:bg-blue-700"
												: "bg-gray-100 text-gray-700 hover:bg-gray-200"
										}`}>
										{isSelected ? (
											<>
												<CheckCircle className="h-4 w-4" />
												Selected
											</>
										) : (
											<>
												Select Template
												<ArrowRight className="h-4 w-4" />
											</>
										)}
									</button>
								</div>
							</CardContent>
						</Card>
					);
				})}
			</div>

			{/* Continue Button */}
			{showContinue && selectedTemplate && onContinue && (
				<div className="text-center">
					<button
						onClick={onContinue}
						className="px-8 py-4 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1 flex items-center gap-3 mx-auto">
						Continue with{" "}
						{templates.find((t) => t.type === selectedTemplate)?.title} Template
						<ArrowRight className="h-5 w-5" />
					</button>
				</div>
			)}

			{/* Template Comparison */}
			{selectedTemplate && (
				<div className="mt-8 p-6 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
					<div className="text-center">
						<h3 className="text-xl font-bold text-gray-900 mb-2">
							You selected:{" "}
							{templates.find((t) => t.type === selectedTemplate)?.title}
						</h3>
						<p className="text-gray-700 mb-4">
							{templates.find((t) => t.type === selectedTemplate)?.description}
						</p>
						<div className="flex flex-wrap justify-center gap-2">
							{templates
								.find((t) => t.type === selectedTemplate)
								?.features.map((feature, index) => (
									<span
										key={index}
										className="px-3 py-1 bg-white text-blue-700 text-sm rounded-full border border-blue-200">
										{feature}
									</span>
								))}
						</div>
					</div>
				</div>
			)}
		</div>
	);
}
