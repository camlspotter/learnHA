import os
import argparse
from typeguard import typechecked
from pydantic.dataclasses import dataclass
from typing import Optional

from hybridlearner.utils.argparse_bool import argparse_bool
from hybridlearner.types import Invariant
from hybridlearner.simulation.input import (
    generate_simulation_input,
    SignalType,
    parse_signal_types,
)
from hybridlearner.parser import parse_invariant


@dataclass
class Options:
    time_horizon: float
    sampling_time: float
    fixed_interval_data: bool
    invariant: Invariant
    number_of_cps: dict[str, int]
    signal_types: dict[str, SignalType]
    seed: Optional[int]


def parse_number_of_cps(s: str) -> dict[str, int]:
    if s == "":
        return {}
    def parse_ncps(s: str) -> tuple[str, int]:
        match s.split(":"):
            case (var, n):
                return (var, int(n))
            case _:
                assert False, "Invalid number of control points spec: " + s

    return dict([parse_ncps(s) for s in s.split(",")])


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
