"use client";

import { useEffect, useMemo, useState } from "react";
import Button from "@/components/ui/button";
import { Canvas, useLoader } from "@react-three/fiber";
import { OrbitControls, GizmoHelper, Edges } from "@react-three/drei";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import * as THREE from "three";
import { StlModel } from "../../components/rendering/STLModel";
import {
  PositionItem,
  PackingResult,
  PackingResponse,
  getRotationFromKey,
} from "@/lib/packing";

function ArticleMesh({
  item,
  modelUrl,
  scaledLength,
}: {
  item: PositionItem;
  modelUrl: string;
  scaledLength: number;
}) {
  const rotation = getRotationFromKey(item.rotation_key);

  return (
    <StlModel
      url={modelUrl}
      position={[item.x, item.y, item.z]}
      rotationX={THREE.MathUtils.degToRad(rotation[0])}
      rotationY={THREE.MathUtils.degToRad(rotation[1])}
      rotationZ={THREE.MathUtils.degToRad(rotation[2])}
      scaled_length={scaledLength}
      color="#49b749"
      castShadow
      receiveShadow
    />
  );
}

function BoxPreview({
  result,
  modelUrl,
}: {
  result: PackingResult;
  modelUrl: string;
}) {
  const { length, width, height } = result.box_dimensions;
  const effectiveScaledLength =
    result.scaledLength && result.scaledLength > 0
      ? result.scaledLength
      : result.article_dims.length;

  return (
    <Canvas
      shadows
      camera={{
        position: [length * 1.5, height * 1.2, width * 1.5],
        fov: 45,
      }}
      style={{
        width: "100%",
        height: "600px",
        background: "#f8fafc",
        borderRadius: "12px",
      }}
    >
      <ambientLight intensity={0.7} />
      <directionalLight position={[500, 800, 500]} intensity={1} castShadow />

      <group>
        <mesh position={[length / 2, width / 2, height / 2]}>
          <boxGeometry args={[length, width, height]} />
          <meshStandardMaterial color="#94a3b8" transparent opacity={0.15} />
          <Edges color="#475569" />
        </mesh>
        <axesHelper args={[100]} />

        {result.positions.map((item, index) => (
          <ArticleMesh
            key={index}
            item={item}
            modelUrl={modelUrl}
            scaledLength={effectiveScaledLength}
          />
        ))}
      </group>

      <gridHelper args={[Math.max(length, width) * 2, 20]} />
      <OrbitControls />
    </Canvas>
  );
}

type SortMode = "size" | "lhm";

export default function PackingResultsPage() {
  const [data, setData] = useState<PackingResponse | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [sortMode, setSortMode] = useState<SortMode>("size");
  useEffect(() => {
    const raw = localStorage.getItem("packingResults");
    const storedModelUrl = localStorage.getItem("convertedStlUrl");

    if (storedModelUrl) {
      setModelUrl(storedModelUrl);
    }

    if (!raw) return;

    try {
      const parsed = JSON.parse(raw) as PackingResponse;
      setData(parsed);
    } catch (error) {
      console.error("Konnte packingResults nicht lesen:", error);
    }
  }, []);

  // Sortierung: kleinste Verpackung zuerst bzw. hoechste LHM-Kapazitaet zuerst
  const results = useMemo(() => {
    const list = [...(data?.results ?? [])];

    const boxVolume = (result: PackingResult) =>
      result.box_dimensions.length *
      result.box_dimensions.width *
      result.box_dimensions.height;

    if (sortMode === "lhm") {
      list.sort(
        (a, b) => b.lhm_capacity - a.lhm_capacity || boxVolume(a) - boxVolume(b)
      );
    } else {
      list.sort((a, b) => boxVolume(a) - boxVolume(b));
    }

    return list;
  }, [data, sortMode]);

  const current = useMemo(
    () => results[activeIndex] ?? null,
    [results, activeIndex]
  );

  const handleSortChange = (mode: SortMode) => {
    setSortMode(mode);
    setActiveIndex(0);
  };

  const handlePrev = () => {
    setActiveIndex((prev) => Math.max(prev - 1, 0));
  };

  const handleNext = () => {
    setActiveIndex((prev) => Math.min(prev + 1, results.length - 1));
  };

  if (!data || !current) {
    return (
      <main style={{ padding: "24px" }}>
        <h2>Keine Ergebnisse vorhanden</h2>
        <p>Bitte zuerst eine Verpackungssuche durchführen.</p>
      </main>
    );
  }

  return (
    <main style={{ padding: "24px", display: "grid", gap: "24px" }}>
      <div>
        <h1>Verpackungsergebnisse</h1>
        <p>{data.message}</p>
      </div>

      <div
        style={{
          width: "100%",
          display: "flex",
          gap: "12px",
          alignItems: "center",
        }}
      >
        <Button
          variant="primary"
          onClick={handlePrev}
          disabled={activeIndex === 0}
        >
          Zurück
        </Button>

        <span>
          Ergebnis {activeIndex + 1} von {results.length}
        </span>

        <Button
          variant="primary"
          onClick={handleNext}
          disabled={activeIndex === results.length - 1}
        >
          Weiter
        </Button>

        <label
          htmlFor="sortMode"
          style={{ marginLeft: "auto", fontWeight: 600 }}
        >
          Sortieren nach:
        </label>
        <select
          id="sortMode"
          value={sortMode}
          onChange={(e) => handleSortChange(e.target.value as SortMode)}
          style={{
            padding: "6px 10px",
            borderRadius: "8px",
            border: "1px solid #cbd5e1",
            background: "#ffffff",
          }}
        >
          <option value="size">Verpackungsgröße (kleinste zuerst)</option>
          <option value="lhm">LHM-Kapazität (höchste zuerst)</option>
        </select>
      </div>

      <div
        style={{
          background: "#ffffff",
          borderRadius: "12px",
          padding: "20px",
          boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
        }}
      >
        <h2>{current.box}</h2>
        <div style={{ display: "grid", gap: "8px" }}>
          <div>
            <strong>Boxmaße(Innenmaß):</strong> {current.box_dimensions.length}
            {"mm "} × {current.box_dimensions.width}
            {"mm "} × {current.box_dimensions.height}
            {"mm "}
          </div>
          <div>
            <strong>Kapazität:</strong> {current.capacity}{" "}
            <span>Artikel pro Verpackung</span>
          </div>
          {/* 
          <div>
            <strong>Arikelmaße:</strong>{" "}
            {current.article_dims.length.toFixed(2)}
            {"mm "} × {current.article_dims.width.toFixed(2)}
            {"mm "} × {current.article_dims.height.toFixed(2)}
            {"mm "}
          </div>*/}
          <div>
            <strong>LHM-Kapazität:</strong>{" "}
            {current.lhm_capacity * current.positions.length}{" "}
            <span>Artikel pro LHM C</span>
          </div>
          <div>
            <strong>Platziert:</strong> {current.positions.length}{" "}
            <span>Artikel</span>{" "}
          </div>
          <div>
            <strong>Füllgrad:</strong> {(current.fill_rate * 100).toFixed(2)}%
          </div>
          {/* 
          <div>
            <strong>Genutztes Volumen:</strong> {current.used_volume.toFixed(2)}{" "}
            <span>mm²</span>
          </div>
          <div>
            <strong>Leerraum:</strong> {current.empty_volume.toFixed(2)}{" "}
            <span>mm²</span>
          </div>*/}
        </div>
      </div>

      <section
        style={{
          width: "100%",
          background: "#ffffff",
          borderRadius: "12px",
          padding: "20px",
          boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
        }}
      >
        <h2>3D-Visualisierung</h2>
        {modelUrl ? (
          <BoxPreview result={current} modelUrl={modelUrl} />
        ) : (
          <p>Kein Artikel-Mesh gefunden.</p>
        )}
      </section>
    </main>
  );
}
