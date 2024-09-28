from pydantic.dataclasses import dataclass
from functools import reduce
from typing import cast
from frozenlist import FrozenList

from hybridlearner.utils.generator import generate_complete_polynomial
from hybridlearner.utils.math import factorial
from hybridlearner.astdsl import Expr, BinOp, Variable, Value, unparse_expr, parse_expr

VariableAnnotated = list[tuple[dict[str, int], float]]


@dataclass
class Polynomial:
    string: str


@dataclass
class Raw:
    variables: list[str]
    degree: int
    coeffs: list[float]


def raw_to_polynomial(raw: Raw) -> Polynomial:
    va = build_variable_annotated(raw.variables, raw.degree, raw.coeffs)
    return Polynomial(unparse_expr(variable_annotated_to_expr(va)))


def variable_annotated_to_polynomial(va: VariableAnnotated) -> Polynomial:
    return Polynomial(unparse_expr(variable_annotated_to_expr(va)))


def build_polynomial(
    variables: list[str], degree: int, coeffs: list[float]
) -> Polynomial:
    return raw_to_polynomial(Raw(variables, degree, coeffs))


def polynomial_to_variable_annotated(p: Polynomial) -> VariableAnnotated:
    return expr_to_variable_annotated(parse_expr(p.string))


# https://ja.wikipedia.org/wiki/%E9%87%8D%E8%A4%87%E7%B5%84%E5%90%88%E3%81%9B
# "Stars and bars"
def stars_and_bars(nstars: int, nbars: int) -> int:
    return factorial(nstars + nbars) // factorial(nstars) // factorial(nbars)


def ncombs_of_degree(nvars: int, degree: int) -> int:
    # nbars = nvars since
    #  - We have nvars + 1 kinds  (+1 is for the constant)
    #  - nbars = nkinds - 1
    return stars_and_bars(degree, nvars)


def build_variable_annotated(
    variables: list[str], degree: int, coeffs: list[float]
) -> VariableAnnotated:
    tbl = generate_complete_polynomial(len(variables), degree)

    assert len(tbl) == len(coeffs)

    def key(weights: list[int]) -> dict[str, int]:
        return {v: int(w) for (v, w) in zip(variables, weights) if w != 0}

    return [(key(weights), coeff) for (coeff, weights) in zip(coeffs, tbl)]


def unbuild_variable_annotated(
    vars: list[str], degree: int, p: VariableAnnotated
) -> list[float]:
    # Damn, list is not hashable!
    def freeze(xs: list[int]) -> FrozenList[int]:
        fxs = FrozenList(xs)
        fxs.freeze()
        return fxs

    def key_to_weights(key: dict[str, int]) -> FrozenList[int]:
        return freeze([key.get(v, 0) for v in vars])

    weights_to_coeff_tbl = {key_to_weights(k): f for (k, f) in p}
    tbl = generate_complete_polynomial(len(vars), degree)
    return [weights_to_coeff_tbl.get(freeze(weights), 0.0) for weights in tbl]


def key_to_expr(d: dict[str, int]) -> Expr:
    assert d != {}
    vars = [w for (v, n) in d.items() for w in [v] * n]

    def mult(e: Expr, v: str) -> Expr:
        return BinOp(e, '*', Variable(v))

    return reduce(mult, vars[1:], cast(Expr, Variable(vars[0])))


def variable_annotated_to_expr(p: VariableAnnotated) -> Expr:
    def add(e1: Expr, e2: Expr) -> Expr:
        return BinOp(e1, '+', e2)

    def build_comp(key: dict[str, int], coeff: float) -> Expr:
        if key == {}:
            return Value(coeff)
        else:
            return BinOp(key_to_expr(key), '*', Value(coeff))

    comps = [build_comp(key, coeff) for (key, coeff) in p]
    return reduce(add, comps[1:], cast(Expr, comps[0]))


def va_sub(va: VariableAnnotated) -> VariableAnnotated:
    return [(k, -f) for (k, f) in va]


def expr_to_variable_annotated(e: Expr) -> VariableAnnotated:
    match e:
        case BinOp(e1, '+', e2):
            return expr_to_variable_annotated(e1) + expr_to_variable_annotated(e2)
        case BinOp(e1, '-', e2):
            return expr_to_variable_annotated(e1) + va_sub(
                expr_to_variable_annotated(e2)
            )
        case _:
            return [expr_to_comp(e)]


def expr_to_comp(e: Expr) -> tuple[dict[str, int], float]:
    match e:
        case Value(v):
            return ({}, v)
        case Variable(x):
            return ({x: 1}, 1.0)
        case BinOp(Value(v), '*', e):
            (d, f) = expr_to_comp(e)
            return (d, f * v)
        case BinOp(e, '*', Value(v)):
            (d, f) = expr_to_comp(e)
            return (d, f * v)
        case BinOp(Variable(x), '*', e):
            (d, f) = expr_to_comp(e)
            d[x] = d.get(x, 0) + 1  # mutable...
            return (d, f)
        case BinOp(e, '*', Variable(x)):
            (d, f) = expr_to_comp(e)
            d[x] = d.get(x, 0) + 1  # mutable...
            return (d, f)
        case _:
            assert False, f"Invalid polynomial: {unparse_expr(e)}"
