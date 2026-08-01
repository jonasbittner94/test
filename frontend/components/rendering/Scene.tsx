"use client";
import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import {
  OrbitControls,
  GizmoHelper,
  GizmoViewcube,
  ContactShadows,
} from "@react-three/drei";
import { StlModel } from "./STLModel";

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
}: SceneProps) {
  return (
    <Canvas
      frameloop="demand"
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