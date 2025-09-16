import { useQuery } from "@tanstack/react-query";
import { PNLColorSchemeVariant } from "../theme";
import { fetchJSON } from "./api";

interface Account {
  id: string;
  currency: string;
  assetAccount: string;
}

interface Group {
  id: string;
  name: string;
  /** list of asset accounts */
  investments: string[];
}

interface Currency {
  id: string;
  currency: string;
  name: string;
  isInvestment: boolean;
}

export interface ConfigResponse {
  investmentsConfig: {
    accounts: Account[];
    groups: Group[];
    currencies: Currency[];
  };
  operatingCurrencies: string[];
  pnlColorScheme?: PNLColorSchemeVariant;
}

export function useConfig() {
  const params = new URLSearchParams(location.search);
  const url = `config?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<ConfigResponse>(url),
  });
}
