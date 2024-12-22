import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { fetchJSON } from "./api";

interface CashFlowsRequest {
  investmentFilter: string[];
  targetCurrency: string;
}

interface CashFlow {
  date: string;
  amount: { number: number; currency: string };
  isDividend: boolean;
  source: string;
  account: string;
}

export interface CashFlowsResponse {
  cashFlows: CashFlow[];
}

export function useCashFlows(request: CashFlowsRequest): UseQueryResult<CashFlowsResponse> {
  const params = new URLSearchParams(location.search);
  params.set("investments", request.investmentFilter.join(","));
  params.set("currency", request.targetCurrency);
  const url = `cash_flows?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<CashFlowsResponse>(url),
  });
}
