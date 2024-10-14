import argparse
from pydantic.dataclasses import dataclass
from typing import Optional

from hybridlearner.utils.argparse_bool import argparse_bool
from hybridlearner.types import Invariant, Range
from hybridlearner.simulation.input import SignalType, parse_signal_types
from hybridlearner.astdsl import parse_expr
from hybridlearner.astdsl.parser import *


@dataclass
class Options:
    time_horizon: float  # total time of simulation
    sampling_time: float  # simulation frame time
    fixed_interval_data: bool
    invariant: Invariant
    number_of_cps: dict[str, int]
    signal_types: dict[str, SignalType]
    seed: Optional[int]


def parse_number_of_cps(s: str) -> dict[str, int]:
    return parse_dict(parse_variable, parse_int)(parse_expr("{" + s + "}"))


parse_range: Parser[Range] = map_parser(
    lambda x: Range(min=x[0], max=x[1]), parse_tuple2(parse_float, parse_float)
)


def parse_invariant(s: str) -> Invariant:
    return parse_dict(parse_variable, parse_range)(parse_expr("{" + s + "}"))


def add_argument_group(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group('Simulation options', 'Simulation options')
    group.add_argument(
        '-Z',
        '--time-horizon',
        help='The global time horizon of computation',
        type=float,
        required=True,
    )
    group.add_argument(
        '-s',
        '--sampling-time',
        help='The sampling time (time-step)',
        type=float,
        required=True,
    )
    # Beware! argparse's type=bool is broken
    group.add_argument(
        '--fixed-interval-data',
        help='Extract simulation data as fixed interval.  False:data extracted based on the solver in the model.  True:data extracted as fixed time-step(recommended for equivalence testing)',
        type=argparse_bool,
        default=True,
        required=False,
    )
    group.add_argument(
        '--invariant', help='Invariant', type=parse_invariant, required=True
    )
    group.add_argument(
        '--number-of-cps',
        help='Number of control points',
        type=parse_number_of_cps,
        required=True,
    )
    group.add_argument(
        '--signal-types',
        help='Variable signal types',
        type=parse_signal_types,
        required=True,
    )
    group.add_argument('-S', '--seed', help='Seed', type=int, required=False)
