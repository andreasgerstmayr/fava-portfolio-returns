import { useQuery } from "@tanstack/react-query";
import { useFavaFilterSearchParams } from "../routes/__root";
import { PNLColorSchemeVariant } from "../theme";
import { fetchJSON } from "./api";

export type InvestmentId = string;

interface Account {
  id: InvestmentId;
  currency: string;
  assetAccount: string;
}

interface Group {
  id: InvestmentId;
  name: string;
  /** list of asset accounts */
  investments: string[];
}

interface Currency {
  id: InvestmentId;
  currency: string;
  name: string;
  isInvestment: boolean;
}

export interface ConfigResponse {
  language: string | null;
  locale: string | null;
  pnlColorScheme: PNLColorSchemeVariant | null;
  operatingCurrencies: string[];
  investmentsConfig: {
    accounts: Account[];
    groups: Group[];
    currencies: Currency[];
  };
}

export function useConfig() {
  const params = useFavaFilterSearchParams();
  const url = `config?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<ConfigResponse>(url),
  });
}
