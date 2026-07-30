// Gemeinsamer Vertrag fuer die Packmuster-Ergebnisse (Backend /packing/top20).
// Wird vom Producer (rendering) und Consumer (packing-results) genutzt.

export type RotationKey = "xyz" | "xzy" | "yxz" | "yzx" | "zxy" | "zyx";

export type PositionItem = {
  x: number;
  y: number;
  z: number;
  rotation_key: RotationKey;
  pattern_index: number | null;
  rotation?: {
    x: number;
    y: number;
    z: number;
  };
};

export type PackingResult = {
  box: string;
  article_dims: {
    length: number;
    width: number;
    height: number;
  };
  scaledLength: number;
  box_dimensions: {
    length: number;
    width: number;
    height: number;
  };
  capacity: number;
  lhm_capacity: number;
  fill_rate: number;
  positions: PositionItem[];
};

export type PackingResponse = {
  message: string;
  results: PackingResult[];
};

// Zuordnung von rotation_key zur Rotation (Grad) fuer die 3D-Darstellung.
export function getRotationFromKey(
  rotationKey: RotationKey
): [number, number, number] {
  switch (rotationKey) {
    case "xyz":
      return [0, 0, 0];
    case "xzy":
      return [90, 0, 0];
    case "yxz":
      return [0, 0, 90];
    case "yzx":
      return [90, 0, 90];
    case "zxy":
      return [90, 90, 0];
    case "zyx":
      return [0, 90, 0];
    default:
      return [0, 0, 0];
  }
}
