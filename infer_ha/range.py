from pydantic.dataclasses import dataclass
import random

@dataclass
class Range:
    min : float
    max : float

    def __post_init__(self):
        assert self.min <= self.max, "Invalid range"

    def contains(self, x : float) -> bool:
        return self.min <= x <= self.max

    def pick_random_point(self, rng : random.Random) -> float:
        return rng.uniform(self.min, self.max)

assert Range(1,2).contains(1.5), "Range.contains failure"
ex_Range : Range = Range(1, 2)
assert str(ex_Range) == "Range(min=1.0, max=2.0)", "Range bug:" + str(ex_Range)
ex_Range2 : Range = Range(min=1, max=2)
assert str(ex_Range2) == "Range(min=1.0, max=2.0)", "Range bug" + str(ex_Range)
