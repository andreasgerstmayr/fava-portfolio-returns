import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import locales from "./locales";

i18n.use(initReactI18next).init({
  resources: locales,
  lng: "en",
  fallbackLng: "en",
  // The extraction adds empty strings for untranslated translation keys, these should be considered as missing translations
  returnEmptyString: false,
  // do not use key and namespace separators in translation keys
  keySeparator: false,
  nsSeparator: false,
  interpolation: {
    // React already escapes values to protect against XSS
    escapeValue: false,
  },
});
