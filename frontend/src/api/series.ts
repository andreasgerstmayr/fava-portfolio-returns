import { useQueries, useQuery, UseQueryResult } from "@tanstack/react-query";
import { fetchJSON } from "./api";

type SeriesName = string;

interface SeriesRequest {
  investmentFilter: string[];
  targetCurrency: string;
  series: SeriesName[];
}

export type Series = [string, number][];
export interface SeriesResponse {
  series: Record<SeriesName, Series>;
}

export function useSeries(request: SeriesRequest): UseQueryResult<SeriesResponse> {
  const params = new URLSearchParams(location.search); // keep Fava's filters like ?time=...
  params.set("investments", request.investmentFilter.join(","));
  params.set("currency", request.targetCurrency);
  params.set("series", request.series.join(","));
  const url = `series?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<SeriesResponse>(url),
  });
}

export function useMultiSeries(requests: SeriesRequest[]) {
  const urls = requests.map((request) => {
    const params = new URLSearchParams(location.search); // keep Fava's filters like ?time=...
    params.set("investments", request.investmentFilter.join(","));
    params.set("currency", request.targetCurrency);
    params.set("series", request.series.join(","));
    return `series?${params}`;
  });

  return useQueries({
    queries: urls.map((url) => ({
      queryKey: [url],
      queryFn: () => fetchJSON<SeriesResponse>(url),
    })),
    combine: (results) => {
      return {
        isPending: results.some((result) => result.isPending),
        error: results.find((result) => result.error)?.error ?? null,
        data: results.map((result) => result.data),
      };
    },
  });
}
