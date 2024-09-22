# ex.
#
# pipenv run python generate_simulation_inputs.py --num-inputs 100 --time-horizon 13.0 --input-variables 'u' --output-variables 'x,v' --invariant '-9.9 <= u && u <= -9.5 && 10.2 <= x && x <= 10.5 && 15 <= v && v <= 15' --number-of-cps 'u:4' --signal-types 'u:linear' -o _out/simulation_inputs.json

import random
import json
import sys
import argparse
from typing import Optional
from dataclasses import asdict
from typeguard import typechecked
from pydantic.dataclasses import dataclass

from hybridlearner.simulation.input import generate_simulation_input, SignalType, parse_signal_types
import hybridlearner.utils.io as utils_io
from hybridlearner.invariant import Invariant, invariant_of_string
from hybridlearner.common import options as common_options
from hybridlearner.simulation import options as simulation_options

@dataclass
class Options(common_options.Options):
    seed : Optional[int]
    num_inputs : int
    time_horizon : float
    invariant : Invariant
    number_of_cps : dict[str,int]
    signal_types : dict[str,SignalType]
    output_file : Optional[str]

@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="SLX model Simulator")
    common_options.add_argument_group(parser)
    parser.add_argument('--seed', '-s', help='Random seed', type=int, default=None, required=False)
    parser.add_argument('--num-inputs', '-n', help='Number of inputs to be generated', type=int, required=True)
    parser.add_argument('-Z', '--time-horizon', help='The global time horizon of computation', type=float, required=True)
    parser.add_argument('--invariant', help='Invariant', type=invariant_of_string, required=True)
    parser.add_argument('--number-of-cps', help='Number of control points', type=simulation_options.parse_number_of_cps, required=True)
    parser.add_argument('--signal-types', help='Variable types', type=parse_signal_types, required=True)
    parser.add_argument('--output-file', '-o', help='Output filename', type=str, default= None, required=False)

    return Options(**vars(parser.parse_args()))

opts = get_options()

rng = random.Random() if opts.seed is None else random.Random(opts.seed)

sis = [ generate_simulation_input(rng= rng,
                                  time_horizon= opts.time_horizon,
                                  invariant= opts.invariant,
                                  number_of_cps= opts.number_of_cps,
                                  signal_types= opts.signal_types,
                                  input_variables= opts.input_variables,
                                  output_variables= opts.output_variables)
        for _ in range(0, opts.num_inputs) ]

with sys.stdout if opts.output_file is None else utils_io.open_for_write(opts.output_file) as out:
    json.dump([asdict(si) for si in sis], out)
