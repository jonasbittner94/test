// Zentrale Basis-URL des Backends.
// Fallback ist das lokale Backend.
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Baut eine absolute Backend-URL aus einem Pfad, z. B. apiUrl("/packing/top20").
export function apiUrl(path: string): string {
  const base = API_BASE_URL.replace(/\/$/, "");
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${base}${suffix}`;
}