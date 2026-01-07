import {
  AnyRoute,
  InferFullSearchSchema,
  InferFullSearchSchemaInput,
  RegisteredRouter,
  useNavigate,
  useSearch,
} from "@tanstack/react-router";
import { FullSearchSchema, FullSearchSchemaInput } from "@tanstack/router-core";
import { useCallback } from "react";

export function useSearchParam<
  TRoute extends AnyRoute,
  TSearchSchemaInput extends InferFullSearchSchemaInput<TRoute>,
  TSearchSchema extends InferFullSearchSchema<TRoute>,
  TKey extends keyof TSearchSchemaInput,
>(route: TRoute, name: TKey): [TSearchSchema[TKey], (value: TSearchSchemaInput[TKey]) => void] {
  const search = route.useSearch({ select: (x) => x[name] });
  const navigate = route.useNavigate();
  const setter = useCallback(
    (value: TSearchSchemaInput[TKey]) => {
      return navigate({
        to: ".",
        search: (prev) => ({
          ...prev,
          [name]: value,
        }),
        replace: true,
      });
    },
    [name, navigate],
  );

  return [search, setter];
}

export function useGlobalParam<
  TRouter extends RegisteredRouter,
  TSearchSchemaInput extends FullSearchSchemaInput<TRouter["routeTree"]>,
  TSearchSchema extends FullSearchSchema<TRouter["routeTree"]>,
  TKey extends keyof TSearchSchemaInput,
>(name: TKey): [TSearchSchema[TKey], (value: TSearchSchemaInput[TKey]) => void] {
  const search = useSearch<TRouter, undefined, false>({ strict: false, select: (x) => x[name] });
  const navigate = useNavigate();
  const setter = useCallback(
    (value: TSearchSchemaInput[TKey]) => {
      return navigate({
        to: ".",
        search: (prev) => ({
          ...prev,
          [name]: value,
        }),
        replace: true,
      });
    },
    [name, navigate],
  );

  return [search, setter];
}

export function useArrayQueryParam(
  [value, setValue]: [string | undefined, (value: string | undefined) => void],
  delim = "~",
): [string[], (value: string[]) => void] {
  return [
    value ? value.split(delim) : [],
    (value: string[]) => setValue(value.length > 0 ? value.join(delim) : undefined),
  ];
}
