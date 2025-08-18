import "../styles/globals.css";
import type { AppProps } from "next/app";
import Head from "next/head";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

export default function App({ Component, pageProps }: AppProps) {
	// Create a client instance for this app session
	const [queryClient] = useState(() => new QueryClient({
		defaultOptions: {
			queries: {
				// Cache data for 5 minutes by default
				staleTime: 5 * 60 * 1000,
				// Keep data in cache for 10 minutes
				gcTime: 10 * 60 * 1000,
				// Show cached data immediately while fetching fresh data
				refetchOnWindowFocus: false,
				refetchOnMount: false,
				refetchOnReconnect: true,
				// Retry failed requests
				retry: 3,
				retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
			},
		},
	}));

	return (
		<QueryClientProvider client={queryClient}>
			<Head>
				<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
				<title>AI Analytics Dashboard</title>
			</Head>
			<Component {...pageProps} />
			{/* React Query DevTools - only in development */}
			{process.env.NODE_ENV === 'development' && (
				<ReactQueryDevtools initialIsOpen={false} />
			)}
		</QueryClientProvider>
	);
}
