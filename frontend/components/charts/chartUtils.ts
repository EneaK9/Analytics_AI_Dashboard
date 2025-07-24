// Chart utility functions for consistent data handling across all chart components

export interface BaseChartProps {
	data?: any[];
	dropdown_options?: Array<{ value: string; label: string }>;
	title?: string;
	description?: string;
	minimal?: boolean;
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
