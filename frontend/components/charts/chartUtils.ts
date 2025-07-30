// Chart utility functions for consistent data handling across all chart components

export interface BaseChartProps {
	data?: any[];
	dropdown_options?: Array<{ value: string; label: string }>;
	title?: string;
	description?: string;
	minimal?: boolean;
}

export interface RadarChartProps extends BaseChartProps {
	showLabels?: boolean;
}

export interface ScatterChartProps extends BaseChartProps {
	xAxisLabel?: string;
	yAxisLabel?: string;
}

export interface HeatmapChartProps extends BaseChartProps {
	xAxisLabel?: string;
	yAxisLabel?: string;
}

export interface RadialChartProps extends BaseChartProps {
	showLabels?: boolean;
}

export interface PieChartProps extends BaseChartProps {
	showLegend?: boolean;
	chartType?: 'pie' | 'donut';
}

/**
 * Ensures all chart components receive consistent data structure
 */
export function processChartData(data: any[], fallbackData: any[] = []): any[] {
	if (!data || data.length === 0) {
		return fallbackData;
	}
	return data;
}

/**
 * Validates chart data for specific chart types
 */
export function validateChartData(data: any[], chartType: string): boolean {
	if (!data || data.length === 0) return false;
	
	switch (chartType) {
		case 'RadarChart':
			return data.every(item => item.hasOwnProperty('name') && item.hasOwnProperty('value'));
		case 'ScatterChart':
			return data.every(item => item.hasOwnProperty('x') && item.hasOwnProperty('y'));
		case 'HeatmapChart':
			return data.every(item => item.hasOwnProperty('x') && item.hasOwnProperty('y') && item.hasOwnProperty('value'));
		case 'RadialChart':
		case 'PieChart':
			return data.every(item => item.hasOwnProperty('name') && item.hasOwnProperty('value'));
		default:
			return true;
	}
}

/**
 * Formats data for specific chart types
 */
export function formatDataForChart(data: any[], chartType: string): any[] {
	if (!data || data.length === 0) return [];
	
	switch (chartType) {
		case 'RadarChart':
			return data.map(item => ({
				name: String(item.name || item.category || 'Unknown'),
				value: Number(item.value) || 0
			}));
		case 'ScatterChart':
			return data.map(item => ({
				x: Number(item.x) || 0,
				y: Number(item.y) || 0,
				name: String(item.name || 'Point')
			}));
		case 'HeatmapChart':
			return data.map(item => ({
				x: String(item.x || 'X'),
				y: String(item.y || 'Y'),
				value: Number(item.value) || 0
			}));
		case 'RadialChart':
			// Pass raw values to RadialChart component for percentage calculation
			return data.map(item => ({
				name: String(item.name || item.category || 'Unknown'),
				value: Number(item.value) || 0 // Pass raw value
			}));
		case 'PieChart':
			return data.map(item => ({
				name: String(item.name || item.category || 'Unknown'),
				value: Number(item.value) || 0
			}));
		default:
			return data;
	}
}

/**
 * Generate chart colors consistently
 */
export function getChartColor(index: number): string {
	return `hsl(var(--chart-${(index % 5) + 1}))`;
}

/**
 * Process dropdown options with fallbacks
 */
export function processDropdownOptions(
	backendOptions: Array<{ value: string; label: string }>,
	fallbackOptions: Array<{ value: string; label: string }> = []
): Array<{ value: string; label: string }> {
	if (backendOptions && backendOptions.length > 0) {
		return backendOptions;
	}
	return fallbackOptions;
}

/**
 * Safe data extraction with fallbacks
 */
export function safeExtractValue(
	item: any,
	keys: string[],
	fallback: any = 0
): any {
	for (const key of keys) {
		if (item[key] !== undefined && item[key] !== null && item[key] !== "") {
			const value =
				typeof item[key] === "string"
					? parseFloat(item[key].replace(/[^0-9.-]/g, ""))
					: item[key];
			if (!isNaN(value)) {
				return value;
			}
		}
	}
	return fallback;
}

/**
 * Safe string extraction with fallbacks
 */
export function safeExtractString(
	item: any,
	keys: string[],
	fallback: string = "Unknown"
): string {
	for (const key of keys) {
		if (item[key] !== undefined && item[key] !== null && item[key] !== "") {
			return String(item[key]).trim();
		}
	}
	return fallback;
}
