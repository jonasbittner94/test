"use client";

import { useEffect, useState } from "react";
import { BufferGeometry } from "three";
import { STLLoader } from "three-stdlib";
import * as THREE from "three";
import { ConvexGeometry } from "three-stdlib"; // oder "three/examples/jsm/geometries/ConvexGeometry"





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
  onVolumeChange?: (volume: number) => void;
  onSelect?: () => void;
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
  onVolumeChange,
  onSelect,
  showLocalAxes = false,
  axesSize = 40,
}: StlModelProps) {
  const [geometry, setGeometry] = useState<BufferGeometry | null>(null);
  const [boxSize, setBoxSize] = useState<[number, number, number] | null>(null);
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

          const baseBoxSize: [number, number, number] = [
            size.x,
            size.y,
            size.z,
          ];

          const factor =
            scaled_length > 0 && size.x > 0 ? scaled_length / size.x : 1;

          const scaledBoundingBox: [number, number, number] = [
            size.x * factor,
            size.y,
            size.z,
          ];

          setScaleFactor(factor);
          setBoxSize(baseBoxSize);
          onBoundingBoxChange?.(scaledBoundingBox);

         
        
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
    <group
      position={position}
      rotation={[rotationX, rotationY, rotationZ]}
      onClick={(e) => {
        e.stopPropagation();
        onSelect?.();
      }}
    >
      {showLocalAxes && <axesHelper args={[axesSize]} />}

      <mesh
        scale={[scaleFactor, 1, 1]}
        geometry={geometry}
        castShadow={castShadow}
        receiveShadow={receiveShadow}
        onClick={(e) => {
          e.stopPropagation();
          onSelect?.();
        }}
      >
        <meshStandardMaterial color={color} metalness={0.05} roughness={0.45} />
      </mesh>
      {/* 
      {boxSize && (
        <mesh scale={[scaleFactor, 1, 1]}>
          <boxGeometry args={boxSize} />
          <meshBasicMaterial color="#ef4444" wireframe />
        </mesh>
      )}*/}
    </group>
  );
}
