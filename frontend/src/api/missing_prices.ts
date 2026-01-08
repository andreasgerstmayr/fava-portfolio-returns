import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { createURLSearchParamsWithFavaFilters, fetchJSON } from "./api";

export interface MissingPrice {
  currency: string;
  requiredDate: string;
  actualDate: string;
  daysLate: number;
}

export interface MissingPricesResponse {
  missingPrices: MissingPrice[];
  commands: string[];
}

export function useMissingPrices(): UseQueryResult<MissingPricesResponse> {
  const params = createURLSearchParamsWithFavaFilters();
  const url = `missing_prices?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<MissingPricesResponse>(url),
  });
}
