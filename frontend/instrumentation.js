import * as Sentry from "@sentry/nextjs";

export async function register() {
	if (process.env.NEXT_RUNTIME === "nodejs") {
		await import("./sentry.server.config");
	}

	if (process.env.NEXT_RUNTIME === "edge") {
		await import("./sentry.edge.config");
	}

	// Client-side configuration is now handled by instrumentation-client.ts
	// which Next.js will automatically load for client-side code
}

export async function onRequestError(err, request, context) {
	await Sentry.captureRequestError(err, request, context);
}
