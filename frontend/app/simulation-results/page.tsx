"use client";

import { useEffect, useMemo, useState } from "react";

type SimulationBox = {
  name: string;
  length: number;
  width: number;
  height: number;
  capacityLHM: number;
};

type SimulationResult = {
  box: SimulationBox;
  filling_height_m: number;
  filling_height_mm: number;
  relative_filling_height_percent: number;
  total_article_volume_cm3: number;
  used_box_volume_cm3: number;
  packing_density_percent: number;
  articles_per_lhm?: number;
};

type SimulationResponse = {
  message?: string;
  results: SimulationResult[];
};

type SortMode = "filling" | "lhm";

export default function PackingResultsPage() {
  const [data, setData] = useState<SimulationResponse | null>(null);
  const [sortMode, setSortMode] = useState<SortMode>("filling");

  useEffect(() => {
    const raw = localStorage.getItem("simulationResult");

    if (!raw) return;

    try {
      const parsed = JSON.parse(raw) as SimulationResponse;
      setData(parsed);
    } catch (error) {
      console.error("Konnte Simulationsergebnisse nicht lesen:", error);
    }
  }, []);

  // Sortierung: niedrigste relative Fuellhoehe zuerst (meiste Reserve)
  // bzw. hoechste Artikel pro LHM zuerst
  const results = useMemo(() => {
    const list = [...(data?.results ?? [])];

    if (sortMode === "lhm") {
      list.sort(
        (a, b) =>
          (b.articles_per_lhm ?? 0) - (a.articles_per_lhm ?? 0) ||
          a.relative_filling_height_percent - b.relative_filling_height_percent
      );
    } else {
      list.sort(
        (a, b) =>
          b.relative_filling_height_percent - a.relative_filling_height_percent
      );
    }

    return list;
  }, [data, sortMode]);

  if (!data || results.length === 0) {
    return (
      <main style={{ padding: "24px" }}>
        <h2>Keine Simulationsergebnisse vorhanden</h2>
        <p>Bitte zuerst eine Simulation durchführen.</p>
      </main>
    );
  }

  return (
    <main style={{ padding: "24px", display: "grid", gap: "24px" }}>
      <div>
        <h1>Simulationsergebnisse</h1>
        {data.message && <p>{data.message}</p>}
        <p>
          Angezeigt werden {results.length} Ergebnis
          {results.length === 1 ? "" : "se"}.
        </p>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <label htmlFor="sortMode" style={{ fontWeight: 600 }}>
          Sortieren nach:
        </label>
        <select
          id="sortMode"
          value={sortMode}
          onChange={(e) => setSortMode(e.target.value as SortMode)}
          style={{
            padding: "6px 10px",
            borderRadius: "8px",
            border: "1px solid #cbd5e1",
            background: "#ffffff",
          }}
        >
          <option value="filling">relative Füllhöhe (höchste zuerst)</option>
          <option value="lhm">Artikel pro LHM (höchste zuerst)</option>
        </select>
      </div>

      <section
        style={{
          display: "grid",
          gap: "16px",
        }}
      >
        {results.map((result, index) => (
          <div
            key={`${result.box.name}-${index}`}
            style={{
              background: "#ffffff",
              borderRadius: "12px",
              padding: "20px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
              display: "grid",
              gap: "8px",
            }}
          >
            <h2>
              #{index + 1} {result.box.name}
            </h2>

            <div>
              <strong>Boxmaße:</strong> {result.box.length} mm ×{" "}
              {result.box.width} mm × {result.box.height} mm
            </div>

            {result.articles_per_lhm !== undefined && (
              <div>
                <strong>Artikel pro LHM:</strong>{" "}
                {Math.round(result.articles_per_lhm)}
              </div>
            )}

            <div>
              <strong>Füllhöhe:</strong> {result.filling_height_mm.toFixed(2)}{" "}
              mm
            </div>

            <div>
              <strong>Relative Füllhöhe:</strong>{" "}
              {result.relative_filling_height_percent.toFixed(2)} %
            </div>

            <div>
              <strong>Packdichte:</strong>{" "}
              {result.packing_density_percent.toFixed(2)} %
            </div>
          </div>
        ))}
      </section>
    </main>
  );
}
