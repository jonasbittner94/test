from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from math import floor
from app.packing.models import Item, Box



@dataclass
class PackingOptimizer:
    item: Item
    quantity: int
    boxes: List[Box]
    overlap: Optional[Dict[str, float]] = None
    pattern: Optional[Dict] = None
    mesh_volume: Optional[float] = None

    _eps: float = field(default=1e-9, init=False)

    def __post_init__(self):
        if self.overlap is None:
            self.overlap = {"x": 0.0, "y": 0.0, "z": 0.0}

            
    #
    # Geometrie- & Orientierungs-Helfer
    #

    def _scale_dimensions(self, dimensions) -> Tuple[float, float, float]:
        x, y, z = dimensions
        return (x, y, z)

    def volume(self) -> float:
        return self.item.volume

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

    def _pattern_step(self, elements, key: str, full_dim: float) -> float:
        """Rasterschritt (Mitte-zu-Mitte) einer Achse aus der 3D-Anordnung ableiten.

        Der Schritt ist der kleinste Abstand benachbarter Artikel entlang der Achse.
        Ordnet der Nutzer die Artikel enger als ihre Bounding Box an (Abstand < Kante),
        ist der Schritt < full_dim -> bewusste Ueberlappung, die dichter gepackt wird.
        Groessere Luecken werden auf die Kantenlaenge begrenzt (dicht, kein Ueberlappen).
        """
        coords = sorted({round(element["position"][key], 6) for element in elements})
        if len(coords) < 2:
            return full_dim
        gaps = [b - a for a, b in zip(coords, coords[1:]) if b - a > self._eps]
        if not gaps:
            return full_dim
        return min(min(gaps), full_dim)

    #
    # Packmuster-Packing (Greedy Extreme Points + Dual-Dimension-Overlap)
    #
    def _fits_overlap(self, point, full_dims, eff_dims, box: Box, placements) -> bool:
        """Passt der Artikel am Extreme Point?

        Box-Grenze wird mit der VOLLEN Kante geprueft (kein Artikel ragt aus der
        Box). Die Kollision gegen bereits platzierte Artikel wird mit der
        REDUZIERTEN (effektiven) Kante geprueft -> die reduzierten Boxen duerfen
        sich nicht ueberschneiden, wodurch sich die echten (vollen) Artikel genau
        um (Kante - effektiv) ueberlappen = die gewollte Verschachtelung.
        """
        px, py, pz = point
        L, W, H = full_dims
        eL, eW, eH = eff_dims

        if (
            px + L > box.length + self._eps
            or py + W > box.width + self._eps
            or pz + H > box.height + self._eps
        ):
            return False

        for placed in placements:
            ox = min(px + eL, placed["x0"] + placed["length"]) - max(px, placed["x0"])
            oy = min(py + eW, placed["y0"] + placed["width"]) - max(py, placed["y0"])
            oz = min(pz + eH, placed["z0"] + placed["height"]) - max(pz, placed["z0"])
            if ox > self._eps and oy > self._eps and oz > self._eps:
                return False

        return True

    def _pack_pattern(self, box: Box):
        pattern_data = self._get_pattern_data()
        if not pattern_data:
            return None

        # Rasterschritte (Ueberlappung) im Original-Frame: x=Laenge, y=Breite, z=Hoehe.
        # Aus der 3D-Anordnung abgeleitet; Abstand < Kante => bewusste Ueberlappung.
        elements = pattern_data["elements"]
        dim0 = {"x": self.item.length, "y": self.item.width, "z": self.item.height}
        step0 = {
            "x": self._pattern_step(elements, "x", dim0["x"]),
            "y": self._pattern_step(elements, "y", dim0["y"]),
            "z": self._pattern_step(elements, "z", dim0["z"]),
        }

        if any(d <= self._eps for d in dim0.values()):
            return None

        # Fuer jede Box die beste Orientierung suchen: die meisten Artikel auf der
        # x,z-Ebene (Grundflaeche nx*nz), bei Gleichstand groesste Gesamtkapazitaet.
        # Die Ueberlappung (step) dreht mit dem Artikel mit (gleiche Achs-Permutation
        # wie die Kantenmasse). rotation_key wird ausgegeben, damit das Frontend die
        # gewaehlte Drehung darstellt.
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
            if capacity < self.quantity:
                # nur Orientierungen beruecksichtigen, welche die Menge fassen
                continue

            score = (nx * nz, capacity)  # 1. x,z-Ebene, 2. Gesamtkapazitaet
            if best is None or score > best["score"]:
                best = {
                    "rotation_key": orientation["rotation_key"],
                    "dims": (L, W, H),
                    "steps": (sx, sy, sz),
                    "grid": (nx, ny, nz),
                    "capacity": capacity,
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

        # Greedy Extreme-Point-Packing mit Dual-Dimension.
        #   Kollision/EP-Erzeugung -> reduzierte (effektive) Box  => Verschachtelung
        #   Box-Grenze/Rendering   -> volle Box                   => nichts ragt raus
        # Extreme Points werden nach (y, z, x) abgearbeitet: erst die x,z-Ebene
        # fuellen, dann entlang y (Breite) stapeln.
        positions = []
        placements = []
        extreme_points = {(0.0, 0.0, 0.0)}

        while len(positions) < self.quantity and extreme_points:
            placed_in_round = False
            for point in sorted(extreme_points, key=lambda p: (p[1], p[2], p[0])):
                if self._inside_any(point, placements):
                    extreme_points.discard(point)
                    continue
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

        if len(positions) < self.quantity:
            return None

        if self.mesh_volume is not None:
            single_volume = self.mesh_volume
            print(single_volume)
        else: 
            single_volume = (articleLengthReal * articleWidthReal * articleHeightReal)
            print(single_volume,"hat nicht geklappt")

        
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
            "capacityLHM": capacity * box.capacityLHM,
            "fill_rate": fill_rate,
            "empty_volume": empty_volume,
            "used_volume": used_volume,
            "positions": positions,
        }
    
    # ==================================================================
    # Box-Auswahl & Ranking
    # ==================================================================
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

            if result and result["fill_rate"] > 0.5:
                candidates.append(result)


        if not candidates:
            return []

        candidates.sort(
            key=lambda r: (
                -r["fill_rate"],
                r["fill_rate"],
            )
        )

        return candidates[:limit]