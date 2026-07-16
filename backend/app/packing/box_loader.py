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


def load_boxes_from_csv(csv_path: str,quantity:int,bulk:bool,mesh_volume=float
) -> list[Box]:
    path = Path(csv_path)
    boxes: list[Box] = []
    quantity:int
    bulk:bool
    mesh_volume:float


    article_volume=mesh_volume*quantity

    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        if bulk == False:
            #Vorfilerung
            for row in reader:
                length=float(row["length"])
                width=float(row["width"])
                height=float(row["height"])
                box_volume=length*width*height
                if article_volume<=box_volume and (article_volume/box_volume)>0.5 :
                    boxes.append(
                        Box(
                            name=row["Object Name"],
                            length=float(row["length"]),
                            width=float(row["width"]),
                            height=float(row["height"]),
                            capacityLHM=_safe_float(row["Amount per bin box (LHM C)"])
                        )
                )
                    
                boxes.sort(key=lambda box: box.volume)
            return boxes[:200]
        else:
            for row in reader:
                length=float(row["length"])
                width=float(row["width"])
                height=float(row["height"])
                box_volume=length*width*height
                if article_volume<=box_volume and (article_volume/box_volume)>0.6 and (article_volume/box_volume)<0.9 :
                    boxes.append(
                        Box(
                            name=row["Object Name"],
                            length=float(row["length"]),
                            width=float(row["width"]),
                            height=float(row["height"]),
                            capacityLHM=_safe_float(row["Amount per bin box (LHM C)"])
                        )
                )
            boxes.sort(key=lambda box: box.volume)
            return boxes[:20]



                
    