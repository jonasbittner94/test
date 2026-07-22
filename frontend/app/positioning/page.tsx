"use client"; //Rendering auf Client-Seite im Browser

import { useState, useEffect, Suspense, Dispatch, SetStateAction } from "react";
import type { PackingResponse } from "@/lib/packing";
import { useSearchParams } from "next/navigation";
import { ControlPanel } from "../../components/rendering/ControlPanel";
import { Scene } from "../../components/rendering/Scene";
import { useFileUrl } from "./hooks/useFileUrl";
import { useRouter } from "next/navigation";

import { useGridPositions } from "./hooks/useGridPositions";
import { getNumberParam } from "./utils/params";
import Button from "@/components/ui/button";

const GRID_SIZE = 2;
const LAYERS = 2;

function RenderingContent() {
  const router = useRouter();

  const sp = useSearchParams();
  const fileUrl = useFileUrl();

  const activeUrl: string = fileUrl || sp.get("url") || "/models/part.stl";
  const color = sp.get("color") ?? "#49b749";
  const castShadow = sp.get("castShadow") !== "false";
  const receiveShadow = sp.get("receiveShadow") !== "false";

  // Slider-Werte = Abstand (Luecke) zwischen den Artikel-Bounding-Boxes.
  // 0 = buendig aneinander, negativ = bewusste Ueberlappung.
  const [spacingX, setSpacingX] = useState(getNumberParam(sp, "spacingX", 0));
  const [spacingY, setSpacingY] = useState(getNumberParam(sp, "spacingY", 0));
  const [layerGap, setLayerGap] = useState(getNumberParam(sp, "layergap", 0));
  const [rotationAll, setRotationAll] = useState(false);
  const [resetKey, setResetKey] = useState(0);
  const [boundingBox, setBoundingBox] = useState<
    [number, number, number] | null
  >(null);
  const [exactVolume, setExactVolume] = useState<number | null>(null);
  const [packingResult, setPackingResult] = useState<PackingResponse | null>(
    null
  );
  const [loadingPacking, setLoadingPacking] = useState(false);
  const [packingError, setPackingError] = useState("");

  // Artikelgroesse pro Achse (aus der geladenen STL-Bounding-Box), Fallback vor dem Laden.
  // useGridPositions erwartet Mitte-zu-Mitte-Abstaende => Artikelkante + gewuenschter Abstand.
  // Achsen-Zuordnung: spacingX->x, spacingY->z, layerGap->y (siehe useGridPositions).
  const [artX, artY, artZ] = boundingBox ?? [50, 50, 50];
  const basePositions = useGridPositions({
    gridSize: GRID_SIZE,
    layers: LAYERS,
    spacingX: artX + spacingX,
    spacingY: artZ + spacingY,
    layerGap: artY + layerGap,
  });

  const [scaledLength, setScaledLength] = useState<number | undefined>(
    undefined
  );

  useEffect(() => {
    const storedScaledLength = localStorage.getItem("scaled_length");

    if (storedScaledLength !== null) {
      const parsedScaledLength = Number(storedScaledLength);

      if (Number.isFinite(parsedScaledLength)) {
        setScaledLength(parsedScaledLength);
      }
    }
  }, []);

  const [scenePositions, setScenePositions] = useState(basePositions);

  const [rotationsZ, setRotationsZ] = useState<number[]>(() =>
    new Array(scenePositions.length).fill(0)
  );
  const [rotationsX, setRotationsX] = useState<number[]>(() =>
    new Array(scenePositions.length).fill(0)
  );
  const [rotationsY, setRotationsY] = useState<number[]>(() =>
    new Array(scenePositions.length).fill(0)
  );

  useEffect(() => {
    setScenePositions(basePositions);
  }, [basePositions]);

  function getElementsData() {
    return scenePositions.map((position, index) => ({
      index,
      position: {
        x: position[0],
        y: position[1],
        z: position[2],
      },
      rotation: {
        x: rotationsX[index] ?? 0,
        y: rotationsY[index] ?? 0,
        z: rotationsZ[index] ?? 0,
      },
      size: boundingBox
        ? {
            x: boundingBox[0],
            y: boundingBox[1],
            z: boundingBox[2],
          }
        : null,
    }));
  }

  function getPatternPayload() {
    if (!boundingBox) return null;

    const elements = getElementsData().filter(
      (element) => element.size !== null
    );
    if (elements.length === 0) return null;

    const minX = Math.min(...elements.map((e) => e.position.x));
    const minY = Math.min(...elements.map((e) => e.position.y));
    const minZ = Math.min(...elements.map((e) => e.position.z));

    const normalizedElements = elements.map((element) => ({
      index: element.index,
      position: {
        x: element.position.x - minX,
        y: element.position.y - minY,
        z: element.position.z - minZ,
      },
      rotation: element.rotation,
      size: element.size!,
    }));

    const maxX = Math.max(
      ...normalizedElements.map((e) => e.position.x + e.size.x)
    );
    const maxY = Math.max(
      ...normalizedElements.map((e) => e.position.y + e.size.y)
    );
    const maxZ = Math.max(
      ...normalizedElements.map((e) => e.position.z + e.size.z)
    );

    return {
      length: maxX,
      width: maxY,
      height: maxZ,
      count: normalizedElements.length,
      elements: normalizedElements,
    };
  }
  const handleSearchPackaging = async () => {
    setPackingError("");
    setPackingResult(null);

    if (!boundingBox) {
      setPackingError("Bounding Box des Artikels ist noch nicht verfügbar.");
      return;
    }

    const itemQuantity = Number(localStorage.getItem("itemQuantity") ?? "0");
    const [itemLength, itemWidth, itemHeight] = boundingBox;
    const scaled_length =
      scaledLength && scaledLength > 0 ? scaledLength : itemLength;
    const stability = localStorage.getItem("stability") ?? "beliebig";

    if (!itemQuantity || itemQuantity <= 0) {
      setPackingError("Keine gültige Artikelmenge gefunden.");
      return;
    }

    const pattern = getPatternPayload();

    if (!pattern) {
      setPackingError("Pattern konnte nicht bestimmt werden.");
      return;
    }

    try {
      setLoadingPacking(true);

      const response = await fetch("http://localhost:8000/packing/top20", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          item_length: itemLength,
          item_width: itemWidth,
          item_height: itemHeight,
          file_url: activeUrl,
          quantity: itemQuantity,
          scaledLength: scaled_length,
          pattern: pattern,
          mesh_volume: exactVolume,
          stability: stability,
        }),
      });

      console.log(exactVolume);

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || "Fehler bei der Verpackungssuche.");
      }

      localStorage.setItem("packingResults", JSON.stringify(data));
      router.push("/packing-results");
    } catch (error) {
      setPackingError(
        error instanceof Error
          ? error.message
          : "Unbekannter Fehler bei der Verpackungssuche."
      );
    } finally {
      setLoadingPacking(false);
    }
  };

  const rightIndices = (() => {
    const byLayer = new Map<number, { idx: number; x: number }[]>();
    scenePositions.forEach((p, idx) => {
      const arr = byLayer.get(p[1]) ?? [];
      arr.push({ idx, x: p[2] });
      byLayer.set(p[1], arr);
    });
    const indices: number[] = [];
    byLayer.forEach((arr) => {
      const minY = Math.min(...arr.map((a) => a.x));
      arr.forEach((a) => {
        if (a.x === minY) indices.push(a.idx);
      });
    });
    return indices;
  })();

  // Alle drei Achsen-Rotationen teilen dieselbe Logik: entweder nur die rechten
  // Artikel (rightIndices) oder alle (rotationAll) um 90° weiterdrehen.
  const rotate = (setter: Dispatch<SetStateAction<number[]>>) => {
    setter((prev) => {
      const next =
        prev.length === scenePositions.length
          ? [...prev]
          : new Array(scenePositions.length).fill(0);

      const targets = rotationAll
        ? scenePositions.map((_, idx) => idx)
        : rightIndices;

      targets.forEach((i) => {
        next[i] = next[i] + Math.PI / 2;
      });

      return next;
    });
  };

  const handleRotateZ = () => rotate(setRotationsZ);
  const handleRotateX = () => rotate(setRotationsX);
  const handleRotateY = () => rotate(setRotationsY);

  const resetPosition = () => {
    setSpacingX(0);
    setSpacingY(0);
    setLayerGap(0);
    setScenePositions(basePositions);
    setRotationsX(new Array(basePositions.length).fill(0));
    setRotationsY(new Array(basePositions.length).fill(0));
    setRotationsZ(new Array(basePositions.length).fill(0));
    setRotationAll(false);
    setResetKey((prev) => prev + 1);
  };

  return (
    <div
      style={{
        width: "80%",
        height: "80dvh",
        alignSelf: "self-start",
        backgroundColor: "#FFFFFF",
      }}
    >
      <ControlPanel
        spacingX={spacingX}
        spacingY={spacingY}
        layerGap={layerGap}
        onSpacingXChange={setSpacingX}
        onSpacingYChange={setSpacingY}
        onLayerGapChange={setLayerGap}
        onRotateZ={handleRotateZ}
        onRotateX={handleRotateX}
        onRotateY={handleRotateY}
        onRotationAllChange={setRotationAll}
        rotationAll={rotationAll}
        resetPosition={resetPosition}
      />
      <Scene
        url={activeUrl}
        positions={scenePositions}
        rotationsZ={rotationsZ}
        color={color}
        castShadow={castShadow}
        receiveShadow={receiveShadow}
        rotationsX={rotationsX}
        rotationsY={rotationsY}
        onBoundingBoxChange={setBoundingBox}
        resetKey={resetKey}
        scaled_length={scaledLength}
      />
      {packingError && (
        <p style={{ color: "red", marginTop: "12px" }}>{packingError}</p>
      )}

      {packingResult && (
        <pre
          style={{
            marginTop: "12px",
            padding: "12px",
            background: "#f5f5f5",
            borderRadius: "8px",
            overflowX: "auto",
          }}
        >
          {JSON.stringify(packingResult, null, 2)}
        </pre>
      )}

      <div
        style={{ display: "flex", justifyContent: "flex-end", width: "100%" }}
      >
        <Button
          variant="primary"
          style={{ alignItems: "right" }}
          onClick={handleSearchPackaging}
        >
          {loadingPacking ? "Suche..." : "Verpackung suchen"}
        </Button>
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={null}>
      <RenderingContent />
    </Suspense>
  );
}
