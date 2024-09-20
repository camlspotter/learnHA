from typing import Optional, Union, cast
import ast
from numbers import Number
from pydantic.dataclasses import dataclass
from typeguard import typechecked
from hybridlearner.astdsl import parse_expr, Expr, Variable, Value, App, unparse_expr, Dict

@dataclass
class Continuous:
    pass

@dataclass
class Pool:
    pool : list[float]

@dataclass
class Constant:
    constant : float

Annotation = Union[Continuous, Pool, Constant]
AnnotationTbl = dict[int, Annotation] # list[tuple[int, str, Optional[Annotation]]]

def expr_to_annotation(e : Expr) -> Annotation:
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

def parse_annotation(s : str) -> Annotation:
    return expr_to_annotation(parse_expr(s))

def expr_to_annotation_list(e : Expr) -> dict[str, Annotation]:
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

def parse_annotation_list(s : str) -> dict[str, Annotation]:
    if s == "":
        return {}
    else:
        return expr_to_annotation_list(parse_expr(s))

def parse_annotation_tbl(input_variables : list[str], output_variables : list[str], s : str) -> AnnotationTbl:
    tbl = { v : i for (i, v) in enumerate(input_variables + output_variables) }
    annotation_list = parse_annotation_list(s)
    try:
        return { tbl[v] : a for (v, a) in annotation_list.items() }
    except KeyError as e:
        print(f"Annotation {annotation_list} contains unknown variable {e}")
        raise
    
def annotation_to_expr(a : Annotation) -> Expr:
    match a:
        case Continuous():
            return Variable('continuous')
        case Pool(fs):
            return App('pool', [Value(f) for f in fs])
        case Constant(f):
            return App('constant', [Value(f)])
        case _:
            assert False, f"Invalid annotation {a}"

def unparse_annotation(a : Annotation) -> str:
    return unparse_expr(annotation_to_expr(a))
