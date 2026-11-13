// Sentry is opt-in and disabled unless an explicit DSN is provided.
// Never hardcode a DSN here: the release tree must not enable telemetry by
// default, and PII/log capture remains disabled when it is enabled.

import * as Sentry from "@sentry/nextjs";

const dsn = process.env.SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    tracesSampleRate: 0,
    enableLogs: false,
    sendDefaultPii: false,
  });
}
