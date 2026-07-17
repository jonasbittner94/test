"use client";
import { Suspense, useEffect } from "react";
import { Canvas } from "@react-three/fiber";
import {
  OrbitControls,
  GizmoHelper,
  GizmoViewcube,
  ContactShadows,
} from "@react-three/drei";
import { StlModel } from "./STLModel";
import { Matrix4, Vector3, Euler, Quaternion } from "three";

type RotationTuple = [number, number, number];

export type SavedModelTransform = {
  index: number;
  position: [number, number, number];
  rotationEuler: [number, number, number];
  quaternion: number[];
  matrix: number[];
};

export type SceneProps = {
  url: string;
  positions: [number, number, number][];
  rotationsZ: number[];
  rotationsX: number[];
  rotationsY: number[];
  color?: string;
  castShadow?: boolean;
  receiveShadow?: boolean;
  scaled_length?: number;
  onBoundingBoxChange?: (boundingBox: [number, number, number]) => void;
  resetKey?: number;
  onTransformsChange?: (transforms: SavedModelTransform[]) => void;
};

export function Scene({
  url,
  positions,
  rotationsZ,
  rotationsX,
  rotationsY,
  color,
  castShadow = false,
  receiveShadow = false,
  scaled_length,
  onBoundingBoxChange,
  resetKey = 0,
  onTransformsChange,
}: SceneProps) {
  // Transformationen zum Speichern erzeugen
  useEffect(() => {
    const transforms: SavedModelTransform[] = positions.map((position, i) => {
      const rotationEuler: RotationTuple = [
        rotationsX[i] ?? 0,
        rotationsY[i] ?? 0,
        rotationsZ[i] ?? 0,
      ];

      const quaternion = new Quaternion().setFromEuler(
        new Euler(rotationEuler[0], rotationEuler[1], rotationEuler[2], "XYZ")
      );

      const matrix = new Matrix4().compose(
        new Vector3(...position),
        quaternion,
        new Vector3(1, 1, 1)
      );

      return {
        index: i,
        position,
        rotationEuler,
        quaternion: quaternion.toArray(),
        matrix: matrix.toArray(),
      };
    });

    onTransformsChange?.(transforms);
  }, [positions, rotationsX, rotationsY, rotationsZ, onTransformsChange]);

  return (
    <Canvas
      dpr={[1, 2]}
      camera={{ position: [200, 200, 300], fov: 50, near: 0.1, far: 5000 }}
      gl={{ toneMappingExposure: 0.8 }}
    >
      <GizmoHelper alignment="bottom-right" margin={[80, 80]}>
        <GizmoViewcube />
      </GizmoHelper>

      <axesHelper args={[100]} />
      <ambientLight intensity={0.7} />
      <hemisphereLight args={["#ffffff", "#404040", 0.6]} />
      <directionalLight position={[150, 250, 200]} intensity={1.4} castShadow />
      <directionalLight position={[-120, 80, -120]} intensity={0.5} />
      <ContactShadows
        position={[0, 0, 0]}
        opacity={0.4}
        blur={2.5}
        far={50}
        resolution={1024}
        frames={1}
      />
      <Suspense fallback={null}>
        {positions.map((pos, i) => (
          <StlModel
            key={`model-${resetKey}-${i}`}
            url={url}
            rotationZ={rotationsZ[i] ?? 0}
            rotationX={rotationsX[i] ?? 0}
            rotationY={rotationsY[i] ?? 0}
            color={color}
            castShadow={castShadow}
            receiveShadow={receiveShadow}
            position={pos}
            scaled_length={scaled_length}
            // boundingBox nur für den ersten Artikel berechnen
            onBoundingBoxChange={i === 0 ? onBoundingBoxChange : undefined}
            showLocalAxes={true}
            axesSize={40}
          />
        ))}
      </Suspense>
      <OrbitControls makeDefault />
    </Canvas>
  );
}