import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { fetchJSON } from "./api";

interface GroupsRequest {
  currency: string;
}

interface Group {
  name: string;
  currency: string;
  units: { number: number; currency: string }[];
  cashIn: number;
  cashOut: number;
  marketValue: number;
  returns: number;
  returnsPct: number;
  returnsPctAnnualized: number;
  irr: number;
  twr: number;
}

export interface GroupsResponse {
  groups: Group[];
}

export function useGroups(request: GroupsRequest): UseQueryResult<GroupsResponse> {
  const params = new URLSearchParams(location.search);
  params.set("currency", request.currency);
  const url = `groups?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<GroupsResponse>(url),
  });
}
