# pipenv run python compile_ha.py --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 _out/learned_HA.json
import argparse
from dataclasses import dataclass
from hybridlearner.slx_compiler import OdeSolverType, InvariantMode


@dataclass
class Options:
    ode_solver_type: OdeSolverType
    ode_solver: str
    invariant_mode: InvariantMode


def add_argument_group(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group('Compilation options', 'Compilation options')

    group.add_argument(
        '--ode-solver-type', help='ODE solver type', type=OdeSolverType, required=True
    )
    group.add_argument(
        '--ode-solver', help='ODE solver (variable, fixed)', type=str, required=True
    )
    group.add_argument(
        '--invariant-mode',
        help='Invariant mode: (0: Both, 1: Output, 2: None)',
        type=(lambda x: InvariantMode(int(x))),
        required=True,
    )
