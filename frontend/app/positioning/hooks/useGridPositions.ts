import { useMemo } from "react";

type Params = {
  gridSize: number;
  layers: number;
  spacingX: number;
  spacingZ: number;
  layerGap: number;
};

export function useGridPositions({
  gridSize,
  layers,
  spacingX,
  spacingZ,
  layerGap,
}: Params): [number, number, number][] {
  return useMemo(() => {
    const pos: [number, number, number][] = [];

    for (let l = 0; l < layers; l++) {
      for (let i = 0; i < gridSize; i++) {
        for (let j = 0; j < gridSize; j++) {
          const x = (i - (gridSize - 1) / 2) * spacingX;
          const z = (j - (gridSize - 1) / 2) * spacingZ;
          const y = (l - (layers - 1) / 2) * layerGap;

          pos.push([x, y, z]);
        }
      }
    }

    return pos;
  }, [gridSize, layers, spacingX, spacingZ, layerGap]);
}
