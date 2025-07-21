import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { fetchJSON } from "./api";

interface InvestmentsRequest {
  targetCurrency: string;
  groupBy: "group" | "currency";
}

export interface Investment {
  id: string;
  name: string;
  currency: string;
  units: { number: number; currency: string }[];
  costValue: number;
  marketValue: number;
  totalPnl: number;
  realizedPnl: number;
  unrealizedPnl: number;
  irr: number;
  mdm: number;
  twr: number;
}

export interface InvestmentsResponse {
  investments: Investment[];
}

export function useInvestments(request: InvestmentsRequest): UseQueryResult<InvestmentsResponse> {
  const params = new URLSearchParams(location.search);
  params.set("currency", request.targetCurrency);
  params.set("group_by", request.groupBy);
  const url = `investments?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<InvestmentsResponse>(url),
  });
}
