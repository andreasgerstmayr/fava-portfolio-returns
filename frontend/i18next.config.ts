import { defineConfig } from "i18next-cli";

export default defineConfig({
  locales: ["en", "zh"],
  extract: {
    input: "src/**/*.{js,jsx,ts,tsx}",
    output: "src/locales/{{language}}/{{namespace}}.json",
    keySeparator: false,
    nsSeparator: false,
  },
  types: {
    input: ["src/locales/en/*.json"],
    output: "src/locales/i18next.d.ts",
    resourcesFile: "src/locales/translations.d.ts",
  },
});
