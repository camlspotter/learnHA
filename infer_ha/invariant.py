from typeguard import typechecked
from typing import Any
import pyparsing as pp
from infer_ha.range import Range
import random

Invariant = dict[str,Range]  # ∧a_i <= x_i <= b_i

def string_of_invariant(inv : Invariant) -> str:
    return " && ".join([f"{r.min} <= {v} && {v} <= {r.max}" for (v, r) in inv.items()])

def instance_of_invariant(rng : random.Random, inv : Invariant) -> dict[str,float]:
    return { k : range.pick_random_point(rng) for (k, range) in inv.items() }

variable = pp.Word(pp.alphas, pp.alphanums+"_")

def test_variable():
    for test in [
            "x",
            "xyz",
            "xy123",
            "xy_z_12_"
    ]:
        print(variable.parse_string(test))
    
inequality = \
    variable + pp.one_of("<= >=") + pp.common.number \
    ^ pp.common.number + pp.one_of("<= >=") + variable

def test_inequality():
    for test in [
            "x <= 1",
            "x >= 1.23",
            ".12 >= y12",
            "0. <= y"
    ]:
        print(inequality.parse_string(test))

# invariant = pp.delimitedList(inequality, delim = "&&")

def check_inequality(tkns):
    match tkns:
        case [[a, b, c]]:
            if isinstance(a, (int, float)) and isinstance(c, str):
                match b:
                    case ">=":
                       b = "<="
                    case "<=":
                       b = ">="
                    case _:
                       assert False
                return [[((c, b), a)]]
            if isinstance(c, (int, float)) and isinstance(a, str):
                return [[((a, b), c)]]
            assert False, "Invalid inequality: " + tkns
        case _:
            assert False

def check_and(tkns):
    print("&&", tkns)
    match tkns:
        case [[a, "&&", c]]:
            return [a + c]
        case _:
            assert False
        
invariant = pp.infix_notation(
    pp.common.number ^ variable,
    [ (pp.one_of("<= >="), 2, pp.opAssoc.RIGHT, check_inequality),
      (pp.one_of("&&"), 2, pp.opAssoc.RIGHT, check_and)
     ])

def check_invariant(inv):
    match inv:
        case [ineqs]:
            variables = { x for ((x, _), _) in ineqs }
            d = dict(ineqs)
            for x in variables:
                try:
                    min = d[(x, ">=")]
                    max = d[(x, "<=")]
                except KeyError:
                    assert False, f"Invalid range specification for {x}: missing one of range limits: {ineqs}"
                try:
                    d[x] = Range(min, max)
                except e:
                    assert False, f"Invalid range specification for {x}: {ineqs}"
            return d
        case _:
            assert False

@typechecked
def invariant_of_string(s : str) -> Invariant:
    check_invariant(invariant.parse_string(s))

def test_invariant():
    for test in [
            "1 <= x && x <= 1.23 && 0. <= y12 && y12 <= 2.3"
    ]:
        print(invariant.parse_string(test))
        print(check_invariant(invariant.parse_string(test)))

def tests():
    test_variable()
    test_inequality()
    test_invariant()
