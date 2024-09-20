from typing import cast
import random
from typeguard import typechecked
import pyparsing as pp
from hybridlearner.range import Range
from hybridlearner import parser

Invariant = dict[str,Range]  # ∧a_i <= x_i <= b_i

def string_of_invariant(inv : Invariant) -> str:
    return " && ".join([f"{r.min} <= {v} && {v} <= {r.max}" for (v, r) in inv.items()])

def instance_of_invariant(rng : random.Random, inv : Invariant) -> dict[str,float]:
    return { k : range.pick_random_point(rng) for (k, range) in inv.items() }

@typechecked
def invariant_of_string(s : str) -> Invariant:
    return cast(Invariant, parser.check_invariant(parser.invariant.parse_string(s, parse_all=True)))
