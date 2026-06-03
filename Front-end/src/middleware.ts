import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

export default createMiddleware(routing);

export const config = {
  matcher: [
    // Exclude Sentry tunnel route, API routes, Next.js internals, Vercel internals,
    // and static files (paths with file extensions) from i18n middleware.
    "/((?!monitoring|api|_next|_vercel|.*\\..*).*)",
    "/(pt-BR|ja|zh|ar|es|fr|ru|de)/:path*",
  ],
};
