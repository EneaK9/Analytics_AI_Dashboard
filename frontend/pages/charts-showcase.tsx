import React from "react";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { ChartContainer, type ChartConfig } from "@/components/ui/chart";

// Import all chart components
import {
	// Area Charts (5)
	ShadcnAreaChart,
	ShadcnAreaInteractive,
	ShadcnAreaLinear,
	ShadcnAreaStep,
	ShadcnAreaStacked,
	// Bar Charts (9)
	ShadcnBarChart,
	ShadcnBarDefault,
	ShadcnBarHorizontal,
	ShadcnBarLabel,
	ShadcnBarLabelCustom,
	ShadcnBarMixed,
	ShadcnBarMultiple,
	ShadcnBarNegative,
	ShadcnBarStacked,
	// Pie Charts (6)
	ShadcnPieChart,
	ShadcnPieChartLabel,
	ShadcnPieDonutText,
	ShadcnPieInteractive,
	ShadcnPieLegend,
	ShadcnPieSimple,
	// Radar Charts (5)
	ShadcnRadarDefault,
	ShadcnRadarGridFill,
	ShadcnRadarLegend,
	ShadcnRadarLinesOnly,
	ShadcnRadarMultiple,
	// Radial Charts (6)
	ShadcnRadialChart,
	ShadcnRadialLabel,
	ShadcnRadialGrid,
	ShadcnRadialText,
	ShadcnRadialShape,
	ShadcnRadialStacked,
} from "../components/charts";

// Sample data for different chart types
const sampleTimeSeriesData = [
	{ name: "Jan", value: 400, desktop: 240, mobile: 160 },
	{ name: "Feb", value: 300, desktop: 420, mobile: 180 },
	{ name: "Mar", value: 200, desktop: 380, mobile: 220 },
	{ name: "Apr", value: 278, desktop: 290, mobile: 140 },
	{ name: "May", value: 189, desktop: 350, mobile: 200 },
	{ name: "Jun", value: 239, desktop: 310, mobile: 170 },
];

const sampleCategoricalData = [
	{ name: "Product A", value: 400 },
	{ name: "Product B", value: 300 },
	{ name: "Product C", value: 200 },
	{ name: "Product D", value: 278 },
	{ name: "Product E", value: 189 },
];

const sampleNegativeData = [
	{ name: "Jan", value: 100 },
	{ name: "Feb", value: -50 },
	{ name: "Mar", value: 80 },
	{ name: "Apr", value: -30 },
	{ name: "May", value: 120 },
	{ name: "Jun", value: -20 },
];

const samplePieData = [
	{ name: "Desktop", value: 400 },
	{ name: "Mobile", value: 300 },
	{ name: "Tablet", value: 200 },
	{ name: "Other", value: 100 },
];

const sampleRadarData = [
	{ month: "Performance", desktop: 120, mobile: 80 },
	{ month: "Reliability", desktop: 98, mobile: 85 },
	{ month: "Usability", desktop: 86, mobile: 90 },
	{ month: "Security", desktop: 99, mobile: 75 },
	{ month: "Speed", desktop: 85, mobile: 88 },
	{ month: "Features", desktop: 65, mobile: 70 },
];

const sampleRadialData = [
	{ name: "Progress", value: 75, desktop: 90, percentage: 75 },
	{ name: "Performance", value: 60, desktop: 85, percentage: 60 },
	{ name: "Quality", value: 85, desktop: 95, percentage: 85 },
];

// Chart config for all components
const chartConfig: ChartConfig = {
	data: {
		label: "Data",
		color: "hsl(var(--chart-1))",
	},
	desktop: {
		label: "Desktop",
		color: "hsl(var(--chart-1))",
	},
	mobile: {
		label: "Mobile",
		color: "hsl(var(--chart-2))",
	},
	value: {
		label: "Value",
		color: "hsl(var(--chart-1))",
	},
};

interface ChartShowcaseProps {
	title: string;
	description: string;
	componentName: string;
	category: string;
	children: React.ReactNode;
}

const ChartShowcase: React.FC<ChartShowcaseProps> = ({
	title,
	description,
	componentName,
	category,
	children,
}) => (
	<Card className="w-full">
		<CardHeader className="pb-4">
			<div className="flex items-center justify-between">
				<div>
					<CardTitle className="text-lg font-semibold">{title}</CardTitle>
					<CardDescription className="text-sm text-muted-foreground mt-1">
						{description}
					</CardDescription>
				</div>
				<div className="text-right">
					<div className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
						{componentName}
					</div>
					<div className="text-xs text-blue-600 mt-1 font-medium">
						{category}
					</div>
				</div>
			</div>
		</CardHeader>
		<CardContent>
			<div className="h-[300px] w-full">{children}</div>
		</CardContent>
	</Card>
);

const ChartsShowcase: React.FC = () => {
	return (
		<div className="min-h-screen bg-gray-50 py-8">
			<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				{/* Page Header */}
				<div className="text-center mb-12">
					<h1 className="text-4xl font-bold text-gray-900 mb-4">
						📊 Complete Charts Showcase
					</h1>
					<p className="text-xl text-gray-600 max-w-3xl mx-auto">
						Full collection of all Shadcn chart components available in your
						system. Each chart type with multiple variations and styles.
					</p>
					<div className="mt-6 text-sm text-gray-500">
						Total Components:{" "}
						<span className="font-semibold text-blue-600">31 Chart Types</span>
					</div>
				</div>

				{/* Category: Area Charts */}
				<section className="mb-12">
					<h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
						<span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-lg text-lg mr-3">
							📊 AREA CHARTS
						</span>
						(5 variants)
					</h2>
					<div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
						<ChartShowcase
							title="Area Chart (Basic)"
							description="Standard filled area chart"
							componentName="ShadcnAreaChart"
							category="Area Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnAreaChart data={sampleTimeSeriesData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Area Chart Interactive"
							description="Interactive with hover effects"
							componentName="ShadcnAreaInteractive"
							category="Area Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnAreaInteractive
									data={sampleTimeSeriesData}
									minimal={true}
								/>
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Area Chart Linear"
							description="Smooth linear curves"
							componentName="ShadcnAreaLinear"
							category="Area Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnAreaLinear data={sampleTimeSeriesData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Area Chart Step"
							description="Step-wise transitions"
							componentName="ShadcnAreaStep"
							category="Area Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnAreaStep data={sampleTimeSeriesData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Area Chart Stacked"
							description="Multiple series stacked"
							componentName="ShadcnAreaStacked"
							category="Area Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnAreaStacked data={sampleTimeSeriesData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>
					</div>
				</section>

				{/* Category: Bar Charts */}
				<section className="mb-12">
					<h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
						<span className="bg-green-100 text-green-800 px-3 py-1 rounded-lg text-lg mr-3">
							📈 BAR CHARTS
						</span>
						(9 variants)
					</h2>
					<div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
						<ChartShowcase
							title="Bar Chart (Basic)"
							description="Standard vertical bars"
							componentName="ShadcnBarChart"
							category="Bar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnBarChart data={sampleCategoricalData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Bar Chart Default"
							description="Default Shadcn bar chart"
							componentName="ShadcnBarDefault"
							category="Bar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnBarDefault data={sampleCategoricalData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Bar Chart with Labels"
							description="Shows values on bars"
							componentName="ShadcnBarLabel"
							category="Bar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnBarLabel data={sampleCategoricalData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Bar Chart Custom Label"
							description="Custom label positioning"
							componentName="ShadcnBarLabelCustom"
							category="Bar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnBarLabelCustom
									data={sampleTimeSeriesData}
									minimal={true}
								/>
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Bar Chart Horizontal"
							description="Horizontal orientation"
							componentName="ShadcnBarHorizontal"
							category="Bar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnBarHorizontal
									data={sampleCategoricalData}
									minimal={true}
								/>
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Bar Chart Multiple"
							description="Multiple data series"
							componentName="ShadcnBarMultiple"
							category="Bar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnBarMultiple data={sampleTimeSeriesData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Bar Chart Mixed"
							description="Mixed orientation"
							componentName="ShadcnBarMixed"
							category="Bar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnBarMixed data={sampleCategoricalData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Bar Chart Negative"
							description="Supports negative values"
							componentName="ShadcnBarNegative"
							category="Bar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnBarNegative data={sampleNegativeData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Bar Chart Stacked"
							description="Stacked with legend"
							componentName="ShadcnBarStacked"
							category="Bar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnBarStacked data={sampleTimeSeriesData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>
					</div>
				</section>

				{/* Category: Pie Charts */}
				<section className="mb-12">
					<h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
						<span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-lg text-lg mr-3">
							🥧 PIE CHARTS
						</span>
						(6 variants)
					</h2>
					<div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
						<ChartShowcase
							title="Pie Chart (Basic)"
							description="Standard pie chart"
							componentName="ShadcnPieChart"
							category="Pie Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnPieChart data={samplePieData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Pie Chart Simple"
							description="Simple pie chart"
							componentName="ShadcnPieSimple"
							category="Pie Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnPieSimple data={samplePieData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Pie Chart with Labels"
							description="With percentage labels"
							componentName="ShadcnPieChartLabel"
							category="Pie Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnPieChartLabel data={samplePieData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Pie Chart Legend"
							description="With external legend"
							componentName="ShadcnPieLegend"
							category="Pie Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnPieLegend data={samplePieData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Pie Chart Interactive"
							description="Interactive with dropdown"
							componentName="ShadcnPieInteractive"
							category="Pie Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnPieInteractive data={samplePieData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Pie Chart Donut with Text"
							description="Donut with center text"
							componentName="ShadcnPieDonutText"
							category="Pie Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnPieDonutText data={samplePieData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>
					</div>
				</section>

				{/* Category: Radar Charts */}
				<section className="mb-12">
					<h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
						<span className="bg-orange-100 text-orange-800 px-3 py-1 rounded-lg text-lg mr-3">
							🎯 RADAR CHARTS
						</span>
						(5 variants)
					</h2>
					<div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
						<ChartShowcase
							title="Radar Chart Default"
							description="Default Shadcn radar chart"
							componentName="ShadcnRadarDefault"
							category="Radar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnRadarDefault data={sampleRadarData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Radar Chart Lines Only"
							description="Lines only radar chart"
							componentName="ShadcnRadarLinesOnly"
							category="Radar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnRadarLinesOnly data={sampleRadarData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Radar Chart Grid Fill"
							description="Grid filled radar chart"
							componentName="ShadcnRadarGridFill"
							category="Radar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnRadarGridFill data={sampleRadarData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Radar Chart Multiple"
							description="Multiple data radar chart"
							componentName="ShadcnRadarMultiple"
							category="Radar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnRadarMultiple data={sampleRadarData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Radar Chart Legend"
							description="Radar chart with legend"
							componentName="ShadcnRadarLegend"
							category="Radar Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnRadarLegend data={sampleRadarData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>
					</div>
				</section>

				{/* Category: Radial Charts */}
				<section className="mb-12">
					<h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
						<span className="bg-pink-100 text-pink-800 px-3 py-1 rounded-lg text-lg mr-3">
							📉 RADIAL CHARTS
						</span>
						(6 variants)
					</h2>
					<div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
						<ChartShowcase
							title="Radial Chart (Basic)"
							description="Basic circular progress"
							componentName="ShadcnRadialChart"
							category="Radial Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnRadialChart data={sampleRadialData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Radial Chart Label"
							description="With external labels"
							componentName="ShadcnRadialLabel"
							category="Radial Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnRadialLabel data={sampleRadialData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Radial Chart Grid"
							description="With grid lines"
							componentName="ShadcnRadialGrid"
							category="Radial Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnRadialGrid data={sampleRadialData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Radial Chart Text"
							description="With center text display"
							componentName="ShadcnRadialText"
							category="Radial Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnRadialText data={sampleRadialData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Radial Chart Shape"
							description="Custom shaped progress"
							componentName="ShadcnRadialShape"
							category="Radial Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnRadialShape data={sampleRadialData} minimal={true} />
							</ChartContainer>
						</ChartShowcase>

						<ChartShowcase
							title="Radial Chart Stacked"
							description="Multiple stacked rings"
							componentName="ShadcnRadialStacked"
							category="Radial Charts">
							<ChartContainer config={chartConfig} className="h-full w-full">
								<ShadcnRadialStacked
									data={sampleTimeSeriesData}
									minimal={true}
								/>
							</ChartContainer>
						</ChartShowcase>
					</div>
				</section>

				{/* Summary Stats */}
				<section className="bg-white rounded-xl shadow-lg p-8 mb-8">
					<h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">
						📊 Complete Component Summary
					</h2>
					<div className="grid grid-cols-1 md:grid-cols-5 gap-6">
						<div className="text-center">
							<div className="text-3xl font-bold text-blue-600">5</div>
							<div className="text-gray-600">Area Charts</div>
						</div>
						<div className="text-center">
							<div className="text-3xl font-bold text-green-600">9</div>
							<div className="text-gray-600">Bar Charts</div>
						</div>
						<div className="text-center">
							<div className="text-3xl font-bold text-purple-600">6</div>
							<div className="text-gray-600">Pie Charts</div>
						</div>
						<div className="text-center">
							<div className="text-3xl font-bold text-orange-600">5</div>
							<div className="text-gray-600">Radar Charts</div>
						</div>
						<div className="text-center">
							<div className="text-3xl font-bold text-pink-600">6</div>
							<div className="text-gray-600">Radial Charts</div>
						</div>
					</div>
					<div className="mt-6 text-center">
						<div className="text-2xl font-bold text-gray-800">
							Total: 31 Chart Components Available
						</div>
						<p className="text-gray-600 mt-2">
							All components are Shadcn-based with consistent styling and
							theming
						</p>
					</div>
				</section>

				{/* Navigation */}
				<div className="text-center">
					<button
						onClick={() => window.history.back()}
						className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200">
						← Back to Dashboard
					</button>
				</div>
			</div>
		</div>
	);
};

export default ChartsShowcase;
