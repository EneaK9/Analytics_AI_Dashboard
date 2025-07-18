// Existing components
export { default as StatsCard } from "./StatsCard";
export { default as RevenueChart } from "./RevenueChart";
export { default as ExpensesChart } from "./ExpensesChart";
export { default as BusinessOptimization } from "./BusinessOptimization";

// New Tailwind UI Analytics Components
export {
	StatCard,
	SimpleStatCard,
	SimpleStats,
	ChartCard,
} from "./TailwindStats";
export {
	SimpleBarChart,
	SimpleLineChart,
	SimplePieChart,
} from "./TailwindCharts";
export { default as PersonalizedDashboard } from "./PersonalizedDashboard";

// Export types
export type { RevenueData, ExpenseData } from "./types";
