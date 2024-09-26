import argparse
from typeguard import typechecked
from pydantic.dataclasses import dataclass


@dataclass
class Options:
    input_variables: list[str]
    output_variables: list[str]


def parse_variables(s: str) -> list[str]:
    # XXX must have handling of whitespace etc
    if s == "":
        return []
    return s.split(",")


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
