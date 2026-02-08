import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { useFavaFilterSearchParams } from "../routes/__root";
import { fetchJSON } from "./api";
import { InvestmentId } from "./config";
import { Series } from "./metric_values";

interface PortfolioRequest {
  investmentFilter: InvestmentId[];
  targetCurrency: string;
}

export interface PortfolioAllocation {
  name: string;
  currency_id: InvestmentId;
  marketValue: number;
}

export interface PortfolioResponse {
  valueChart: {
    date: string;
    market: number;
    cost: number;
    cash: number;
  }[];
  performanceChart: Series;
  allocation: PortfolioAllocation[];
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
