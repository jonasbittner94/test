"use client";

import Button from "@/components/ui/button";
import { gapSize } from "three/tsl";

type SliderProps = {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
};

function Slider({
  label,
  value,
  onChange,
  min = 5,
  max = 200,
  step = 1,
}: SliderProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <label style={{ fontWeight: 600 }}>{label}</label>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
      <div style={{ display: "flex", gap: 10 }}>
        <Button
          variant="primary"
          onClick={() => onChange(Math.max(min, value - 1))}
          style={{ width: 40, height: 40 }}
        >
          -1
        </Button>
        <Button
          variant="primary"
          onClick={() => onChange(Math.max(min, value + 1))}
          style={{ width: 40, height: 40 }}
        >
          +1
        </Button>
      </div>
      <span style={{ fontSize: 12, color: "#333" }}>{value.toFixed(2)}</span>
    </div>
  );
}

export type ControlPanelProps = {
  spacingX: number;
  spacingY: number;
  layerGap: number;
  onSpacingXChange: (v: number) => void;
  onSpacingYChange: (v: number) => void;
  onLayerGapChange: (v: number) => void;
  rotationAll: boolean;
  onRotationAllChange: (checked: boolean) => void;
  onRotateZ: () => void;
  onRotateX: () => void;
  onRotateY: () => void;
  resetPosition: () => void;
};

export function ControlPanel({
  spacingX,
  spacingY,
  layerGap,
  rotationAll,
  onSpacingXChange,
  onSpacingYChange,
  onLayerGapChange,
  onRotationAllChange,
  onRotateZ,
  onRotateX,
  onRotateY,
  resetPosition,
}: ControlPanelProps) {
  return (
    <div
      style={{
        position: "absolute",
        left: 10,
        top: 100,
        display: "flex",
        flexDirection: "column",
        gap: 12,
        padding: 12,
        width: 240,
        background: "rgba(255, 255, 255, 0.85)",
        backdropFilter: "blur(4px)",
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        zIndex: 10,
      }}
    >
      <Slider
        label="Abstand X (− = Überlappung)"
        value={spacingX}
        onChange={onSpacingXChange}
        min={-100}
        max={200}
      />
      <Slider
        label="Abstand Y (− = Überlappung)"
        value={spacingY}
        onChange={onSpacingYChange}
        min={-100}
        max={200}
      />
      <Slider
        label="Ebenenabstand (− = Überlappung)"
        value={layerGap}
        onChange={onLayerGapChange}
        min={-100}
        max={200}
      />
      <label
        htmlFor="rotation-all"
        style={{ display: "flex", alignItems: "center", gap: 8 }}
      >
        <input
          id="rotation-all"
          type="checkbox"
          name="Rotation für alle Artikel:"
          checked={rotationAll}
          onChange={(e) => onRotationAllChange(e.target.checked)}
        />
        Rotation für alle Artikel
      </label>
      <Button variant="primary" onClick={onRotateZ}>
        Rotieren 90° um Z-Achse
      </Button>
      <Button onClick={onRotateX}>Rotieren 90° um X-Achse </Button>
      <Button onClick={onRotateY}>Rotieren 90° um Y-Achse</Button>
      <Button onClick={resetPosition}>Position zurücksetzen</Button>
    </div>
  );
}
