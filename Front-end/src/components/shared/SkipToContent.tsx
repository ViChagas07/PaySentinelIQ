/**
 * Skip-to-content link — the first focusable element on every page.
 * WCAG 2.4.1 Level A: Bypass Blocks
 *
 * Accepts translated text as a prop from the Server Component layout
 * to avoid needing NextIntlClientProvider context (must render before it).
 */
export function SkipToContent({ label }: { label: string }) {
  return (
    <a
      href="#main-content"
      className="sr-only-focusable"
    >
      {label}
    </a>
  );
}
