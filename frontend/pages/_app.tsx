import "../styles/globals.css";
import type { AppProps } from "next/app";
import Head from "next/head";
import { QueryProvider } from "../providers/QueryProvider";
import { GlobalDataProvider } from "../providers/GlobalDataProvider";

export default function App({ Component, pageProps }: AppProps) {
	return (
		<QueryProvider>
			<GlobalDataProvider>
				<Head>
					<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
					<title>AI Analytics Dashboard</title>
				</Head>
				<Component {...pageProps} />
			</GlobalDataProvider>
		</QueryProvider>
	);
}
