import { withSentryConfig } from "@sentry/nextjs";

/** @type {import('next').NextConfig} */
const nextConfig = {
	reactStrictMode: true,

	// Keep it simple - minimal config
	transpilePackages: [
		"@mui/x-data-grid",
		"@mui/x-data-grid-pro",
		"@mui/x-charts",
		"@mui/x-date-pickers",
		"@mui/x-tree-view",
	],

	// Minimal experimental features
	experimental: {
		optimizePackageImports: ["lucide-react"],
	},

	// API rewrites for backend integration
	async rewrites() {
		if (process.env.NODE_ENV === "development") {
			return [
				{
					source: "/api/:path*",
					destination: "http://localhost:8000/api/:path*",
				},
			];
		}
		return [];
	},

	// Basic optimizations only
	poweredByHeader: false,
	compress: true,

	// TypeScript configuration
	typescript: {
		ignoreBuildErrors: true,
	},

	// ESLint configuration
	eslint: {
		ignoreDuringBuilds: true,
	},

	// Image optimization
	images: {
		formats: ["image/webp", "image/avif"],
		minimumCacheTTL: 60,
	},
};

// Sentry configuration options
const sentryWebpackPluginOptions = {
	// Additional config options for the Sentry webpack plugin. Keep in mind that
	// the following options are set automatically, and overriding them is not
	// recommended:
	//   release, url, configFile, stripPrefix, urlPrefix, include, ignore

	org: process.env.SENTRY_ORG,
	project: process.env.SENTRY_PROJECT,

	// Only print logs for uploading source maps in CI
	silent: !process.env.CI,

	// For all available options, see:
	// https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

	// Upload a larger set of source maps for prettier stack traces (increases build time)
	widenClientFileUpload: true,

	// Automatically tree-shake Sentry logger statements to reduce bundle size
	disableLogger: true,

	// Hides source maps from generated client bundles
	hideSourceMaps: true,

	// Automatically tree-shake Sentry logger statements to reduce bundle size
	disableLogger: true,
};

// Make sure adding Sentry options is the last code to run before exporting
export default withSentryConfig(nextConfig, sentryWebpackPluginOptions);
