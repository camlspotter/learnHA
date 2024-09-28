"""
Simple DSL using Python AST

Very small subset of Python expressions is supported.
Equivalent type definition in OCaml:

type expr = 
  | App of string * expr list (* f(e1, e2, ..) *)
  | BinOp of expr * string * expr (* e1 op e2 *)
  | Value of value (* int or float *)
  | List of expr list (* [e1, e2, .. ] *)
  | Tuple of expr list (* (e1, e2, .. ) *)
  | Dict of (expr * expr) list (* { k1: v1, k2: v2, .. } *)
  | Set of expr list (* { e1, e2, .. } *)
  | Variable of string (* x, y, etc *)
"""

import ast
from typing import Union, cast
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass
class App:
    func: str
    args: list['Expr']


@dataclass
class BinOp:
    left: 'Expr'
    op: str
    right: 'Expr'


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class Value:
    value: Union[int, float]


@dataclass
class List:
    list: list['Expr']


@dataclass
class Tuple:
    tuple: list['Expr']


@dataclass
class Dict:
    dict: list[tuple['Expr', 'Expr']]


@dataclass
class Set:
    set: list['Expr']


@dataclass
class Variable:
    id: str


Expr = Union[App, BinOp, Value, List, Variable, Tuple, Dict, Set]

binops_name_symbol: dict[str, str] = {'Mult': '*', 'Add': '+', 'Sub': '-'}

binops_symbol_value: dict[str, ast.operator] = {
    '*': ast.Mult(),
    '+': ast.Add(),
    '-': ast.Sub(),
}


def expr(e: ast.expr) -> Expr:
    if isinstance(e, ast.Call):
        if isinstance(e.func, ast.Name):
            f = e.func.id
        else:
            assert False, f"Call but func is not Name?! f{ast.dump(e)}"
        args = [expr(e2) for e2 in e.args]
        return App(f, args)
    elif isinstance(e, ast.BinOp):
        return BinOp(
            expr(e.left), binops_name_symbol[type(e.op).__name__], expr(e.right)
        )
    elif isinstance(e, ast.UnaryOp):
        match type(e.op).__name__:
            case "USub":
                match expr(e.operand):
                    case Value(v):
                        return Value(-v)
                    case _:
                        assert False, f"Unsupported unary op argument {e}"
            case n:
                assert False, f"Unsupported unary op {n}"
    elif isinstance(e, ast.Constant):
        return Value(e.value)
    elif isinstance(e, ast.List):
        return List([expr(e2) for e2 in e.elts])
    elif isinstance(e, ast.Tuple):
        return Tuple([expr(e2) for e2 in e.elts])
    elif isinstance(e, ast.Dict):
        return Dict(
            list(
                zip(
                    [expr(cast(ast.expr, e2)) for e2 in e.keys],  # cast was required
                    [expr(e2) for e2 in e.values],
                )
            )
        )
    elif isinstance(e, ast.Set):
        return Set([expr(e2) for e2 in e.elts])
    elif isinstance(e, ast.Name):
        return Variable(e.id)
    else:
        assert False, f"Unsupported expression: {ast.unparse(e)}, {e}"


def parse_expr(s: str) -> Expr:
    try:
        return expr(ast.parse(s, mode='eval').body)
    except SyntaxError:
        assert False, f"Invalid Python expression: {s}"


def unparse_expr(e: Expr) -> str:
    def unparse(e: Expr) -> ast.expr:
        match e:
            case App(f, args):
                return ast.Call(ast.Name(f), [unparse(a) for a in args], keywords=[])
            case BinOp(left, op, right):
                return ast.BinOp(unparse(left), binops_symbol_value[op], unparse(right))
            case Value(a):
                return ast.Constant(a)
            case List(es):
                return ast.List([unparse(e) for e in es])
            case Tuple(es):
                return ast.Tuple([unparse(e) for e in es])
            case Dict(kvs):
                return ast.Dict(
                    [unparse(k) for (k, _) in kvs], [unparse(v) for (_, v) in kvs]
                )
            case Set(es):
                return ast.Set([unparse(e) for e in es])
            case Variable(s):
                return ast.Name(s)
            case _:
                assert False, f"Invalid Expr {e}"

    return ast.unparse(ast.Expression(unparse(e)))

def get_variable(e : Expr) -> str:
    match e:
        case Variable(x):
            return x
        case _:
            assert False, "Variable expected"

def get_int(e : Expr) -> int:
    match e:
        case Value(x):
            if isinstance(x, int):
                return x
            assert False, "Integer expected"
        case _:
            assert False, "Integer expected"
