import { decodeDelimitedArray, encodeDelimitedArray } from "serialize-query-params";

/** Uses a comma to delimit entries. e.g. ['a', 'b'] => qp?=a,b */
export const CommaArrayParam = {
  encode: (array: (string | null)[] | null | undefined): string | null | undefined => encodeDelimitedArray(array, ","),

  decode: (arrayStr: string | (string | null)[] | null | undefined): (string | null)[] | null | undefined =>
    decodeDelimitedArray(arrayStr, ","),
};
