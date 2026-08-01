'''Packmuster-Optimierung: sucht fuer eine Artikelmenge die passenden Boxen.'''

from typing import List, Optional, Dict
from dataclasses import dataclass, field
from math import floor
from app.packing.models import Item, Box


@dataclass
class PackingOptimizer:
    item: Item
    quantity: int
    boxes: List[Box] = field(default_factory=list)
    pattern: Optional[Dict] = None
    mesh_volume: Optional[float] = None
    fill_residual: bool = True


    # numerische toleranz gegen rundungsfehler beim vergleichen von massen
    _toleranz: float = field(default=1e-9, init=False)

    #
    # Geometrie- & Orientierungs-Helfer
    #

    def _fill_remaining_space(self, region, orientations):
        """Packt den Restraum neben dem Hauptraster mit so vielen artikeln wie möglich."""
        x0, y0, z0, rest_x, rest_y, rest_z = region

        best_fit = None
        for orientation in orientations:
            length, width, height = orientation["dimensions"]
            count_x = int((rest_x + self._toleranz) // length)
            count_y = int((rest_y + self._toleranz) // width)
            count_z = int((rest_z + self._toleranz) // height)
            count = count_x * count_y * count_z
            if count > 0 and (best_fit is None or count > best_fit["count"]):
                best_fit = {
                    "count": count,
                    "dims": (length, width, height),
                    "grid": (count_x, count_y, count_z),
                    "rotation_key": orientation["rotation_key"],
                }

        if best_fit is None:
            return [], 0

        length, width, height = best_fit["dims"]
        count_x, count_y, count_z = best_fit["grid"]
        positions = [
            {
                "x": x0 + i * length + length / 2,
                "y": y0 + j * width + width / 2,
                "z": z0 + k * height + height / 2,
                "rotation_key": best_fit["rotation_key"],
                "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
                "pattern_index": None,
            }
            for i in range(count_x)
            for j in range(count_y)
            for k in range(count_z)
        ]
        return positions, best_fit["count"]

    def _unique_orientations(self):
        """alle artikel-orientierungen ohne doppelte kantenlaengen-tripel."""
        unique = []
        seen = set()

        for orientation in self.item.orientations():
            dimensions = tuple(orientation["dimensions"])
            if dimensions in seen:
                continue

            seen.add(dimensions)
            unique.append(
                {
                    "dimensions": dimensions,
                    "rotation_key": orientation["rotation_key"],
                }
            )

        return unique

    #
    # Pattern-Daten & Ueberlappung aus der 3D-Anordnung
    #

    def _normalized_elements(self):
        """packmuster-elemente mit ausgedrehten abmessungen, in den ursprung
        verschoben. none, wenn kein packmuster vorliegt."""
        if not self.pattern:
            return None

        elements = self.pattern.get("elements", [])
        if not elements:
            return None

        prepared_elements = [
            {
                "index": element["index"],
                "position": element["position"],
                "rotation": element.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0}),
                "size": self._rotated_size(
                    element["size"],
                    element.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0}),
                ),
            }
            for element in elements
        ]

        min_x = min(element["position"]["x"] for element in prepared_elements)
        min_y = min(element["position"]["y"] for element in prepared_elements)
        min_z = min(element["position"]["z"] for element in prepared_elements)

        return [
            {
                "index": element["index"],
                "position": {
                    "x": element["position"]["x"] - min_x,
                    "y": element["position"]["y"] - min_y,
                    "z": element["position"]["z"] - min_z,
                },
                "rotation": element["rotation"],
                "size": element["size"],
            }
            for element in prepared_elements
        ]

    def effective_article_volume(self) -> float:
        """Artikelvolumen fuer die Box-Vorfilterung. Bei starker Ueberlappung ist
        der Rasterabstand kleiner als das Mesh -> dann zaehlt der Raster-Quader."""
        elements = self._normalized_elements()
        if not elements:
            return self.mesh_volume

        step_volume = (
            self._pattern_step(elements, "x", self.item.length)
            * self._pattern_step(elements, "y", self.item.width)
            * self._pattern_step(elements, "z", self.item.height)
        )
        return min(self.mesh_volume, step_volume)

    def _pattern_step(self, elements, key: str, full_dimension: float) -> float:
        """schrittweite entlang einer achse = kleinster abstand zwischen zwei
        artikelpositionen. bei nur einem artikel fallback auf volle kantenlaenge."""
        coords = sorted({round(element["position"][key], 6) for element in elements})
        if len(coords) < 2:
            return full_dimension

        gaps = [b - a for a, b in zip(coords, coords[1:]) if b - a > self._toleranz]
        if not gaps:
            return full_dimension

        return min(gaps)

    def _fits_overlap(self, point, full_dims, effective_dims, box: Box, placements) -> bool:
        """passt der artikel an diesen punkt, ohne die box zu verlassen und ohne
        den durch die schrittweiten definierten mindestabstand zu verletzen?"""
        px, py, pz = point
        length, width, height = full_dims
        effective_length, effective_width, effective_height = effective_dims

        if (
            px + length > box.length + self._toleranz
            or py + width > box.width + self._toleranz
            or pz + height > box.height + self._toleranz
        ):
            return False

        for placed in placements:
            dx = abs(px - placed["x0"])
            dy = abs(py - placed["y0"])
            dz = abs(pz - placed["z0"])

            if (
                dx < effective_length - self._toleranz
                and dy < effective_width - self._toleranz
                and dz < effective_height - self._toleranz
            ):
                return False

        return True

    #
    # Packlogik
    #

    def _build_pattern_lookup(self, elements, base_steps):
        """ordnet jeder rasterzelle (ix, iy, iz) rotation und index aus dem
        packmuster zu und liefert die groesse des musters in zellen."""
        step_x, step_y, step_z = base_steps["x"], base_steps["y"], base_steps["z"]

        lookup = {}
        for element in elements:
            ix = int(round(element["position"]["x"] / step_x)) if step_x > self._toleranz else 0
            iy = int(round(element["position"]["y"] / step_y)) if step_y > self._toleranz else 0
            iz = int(round(element["position"]["z"] / step_z)) if step_z > self._toleranz else 0

            lookup[(ix, iy, iz)] = {
                "rotation": element.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0}),
                "index": element["index"],
            }

        pattern_grid = (
            max((key[0] for key in lookup), default=0) + 1,
            max((key[1] for key in lookup), default=0) + 1,
            max((key[2] for key in lookup), default=0) + 1,
        )
        return lookup, pattern_grid

    def _find_best_orientation(self, box: Box, base_dimensions, base_steps):

        """sucht die orientierung, die die menge mit dem wenigsten verschenkten
        platz unterbringt."""
        unique_orientations = self._unique_orientations()

        best = None
        for orientation in self.item.orientations():
            axis_x, axis_y, axis_z = orientation["rotation_key"]

            length = base_dimensions[axis_x]
            width = base_dimensions[axis_y]
            height = base_dimensions[axis_z]

            step_x = base_steps[axis_x]
            step_y = base_steps[axis_y]
            step_z = base_steps[axis_z]

            if (
                length > box.length + self._toleranz
                or width > box.width + self._toleranz
                or height > box.height + self._toleranz
            ):
                continue

            if step_x <= self._toleranz or step_y <= self._toleranz or step_z <= self._toleranz:
                continue

            count_x = floor((box.length - length + self._toleranz) / step_x) + 1
            count_y = floor((box.width - width + self._toleranz) / step_y) + 1
            count_z = floor((box.height - height + self._toleranz) / step_z) + 1
            if count_x <= 0 or count_y <= 0 or count_z <= 0:
                continue

            main_capacity = count_x * count_y * count_z

            used_x = (count_x - 1) * step_x + length
            used_y = (count_y - 1) * step_y + width
            used_z = (count_z - 1) * step_z + height
            residual_positions = []
            residual_count = 0

            if self.fill_residual:

                regions = [
                    (used_x, 0.0, 0.0, box.length - used_x, box.width, box.height),
                    (0.0, used_y, 0.0, used_x, box.width - used_y, box.height),
                    (0.0, 0.0, used_z, used_x, used_y, box.height - used_z),
                ]

                for region in regions:
                    region_positions, region_count = self._fill_remaining_space(region, unique_orientations)
                    residual_positions += region_positions
                    residual_count += region_count

            total_capacity = main_capacity + residual_count
            if total_capacity < self.quantity:
                continue

            required_main = min(self.quantity, main_capacity)
            used_layers_z = min(
                count_z,
                (required_main + count_x * count_y - 1) // (count_x * count_y),
            )
            compact_used_z = (used_layers_z - 1) * step_z + height if used_layers_z > 0 else 0.0

            estimated_used_volume = used_x * used_y * compact_used_z
            excess_capacity = total_capacity - self.quantity

            score = (-excess_capacity, -estimated_used_volume)

            if best is None or score > best["score"]:
                best = {
                    "rotation_key": orientation["rotation_key"],
                    "dims": (length, width, height),
                    "steps": (step_x, step_y, step_z),
                    "capacity": total_capacity,
                    "residual_positions": residual_positions,
                    "score": score,
                }

        return best

    def _place_articles(self, box: Box, best, pattern_lookup, pattern_grid):
        """greedy extreme-point-packing: platziert artikel an den freien ecken,
        abgearbeitet nach y, z, x (erst die ebene, dann die hoehe)."""
        full_dims = best["dims"]
        effective_dims = best["steps"]
        length, width, height = full_dims
        effective_length, effective_width, effective_height = effective_dims
        rotation_key = best["rotation_key"]
        pattern_nx, pattern_ny, pattern_nz = pattern_grid

        positions = []
        placements = []
        extreme_points = {(0.0, 0.0, 0.0)}

        while len(positions) < self.quantity and extreme_points:
            placed_in_round = False
            for point in sorted(extreme_points, key=lambda p: (p[0], p[2], p[1])):
                extreme_points.discard(point)

                if not self._fits_overlap(point, full_dims, effective_dims, box, placements):
                    continue

                px, py, pz = point
                ix = int(round(px / effective_length)) if effective_length > self._toleranz else 0
                iy = int(round(py / effective_width)) if effective_width > self._toleranz else 0
                iz = int(round(pz / effective_height)) if effective_height > self._toleranz else 0

                pattern_key = (
                    ix % pattern_nx if pattern_nx > 0 else 0,
                    iy % pattern_ny if pattern_ny > 0 else 0,
                    iz % pattern_nz if pattern_nz > 0 else 0,
                )
                pattern_match = pattern_lookup.get(pattern_key)
                if pattern_match is None:
                    pattern_match = {"rotation": {"x": 0.0, "y": 0.0, "z": 0.0}, "index": None}

                placements.append(
                    {
                        "x0": px,
                        "y0": py,
                        "z0": pz,
                        "length": length,
                        "width": width,
                        "height": height,
                    }
                )
                positions.append(
                    {
                        "x": px + length / 2,
                        "y": py + width / 2,
                        "z": pz + height / 2,
                        "rotation_key": rotation_key,
                        "rotation": pattern_match["rotation"],
                        "pattern_index": pattern_match["index"],
                    }
                )

                extreme_points.add((round(px + effective_length, 6), py, pz))
                extreme_points.add((px, round(py + effective_width, 6), pz))
                extreme_points.add((px, py, round(pz + effective_height, 6)))
                placed_in_round = True
                break

            if not placed_in_round:
                break

        return positions

    def _build_result(self, box: Box, best, positions):
        """baut das ergebnis-dict fuer eine box (masse, fuellgrad, positionen)."""
        article_length, article_width, article_height = best["dims"]

        if self.mesh_volume is not None:
            single_volume = self.mesh_volume
        else:
            single_volume = article_length * article_width * article_height

        used_volume = single_volume * self.quantity

        return {
            "box": box.name,
            "box_dimensions": {
                "length": box.length,
                "width": box.width,
                "height": box.height,
            },
            "article_dims": {
                "length": article_length,
                "width": article_width,
                "height": article_height,
            },
            "scaledLength": self.item.length,
            "capacity": best["capacity"],
            "fill_rate": used_volume / box.volume if box.volume > 0 else 0.0,
            "positions": positions,
        }

    def _rotated_size(self, size, rotation):
        """berechnet die effektiven achsparallelen abmessungen nach 90-grad-rotationen."""
        dims = [size["x"], size["y"], size["z"]]

        quarter_turn = 1.5707963267948966
        rx = int(round(rotation.get("x", 0.0) / quarter_turn)) % 4
        ry = int(round(rotation.get("y", 0.0) / quarter_turn)) % 4
        rz = int(round(rotation.get("z", 0.0) / quarter_turn)) % 4

        for _ in range(rx):
            dims[1], dims[2] = dims[2], dims[1]
        for _ in range(ry):
            dims[0], dims[2] = dims[2], dims[0]
        for _ in range(rz):
            dims[0], dims[1] = dims[1], dims[0]

        return {
            "x": dims[0],
            "y": dims[1],
            "z": dims[2],
        }

    def _pack_pattern(self, box: Box):
        elements = self._normalized_elements()
        if not elements:
            return None

        base_dimensions = {
            "x": max(element["size"]["x"] for element in elements),
            "y": max(element["size"]["y"] for element in elements),
            "z": max(element["size"]["z"] for element in elements),
        }

        if any(dimension <= self._toleranz for dimension in base_dimensions.values()):
            return None

        base_steps = {
            axis: self._pattern_step(elements, axis, base_dimensions[axis])
            for axis in ("x", "y", "z")
        }

        pattern_lookup, pattern_grid = self._build_pattern_lookup(elements, base_steps)

        best = self._find_best_orientation(box, base_dimensions, base_steps)
        if best is None:
            return None

        positions = self._place_articles(box, best, pattern_lookup, pattern_grid)

        for residual_position in best["residual_positions"]:
            if len(positions) >= self.quantity:
                break
            positions.append(residual_position)

        if len(positions) < self.quantity:
            return None

        return self._build_result(box, best, positions)

    #
    # Box-Auswahl & Ranking
    #

    def find_top_boxes(self, limit: int = 5):
        # box_loader hat bereits nach Abmessungen dedupliziert
        candidates = []

        for box in self.boxes:
            result = self._pack_pattern(box) if self.pattern else None
            if result:
                result["lhm_capacity"] = box.lhm_capacity
                candidates.append(result)

        candidates.sort(
            key=lambda result: result["box_dimensions"]["length"]
            * result["box_dimensions"]["width"]
            * result["box_dimensions"]["height"]
        )

        return candidates[:limit]
