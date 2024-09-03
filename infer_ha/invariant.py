from typeguard import typechecked
import pyparsing as pp
from infer_ha.range import Range
import random

Invariant = dict[str,Range]  # ∧a_i <= x_i <= b_i

def string_of_invariant(inv : Invariant) -> str:
    return " && ".join([f"{r.min} <= {v} && {v} <= {r.max}" for (v, r) in inv.items()])

def instance_of_invariant(rng : random.Random, inv : Invariant) -> dict[str,float]:
    return { k : range.pick_random_point(rng) for (k, range) in inv.items() }

variable = pp.Word(pp.alphas, pp.alphanums+"_")

inequality = \
    variable + pp.one_of("<= >=") + pp.common.number \
    ^ pp.common.number + pp.one_of("<= >=") + variable

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
            invariant : Invariant = {}
            variables = { x for ((x, _), _) in ineqs }
            d = dict(ineqs)
            for x in variables:
                try:
                    min = d[(x, ">=")]
                    max = d[(x, "<=")]
                except KeyError:
                    assert False, f"Invalid range specification for {x}: missing one of range limits: {ineqs}"
                try:
                    invariant[x] = Range(min, max)
                except:
                    assert False, f"Invalid range specification for {x}: Range({min}, {max})"
            return invariant
        case _:
            assert False

@typechecked
def invariant_of_string(s : str) -> Invariant:
    return check_invariant(invariant.parse_string(s))
