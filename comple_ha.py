# pipenv run python comple_ha.py --output-matlab-script x.m --ode-solver-type fixed --simulink-model-name learned_model0 --invariant-mode 2  --ode-solver ode ../../build/_result/bball/BeforeAnnotation/learned_HA.json
from os import path
from io import TextIOWrapper
import textwrap
import json

from dataclasses import dataclass
import argparse
import infer_ha.utils.io as utils_io
from infer_ha.simulation_script import generate_simulation_script
from infer_ha.slx_compiler import OdeSolverType, InvariantMode, compile
from infer_ha.HA import HybridAutomaton

@dataclass
class Options:
    ha_json_file : str
    output_matlab_script : str
    ode_solver_type : OdeSolverType
    ode_solver : str
    simulink_model_name : str
    invariant_mode : InvariantMode

def xxx(s : str):
    return OdeSolverType(s)
    
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="Hybrid Automaton to SLX compiler")
    parser.add_argument('ha_json_file', metavar='ha-json-file', type=str, help='Hybrid Automaton definition JSON file')
    parser.add_argument('--output-matlab-script', '-o', help='MATLAB script to build SLX model', type=str)
    parser.add_argument('--ode-solver-type', help='ODE solver type',
                        type=str, choices= [t.value for t in OdeSolverType], required=True)
    parser.add_argument('--ode-solver', help='ODE solver', type=str, required=True)
    parser.add_argument('--simulink-model-name', help='Simulink model name', type=str, required=True)
    parser.add_argument('--invariant-mode', help='Invariant mode',
                        type=int, choices= [m.value for m in InvariantMode], required=True)
    args = vars(parser.parse_args())

    args['ode_solver_type'] = OdeSolverType(args['ode_solver_type'])
    args['invariant_mode'] = InvariantMode(args['invariant_mode'])

    return Options(**args)

def run() -> None:
    opt = get_options()

    with open(opt.ha_json_file, 'r', encoding='utf-8') as file:
        ha = HybridAutomaton(**json.load(file))

    with utils_io.open_for_write(opt.output_matlab_script) as out:
        compile(out,
                ha,
                opt.ode_solver_type,
                opt.ode_solver,
                opt.simulink_model_name,
                opt.invariant_mode)
    
if __name__ == '__main__':
    run()
