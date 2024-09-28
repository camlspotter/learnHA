from typing import Optional, Union, cast
import ast
from numbers import Number
from pydantic.dataclasses import dataclass
from typeguard import typechecked
from hybridlearner.astdsl import parse_expr, unparse_expr, Expr
from hybridlearner.astdsl.parser import *


@dataclass
class Continuous:
    pass


@dataclass
class Pool:
    pool: list[float]


@dataclass
class Constant:
    constant: float


Annotation = Union[Continuous, Pool, Constant]
AnnotationDict = dict[str, Annotation]
AnnotationTbl = dict[
    int, Annotation
]  # AnnotationDict replaced its variable names by variable indices


def parse_annotation(e: Expr) -> Annotation:
    match e:
        case Variable('continuous'):
            return Continuous()
        case App('pool', args):
            return Pool([parse_float(a) for a in args])
        case App('constant', [a]):
            return Constant(parse_float(a))
        case _:
            assert False, f"Invalid annotation: {unparse_expr(e)}"


def parse_annotation_dict(s: str) -> AnnotationDict:
    return parse_dict(parse_variable, parse_annotation)(parse_expr("{" + s + "}"))


def convert_annotation_dict(
    input_variables: list[str], output_variables: list[str], ad: AnnotationDict
) -> AnnotationTbl:
    tbl = {v: i for (i, v) in enumerate(input_variables + output_variables)}
    try:
        return {tbl[v]: a for (v, a) in ad.items()}
    except KeyError as e:
        print(f"Annotation {ad} contains unknown variable {e}")
        raise


def annotation_to_expr(a: Annotation) -> Expr:
    match a:
        case Continuous():
            return Variable('continuous')
        case Pool(fs):
            return App('pool', [Value(f) for f in fs])
        case Constant(f):
            return App('constant', [Value(f)])
        case _:
            assert False, f"Invalid annotation {a}"


def unparse_annotation(a: Annotation) -> str:
    return unparse_expr(annotation_to_expr(a))
