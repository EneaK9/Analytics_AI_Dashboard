import * as React from "react";
import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import OutlinedInput from "@mui/material/OutlinedInput";
import InputAdornment from "@mui/material/InputAdornment";
import IconButton from "@mui/material/IconButton";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import ClearIcon from "@mui/icons-material/Clear";
import api from "../../../lib/axios";
interface UseDashboardMetricsReturn {
	data: any;
	loading: boolean;
	error: string | null;
	refetch: () => Promise<void>;
}

interface DateRange {
	start: any;
	end: any;
	label?: string;
}

interface DataTablesPageProps {
	user?: {
		company_name: string;
		email: string;
		client_id: string;
	};
	dashboardMetrics?: UseDashboardMetricsReturn;
	dateRange?: DateRange;
}

export default function DataTablesPage({ user, dashboardMetrics, dateRange }: DataTablesPageProps) {
	// State for date-filtered data
	const [dateFilteredData, setDateFilteredData] = React.useState<any>(null);
	const [isLoadingDateFilter, setIsLoadingDateFilter] = React.useState(false);
	const [dateFilterError, setDateFilterError] = React.useState<string | null>(null);

	// Extract shared dashboard metrics data
	const metricsData = dashboardMetrics?.data;
	const loading = dashboardMetrics?.loading ?? true;
	const error = dashboardMetrics?.error;

	// Helper function to check if dateRange represents "today" (no filtering needed)
	const isDateRangeToday = React.useCallback((dateRange: any) => {
		if (!dateRange || !dateRange.start) return false;
		
		const today = new Date();
		const selectedDate = dateRange.start?.format ? 
			new Date(dateRange.start.format('YYYY-MM-DD')) : 
			new Date(dateRange.start);
		
		return selectedDate.toDateString() === today.toDateString();
	}, []);

	// Load date-filtered data when dateRange changes
	const loadDateFilteredData = React.useCallback(async () => {
		// Check if no date filter or if the date is today (use shared data)
		if (!user?.client_id || !dateRange || (!dateRange.start && !dateRange.end) || isDateRangeToday(dateRange)) {
			const isToday = isDateRangeToday(dateRange);
			console.log(isToday ? "📅 Today selected - using shared data for tables (no filtering needed)" : "📊 No date filter applied - using shared data for tables");
			setDateFilteredData(null);
			setDateFilterError(null);
			return;
		}

		console.log("📅 Loading date-filtered data for Data Tables:", {
			start: dateRange.start?.format ? dateRange.start.format('YYYY-MM-DD') : dateRange.start,
			end: dateRange.end?.format ? dateRange.end.format('YYYY-MM-DD') : dateRange.end,
			label: dateRange.label
		});

		setIsLoadingDateFilter(true);
		setDateFilterError(null);

		try {
			const params = new URLSearchParams();
			params.append('fast_mode', 'true');
			
			if (dateRange.start) {
				const startDate = dateRange.start?.format ? dateRange.start.format('YYYY-MM-DD') : dateRange.start;
				params.append('start_date', startDate);
			}
			if (dateRange.end) {
				const endDate = dateRange.end?.format ? dateRange.end.format('YYYY-MM-DD') : dateRange.end;
				params.append('end_date', endDate);
			}

			const response = await api.get(`/dashboard/metrics?${params.toString()}`);
			
			if (response.data && response.data.llm_analysis) {
				console.log("✅ Date-filtered data loaded for Data Tables");
				setDateFilteredData(response.data.llm_analysis);
			} else {
				console.error("❌ No LLM analysis in date-filtered response for tables");
				setDateFilterError("No data available for selected date range");
			}
		} catch (error) {
			console.error("❌ Error loading date-filtered data for tables:", error);
			setDateFilterError("Failed to load date-filtered data");
		} finally {
			setIsLoadingDateFilter(false);
		}
	}, [user?.client_id, dateRange, isDateRangeToday]);

	// Trigger date filtering when dateRange changes
	React.useEffect(() => {
		loadDateFilteredData();
	}, [loadDateFilteredData]);

    // Determine which data to use: date-filtered or shared
    const activeData = dateFilteredData || metricsData;
    const isActivelyLoading = loading || isLoadingDateFilter;
    const activeError = error || dateFilterError;
    // Prepare tables and local tab state UNCONDITIONALLY to preserve hook order
    const validTables = (activeData?.tables || []).filter((table: any) => (
        table?.columns && Array.isArray(table.columns) && table?.data && Array.isArray(table.data)
    ));
  const [activeTab, setActiveTab] = React.useState(0);
  // Debounced row search (per-table)
  const [tableSearchInput, setTableSearchInput] = React.useState("");
  const [tableSearch, setTableSearch] = React.useState("");
  React.useEffect(() => {
    const h = setTimeout(() => setTableSearch(tableSearchInput.trim()), 300);
    return () => clearTimeout(h);
  }, [tableSearchInput]);

	if (isActivelyLoading) {
		return (
			<Box sx={{ 
				display: 'flex', 
				justifyContent: 'center', 
				alignItems: 'center', 
				minHeight: '400px',
				flexDirection: 'column',
				gap: 2
			}}>
				<CircularProgress size={60} />
				<Typography variant="h6" color="text.secondary">
					{isLoadingDateFilter ? "Loading Date-Filtered Tables..." : "Loading Data Tables..."}
				</Typography>
			</Box>
		);
	}

	if (activeError) {
		return (
			<Box sx={{ p: 3 }}>
				<Alert severity="error" sx={{ mb: 2 }}>
					{activeError}
				</Alert>
			</Box>
		);
	}

  const hasLLMTables = activeData?.tables && activeData.tables.length > 0;

  // If no tables at all, show friendly message
  if (!hasLLMTables) {
    return (
      <Box sx={{ p: 3 }}>
        <Card sx={{ bgcolor: "grey.50", border: "2px dashed #ccc", textAlign: "center", p: 4 }}>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
            No Data Tables Available
          </Typography>
          <Typography color="text.secondary">
            Upload some data to see analysis tables and insights here.
          </Typography>
        </Card>
      </Box>
    );
  }

  // If after filtering none are valid, show message
  if (validTables.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <Card sx={{ bgcolor: "grey.50", border: "2px dashed #ccc", textAlign: "center", p: 4 }}>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
            📊 No Valid Tables Available
          </Typography>
          <Typography color="text.secondary">
            Upload some data to see analysis tables and insights here.
          </Typography>
        </Card>
      </Box>
    );
  }

  // Search highlight state
  const [highlightQuery, setHighlightQuery] = React.useState<string>("");
  const [forceRenderTick, setForceRenderTick] = React.useState(0);
  React.useEffect(() => {
    const handler = (e: any) => {
      const q = ((e?.detail?.query) || '').toString().toLowerCase();
      setHighlightQuery(q);
      // Nudge Tabs to re-evaluate label rendering
      setForceRenderTick((t) => t + 1);
    };
    window.addEventListener('dashboard-search', handler);
    return () => window.removeEventListener('dashboard-search', handler);
  }, []);

  return (
		<Box sx={{ p: 3 }}>
			<Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
				Data Tables
			</Typography>
			<Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>
				All your data is gathered here in tabular format
			</Typography>

			{/* Date Filter Indicator - Only show for non-today dates */}
			{dateRange && !isDateRangeToday(dateRange) && (
				<Alert severity="info" sx={{ mb: 3 }}>
					📅 Showing data for: <strong>{dateRange.label}</strong>
				</Alert>
			)}

      {/* LLM Analysis Tables - Tabbed Switcher */}
      <Box sx={{ width: '100%' }}>
        <Tabs
          value={Math.min(activeTab, validTables.length - 1)}
          onChange={(_, v) => setActiveTab(v)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ 
            mb: 2,
            '& .MuiTab-root': {
              border: 'none',
              '&:hover': {
                backgroundColor: 'transparent',
              }
            }
          }}
        >
          {validTables.map((table: any, index: number) => {
            const name = table.display_name || `Table ${index + 1}`;
            const q = highlightQuery;
            const parts = q ? name.split(new RegExp(`(${q})`, 'ig')) : [name];
            return (
              <Tab
                key={`${index}-${forceRenderTick}`}
                label={q ? (
                  <>
                    {parts.map((p: string, i: number) => (
                      p.toLowerCase() === q ? (
                        <Box key={i} component="span" sx={{ bgcolor: 'rgba(255, 235, 59, 0.5)', borderRadius: '4px', px: 0.5 }}>{p}</Box>
                      ) : (
                        <Box key={i} component="span">{p}</Box>
                      )
                    ))}
                  </>
                ) : name}
              />
            );
          })}
        </Tabs>

        {(() => {
          const table = validTables[Math.min(activeTab, validTables.length - 1)];
          return (
            <Card sx={{ height: '100%' }}>
              <CardHeader
                title={(() => {
                  const name = table.display_name || `Table ${activeTab + 1}`;
                  const q = highlightQuery;
                  if (q && name.toLowerCase().includes(q)) {
                    return (
                      <>
                        {name.split(new RegExp(`(${q})`, 'ig')).map((part: string, i: number) => (
                          part.toLowerCase() === q ? (
                            <Box key={i} component="span" sx={{ bgcolor: 'rgba(255, 235, 59, 0.5)', borderRadius: '4px', px: 0.5 }}>{part}</Box>
                          ) : (
                            <Box key={i} component="span">{part}</Box>
                          )
                        ))}
                      </>
                    );
                  }
                  return name;
                })()}
                subheader={`${table.data.length} rows of data`}
              />
              <CardContent sx={{ p: 0 }}>
                {/* Inline search for table rows */}
                <Box sx={{ px: 2, py: 1.5, display: 'flex', justifyContent: 'flex-end' }}>
                  <OutlinedInput
                    size="small"
                    value={tableSearchInput}
                    onChange={(e) => setTableSearchInput(e.target.value)}
                    placeholder="Search rows…"
                    endAdornment={
                      <InputAdornment position="end">
                        {tableSearchInput && (
                          <IconButton size="small" onClick={() => setTableSearchInput("")}>
                            <ClearIcon fontSize="small" />
                          </IconButton>
                        )}
                        <SearchRoundedIcon fontSize="small" sx={{ color: 'text.secondary', ml: 0.5 }} />
                      </InputAdornment>
                    }
                    sx={{ width: { xs: '100%', md: 320 } }}
                  />
                </Box>
                <Box sx={{ width: '100%', height: { xs: '60vh', md: '70vh' }, overflow: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'auto' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f5f5f5' }}>
                        {table.columns.map((column: string, colIndex: number) => (
                          <th
                            key={colIndex}
                            style={{
                              position: 'sticky',
                              top: 0,
                              zIndex: 1,
                              padding: '12px',
                              textAlign: 'left',
                              borderBottom: '1px solid #ddd',
                              fontWeight: 'bold',
                              background: '#f5f5f5'
                            }}
                          >
                            {column}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {table.data.filter((row: any) => {
                        const q = tableSearch.trim().toLowerCase();
                        if (!q) return true;
                        try {
                          if (Array.isArray(row)) return row.some((c: any) => String(c ?? '').toLowerCase().includes(q));
                          if (row && typeof row === 'object') return Object.values(row).some((c: any) => String(c ?? '').toLowerCase().includes(q));
                          return String(row ?? '').toLowerCase().includes(q);
                        } catch { return false; }
                      }).map((row: any, rowIndex: number) => (
                        <tr key={rowIndex}>
                          {Array.isArray(row)
                            ? row.map((cell: any, cellIndex: number) => (
                                <td key={cellIndex} style={{ padding: '12px', borderBottom: '1px solid #eee', whiteSpace: 'nowrap' }}>
                                  {(() => { const text = String(cell ?? '-'); const q = tableSearch.trim();
                                    if (q && text.toLowerCase().includes(q.toLowerCase())) {
                                      return <>{text.split(new RegExp(`(${q})`, 'ig')).map((p, i) => p.toLowerCase() === q.toLowerCase() ? <span key={i} style={{ backgroundColor: 'rgba(255, 235, 59, 0.5)', borderRadius: 4 }}>{p}</span> : <span key={i}>{p}</span>)}</>;
                                    } return text; })()}
                                </td>
                              ))
                            : table.columns.map((column: string, cellIndex: number) => (
                                <td key={cellIndex} style={{ padding: '12px', borderBottom: '1px solid #eee', whiteSpace: 'nowrap' }}>
                                  {(() => { const text = String(row[column] ?? '-'); const q = tableSearch.trim();
                                    if (q && text.toLowerCase().includes(q.toLowerCase())) {
                                      return <>{text.split(new RegExp(`(${q})`, 'ig')).map((p, i) => p.toLowerCase() === q.toLowerCase() ? <span key={i} style={{ backgroundColor: 'rgba(255, 235, 59, 0.5)', borderRadius: 4 }}>{p}</span> : <span key={i}>{p}</span>)}</>;
                                    } return text; })()}
                                </td>
                              ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Box>
              </CardContent>
            </Card>
          );
        })()}
      </Box>
		</Box>
	);
}
