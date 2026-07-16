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

export type SourceUnit = "mm" | "cm" | "m" | "in";

export const unitToMm: Record<SourceUnit, number> = {
  mm: 1,
  cm: 10,
  m: 1000,
  in: 25.4,
};
