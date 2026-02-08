import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { useFavaFilterSearchParams } from "../routes/__root";
import { fetchJSON } from "./api";
import { InvestmentId } from "./config";

interface CashFlowsRequest {
  investmentFilter: InvestmentId[];
  targetCurrency: string;
  interval: "monthly" | "yearly";
}

interface CashFlow {
  date: string;
  amount: { number: number; currency: string };
  isDividend: boolean;
  source: string;
  account: string;
  transaction: string;
}

export interface CashFlowsResponse {
  chart: { date: string; div: number; exdiv: number }[];
  table: CashFlow[];
}

export function useCashFlows(request: CashFlowsRequest): UseQueryResult<CashFlowsResponse> {
  const params = useFavaFilterSearchParams();
  params.set("investments", request.investmentFilter.join(","));
  params.set("currency", request.targetCurrency);
  params.set("interval", request.interval);
  const url = `cash_flows?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<CashFlowsResponse>(url),
  });
}
