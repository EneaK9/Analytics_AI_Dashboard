/**
 * Optimized Data Tables Page
 * Uses global state and raw data service with pagination for efficient data management
 */

import * as React from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import OutlinedInput from "@mui/material/OutlinedInput";
import InputAdornment from "@mui/material/InputAdornment";
import IconButton from "@mui/material/IconButton";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import ClearIcon from "@mui/icons-material/Clear";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Button from "@mui/material/Button";
import RefreshIcon from "@mui/icons-material/Refresh";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Badge from "@mui/material/Badge";
import Pagination from "@mui/material/Pagination";
import Skeleton from "@mui/material/Skeleton";
import LinearProgress from "@mui/material/LinearProgress";

import { useRawDataTables, useRawDataFilters, useAvailableTables } from "../../../store/globalDataStore";
import { rawDataService } from "../../../lib/rawDataService";

interface OptimizedDataTablesPageProps {
  user?: {
    company_name: string;
    email: string;
    client_id: string;
  };
}

export default function OptimizedDataTablesPage({ user }: OptimizedDataTablesPageProps) {
  const { data: rawData, loading, paginationLoading, error, fetch: fetchRawData } = useRawDataTables();
  const { filters, setFilters } = useRawDataFilters();
  const { data: availableTables, loading: tablesLoading, error: tablesError, fetch: fetchAvailableTables } = useAvailableTables();

  // Local state for search input (debounced)
  const [searchInput, setSearchInput] = React.useState(filters.search);
  const [selectedPlatform, setSelectedPlatform] = React.useState<'shopify' | 'amazon'>('shopify');

  // Sync search input with global state when filters change externally
  React.useEffect(() => {
    setSearchInput(filters.search);
  }, [filters.search]);

  // Sync selected platform with filters
  React.useEffect(() => {
    setSelectedPlatform(filters.platform);
  }, [filters.platform]);

  // Debug logging
  React.useEffect(() => {
    console.log('📊 OptimizedDataTablesPage mounted with user:', user);
    console.log('🔑 Client ID:', user?.client_id);
    console.log('🎛️ Current filters:', filters);
    console.log('📋 Available tables:', availableTables);
  }, [user, filters, availableTables]);

  // Fetch available tables on mount
  React.useEffect(() => {
    if (user?.client_id) {
      console.log('🔄 Fetching available tables for client:', user.client_id);
      fetchAvailableTables(user.client_id);
    }
  }, [user?.client_id, fetchAvailableTables]);

  // Early return if no user
  if (!user?.client_id) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning" sx={{ mb: 2 }}>
          User authentication required. Please log in to view data tables.
        </Alert>
      </Box>
    );
  }

  // Debounced search
  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== filters.search) {
        console.log('🔍 Search input changed to:', searchInput);
        setFilters({ search: searchInput, page: 1 }); // Reset to page 1 when searching
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [searchInput, setFilters, filters.search]);

  // Fetch data when filters change or on mount
  React.useEffect(() => {
    if (user?.client_id) {
      console.log('🔄 Filters changed, fetching data:', filters);
      fetchRawData(user.client_id);
    }
  }, [filters.platform, filters.dataType, filters.page, filters.search, user?.client_id, fetchRawData]);

  // Handle platform change
  const handlePlatformChange = (_: React.SyntheticEvent, platform: 'shopify' | 'amazon') => {
    if (!platform) return; // Handle case where tab is deselected
    
    console.log('🏪 Platform changed to:', platform, 'from:', selectedPlatform);
    console.log('🏪 Available tables for platform:', availableTables?.available_tables[platform]);
    
    setSelectedPlatform(platform);
    
    // Find the first available data type for this platform
    const availableDataTypes = availableTables?.available_tables[platform] || [];
    if (availableDataTypes.length > 0) {
      const defaultDataType = availableDataTypes.find(t => t.data_type === 'products') || availableDataTypes[0];
      console.log('🏪 Setting default data type to:', defaultDataType.data_type);
      
      setFilters({ 
        platform, 
        dataType: defaultDataType.data_type as 'products' | 'orders',
        page: 1,
        search: '' // Clear search when switching platforms
      });
      
      // Clear search input UI as well
      setSearchInput('');
    }
  };

  // Handle data type change
  const handleDataTypeChange = (_: React.SyntheticEvent, dataType: string) => {
    if (!dataType) return; // Handle case where tab is deselected
    
    console.log('📦 Data type changed to:', dataType, 'Current platform:', selectedPlatform);
    setFilters({ 
      dataType: dataType as 'products' | 'orders', 
      page: 1,
      search: '' // Clear search when switching data types
    });
    
    // Clear search input UI as well
    setSearchInput('');
  };

  // Handle page change
  const handlePageChange = (_: React.ChangeEvent<unknown>, page: number) => {
    console.log('📄 Page changed to:', page, 'Current filters:', filters);
    setFilters({ page });
    
    // Scroll to top when changing pages for better UX
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handle refresh
  const handleRefresh = () => {
    if (user?.client_id) {
      fetchRawData(user.client_id, true); // Force refresh
    }
  };



  // Helper function to highlight search matches
  const highlightSearchText = React.useCallback((text: string, searchTerm: string) => {
    if (!searchTerm || !text || rawData?.search_fallback) {
      return text;
    }

    const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => {
      if (part.toLowerCase() === searchTerm.toLowerCase()) {
        return (
          <span 
            key={index} 
            style={{ 
              backgroundColor: '#fff176', // Yellow highlight
              padding: '1px 2px',
              borderRadius: '2px',
              fontWeight: '600'
            }}
          >
            {part}
          </span>
        );
      }
      return part;
    });
  }, [rawData?.search_fallback]);

  // Skeleton Table Component for loading states
  const SkeletonTable = () => (
    <Box sx={{ p: 2 }}>
      {Array.from({ length: 10 }).map((_, index) => (
        <Skeleton key={index} variant="rectangular" height={40} sx={{ mb: 1 }} />
      ))}
    </Box>
  );

  // Loading state for available tables
  if (tablesLoading) {
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
          Loading Available Tables...
        </Typography>
      </Box>
    );
  }

  // Error state for available tables
  if (tablesError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load available tables: {tablesError}
        </Alert>
        <Stack direction="row" spacing={2} justifyContent="center">
          <Button
            variant="contained"
            onClick={() => fetchAvailableTables(user.client_id, true)}
            startIcon={<RefreshIcon />}
          >
            Retry
          </Button>
        </Stack>
      </Box>
    );
  }

  // No available tables
  if (!availableTables || Object.keys(availableTables.available_tables).length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <Card sx={{ bgcolor: "grey.50", border: "2px dashed #ccc", textAlign: "center", p: 4 }}>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
            📊 No Data Tables Available
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>
            No organized data tables found for this client. Data may need to be organized first.
          </Typography>
          <Stack direction="row" spacing={2} justifyContent="center">
            <Button
              variant="contained"
              onClick={() => fetchAvailableTables(user.client_id, true)}
              startIcon={<RefreshIcon />}
            >
              Refresh
            </Button>
          </Stack>
        </Card>
      </Box>
    );
  }

  // Get available platforms and data types
  const availablePlatforms = Object.keys(availableTables.available_tables) as ('shopify' | 'amazon')[];
  const currentPlatformTables = availableTables.available_tables[selectedPlatform] || [];

  // Loading state for data
  if (loading) {
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
          Loading Data Tables...
        </Typography>
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button 
          variant="contained" 
          onClick={handleRefresh}
          startIcon={<RefreshIcon />}
        >
          Try Again
        </Button>
      </Box>
    );
  }

  // No data state
  if (!rawData || rawData.data.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <Card sx={{ bgcolor: "grey.50", border: "2px dashed #ccc", textAlign: "center", p: 4 }}>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
            📊 No Data Available
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>
            {rawData?.pagination.total_records === 0 
              ? "No data found for the selected filters."
              : "No data matches the current search criteria."
            }
          </Typography>
          <Stack direction="row" spacing={2} justifyContent="center">
            <Button 
              variant="contained" 
              onClick={handleRefresh}
              startIcon={<RefreshIcon />}
            >
              Refresh Data
            </Button>
          </Stack>
        </Card>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
        Data Tables
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 2 }}>
        All your data is  here organized in tabular format
      </Typography>

      {/* Platform and Data Type Tabs */}
      <Stack direction="row" spacing={2} sx={{ mb: 3 }} flexWrap="wrap">
        {/* Platform Tabs */}
        <Tabs
          value={selectedPlatform}
          onChange={handlePlatformChange}
          variant="standard"
          sx={{ 
            minHeight: 40,
            '& .MuiTab-root': { 
              minHeight: 40, 
              fontSize: '0.85rem',
              textTransform: 'none',
              fontWeight: 500
            }
          }}
        >
          {availablePlatforms.map((platform) => (
            <Tab
              key={platform}
              value={platform}
              label={
                <Stack direction="row" spacing={0.5} alignItems="center">
                  <span>{platform === 'shopify' ? '🛍️' : '📦'}</span>
                  <span>{platform.charAt(0).toUpperCase() + platform.slice(1)}</span>
                  <Chip 
                    label={availableTables.available_tables[platform].length} 
                    size="small" 
                    color="primary"
                    sx={{ 
                      height: 18, 
                      fontSize: '0.65rem',
                      '& .MuiChip-label': { px: 0.5 }
                    }}
                  />
                </Stack>
              }
            />
          ))}
        </Tabs>

        {/* Data Type Tabs */}
        {currentPlatformTables.length > 0 && (
          <Tabs
            value={filters.dataType}
            onChange={handleDataTypeChange}
            variant="standard"
            sx={{ 
              minHeight: 40,
              '& .MuiTab-root': { 
                minHeight: 40, 
                fontSize: '0.85rem',
                textTransform: 'none',
                fontWeight: 500
              }
            }}
          >
            {currentPlatformTables.map((table) => (
              <Tab
                key={table.data_type}
                value={table.data_type}
                label={
                  <Stack direction="row" spacing={0.5} alignItems="center">
                    <span>{table.data_type === 'products' ? '📦' : '🛒'}</span>
                    <span>{table.data_type.charAt(0).toUpperCase() + table.data_type.slice(1)}</span>
                    <Chip 
                      label={table.count.toLocaleString()} 
                      size="small" 
                      color="secondary"
                      sx={{ 
                        height: 18, 
                        fontSize: '0.65rem',
                        '& .MuiChip-label': { px: 0.5 }
                      }}
                    />
                  </Stack>
                }
              />
            ))}
          </Tabs>
        )}
      </Stack>

      {/* Search Fallback Alert */}
      {rawData?.search_fallback && rawData?.search && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            🔍 No results found for "<strong>{rawData.search}</strong>". Showing all data instead.
          </Typography>
        </Alert>
      )}

      {/* Current Table Summary */}
      {rawData && (
        <Box sx={{ mb: 3 }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="space-between" alignItems={{ sm: 'center' }}>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              <Chip 
                label={`${rawData.pagination.total_records.toLocaleString()} Total Records`} 
                color="primary" 
                variant="outlined" 
              />
              <Chip 
                label={`Page ${rawData.pagination.current_page}/${rawData.pagination.total_pages}`} 
                color="secondary" 
                variant="outlined" 
              />
            </Stack>
            <Button
              variant="outlined"
              onClick={handleRefresh}
              startIcon={<RefreshIcon />}
              size="small"
            >
              Refresh
            </Button>
          </Stack>
        </Box>
      )}

      {/* Data Table */}
      <Card sx={{ height: '100%' }}>
        <CardHeader
          title={rawData.display_name}
          subheader={rawData.message}
          action={
            <Stack direction="row" spacing={2} alignItems="center">
              {/* Search Box */}
              <OutlinedInput
                size="small"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder={rawData.search_fallback ? "Search (showing all data)" : "Search all data..."}
                endAdornment={
                  <InputAdornment position="end">
                    {searchInput && (
                      <IconButton size="small" onClick={() => setSearchInput("")}>
                        <ClearIcon fontSize="small" />
                      </IconButton>
                    )}
                    <SearchRoundedIcon fontSize="small" sx={{ color: 'text.secondary', ml: 0.5 }} />
                  </InputAdornment>
                }
                sx={{ 
                  width: { xs: '100%', md: 320 },
                  '& .MuiOutlinedInput-root': {
                    borderColor: rawData.search_fallback ? 'info.main' : undefined,
                  }
                }}
              />
            </Stack>
          }
        />
        <CardContent sx={{ p: 0 }}>
          {/* Pagination Loading Indicator */}
          {paginationLoading && (
            <LinearProgress sx={{ position: 'absolute', top: 0, left: 0, right: 0, zIndex: 2 }} />
          )}
          
          {/* Data Table */}
          <Box sx={{ 
            width: '100%', 
            height: { xs: '50vh', md: '60vh' }, 
            overflow: 'auto',
            position: 'relative',
            opacity: paginationLoading ? 0.7 : 1,
            transition: 'opacity 0.2s ease-in-out'
          }}>
            {paginationLoading ? (
              <SkeletonTable />
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'auto' }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5' }}>
                  {rawData.columns.map((column, colIndex) => (
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
                {rawData.data.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    {rawData.columns.map((column, cellIndex) => {
                      const cellValue = row[column];
                      const text = String(cellValue ?? '-');
                      const searchTerm = filters.search.trim();
                      
                      return (
                        <td 
                          key={cellIndex} 
                          style={{ 
                            padding: '12px', 
                            borderBottom: '1px solid #eee', 
                            whiteSpace: 'nowrap',
                            maxWidth: '200px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                          }}
                          title={text} // Show full text on hover
                        >
                          {searchTerm && text.toLowerCase().includes(searchTerm.toLowerCase()) && !rawData.search_fallback ? 
                            highlightSearchText(text, searchTerm) : 
                            text
                          }
                        </td>
                      );
                    })}
                  </tr>
                                  ))}
                </tbody>
              </table>
            )}
          </Box>

          {/* Pagination */}
          {rawData.pagination.total_pages > 1 && (
            <Box sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
              <Pagination
                count={rawData.pagination.total_pages}
                page={rawData.pagination.current_page}
                onChange={handlePageChange}
                color="primary"
                size="large"
                showFirstButton
                showLastButton
                disabled={paginationLoading}
                sx={{
                  '& .MuiPaginationItem-root': {
                    transition: 'all 0.2s ease-in-out',
                  },
                  '& .MuiPaginationItem-root.Mui-disabled': {
                    opacity: 0.6,
                  }
                }}
              />
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}