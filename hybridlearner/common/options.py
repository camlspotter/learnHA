import argparse
from typeguard import typechecked
from pydantic.dataclasses import dataclass
from hybridlearner.astdsl import parse_expr, Variable, Tuple, Expr

@dataclass
class Options:
    input_variables: list[str]
    output_variables: list[str]


def parse_variables(s: str) -> list[str]:
    if s == "":
        return []
    match parse_expr(s):
        case Variable(x):
            return [x]
        case Tuple(es):
            def f(e : Expr) -> str:
                match e:
                    case Variable(x):
                        return x
                    case _:
                        assert False, "Invalid expression for variable list"
            return [f(e) for e in es]
        case _:
            assert False, "Invalid expression for variable list"
        


def add_argument_group(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group(
        'Common options', 'Common options to HybridLearner'
    )
    group.add_argument(
        '--input-variables', help='Input variables', type=parse_variables, required=True
    )
    group.add_argument(
        '--output-variables',
        help='Output variables',
        type=parse_variables,
        required=True,
    )
