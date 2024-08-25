from os import path
from io import TextIOWrapper
import textwrap

from dataclasses import dataclass
import argparse
import infer_ha.utils.io as utils_io
from infer_ha.simulation_script import generate_simulation_script

@dataclass
class Options():
    title : str
    script_file : str
    simulink_model_file : str
    output_file : str
    time_horizon : float
    sampling_time : float
    fixed_interval_data : bool
    input_variables : list[str]
    output_variables : list[str]
    
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="Simulation runner builder")
    parser.add_argument('--title', help='Title', type=str, default= "DefaultTitle", required=False)
    parser.add_argument('--script-file', help='Script file destination', type=str, required=True)
    parser.add_argument('--simulink-model-file', help='SLX model file', type=str, required=True)
    parser.add_argument('--output-file', help='Timeseries output destination', type=str, required=True)
    parser.add_argument('-Z', '--time-horizon', help='The global time horizon of computation', type=float, required=True)
    parser.add_argument('-s', '--sampling-time', help='The sampling time (time-step)', type=float, required=True)
    parser.add_argument('--fixed-interval-data', help='Extract simulation data as fixed interval.  False:data extracted based on the solver in the model.  True:data extracted as fixed time-step(recommended for equivalence testing)', type=bool, default=True, required=False)
    parser.add_argument('--input-variables', help='Input variables', type=str, required=True)
    parser.add_argument('--output-variables', help='Output variables', type=str, required=True)
    args = vars(parser.parse_args())

    args['input_variables'] = [] if args['input_variables'] == "" else args['input_variables'].split(",")
    args['output_variables'] = [] if args['output_variables'] == "" else args['output_variables'].split(",")

    return Options(**args)

def run() -> None:
    opt = get_options()
    with utils_io.open_for_write(opt.script_file) as out:
        generate_simulation_script(out,
                                   opt.title,
                                   opt.simulink_model_file,
                                   opt.output_file,
                                   opt.time_horizon,
                                   opt.sampling_time,
                                   opt.fixed_interval_data,
                                   opt.input_variables,
                                   opt.output_variables)

    
if __name__ == '__main__':
    run()
