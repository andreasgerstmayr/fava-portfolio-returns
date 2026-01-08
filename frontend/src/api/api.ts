export interface APIResponse<T> {
  success: boolean;
  error?: string;
  data: T;
}

export async function fetchJSON<T>(endpoint: string): Promise<T> {
  const response = await fetch(endpoint);
  const json = (await response.json()) as APIResponse<T>;
  if (!response.ok || !json.success) {
    throw new Error(json.error);
  }
  return json.data;
}

/** add Fava time, account and custom ledger filters */
export function createURLSearchParamsWithFavaFilters() {
  const params = new URLSearchParams();
  const currentParams = new URLSearchParams(location.search);

  for (const key of ["time", "account", "filter"]) {
    const value = currentParams.get(key);
    if (value) {
      params.set(key, value);
    }
  }

  return params;
}
