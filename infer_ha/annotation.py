from typing import Optional, Any, Union, cast
import ast
from numbers import Number
from pydantic.dataclasses import dataclass
from typeguard import typechecked
from infer_ha.astdsl import parse_expr, Expr, Variable, Value, App, unparse_expr, Dict

@dataclass
class Continuous:
    pass

@dataclass
class Pool:
    pool : list[float]

@dataclass
class Constant:
    constant : float

VarType = Union[Continuous, Pool, Constant]
VarTypeTbl = dict[int, VarType] # list[tuple[int, str, Optional[VarType]]]

def expr_to_annotation(e : Expr) -> VarType:
    def num(a : Expr) -> float:
        match a:
            case Value(v) if isinstance(v, Number):
                return cast(float, v)
            case _:
                assert False, f"Expected number: {unparse_expr(a)}"
    match e:
        case Variable('continuous'):
            return Continuous()
        case App('pool', args):
            return Pool([ num(a) for a in args ])
        case App('constant', [a]):
            return Constant(num(a))
        case _:
            assert False, f"Invalid annotation: {unparse_expr(e)}"

def parse_annotation(s : str) -> VarType:
    return expr_to_annotation(parse_expr(s))

def expr_to_annotation_list(e : Expr) -> dict[str, VarType]:
    match e:
        case Dict(kvs):
            def var(k : Expr) -> str:
                match k:
                    case Variable(v):
                        return v
                    case _:
                        assert False, f"Variable expected: {unparse_expr(k)}"
            return { var(k):expr_to_annotation(v) for (k,v) in kvs }

        case _:
            assert False, f"Invalid annotation list: {unparse_expr(e)}"

def parse_annotation_list(s : str) -> dict[str, VarType]:
    return expr_to_annotation_list(parse_expr(s))

def annotation_to_expr(a : VarType) -> Expr:
    match a:
        case Continuous():
            return Variable('continuous')
        case Pool(fs):
            return App('pool', [Value(f) for f in fs])
        case Constant(f):
            return App('constant', [Value(f)])
        case _:
            assert False, f"Invalid annotation {a}"

def unparse_annotation(a : VarType) -> str:
    return unparse_expr(annotation_to_expr(a))
