import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { MetricName } from "../components/MetricSelection";
import { useFavaFilterSearchParams } from "../routes/__root";
import { fetchJSON } from "./api";

export type Series = [string, number][];

interface MetricValuesRequest {
  investmentFilter: string[];
  targetCurrency: string;
  metric: MetricName;
  interval: "series" | "rolling_1y" | "heatmap" | "yearly" | "periods";
}

export interface MetricValuesResponse {
  series: Series;
}

export function useMetricValues(request: MetricValuesRequest): UseQueryResult<MetricValuesResponse> {
  const params = useFavaFilterSearchParams();
  params.set("investments", request.investmentFilter.join(","));
  params.set("currency", request.targetCurrency);
  params.set("metric", request.metric);
  params.set("interval", request.interval);
  const url = `metric_values?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<MetricValuesResponse>(url),
  });
}
