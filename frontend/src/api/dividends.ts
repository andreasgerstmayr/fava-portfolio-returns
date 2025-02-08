import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { fetchJSON } from "./api";

interface DividendsRequest {
  investmentFilter: string[];
  targetCurrency: string;
  interval: "monthly" | "yearly";
}

export interface DividendsResponse {
  intervals: string[];
  chart: Record<string, string | number>[];
}

export function useDividends(request: DividendsRequest): UseQueryResult<DividendsResponse> {
  const params = new URLSearchParams(location.search);
  params.set("investments", request.investmentFilter.join(","));
  params.set("currency", request.targetCurrency);
  params.set("interval", request.interval);
  const url = `dividends?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<DividendsResponse>(url),
  });
}
