import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { useFavaFilterSearchParams } from "../routes/__root";
import { fetchJSON } from "./api";
import { Series } from "./returns";

interface PortfolioRequest {
  investmentFilter: string[];
  targetCurrency: string;
}

export interface PortfolioResponse {
  valueChart: {
    date: string;
    market: number;
    cost: number;
    cash: number;
  }[];
  performanceChart: Series;
  allocation: {
    name: string;
    currency: string;
    marketValue: number;
  }[];
}

export function usePortfolio(request: PortfolioRequest): UseQueryResult<PortfolioResponse> {
  const params = useFavaFilterSearchParams();
  params.set("investments", request.investmentFilter.join(","));
  params.set("currency", request.targetCurrency);
  const url = `portfolio?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<PortfolioResponse>(url),
  });
}
