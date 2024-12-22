import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { fetchJSON } from "./api";

interface SummaryRequest {
  investmentFilter: string[];
  targetCurrency: string;
}

export interface SummaryResponse {
  summary: {
    cashIn: number;
    cashOut: number;
    marketValue: number;
    returns: number;
    returnsPct: number;
    returnsPctAnnualized: number;
    irr: number;
    twr: number;
  };
}

export function useSummary(request: SummaryRequest): UseQueryResult<SummaryResponse> {
  const params = new URLSearchParams(location.search);
  params.set("investments", request.investmentFilter.join(","));
  params.set("currency", request.targetCurrency);
  const url = `summary?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<SummaryResponse>(url),
  });
}
