"use client";

import { useEffect, useState } from "react";
import { BufferGeometry } from "three";
import { STLLoader } from "three-stdlib";
import * as THREE from "three";
import { ConvexGeometry } from "three-stdlib"; // oder "three/examples/jsm/geometries/ConvexGeometry"

function calculateEnclosedVolume(geometry: THREE.BufferGeometry): number {
  if (!geometry || !geometry.isBufferGeometry) return 0;

  // 1. Extrahiere alle Punkte aus dem Mesh
  const positionAttr = geometry.attributes.position;
  const points: THREE.Vector3[] = [];
  for (let i = 0; i < positionAttr.count; i++) {
    points.push(new THREE.Vector3().fromBufferAttribute(positionAttr, i));
  }

  try {
    // 2. Erzeuge die konvexe Hülle (schließt alle Hohlräume und Löcher)
    const convexGeom = new ConvexGeometry(points);
    
    // 3. Berechne das Volumen dieser geschlossenen Hülle mit der Standard-Pyramiden-Methode
    const volume = calculateMeshVolume(convexGeom); // Deine bisherige Methode
    
    convexGeom.dispose(); // Speicher freigeben
    return volume;
  } catch (err) {
    console.error("Konvexe Hülle konnte nicht berechnet werden, nutze Bounding Box:", err);
    // Fallback auf Bounding Box Volumen
    geometry.computeBoundingBox();
    const size = new THREE.Vector3();
    geometry.boundingBox?.getSize(size);
    return size.x * size.y * size.z;
  }
}
//Berechnung des genauen Volumens des Artikels
function calculateMeshVolume(geometry: THREE.BufferGeometry): number {
  if (!geometry || !geometry.isBufferGeometry) return 0;

  const position = geometry.attributes.position;
  const index = geometry.index;
  let sum = 0;

  const p1 = new THREE.Vector3();
  const p2 = new THREE.Vector3();
  const p3 = new THREE.Vector3();

  function signedVolumeOfTriangle(v1: THREE.Vector3, v2: THREE.Vector3, v3: THREE.Vector3) {
    return v1.dot(v2.cross(v3)) / 6.0;
  }

  if (index !== null) {
    for (let i = 0; i < index.count; i += 3) {
      p1.fromBufferAttribute(position, index.getX(i));
      p2.fromBufferAttribute(position, index.getY(i));
      p3.fromBufferAttribute(position, index.getZ(i));
      sum += signedVolumeOfTriangle(p1, p2, p3);
    }
  } else {
    for (let i = 0; i < position.count; i += 3) {
      p1.fromBufferAttribute(position, i);
      p2.fromBufferAttribute(position, i + 1);
      p3.fromBufferAttribute(position, i + 2);
      sum += signedVolumeOfTriangle(p1, p2, p3);
    }
  }
  console.log(Math.abs(sum))
  return Math.abs(sum);
}


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

          //berechnung des Artikel Volumens
          const baseVolume = calculateEnclosedVolume(geom);

          //Skallierung des Volumens, bei Skallierung der X-Achse
          const finalVolume = baseVolume * factor * 1 * 1;
          
          onVolumeChange?.(finalVolume);
        
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
  }, [url, scaled_length, onBoundingBoxChange,onVolumeChange]);

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
