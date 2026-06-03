import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["en", "pt-BR", "ja", "zh", "ar", "es", "fr", "ru", "de"],
  defaultLocale: "en",
  localePrefix: "as-needed",
});
