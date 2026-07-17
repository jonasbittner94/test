from dataclasses import dataclass
from itertools import permutations


@dataclass
class Item:
    length: float
    width: float
    height: float
    weight: float

    @property
    def volume(self):
            return self.length * self.width * self.height

            

    def orientations(self):
        return [
            {"rotation_key": "xyz", "dimensions": (self.length, self.width, self.height)},
            {"rotation_key": "xzy", "dimensions": (self.length, self.height, self.width)},
            {"rotation_key": "yxz", "dimensions": (self.width, self.length, self.height)},
            {"rotation_key": "yzx", "dimensions": (self.width, self.height, self.length)},
            {"rotation_key": "zxy", "dimensions": (self.height, self.length, self.width)},
            {"rotation_key": "zyx", "dimensions": (self.height, self.width, self.length)},
        ]

@dataclass
class Box:
    name: str
    length: float
    width: float
    height: float
    capacityLHM:float

    @property
    def volume(self):
        return self.length * self.width * self.height

