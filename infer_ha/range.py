from pydantic.dataclasses import dataclass
import random

@dataclass
class Range:
    min : float
    max : float

    def __post_init__(self) -> None:
        assert self.min <= self.max, "Invalid range"

    def contains(self, x : float) -> bool:
        return self.min <= x <= self.max

    def pick_random_point(self, rng : random.Random) -> float:
        return rng.uniform(self.min, self.max)
