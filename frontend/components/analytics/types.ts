// Type definitions for analytics data
export interface RevenueData {
	month: string;
	revenue: number;
}

export interface ExpenseData {
	category: string;
	amount: number;
}

export interface DashboardData {
	revenue: RevenueData[];
	expenses: ExpenseData[];
}
