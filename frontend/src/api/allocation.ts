import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { fetchJSON } from "./api";

interface AllocationRequest {
  investmentFilter: string[];
  targetCurrency: string;
}

export interface AllocationResponse {
  allocation: {
    commodity: string;
    currency: string;
    marketValue: number;
  }[];
}

export function useAllocation(request: AllocationRequest): UseQueryResult<AllocationResponse> {
  const params = new URLSearchParams(location.search);
  params.set("investments", request.investmentFilter.join(","));
  params.set("currency", request.targetCurrency);
  const url = `allocation?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<AllocationResponse>(url),
  });
}
