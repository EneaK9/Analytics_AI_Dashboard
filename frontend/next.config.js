/** @type {import('next').NextConfig} */
const nextConfig = {
	reactStrictMode: true,

	// Enable Turbopack (now stable)
	turbopack: {
		rules: {
			"*.svg": {
				loaders: ["@svgr/webpack"],
				as: "*.js",
			},
		},
	},

	// Enable experimental features from Next.js 15.3
	experimental: {
		// Enable optimized package imports
		optimizePackageImports: ["lucide-react", "recharts"],
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
