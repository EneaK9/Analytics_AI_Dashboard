/** @type {import('next').NextConfig} */
const nextConfig = {
	reactStrictMode: true,

	// Enable experimental features from Next.js 15.3
	experimental: {
		// Enable Turbopack for faster builds (alpha feature)
		turbo: {
			rules: {
				"*.svg": {
					loaders: ["@svgr/webpack"],
					as: "*.js",
				},
			},
		},
		// Enable optimized package imports
		optimizePackageImports: ["lucide-react", "recharts"],
	},

	// API rewrites for backend integration
	async rewrites() {
		return [
			{
				source: "/api/:path*",
				destination: "http://localhost:8000/api/:path*",
			},
		];
	},

	// Performance optimizations
	poweredByHeader: false,
	compress: true,

	// TypeScript configuration
	typescript: {
		// Enable strict type checking
		tsconfigPath: "./tsconfig.json",
	},

	// ESLint configuration
	eslint: {
		// Enable ESLint during builds
		ignoreDuringBuilds: false,
	},

	// Image optimization
	images: {
		formats: ["image/webp", "image/avif"],
		minimumCacheTTL: 60,
	},
};

module.exports = nextConfig;
