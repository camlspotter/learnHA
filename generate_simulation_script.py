#!/usr/bin/env pipenv-shebang

# Usage examples
#
# pipenv run python ./generate_simulation_script.py --script-file _out/original_model_simulate.m.bypython --simulink-model-file data/models/ex_sldemo_bounce_Input.slx  --time-horizon 10 --sampling-time 0.01 --fixed-interval-data False --input-variables "u" --output-variables "x,v"

import os
import argparse
from typeguard import typechecked
from pydantic.dataclasses import dataclass

import hybridlearner.utils.io as utils_io
from hybridlearner.simulation.script import generate_simulation_script
from hybridlearner.utils.argparse_bool import argparse_bool
from hybridlearner.common import options as common_options


@dataclass
class Options(common_options.Options):
    title: str
    script_file: str
    simulink_model_file: str
    time_horizon: float
    sampling_time: float
    fixed_interval_data: bool


@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="Simulation runner builder")
    common_options.add_argument_group(parser)
    parser.add_argument(
        '--title', help='Title', type=str, default="DefaultTitle", required=False
    )
    parser.add_argument(
        '--script-file', help='Script file destination', type=str, required=True
    )
    parser.add_argument(
        '--simulink-model-file',
        help='SLX model file',
        type=os.path.abspath,
        required=True,
    )
    parser.add_argument(
        '-Z',
        '--time-horizon',
        help='The global time horizon of computation',
        type=float,
        required=True,
    )
    parser.add_argument(
        '-s',
        '--sampling-time',
        help='The sampling time (time-step)',
        type=float,
        required=True,
    )
    # Beware! argparse's type=bool is broken
    parser.add_argument(
        '--fixed-interval-data',
        help='Extract simulation data as fixed interval.  False:data extracted based on the solver in the model.  True:data extracted as fixed time-step(recommended for equivalence testing)',
        type=argparse_bool,
        default=True,
        required=False,
    )

    return Options(**vars(parser.parse_args()))


def run() -> None:
    opt = get_options()
    with utils_io.open_for_write(opt.script_file) as out:
        generate_simulation_script(
            out,
            opt.title,
            opt.simulink_model_file,
            opt.time_horizon,
            opt.sampling_time,
            opt.fixed_interval_data,
            opt.input_variables,
            opt.output_variables,
        )


if __name__ == '__main__':
    run()
