// Sentry is opt-in and disabled unless an explicit public DSN is provided.
// Never hardcode a DSN here: the release tree must not enable telemetry by
// default, and PII/replay/log capture remains disabled when it is enabled.

import * as Sentry from "@sentry/nextjs";

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    tracesSampleRate: 0,
    enableLogs: false,
    sendDefaultPii: false,
  });
}

export const onRouterTransitionStart = Sentry.captureRouterTransitionStart;
