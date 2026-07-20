'''Logik zum einlesen der Verpackungen'''

import csv
from pathlib import Path
from app.packing.optimizer import Box

#float nur speichern, wenn Wert vorhanden, sonst 0
def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_boxes_from_csv(csv_path: str,quantity:int,bulk:bool,mesh_volume:float,stability:str,estimated_packing_density: float | None = None,
) -> list[Box]:
    path = Path(csv_path)
    boxes: list[Box] = []


    article_volume=mesh_volume*quantity

    print(article_volume)

    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

    #Packmuster-Pfad
        if bulk is False:
            for row in reader:
                row_stability = row.get("Stabilität", "")

                if stability != "beliebig" and stability!="" and row_stability != stability:
                    continue
                
                #Vorfilerung
                length=float(row["length"])
                width=float(row["width"])
                height=float(row["height"])
                box_volume=length*width*height

                if article_volume<=box_volume:
                    boxes.append(
                        Box(
                            name=row["Object Name"],
                            length=float(row["length"]),
                            width=float(row["width"]),
                            height=float(row["height"]),
                            lhm_capacity=_safe_float(row["Amount per bin box (LHM C)"])
                        )
                )
                    
            boxes.sort(key=lambda box: box.volume)
            return boxes[:200]
        
        #Schüttgut-Pfad
        else:
            upper_density_limit = (
                min(0.60, estimated_packing_density * 1.3)
                if estimated_packing_density is not None
                else 0.40
            )
            lower_density_limit = 0.15
            for row in reader:
                row_stability = row.get("Stabilität", "")

                if stability != "beliebig" and stability!="" and row_stability != stability:
                    continue
                
                length=float(row["length"])
                width=float(row["width"])
                height=float(row["height"])
                box_volume=length*width*height
                required_density = article_volume / box_volume if box_volume > 0 else 0

                # Zufallsschuettung erreicht real nur ~35-55 % Dichte. Boxen mit
                # theoretischer Auslastung >0.55 koennen daher nie passen; die
                # Untergrenze 0.25 sortiert stark ueberdimensionierte Boxen aus.
                if (article_volume<=box_volume and required_density > lower_density_limit
                and required_density < upper_density_limit):
                    boxes.append(
                        Box(
                            name=row["Object Name"],
                            length=float(row["length"]),
                            width=float(row["width"]),
                            height=float(row["height"]),
                            lhm_capacity=_safe_float(row["Amount per bin box (LHM C)"])
                        )
                    
                )
            boxes.sort(key=lambda box: box.volume)
            return boxes[:20]



                
    