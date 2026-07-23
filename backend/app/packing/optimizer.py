from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from math import floor
from app.packing.models import Item, Box
from app.packing.lhm import get_lhm_capacity
from itertools import permutations




@dataclass
class PackingOptimizer:
    item: Item
    quantity: int
    boxes: List[Box]
    pattern: Optional[Dict] = None
    mesh_volume: Optional[float] = None

    _eps: float = field(default=1e-9, init=False)
    _lhm_length: float = field(default=600.0, init=False)
    _lhm_width: float = field(default=400.0, init=False)
    _lhm_height: float = field(default=220.0, init=False)


    #
    # Geometrie- & Orientierungs-Helfer
    #

    def _scale_dimensions(self, dimensions) -> Tuple[float, float, float]:
        x, y, z = dimensions
        return (x, y, z)
    
    #Füllung des Restraumes naben dem Packmuster
    def _fill_residual(self, region, orientations):
        #Füllung des Restraumes naben dem Packmuster
        x0, y0, z0, rx, ry, rz = region

        best = None
        for orientation in orientations:
            L, W, H = orientation["dimensions"]
            nx = int((rx + self._eps) // L)
            ny = int((ry + self._eps) // W)
            nz = int((rz + self._eps) // H)
            count = nx * ny * nz
            if count > 0 and (best is None or count > best["count"]):
                best = {
                    "count": count,
                    "dims": (L, W, H),
                    "grid": (nx, ny, nz),
                    "rotation_key": orientation["rotation_key"],
                }

        if best is None:
            return [], 0

        L, W, H = best["dims"]
        nx, ny, nz = best["grid"]
        positions = [
            {
                "x": x0 + i * L + L / 2,
                "y": y0 + j * W + W / 2,
                "z": z0 + k * H + H / 2,
                "orientation": (L, W, H),
                "rotation_key": best["rotation_key"],
                "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
                "pattern_index": None,
            }
            for i in range(nx)
            for j in range(ny)
            for k in range(nz)
        ]
        return positions, best["count"]

    #ausgabe einer Liste mit allen einzigartigen Orientierungen des Artikels
    def _unique_orientations(self):
        unique = []
        seen = set()

        for orientation_data in self.item.orientations():
            dims = tuple(orientation_data["dimensions"])
            scaled_dims = self._scale_dimensions(dims)

            if scaled_dims in seen:
                continue

            seen.add(scaled_dims)
            unique.append(
                {
                    "dimensions": scaled_dims,
                    "rotation_key": orientation_data["rotation_key"],
                }
            )

        return unique
    
    #liegt der Artikel in einem bereits platzierten anderen Artikel
    def _inside_any(self, point, placements) -> bool:
        px, py, pz = point

        for placed in placements:
            if (
                placed["x0"] + self._eps < px < placed["x0"] + placed["length"] - self._eps
                and placed["y0"] + self._eps < py < placed["y0"] + placed["width"] - self._eps
                and placed["z0"] + self._eps < pz < placed["z0"] + placed["height"] - self._eps
            ):
                return True

        return False

    #
    # Pattern-Daten & Ueberlappung aus der 3D-Anordnung
    #
    def _get_pattern_data(self):
        if not self.pattern:
            return None

        elements = self.pattern.get("elements", [])
        if not elements:
            return None
        
        #untere Ecke getten
        min_x = min(element["position"]["x"] for element in elements)
        min_y = min(element["position"]["y"] for element in elements)
        min_z = min(element["position"]["z"] for element in elements)

        #Obere Ecke getten
        max_x = max(
            element["position"]["x"] + element["size"]["x"] for element in elements
        )
        max_y = max(
            element["position"]["y"] + element["size"]["y"] for element in elements
        )
        max_z = max(
            element["position"]["z"] + element["size"]["z"] for element in elements
        )

        normalized_elements = [
            {
                "index": element["index"],
                "position": {
                    "x": element["position"]["x"] - min_x,
                    "y": element["position"]["y"] - min_y,
                    "z": element["position"]["z"] - min_z,
                },
                "rotation": element.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0}),
                "size": element["size"],
            }
            for element in elements
        ]
        pattern_length = max_x - min_x
        pattern_width = max_y - min_y
        pattern_height = max_z - min_z
        pattern_volume = pattern_length * pattern_width * pattern_height
        pattern_count= len(normalized_elements)
        article_volume = pattern_volume / pattern_count if pattern_count > 0 else 0

        return {
            "elements": normalized_elements,
            "length": pattern_length,
            "width": pattern_width,
            "height": pattern_height,
            "count": pattern_count,
            "normArtVol":article_volume,
        }

    #Abstand zwischen den Artikeln bestimmen, der als ein Schritt für das Packmuster genutzt wird
        #Ist eine Lücke zwischen den Artikeln, wir der Abstand auf die Kantenlänge der Achse gesetzt
    def _pattern_step(self, elements, key: str, full_dim: float) -> float:
        coords = sorted({round(element["position"][key], 6) for element in elements})
        if len(coords) < 2:
            return full_dim
        gaps = [b - a for a, b in zip(coords, coords[1:]) if b - a > self._eps]
        if not gaps:
            return full_dim
        return min(min(gaps), full_dim)

    #Prüfung ob eine Kollision mit einem gepackten Artikel entsteht ( > erlaubtes Overlap)           
    def _fits_overlap(self, point, full_dims, eff_dims, box: Box, placements) -> bool:
        px, py, pz = point
        L, W, H = full_dims
        eL, eW, eH = eff_dims

        #Prüfung mit vollen Dimensionen ob die Boxgrenze überschritten wird
        if (
            px + L > box.length + self._eps
            or py + W > box.width + self._eps
            or pz + H > box.height + self._eps
        ):
            return False
        #Prüfung mit reduzierten Dimensionen ob der Artikel mit einem bereits platzierten Artikel kollidiert 
        for placed in placements:
            ox = min(px + eL, placed["x0"] + placed["length"]) - max(px, placed["x0"])
            oy = min(py + eW, placed["y0"] + placed["width"]) - max(py, placed["y0"])
            oz = min(pz + eH, placed["z0"] + placed["height"]) - max(pz, placed["z0"])
            if ox > self._eps and oy > self._eps and oz > self._eps:
                return False

        return True
    
    #Echte Packlogik
    def _pack_pattern(self, box: Box):
        pattern_data = self._get_pattern_data()
        if not pattern_data:
            return None


        elements = pattern_data["elements"]
        dim0 = {"x": self.item.length, "y": self.item.width, "z": self.item.height}
        step0 = {
            "x": self._pattern_step(elements, "x", dim0["x"]),
            "y": self._pattern_step(elements, "y", dim0["y"]),
            "z": self._pattern_step(elements, "z", dim0["z"]),
        }

        if any(d <= self._eps for d in dim0.values()):
            return None
        
        unique_orients = self._unique_orientations()

        # Fuer jede Box die beste Orientierung suchen (meiste Artikel aus x,z Ebene)
        best = None
        for orientation in self.item.orientations():
            a, b, c = orientation["rotation_key"]
            L, W, H = dim0[a], dim0[b], dim0[c]
            sx, sy, sz = step0[a], step0[b], step0[c]

            if (
                L > box.length + self._eps
                or W > box.width + self._eps
                or H > box.height + self._eps
            ):
                continue

            nx = floor((box.length - L + self._eps) / sx) + 1
            ny = floor((box.width - W + self._eps) / sy) + 1
            nz = floor((box.height - H + self._eps) / sz) + 1
            if nx <= 0 or ny <= 0 or nz <= 0:
                continue

            capacity = nx * ny * nz

            # Vom Hauptgrid belegter Quader
            used_x = (nx - 1) * sx + L
            used_y = (ny - 1) * sy + W
            used_z = (nz - 1) * sz + H

            # Drei ueberlappungsfreie Restquader: Streifen in x, y und z
            regions = [
                (used_x, 0.0, 0.0, box.length - used_x, box.width, box.height),
                (0.0, used_y, 0.0, used_x, box.width - used_y, box.height),
                (0.0, 0.0, used_z, used_x, used_y, box.height - used_z),
            ]
            residual_positions = []
            residual_count = 0
            for region in regions:
                positions_r, count_r = self._fill_residual(region, unique_orients)
                residual_positions += positions_r
                residual_count += count_r

            total_capacity = capacity + residual_count
            if total_capacity < self.quantity:
                # Menge passt auch mit Restraum nicht -> Orientierung verwerfen
                continue

            required_main = min(self.quantity, capacity)

            used_layers_z = min(
                nz,
                (required_main + nx * ny - 1) // (nx * ny),
            )

            compact_used_z = (
                (used_layers_z - 1) * sz + H
                if used_layers_z > 0
                else 0.0
            )

            estimated_used_volume = used_x * used_y * compact_used_z
            excess_capacity = total_capacity - self.quantity

            score = (
                -estimated_used_volume,
                -excess_capacity,
                capacity,
            )


            if best is None or score > best["score"]:
                best = {
                    "rotation_key": orientation["rotation_key"],
                    "dims": (L, W, H),
                    "steps": (sx, sy, sz),
                    "grid": (nx, ny, nz),
                    "capacity": total_capacity,
                    "residual_positions": residual_positions,
                    "score": score,
                }

        if best is None:
            return None

        articleLengthReal, articleWidthReal, articleHeightReal = best["dims"]
        full_dims = best["dims"]
        eff_dims = best["steps"]
        L, W, H = full_dims
        eL, eW, eH = eff_dims
        nx, ny, nz = best["grid"]
        capacity = best["capacity"]
        rotation_key = best["rotation_key"]

        # Greedy Extreme-Point-Packing
        # abarbeitung nach y,z,x (Erst Ebene, dann höhe)
        positions = []
        placements = []
        extreme_points = {(0.0, 0.0, 0.0)}

        while len(positions) < self.quantity and extreme_points:
            placed_in_round = False
            for point in sorted(extreme_points, key=lambda p: (p[1], p[2], p[0])):
                extreme_points.discard(point)
        
                # 2. Prüfen, ob er überhaupt in die Box passt und nicht kollidiert
                if not self._fits_overlap(point, full_dims, eff_dims, box, placements):
                    continue

                px, py, pz = point
                placements.append(
                    {
                        "x0": px,
                        "y0": py,
                        "z0": pz,
                        "length": eL,
                        "width": eW,
                        "height": eH,
                    }
                )
                positions.append(
                    {
                        "x": px + L / 2,
                        "y": py + W / 2,
                        "z": pz + H / 2,
                        "orientation": full_dims,
                        "rotation_key": rotation_key,
                        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
                        "pattern_index": None,
                    }
                )

                extreme_points.discard(point)
                extreme_points.add((round(px + eL, 6), py, pz))
                extreme_points.add((px, round(py + eW, 6), pz))
                extreme_points.add((px, py, round(pz + eH, 6)))
                placed_in_round = True
                break  # nach jeder Platzierung Extreme Points neu bewerten

            if not placed_in_round:
                break

        for residual_position in best["residual_positions"]:
            if len(positions) >= self.quantity:
                break
            positions.append(residual_position)

        if len(positions) < self.quantity:
            return None

        if self.mesh_volume is not None:
            single_volume = self.mesh_volume
        else: 
            single_volume = (articleLengthReal * articleWidthReal * articleHeightReal)

        print("single_volume",single_volume)
        used_volume = single_volume*self.quantity
        fill_rate = used_volume / box.volume if box.volume > 0 else 0.0
        empty_volume = box.volume - used_volume

        return {
            "box": box.name,
            "box_dimensions": {
                "length": box.length,
                "width": box.width,
                "height": box.height,
            },
            "article_dims": {
                "length": articleLengthReal,
                "width": articleWidthReal,
                "height": articleHeightReal,
            },
            "orientation": full_dims,
            "rotation_key": rotation_key,
            "scaledLength": self.item.length,
            "pattern": {
                "length": pattern_data["length"],
                "width": pattern_data["width"],
                "height": pattern_data["height"],
                "count": pattern_data["count"],
            },
            "grid": {
                "nx": nx,
                "ny": ny,
                "nz": nz,
            },
            "capacity": capacity,
            "capacityLHM": self.quantity * box.capacityLHM,
            "fill_rate": fill_rate,
            "empty_volume": empty_volume,
            "used_volume": used_volume,
            "positions": positions,
        }
    
    # Box-Auswahl & Ranking
    def evaluate_box(self, box: Box):
        if self.pattern:
            return self._pack_pattern(box)

    def find_top_boxes(self, limit: int = 5):
        seen_dimensions: set[tuple[float, float, float]] = set()
        candidates = []

        for box in self.boxes:
            dimensions = (box.length, box.width, box.height)

            if dimensions in seen_dimensions:
                continue

            result = self.evaluate_box(box)
            seen_dimensions.add(dimensions)

            if result:# and result["fill_rate"] > 0.5:
                result["lhm_capacity"] = get_lhm_capacity(box)
                candidates.append(result)


        if not candidates:
            return []

        candidates.sort(key=lambda r: r["box_dimensions"]["length"]
                        * r["box_dimensions"]["width"]
                        * r["box_dimensions"]["height"])
        

        return candidates[:limit]
    