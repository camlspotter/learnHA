import argparse
from pydantic.dataclasses import dataclass
from hybridlearner.astdsl import parse_expr
from hybridlearner.astdsl.parser import *


@dataclass
class Options:
    input_variables: list[str]
    output_variables: list[str]


def parse_variables(s: str) -> list[str]:
    return parse_list(parse_variable)(parse_expr("[" + s + "]"))


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
