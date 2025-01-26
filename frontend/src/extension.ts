import { renderApp } from "./app";

export default {
  onExtensionPageLoad() {
    const container = document.getElementById("favaPortfolioReturnsApp");
    renderApp(container!);
  },
};
