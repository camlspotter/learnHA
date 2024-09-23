from typing import cast
from typeguard import typechecked
import numpy as np
from numpy.typing import NDArray
from pydantic.dataclasses import dataclass
import random
from hybridlearner import parser

MATRIX = NDArray[np.float64]

# Like range but in integers inclusive
@dataclass
class Span:
    start : int
    end : int # included

    def stop(self) -> int:
        return self.end + 1

    def range(self) -> range:
        return range(self.start, self.end+1)

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

Invariant = dict[str,Range]  # ∧a_i <= x_i <= b_i

def string_of_invariant(inv : Invariant) -> str:
    return " && ".join([f"{r.min} <= {v} && {v} <= {r.max}" for (v, r) in inv.items()])

def instance_of_invariant(rng : random.Random, inv : Invariant) -> dict[str,float]:
    return { k : range.pick_random_point(rng) for (k, range) in inv.items() }

@typechecked
def invariant_of_string(s : str) -> Invariant:
    return cast(Invariant, parser.check_invariant(parser.invariant.parse_string(s, parse_all=True)))

# XXX For now supports only 1st degree polynomials
Polynomial = dict[str,float] # Σ_i1x_i +c

def string_of_polynomial(p : Polynomial) -> str:
    return " + ".join([( f"{v}" if k == "1" else f"{v} * {k}") for (k,v) in p.items()])

def build_polynomial(vars : list[str], coeffs_and_intercept : list[float] ) -> Polynomial:
    assert len(vars) + 1 == len(coeffs_and_intercept)
    return { (vars[i] if i < len(coeffs_and_intercept) - 1 else "1"): c
             for (i, c) in enumerate(coeffs_and_intercept) }

