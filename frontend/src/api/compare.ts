import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { MetricName } from "../components/MetricSelection";
import { useFavaFilterSearchParams } from "../routes/__root";
import { fetchJSON } from "./api";
import { Series } from "./metric_values";

interface CompareRequest {
  investmentFilter: string[];
  targetCurrency: string;
  metric: MetricName;
  compareWith: string[];
}

export interface NamedSeries {
  name: string;
  data: Series;
  /** amount <0 for buy, >0 for sell */
  cashFlows: Series;
}

export interface CompareResponse {
  series: NamedSeries[];
}

export function useCompare(request: CompareRequest): UseQueryResult<CompareResponse> {
  const params = useFavaFilterSearchParams();
  params.set("investments", request.investmentFilter.join(","));
  params.set("currency", request.targetCurrency);
  params.set("metric", request.metric);
  params.set("compareWith", request.compareWith.join(","));
  const url = `compare?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<CompareResponse>(url),
  });
}
