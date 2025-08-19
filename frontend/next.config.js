/** @type {import('next').NextConfig} */
const nextConfig = {
	reactStrictMode: true,

	// Temporarily disable Turbopack to fix unload event issues
	// turbopack: {
	// 	rules: {
	// 		"*.svg": {
	// 			loaders: ["@svgr/webpack"],
	// 			as: "*.js",
	// 		},
	// 	},
	// },

	// Transpile Material UI packages to handle CSS imports
	transpilePackages: [
		"@mui/x-data-grid",
		"@mui/x-data-grid-pro",
		"@mui/x-charts",
		"@mui/x-date-pickers",
		"@mui/x-tree-view",
	],

	// Enable experimental features from Next.js 15.3
	experimental: {
		// Enable optimized package imports
		optimizePackageImports: ["lucide-react", "recharts"],
		// Disable features that use deprecated unload events
		appDocumentPreloading: false,
		optimisticClientCache: false,
	},

	// API rewrites for backend integration
	async rewrites() {
		// Only use rewrites in development
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

	// Performance optimizations
	poweredByHeader: false,
	compress: true,

	// TypeScript configuration
	typescript: {
		// Ignore TypeScript errors during production builds
		ignoreBuildErrors: true,
	},

	// ESLint configuration
	eslint: {
		// Ignore ESLint errors during production builds for faster deployment
		ignoreDuringBuilds: true,
	},

	// Image optimization
	images: {
		formats: ["image/webp", "image/avif"],
		minimumCacheTTL: 60,
	},
};

module.exports = nextConfig;
