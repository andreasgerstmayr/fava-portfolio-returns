import { keepPreviousData, useQuery, UseQueryResult } from "@tanstack/react-query";
import { useFavaFilterSearchParams } from "../routes/__root";
import { fetchJSON } from "./api";

interface AssetAllocationRequest {
  targetCurrency: string;
  /** class rebalancing: fewest trades instead of proportional split */
  minimize: boolean;
}

export interface AssetAllocationAsset {
  commodity: string;
  name: string;
  /** target allocation in percent */
  targetPct: number;
  /** current allocation in percent */
  currentPct: number;
  /** current market value in the target currency */
  value: number;
  /** deviation from target in percentage points (positive => overweight) */
  devPct: number;
  /** deviation from target in the target currency (positive => overweight) */
  devValue: number;
  /** whether the deviation exceeds this asset's own threshold */
  over: boolean;
  /** divergence threshold of this asset, in percentage points, derived from its target */
  thresholdPct: number;
}

export interface AssetAllocationHolding {
  commodity: string;
  name: string;
  value: number;
  /** why the holding was excluded (only set for class reports) */
  reason?: string;
}

/** a per-commodity buy/sell suggestion within an asset class */
export interface AssetAllocationMember {
  commodity: string;
  name: string;
  value: number;
  /** trade amount in the target currency (positive => sell, negative => buy) */
  tradeValue: number;
}

export interface AssetAllocationClassRow {
  assetClass: string;
  targetPct: number;
  currentPct: number;
  value: number;
  devPct: number;
  devValue: number;
  over: boolean;
  /** per-commodity rebalance breakdown that closes this class's gap */
  members: AssetAllocationMember[];
  /** true if nothing is currently held in this class */
  noHoldings: boolean;
  /** amount (target currency) that could not be reconciled within constraints */
  shortfall: number;
  /** divergence threshold of this class, in percentage points, derived from its target */
  thresholdPct: number;
}

/** by-commodity sub-report */
export interface AssetAllocationCommodityReport {
  diverged: boolean;
  assets: AssetAllocationAsset[];
  /** held commodities that are not part of the target allocation */
  unconfigured: AssetAllocationHolding[];
  /** sum of the target allocation, should be 100% */
  targetSum: number;
  targetSumOk: boolean;
}

/** by-asset-class sub-report */
export interface AssetAllocationClassReport {
  diverged: boolean;
  /** whether the fewest-trades rebalancing strategy was used */
  minimize: boolean;
  classes: AssetAllocationClassRow[];
  /** held commodities without a targeted asset class */
  unconfigured: AssetAllocationHolding[];
  targetSum: number;
  targetSumOk: boolean;
}

/**
 * The divergence band of a portfolio, as two caps combined with min(): an
 * absolute one in percentage points of the portfolio, and a relative one as a
 * fraction of each target.
 */
export interface AssetAllocationBand {
  ofPortfolio: number;
  ofTarget: number;
}

export interface AssetAllocationPortfolio {
  name: string;
  /** account regexes of this portfolio */
  accounts: string[];
  currency: string;
  totalValue: number;
  /** the portfolio's divergence band */
  band: AssetAllocationBand;
  /** held commodities that could not be valued (no known price) */
  unpriced: string[];
  /** by-commodity sub-report, or null if the portfolio defines no commodities */
  commodityReport: AssetAllocationCommodityReport | null;
  /** by-asset-class sub-report, or null if the portfolio defines no classes */
  classReport: AssetAllocationClassReport | null;
}

export interface AssetAllocationResponse {
  portfolios: AssetAllocationPortfolio[];
}

export function useAssetAllocation(request: AssetAllocationRequest): UseQueryResult<AssetAllocationResponse> {
  const params = useFavaFilterSearchParams();
  params.set("currency", request.targetCurrency);
  if (request.minimize) {
    params.set("minimize", "1");
  }
  const url = `asset_allocation?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<AssetAllocationResponse>(url),
    // the reports stay on screen while a refetch runs, so flipping the rebalancing
    // strategy does not scroll the page away
    placeholderData: keepPreviousData,
  });
}
