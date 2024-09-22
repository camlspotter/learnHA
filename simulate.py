# ex.
#
# pipenv run python simulate.py --simulink-model-file ../../src/test_cases/engine/learn_ha_loop/ex_sldemo_bounce_Input.slx --time-horizon 13.0 --sampling-time 0.001 --fixed-interval-data False --input-variables 'u' --output-variables 'x,v' --invariant '-9.9 <= u && u <= -9.5 && 10.2 <= x && x <= 10.5 && 15 <= v && v <= 15' --number-of-cps 'u:4' --signal-types 'u:linear' -o _out/model_simulation.txt -S 0 -n 64

import os
import random
import argparse
from typeguard import typechecked
from pydantic.dataclasses import dataclass
from typing import Optional

from hybridlearner.simulation import simulate_list
from hybridlearner.simulation.input import generate_simulation_input, parse_signal_types, SignalType
from hybridlearner.simulation.script import generate_simulation_script
from hybridlearner.utils.argparse_bool import argparse_bool
import hybridlearner.utils.io as utils_io
from hybridlearner.types import Invariant, invariant_of_string
from hybridlearner.common import options as common_options
from hybridlearner.simulation import options as simulation_options

@dataclass
class Options(common_options.Options, simulation_options.Options):
    output_file : str

@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="SLX model Simulator")

    common_options.add_argument_group(parser)
    simulation_options.add_argument_group(parser)
    parser.add_argument('--output-file', '-o', help='Output filename', type=os.path.abspath, required=True)

    return Options(**vars(parser.parse_args()))

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
