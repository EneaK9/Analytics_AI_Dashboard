import { useState, useEffect, useCallback } from 'react';
import api from '../lib/axios';

interface LLMTable {
	display_name: string;
	columns: string[];
	data: any[];
}

interface LLMChart {
	display_name: string;
	chart_type: string;
	data: any[];
	x_axis?: string;
	y_axis?: string;
}

interface LLMKpi {
	display_name: string;
	value: string | number;
	format?: string;
	trend?: 'up' | 'down' | 'neutral';
	change?: string;
}

interface LLMAnalysis {
	kpis?: LLMKpi[];
	charts?: LLMChart[];
	tables?: LLMTable[];
	business_analysis?: string;
	performance_insights?: string;
	recommendations?: string[];
}

interface DashboardMetricsResponse {
	llm_analysis: LLMAnalysis;
	success: boolean;
	message?: string;
}

interface UseDashboardMetricsReturn {
    data: LLMAnalysis | null;
    loading: boolean;
    error: string | null;
    refetch: (opts?: { startDate?: string; endDate?: string; preset?: string }) => Promise<void>;
}

// COMMENTED OUT: This hook uses the dashboard/metrics endpoint
// export function useDashboardMetrics(userId?: string): UseDashboardMetricsReturn {
// 	const [data, setData] = useState<LLMAnalysis | null>(null);
// 	const [loading, setLoading] = useState(true);
// 	const [error, setError] = useState<string | null>(null);

//     const fetchData = useCallback(async (opts?: { startDate?: string; endDate?: string; preset?: string }) => {
// 		if (!userId) {
// 			setData(null);
// 			setLoading(false);
// 			return;
// 		}

// 		try {
// 			setLoading(true);
// 			setError(null);
			
// 			console.log("🚀 Fetching dashboard metrics from hook");
//             const params: string[] = ["fast_mode=true"];
//             if (opts?.startDate) params.push(`start_date=${encodeURIComponent(opts.startDate)}`);
//             if (opts?.endDate) params.push(`end_date=${encodeURIComponent(opts.endDate)}`);
//             if (opts?.preset) params.push(`preset=${encodeURIComponent(opts.preset)}`);
//             const query = params.length ? `?${params.join("&")}` : "";
//             const response = await api.get(`/dashboard/metrics${query}`);

// 			if (response.data && response.data.llm_analysis) {
// 				const analysis = response.data.llm_analysis;
// 				setData(analysis);
				
// 				console.log("✅ Dashboard metrics loaded via hook:", {
// 					hasKpis: !!analysis.kpis,
// 					kpisCount: analysis.kpis?.length || 0,
// 					hasCharts: !!analysis.charts,
// 					chartsCount: analysis.charts?.length || 0,
// 					hasTables: !!analysis.tables,
// 					tablesCount: analysis.tables?.length || 0,
// 				});
// 			} else {
// 				console.warn("⚠️ No LLM analysis found in response");
// 				setData(null);
// 			}
// 		} catch (err: any) {
// 			console.error("❌ Error fetching dashboard metrics:", err);
// 			setError(err.response?.data?.detail || err.message || "Failed to load dashboard metrics");
// 			setData(null);
// 		} finally {
// 			setLoading(false);
// 		}
//     }, [userId]);

// 	// Initial load
// 	useEffect(() => {
// 		fetchData();
// 	}, [userId]); // Use userId directly instead of fetchData to avoid infinite loop

// 	// Return the hook interface
// 	return {
// 		data,
// 		loading,
// 		error,
// 		refetch: fetchData
// 	};
// }

// Fallback hook that returns empty data
export function useDashboardMetrics(userId?: string): UseDashboardMetricsReturn {
	return {
		data: null,
		loading: false,
		error: null,
		refetch: async () => {
			console.log("🚫 Dashboard metrics hook is disabled");
		}
	};
}

export default useDashboardMetrics;
