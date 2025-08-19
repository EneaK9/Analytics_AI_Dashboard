module.exports = {
	plugins: {
		tailwindcss: {},
		autoprefixer: {
			overrideBrowserslist: [
				"last 2 versions",
				"> 1%",
				"not dead",
				"not ie 11",
				"ios >= 12",
				"safari >= 12",
			],
			cascade: false,
			remove: false, // Don't remove old prefixes for compatibility
		},
	},
};
