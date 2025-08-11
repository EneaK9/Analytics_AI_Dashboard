import * as React from 'react';
import FormControl from '@mui/material/FormControl';
import InputAdornment from '@mui/material/InputAdornment';
import OutlinedInput from '@mui/material/OutlinedInput';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';

interface SearchProps {
  onSearch?: (query: string) => void;
  placeholder?: string;
  debounceMs?: number;
}

export default function Search({ onSearch, placeholder = 'Search…', debounceMs = 300 }: SearchProps) {
  const [value, setValue] = React.useState('');

  const submit = React.useCallback((q: string) => {
    if (onSearch) onSearch(q);
  }, [onSearch]);

  // Debounce on value changes
  React.useEffect(() => {
    const handle = setTimeout(() => submit(value.trim()), debounceMs);
    return () => clearTimeout(handle);
  }, [value, submit, debounceMs]);

  return (
    <FormControl sx={{ width: { xs: '100%', md: '25ch' } }} variant="outlined">
      <OutlinedInput
        size="small"
        id="search"
        placeholder={placeholder}
        sx={{ flexGrow: 1 }}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        // Enter not required; debounced onChange handles search
        startAdornment={
          <InputAdornment position="start" sx={{ color: 'text.primary' }}>
            <SearchRoundedIcon fontSize="small" />
          </InputAdornment>
        }
        inputProps={{
          'aria-label': 'search',
        }}
      />
    </FormControl>
  );
}
