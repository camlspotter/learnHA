# ex.
#
# pipenv run python generate_simulation_inputs.py --num-inputs 100 --time-horizon 13.0 --input-variables 'u' --output-variables 'x,v' --invariant '-9.9 <= u && u <= -9.5 && 10.2 <= x && x <= 10.5 && 15 <= v && v <= 15' --number-of-cps 'u:4' --var-types 'u:linear' -o simulation_inputs.json

import os
import random
import json
import sys
import argparse
from typing import Optional
from dataclasses import asdict
from typeguard import typechecked
from pydantic.dataclasses import dataclass

from infer_ha.simulation_input import generate_simulation_input, VarType
import infer_ha.utils.io as utils_io
from infer_ha.invariant import Invariant, invariant_of_string

@dataclass
class Options:
    seed : Optional[int]
    num_inputs : int
    time_horizon : float
    input_variables : list[str]
    output_variables : list[str]
    invariant : Invariant
    number_of_cps : dict[str,int]
    var_types : dict[str,VarType]
    output_file : Optional[str]

def parse_number_of_cps(s : str) -> dict[str,int]:
    def parse_ncps(s : str) -> tuple[str,int]:
        match s.split(":"):
            case (var, n):
                return (var, int(n))
            case _:
                assert False, "Invalid number of control points spec: " + s
    return dict([parse_ncps(s) for s in s.split(",")])

def parse_var_types(s : str) -> dict[str,VarType]:
    def parse_vt(s : str) -> tuple[str,VarType]:
        match s.split(":"):
            case (var, vt):
                return (var, VarType(vt))
            case _:
                assert False, "Invalid number of var type: " + s
    return dict([parse_vt(s) for s in s.split(",")])

@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="SLX model Simulator")

    parser.add_argument('--seed', '-s', help='Random seed', type=int, default=None, required=False)
    parser.add_argument('--num-inputs', '-n', help='Number of inputs to be generated', type=int, required=True)
    parser.add_argument('-Z', '--time-horizon', help='The global time horizon of computation', type=float, required=True)
    parser.add_argument('--input-variables', help='Input variables', type=str, required=True)
    parser.add_argument('--output-variables', help='Output variables', type=str, required=True)
    parser.add_argument('--invariant', help='Invariant', type=str, required=True)
    parser.add_argument('--number-of-cps', help='Number of control points', type=str, required=True)
    parser.add_argument('--var-types', help='Variable types', type=str, required=True)
    parser.add_argument('--output-file', '-o', help='Output filename', type=str, default= None, required=False)

    args = vars(parser.parse_args())

    args['input_variables'] = [] if args['input_variables'] == "" else args['input_variables'].split(",")
    args['output_variables'] = [] if args['output_variables'] == "" else args['output_variables'].split(",")
    args['invariant'] = invariant_of_string(args['invariant'])
    args['number_of_cps'] = parse_number_of_cps(args['number_of_cps'])
    args['var_types'] = parse_var_types(args['var_types'])

    return Options(**args)

opts = get_options()

rng = random.Random() if opts.seed is None else random.Random(opts.seed)

sis = [ generate_simulation_input(rng= rng,
                                  time_horizon= opts.time_horizon,
                                  invariant= opts.invariant,
                                  number_of_cps= opts.number_of_cps,
                                  var_types= opts.var_types,
                                  input_variables= opts.input_variables,
                                  output_variables= opts.output_variables)
        for _ in range(0, opts.num_inputs) ]

with sys.stdout if opts.output_file is None else utils_io.open_for_write(opts.output_file) as out:
    json.dump([asdict(si) for si in sis], out)
