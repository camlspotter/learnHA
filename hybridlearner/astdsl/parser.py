from typing import TypeVar, Callable
from .astdsl import *

A = TypeVar('A')
B = TypeVar('B')

Parser = Callable[[Expr], A]


def map_parser(f: Callable[[A], B], parser_a: Parser[A]) -> Parser[B]:
    def g(e: Expr) -> B:
        return f(parser_a(e))

    return g


def parse_variable(e: Expr) -> str:
    match e:
        case Variable(v):
            return v
        case _:
            assert False, f"Variable expected: {unparse_expr(e)}"


def parse_int(e: Expr) -> int:
    match e:
        case Value(v):
            if isinstance(v, int):
                return int(v)
            else:
                assert False, f"Integer expected: {unparse_expr(e)}"
        case _:
            assert False, f"Integer expected: {unparse_expr(e)}"


def parse_float(e: Expr) -> float:
    match e:
        case Value(v):
            return float(v)
        case _:
            assert False, f"Float expected: {unparse_expr(e)}"


def parse_tuple2(parse_a: Parser[A], parse_b: Parser[B]) -> Parser[tuple[A, B]]:
    def p(e: Expr) -> tuple[A, B]:
        match e:
            case Tuple([a, b]):
                return (parse_a(a), parse_b(b))
            case _:
                assert False, f"Tuple expected: {unparse_expr(e)}"

    return p


def parse_dict(parse_k: Parser[A], parse_v: Parser[B]) -> Parser[dict[A, B]]:
    def p(e: Expr) -> dict[A, B]:
        match e:
            case Dict(kvs):
                return {parse_k(k): parse_v(v) for (k, v) in kvs}
            case _:
                assert False, f"Dict expected: {unparse_expr(e)}"

    return p


def parse_list(parse_x: Parser[A]) -> Parser[list[A]]:
    def p(e: Expr) -> list[A]:
        match e:
            case List(xs):
                return [parse_x(x) for x in xs]
            case _:
                assert False, f"List expected: {unparse_expr(e)}"

    return p
