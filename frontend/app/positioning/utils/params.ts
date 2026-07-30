import type { ReadonlyURLSearchParams } from "next/navigation";

export const getNumberParam = (
  sp: ReadonlyURLSearchParams,
  key: string,
  fallback: number
): number => {
  const v = sp.get(key);
  const n = v ? Number(v) : NaN;
  return Number.isFinite(n) ? n : fallback;
};
