// Example: How to use TailAdmin Analytics Components as Separate Modules
import React from "react";
import { TrendingUp, DollarSign, PieChart, Users } from "lucide-react";

// Import each analytics component as a separate module
import {
	StatsCard,
	RevenueChart,
	ExpensesChart,
	BusinessOptimization,
	RevenueData,
	ExpenseData,
} from "../components/analytics";

// Sample data for demonstration
const sampleRevenueData: RevenueData[] = [
	{ month: "Jan", revenue: 45000 },
	{ month: "Feb", revenue: 52000 },
	{ month: "Mar", revenue: 48000 },
	{ month: "Apr", revenue: 61000 },
	{ month: "May", revenue: 55000 },
	{ month: "Jun", revenue: 67000 },
];

const sampleExpenseData: ExpenseData[] = [
	{ category: "Office Rent", amount: 25000 },
	{ category: "Marketing", amount: 15000 },
	{ category: "Technology", amount: 12000 },
	{ category: "Operations", amount: 18000 },
];

const AnalyticsModulesExample: React.FC = () => {
	return (
		<div className="p-6 space-y-6">
			<h1 className="text-2xl font-bold">
				TailAdmin Analytics Components - Modular Usage
			</h1>

			{/* Using StatsCard as a separate module */}
			<section>
				<h2 className="text-xl font-semibold mb-4">1. StatsCard Module</h2>
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
					<StatsCard
						title="Total Revenue"
						value="$327,000"
						icon={TrendingUp}
						iconBgColor="bg-meta-3/10"
						iconColor="text-meta-3"
						trend={{ value: "12.5%", isPositive: true }}
					/>

					<StatsCard
						title="Monthly Expenses"
						value="$70,000"
						icon={DollarSign}
						iconBgColor="bg-meta-1/10"
						iconColor="text-meta-1"
						trend={{ value: "3.2%", isPositive: false }}
					/>

					<StatsCard
						title="Net Profit"
						value="$257,000"
						icon={PieChart}
						iconBgColor="bg-primary/10"
						iconColor="text-primary"
						trend={{ value: "18.7%", isPositive: true }}
					/>

					<StatsCard
						title="Active Users"
						value="12,450"
						icon={Users}
						iconBgColor="bg-meta-6/10"
						iconColor="text-meta-6"
						trend={{ value: "8.1%", isPositive: true }}
					/>
				</div>
			</section>

			{/* Using RevenueChart as a separate module */}
			<section>
				<h2 className="text-xl font-semibold mb-4">2. RevenueChart Module</h2>
				<div className="grid grid-cols-1 gap-4">
					<RevenueChart
						data={sampleRevenueData}
						title="Monthly Revenue Analytics"
						subtitle="Revenue performance over the last 6 months"
					/>
				</div>
			</section>

			{/* Using ExpensesChart as a separate module */}
			<section>
				<h2 className="text-xl font-semibold mb-4">3. ExpensesChart Module</h2>
				<div className="grid grid-cols-1 gap-4">
					<ExpensesChart
						data={sampleExpenseData}
						title="Business Expenses Analysis"
						subtitle="Cost breakdown by department"
					/>
				</div>
			</section>

			{/* Using BusinessOptimization as a separate module */}
			<section>
				<h2 className="text-xl font-semibold mb-4">
					4. BusinessOptimization Module
				</h2>
				<div className="grid grid-cols-1 gap-4">
					<BusinessOptimization
						currentExpenses={sampleExpenseData}
						onOptimizationComplete={(result) => {
							console.log("Optimization result:", result);
							alert(`Optimization completed: ${result.message}`);
						}}
					/>
				</div>
			</section>

			{/* Module Import Examples */}
			<section className="bg-gray-50 p-6 rounded-lg">
				<h2 className="text-xl font-semibold mb-4">
					5. How to Import Each Module
				</h2>
				<div className="bg-gray-800 text-green-400 p-4 rounded-lg font-mono text-sm">
					<div className="mb-2">{`// Import individual components as modules`}</div>
					<div className="mb-2">
						import {"{"} StatsCard {"}"} from
						&apos;../components/analytics&apos;;
					</div>
					<div className="mb-2">
						import {"{"} RevenueChart {"}"} from
						&apos;../components/analytics&apos;;
					</div>
					<div className="mb-2">
						import {"{"} ExpensesChart {"}"} from
						&apos;../components/analytics&apos;;
					</div>
					<div className="mb-2">
						import {"{"} BusinessOptimization {"}"} from
						&apos;../components/analytics&apos;;
					</div>
					<div className="mb-4"></div>
					<div className="mb-2">{`// Or import all at once`}</div>
					<div className="mb-2">
						import {"{"}StatsCard, RevenueChart, ExpensesChart,
						BusinessOptimization{"}"} from &apos;../components/analytics&apos;;
					</div>
				</div>
			</section>

			{/* Customization Examples */}
			<section className="bg-blue-50 p-6 rounded-lg">
				<h2 className="text-xl font-semibold mb-4">6. Customization Options</h2>
				<div className="space-y-4">
					<div>
						<h3 className="font-semibold text-blue-800">
							StatsCard Customization:
						</h3>
						<ul className="text-sm text-blue-700 ml-4 list-disc">
							<li>Custom icons from Lucide React</li>
							<li>Custom background colors (iconBgColor)</li>
							<li>Custom icon colors (iconColor)</li>
							<li>Trend indicators (positive/negative)</li>
						</ul>
					</div>

					<div>
						<h3 className="font-semibold text-blue-800">
							Chart Customization:
						</h3>
						<ul className="text-sm text-blue-700 ml-4 list-disc">
							<li>Custom titles and subtitles</li>
							<li>ApexCharts configuration options</li>
							<li>Responsive design</li>
							<li>TailAdmin color scheme</li>
						</ul>
					</div>

					<div>
						<h3 className="font-semibold text-blue-800">
							BusinessOptimization Customization:
						</h3>
						<ul className="text-sm text-blue-700 ml-4 list-disc">
							<li>Custom expense data input</li>
							<li>Callback functions for results</li>
							<li>Loading states</li>
							<li>Error handling</li>
						</ul>
					</div>
				</div>
			</section>
		</div>
	);
};

export default AnalyticsModulesExample;
