import { useQuery } from "@tanstack/react-query";
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
}

export interface ConfigResponse {
  investments: {
    accounts: Account[];
    groups: Group[];
    currencies: Currency[];
  };
  operatingCurrencies: string[];
  /** Fava date range */
  dateRange: string;
}

export function useConfig() {
  const params = new URLSearchParams(location.search);
  const url = `config?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<ConfigResponse>(url),
  });
}
