import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { ReturnsMethod } from "../components/ReturnsMethodSelection";
import { fetchJSON } from "./api";

export type Series = [string, number][];

interface ReturnsRequest {
  investmentFilter: string[];
  targetCurrency: string;
  method: ReturnsMethod;
  interval: "heatmap" | "yearly" | "periods";
}

export interface ReturnsResponse {
  returns: Series;
}

export function useReturns(request: ReturnsRequest): UseQueryResult<ReturnsResponse> {
  const params = new URLSearchParams(location.search); // keep Fava's filters like ?time=...
  params.set("investments", request.investmentFilter.join(","));
  params.set("currency", request.targetCurrency);
  params.set("method", request.method);
  params.set("interval", request.interval);
  const url = `returns?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<ReturnsResponse>(url),
  });
}
