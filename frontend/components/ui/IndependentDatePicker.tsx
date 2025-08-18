/**
 * Independent Date Picker Component
 * Each metric component gets its own date picker that doesn't affect others
 */

import React, { memo, useCallback } from 'react';
import { Calendar, Clock } from 'lucide-react';
import { DateRange } from '../../hooks/useOptimizedDashboardData';

interface IndependentDatePickerProps {
  dateRange: DateRange;
  onDateRangeChange: (dateRange: DateRange) => void;
  platform: 'shopify' | 'amazon' | 'combined';
  disabled?: boolean;
  className?: string;
}

const presetOptions = [
  { value: '7d', label: '7 Days', days: 7 },
  { value: '30d', label: '30 Days', days: 30 },
  { value: '90d', label: '90 Days', days: 90 },
] as const;

const formatDateForAPI = (date: Date): string => {
  return date.toISOString().split('T')[0];
};

const getDateRangeFromPreset = (preset: '7d' | '30d' | '90d'): DateRange => {
  const endDate = new Date();
  const startDate = new Date();
  
  switch (preset) {
    case '7d':
      startDate.setDate(endDate.getDate() - 7);
      break;
    case '30d':
      startDate.setDate(endDate.getDate() - 30);
      break;
    case '90d':
      startDate.setDate(endDate.getDate() - 90);
      break;
  }
  
  return {
    startDate: formatDateForAPI(startDate),
    endDate: formatDateForAPI(endDate),
    preset,
  };
};

const IndependentDatePicker: React.FC<IndependentDatePickerProps> = memo(({
  dateRange,
  onDateRangeChange,
  platform,
  disabled = false,
  className = '',
}) => {
  const handlePresetChange = useCallback((preset: '7d' | '30d' | '90d') => {
    const newDateRange = getDateRangeFromPreset(preset);
    onDateRangeChange(newDateRange);
  }, [onDateRangeChange]);

  const handleCustomDateChange = useCallback((field: 'startDate' | 'endDate', value: string) => {
    const newDateRange: DateRange = {
      ...dateRange,
      [field]: value,
      preset: 'custom',
    };
    onDateRangeChange(newDateRange);
  }, [dateRange, onDateRangeChange]);

  const getPlatformColor = () => {
    switch (platform) {
      case 'shopify':
        return 'border-green-200 bg-green-50';
      case 'amazon':
        return 'border-orange-200 bg-orange-50';
      case 'combined':
        return 'border-blue-200 bg-blue-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg border ${getPlatformColor()} ${className}`}>
      {/* Platform indicator */}
      <div className="flex items-center gap-2">
        <Calendar className="h-4 w-4 text-gray-600" />
        <span className="text-sm font-medium text-gray-700 capitalize">
          {platform === 'combined' ? 'All Platforms' : platform}
        </span>
      </div>

      {/* Preset buttons */}
      <div className="flex rounded-md border border-gray-300 bg-white overflow-hidden">
        {presetOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => handlePresetChange(option.value)}
            disabled={disabled}
            className={`px-3 py-1 text-sm font-medium transition-colors border-r border-gray-300 last:border-r-0 ${
              dateRange.preset === option.value
                ? 'bg-blue-500 text-white'
                : 'text-gray-600 hover:bg-gray-50 disabled:hover:bg-white'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {/* Custom date inputs */}
      <div className="flex items-center gap-2 text-sm">
        <Clock className="h-3 w-3 text-gray-500" />
        <input
          type="date"
          value={dateRange.startDate}
          onChange={(e) => handleCustomDateChange('startDate', e.target.value)}
          disabled={disabled}
          className="px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
        <span className="text-gray-400">to</span>
        <input
          type="date"
          value={dateRange.endDate}
          onChange={(e) => handleCustomDateChange('endDate', e.target.value)}
          disabled={disabled}
          className="px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
      </div>

      {/* Current range indicator */}
      {dateRange.preset && (
        <div className="text-xs text-gray-500 bg-white px-2 py-1 rounded border">
          Last {presetOptions.find(p => p.value === dateRange.preset)?.days} days
        </div>
      )}
    </div>
  );
});

IndependentDatePicker.displayName = 'IndependentDatePicker';

export default IndependentDatePicker;
