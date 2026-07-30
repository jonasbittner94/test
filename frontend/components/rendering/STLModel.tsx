"use client";

import { useEffect, useState } from "react";
import { BufferGeometry } from "three";
import { STLLoader } from "three-stdlib";
import * as THREE from "three";

export type StlModelProps = {
  url: string;
  position?: [number, number, number];
  rotationZ?: number;
  rotationX?: number;
  rotationY?: number;
  castShadow?: boolean;
  receiveShadow?: boolean;
  color?: string;
  scaled_length?: number;
  onBoundingBoxChange?: (boundingBox: [number, number, number]) => void;
  showLocalAxes?: boolean;
  axesSize?: number;
};

export function StlModel({
  url,
  position = [0, 0, 0],
  rotationZ = 0,
  rotationX = 0,
  rotationY = 0,
  castShadow = true,
  receiveShadow = true,
  color = "darkgreen",
  scaled_length = 0,
  onBoundingBoxChange,
  showLocalAxes = false,
  axesSize = 40,
}: StlModelProps) {
  const [geometry, setGeometry] = useState<BufferGeometry | null>(null);
  const [scaleFactor, setScaleFactor] = useState<number>(1);

  useEffect(() => {
    let mounted = true;
    new STLLoader().load(
      url,
      (geom) => {
        if (!mounted) return;
        geom.computeVertexNormals();
        geom.computeBoundingBox();

        if (geom.boundingBox) {
          const size = new THREE.Vector3();
          geom.boundingBox.getSize(size);

          const factor =
            scaled_length > 0 && size.x > 0 ? scaled_length / size.x : 1;

          setScaleFactor(factor);
          onBoundingBoxChange?.([size.x * factor, size.y, size.z]);
        }

        geom.center();
        setGeometry(geom);
      },
      undefined,
      (err) => console.error("Failed to load STL:", err)
    );
    return () => {
      mounted = false;
    };
  }, [url, scaled_length, onBoundingBoxChange]);

  if (!geometry) return null;

  return (
    <group position={position} rotation={[rotationX, rotationY, rotationZ]}>
      {showLocalAxes && <axesHelper args={[axesSize]} />}

      <mesh
        scale={[scaleFactor, 1, 1]}
        geometry={geometry}
        castShadow={castShadow}
        receiveShadow={receiveShadow}
      >
        <meshStandardMaterial color={color} metalness={0.05} roughness={0.45} />
      </mesh>
    </group>
  );
}
