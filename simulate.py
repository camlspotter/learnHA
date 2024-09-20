# ex.
#
# pipenv run python simulate.py --simulink-model-file ../../src/test_cases/engine/learn_ha_loop/ex_sldemo_bounce_Input.slx --time-horizon 13.0 --sampling-time 0.001 --fixed-interval-data False --input-variables 'u' --output-variables 'x,v' --invariant '-9.9 <= u && u <= -9.5 && 10.2 <= x && x <= 10.5 && 15 <= v && v <= 15' --number-of-cps 'u:4' --signal-types 'u:linear' -o model_simulation.txt -S 0 -n 64

import os
import random
import argparse
from typeguard import typechecked
from pydantic.dataclasses import dataclass
from typing import Optional

from infer_ha.simulation.simulate import simulate_list
from infer_ha.simulation.simulation_input import generate_simulation_input, SignalType
from infer_ha.simulation.simulation_script import generate_simulation_script
from infer_ha.utils.argparse_bool import argparse_bool
import infer_ha.utils.io as utils_io
from infer_ha.invariant import Invariant, invariant_of_string

@dataclass
class Options:
    simulink_model_file : str
    time_horizon : float
    sampling_time : float
    fixed_interval_data : bool
    input_variables : list[str]
    output_variables : list[str]
    invariant : Invariant
    number_of_cps : dict[str,int]
    signal_types : dict[str,SignalType]
    output_file : str
    seed : Optional[int]
    nsimulations : int

def parse_number_of_cps(s : str) -> dict[str,int]:
    def parse_ncps(s : str) -> tuple[str,int]:
        match s.split(":"):
            case (var, n):
                return (var, int(n))
            case _:
                assert False, "Invalid number of control points spec: " + s
    return dict([parse_ncps(s) for s in s.split(",")])

def parse_signal_types(s : str) -> dict[str,SignalType]:
    def parse_vt(s : str) -> tuple[str,SignalType]:
        match s.split(":"):
            case (var, vt):
                return (var, SignalType(vt))
            case _:
                assert False, "Invalid number of var type: " + s
    return dict([parse_vt(s) for s in s.split(",")])

@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="SLX model Simulator")
    parser.add_argument('--simulink-model-file', help='SLX model file', type=str, required=True)
    parser.add_argument('-Z', '--time-horizon', help='The global time horizon of computation', type=float, required=True)
    parser.add_argument('-s', '--sampling-time', help='The sampling time (time-step)', type=float, required=True)
    # Beware! argparse's type=bool is broken
    parser.add_argument('--fixed-interval-data', help='Extract simulation data as fixed interval.  False:data extracted based on the solver in the model.  True:data extracted as fixed time-step(recommended for equivalence testing)', type=argparse_bool, default=True, required=False)
    parser.add_argument('--input-variables', help='Input variables', type=str, required=True)
    parser.add_argument('--output-variables', help='Output variables', type=str, required=True)
    parser.add_argument('--invariant', help='Invariant', type=str, required=True)
    parser.add_argument('--number-of-cps', help='Number of control points', type=str, required=True)
    parser.add_argument('--signal-types', help='Variable signal types', type=str, required=True)
    parser.add_argument('--output-file', '-o', help='Output filename', type=str, required=True)
    parser.add_argument('-S', '--seed', help='Seed', type=int, required=False)
    parser.add_argument('-n', '--nsimulations', help='Number of simulations', type=int, default=1, required=False)

    parsed = parser.parse_args()
    args = vars(parsed)

    args['input_variables'] = [] if args['input_variables'] == "" else args['input_variables'].split(",")
    args['output_variables'] = [] if args['output_variables'] == "" else args['output_variables'].split(",")
    args['invariant'] = invariant_of_string(args['invariant'])
    args['number_of_cps'] = parse_number_of_cps(args['number_of_cps'])
    args['signal_types'] = parse_signal_types(args['signal_types'])

    args['simulink_model_file'] = os.path.abspath(args['simulink_model_file'])
    args['output_file'] = os.path.abspath(args['output_file'])

    return Options(**args)

opts = get_options()

script_file= os.path.join(os.path.dirname(opts.output_file), "simulate_model.m")

with utils_io.open_for_write(script_file) as out:
    generate_simulation_script(out= out,
                               title= 'Title',
                               simulink_model_file= opts.simulink_model_file,
                               time_horizon= opts.time_horizon,
                               sampling_time= opts.sampling_time,
                               fixed_interval_data= opts.fixed_interval_data,
                               input_variables= opts.input_variables,
                               output_variables = opts.output_variables)

print("Random seed", opts.seed)

rng= random.Random() if opts.seed is None else random.Random(opts.seed)

inputs = [ generate_simulation_input(rng,
                                     time_horizon= opts.time_horizon,
                                     invariant= opts.invariant,
                                     number_of_cps= opts.number_of_cps,
                                     signal_types= opts.signal_types,
                                     input_variables= opts.input_variables,
                                     output_variables= opts.output_variables)
           for _ in range(opts.nsimulations) ]

simulate_list(script_file= script_file,
              output_file= opts.output_file,
              input_variables= opts.input_variables,
              output_variables= opts.output_variables,
              inputs= inputs)
