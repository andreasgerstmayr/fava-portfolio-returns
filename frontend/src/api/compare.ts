import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { fetchJSON } from "./api";
import { Series } from "./returns";

interface CompareRequest {
  investmentFilter: string[];
  targetCurrency: string;
  method: string;
  compareWith: string[];
}

interface NamedSeries {
  name: string;
  data: Series;
  cash_flows?: Series;
}

export interface CompareResponse {
  series: NamedSeries[];
}

export function useCompare(request: CompareRequest): UseQueryResult<CompareResponse> {
  const params = new URLSearchParams(location.search); // keep Fava's filters like ?time=...
  params.set("investments", request.investmentFilter.join(","));
  params.set("currency", request.targetCurrency);
  params.set("method", request.method);
  params.set("compareWith", request.compareWith.join(","));
  const url = `compare?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<CompareResponse>(url),
  });
}
