"use client"; //Rendering auf Client-Seite im Browser

import { useState, useEffect, Suspense, Dispatch, SetStateAction } from "react";
import { useSearchParams } from "next/navigation";
import {
  ControlPanel,
  type RotationMode,
} from "../../components/rendering/ControlPanel";
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
  const [rotationMode, setRotationMode] = useState<RotationMode>("right");
  const [resetKey, setResetKey] = useState(0);
  const [boundingBox, setBoundingBox] = useState<
    [number, number, number] | null
  >(null);
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

  const hasNegativeSpacing = spacingX < 0 || spacingY < 0 || layerGap < 0;
  const hasScaledLength = scaledLength !== undefined && scaledLength > 0;

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

  // Das Backend normalisiert die Positionen in den Ursprung und leitet die
  // Musterabmessungen selbst ab -> hier reichen die rohen Elemente.
  function getPatternPayload() {
    if (!boundingBox || scenePositions.length === 0) return null;

    const [sizeX, sizeY, sizeZ] = boundingBox;

    return {
      elements: scenePositions.map((position, index) => ({
        index,
        position: { x: position[0], y: position[1], z: position[2] },
        rotation: {
          x: rotationsX[index] ?? 0,
          y: rotationsY[index] ?? 0,
          z: rotationsZ[index] ?? 0,
        },
        size: { x: sizeX, y: sizeY, z: sizeZ },
      })),
    };
  }

  const handleSearchPackaging = async () => {
    setPackingError("");

    if (!boundingBox) {
      setPackingError("Bounding Box des Artikels ist noch nicht verfügbar.");
      return;
    }

    const itemQuantity = Number(localStorage.getItem("itemQuantity") ?? "0");
    const [itemLength, itemWidth, itemHeight] = boundingBox;
    const scaled_length =
      scaledLength && scaledLength > 0 ? scaledLength : itemLength;
    const stability = localStorage.getItem("stability") ?? "beliebig";
    const fillResidual = localStorage.getItem("fillResidual") !== "false";

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
          item_width: itemWidth,
          item_height: itemHeight,
          file_url: activeUrl,
          quantity: itemQuantity,
          scaledLength: scaled_length,
          pattern: pattern,
          stability: stability,
          fill_residual: fillResidual,
        }),
      });

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

  // Artikel am Rand einer Ebene: je Ebene (y) die Positionen mit minimalem bzw.
  // maximalem Wert auf der gewaehlten Achse.
  const edgeIndicesPerLayer = (axis: 0 | 2, pick: "min" | "max") => {
    const byLayer = new Map<number, number[]>();
    scenePositions.forEach((p, idx) => {
      byLayer.set(p[1], [...(byLayer.get(p[1]) ?? []), idx]);
    });

    const indices: number[] = [];
    byLayer.forEach((layer) => {
      const values = layer.map((idx) => scenePositions[idx][axis]);
      const target = pick === "min" ? Math.min(...values) : Math.max(...values);
      layer.forEach((idx) => {
        if (scenePositions[idx][axis] === target) indices.push(idx);
      });
    });
    return indices;
  };

  const getTargetIndices = () => {
    switch (rotationMode) {
      case "all":
        return scenePositions.map((_, idx) => idx);
      case "back":
        return edgeIndicesPerLayer(0, "max");
      case "top": {
        const maxY = Math.max(...scenePositions.map((p) => p[1]));
        return scenePositions
          .map((p, idx) => (p[1] === maxY ? idx : -1))
          .filter((idx) => idx >= 0);
      }
      case "right":
      default:
        return edgeIndicesPerLayer(2, "min");
    }
  };

  // Alle drei Achsen-Rotationen teilen dieselbe Logik: entweder nur die rechten
  // Artikel (rightIndices) oder alle (rotationAll) um 90° weiterdrehen.
  const rotate = (setter: Dispatch<SetStateAction<number[]>>) => {
    setter((prev) => {
      const next =
        prev.length === scenePositions.length
          ? [...prev]
          : new Array(scenePositions.length).fill(0);

      const targets = getTargetIndices();

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
    setRotationMode("right");
    setResetKey((prev) => prev + 1);
  };

  return (
    <div
      style={{
        width: "100%",
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
        onRotationModeChange={setRotationMode}
        rotationMode={rotationMode}
        resetPosition={resetPosition}
      />

      <div
        style={{
          position: "relative",
          width: "100%",
          height: "100%",
        }}
      >
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

        {(hasNegativeSpacing || hasScaledLength) && (
          <div
            style={{
              position: "absolute",
              top: "16px",
              right: "16px",
              width: "280px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
              zIndex: 10,
            }}
          >
            {hasNegativeSpacing && (
              <div
                style={{
                  padding: "12px 16px",
                  backgroundColor: "#f8d7da",
                  color: "#842029",
                  border: "1px solid #f5c2c7",
                  borderRadius: "8px",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                }}
              >
                Warnung: Die Hüllgeometrien der Artikel überschneiden sich
                jetzt. Bitte achten Sie darauf, dass die echten Geometrien sich
                nicht berühren!
              </div>
            )}

            {hasScaledLength && (
              <div
                style={{
                  padding: "12px 16px",
                  backgroundColor: "#f8d7da",
                  color: "#842029",
                  border: "1px solid #f5c2c7",
                  borderRadius: "8px",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                }}
              >
                Hinweis: Es handelt sich um eine skallierte Version der
                CAD-Datei. Die Artikelgeometrie kann vom echten Artikel
                abweichen.
              </div>
            )}
          </div>
        )}
      </div>

      {packingError && (
        <p style={{ color: "red", marginTop: "12px" }}>{packingError}</p>
      )}

      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          width: "100%",
          marginTop: "12px",
        }}
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
