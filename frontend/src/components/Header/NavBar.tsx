import { Box } from "@mui/material";
import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { retainSearchParams } from "../../routes/__root";

export function NavBar() {
  const { t } = useTranslation();

  return (
    <Box className="headerline" sx={{ ".active": { color: "inherit" } }}>
      <h3>
        <Link to="/portfolio" search={retainSearchParams}>
          {t("Portfolio")}
        </Link>
      </h3>
      <h3>
        <Link to="/performance" search={retainSearchParams}>
          {t("Performance")}
        </Link>
      </h3>
      <h3>
        <Link to="/returns" search={retainSearchParams}>
          {t("Returns")}
        </Link>
      </h3>
      <h3>
        <Link to="/metrics" search={retainSearchParams}>
          {t("Metrics")}
        </Link>
      </h3>
      <h3>
        <Link to="/dividends" search={retainSearchParams}>
          {t("Dividends")}
        </Link>
      </h3>
      <h3>
        <Link to="/cash_flows" search={retainSearchParams}>
          {t("Cash Flows")}
        </Link>
      </h3>
      <h3>
        <Link to="/groups" search={retainSearchParams}>
          {t("Groups")}
        </Link>
      </h3>
      <h3>
        <Link to="/investments" search={retainSearchParams}>
          {t("Investments")}
        </Link>
      </h3>
      <h3>
        <Link to="/missing_prices" search={retainSearchParams}>
          {t("Missing Prices")}
        </Link>
      </h3>
      <h3>
        <Link to="/help" search={retainSearchParams}>
          {t("Help")}
        </Link>
      </h3>
    </Box>
  );
}
