# pipenv run python comple_ha.py --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 learned_HA.json
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
from infer_ha.matlab_engine import matlab_engine

@dataclass
class Options:
    ode_solver_type : OdeSolverType
    ode_solver : str
    invariant_mode : InvariantMode
    ha_json_file : str             # aaa/bbb/learned_ha.json
    output_matlab_script : str     # aaa/bbb/learned_ha_compile.m
    simulink_model_name : str      # aaa/bbb/learned_ha

def get_options() -> Options:
    parser = argparse.ArgumentParser(description="Hybrid Automaton to SLX compiler")
    parser.add_argument('ha_json_file', metavar='ha.json', type=str, help='Hybrid Automaton definition JSON path')
    parser.add_argument('--ode-solver-type', help='ODE solver type',
                        type=str, choices= [t.value for t in OdeSolverType], required=True)
    parser.add_argument('--ode-solver', help='ODE solver', type=str, required=True)
    parser.add_argument('--output-file', "-o", metavar='ha.slx', help='Output SLX model path', type=str, default= '', required=False)
    parser.add_argument('--invariant-mode', help='Invariant mode',
                        type=int, choices= [m.value for m in InvariantMode], required=True)
    args = vars(parser.parse_args())

    args['ode_solver_type'] = OdeSolverType(args['ode_solver_type'])
    args['invariant_mode'] = InvariantMode(args['invariant_mode'])

    assert path.splitext(args['ha_json_file'])[1] == ".json", "Hybrid Automaton definition path must have extension .json"
    args['output_file'] = path.splitext(args['ha_json_file'])[0] + ".slx" if args['output_file'] == "" else args['output_file']
    output_file_body_ext = path.splitext(args['output_file'])
    assert output_file_body_ext[1] == ".slx", "Output SLX model path must have extension .slx"
    args['output_matlab_script'] = output_file_body_ext[0] + "_compile.m"
    args['simulink_model_name'] = path.basename(output_file_body_ext[0])

    print("source:", args['ha_json_file'])
    print("output:", args['output_file'])
    print("compile_script:", args['output_matlab_script'])
    print("simulink_model_name:", args['simulink_model_name'])
    
    del args['output_file']

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

    matlab_engine.run(opt.output_matlab_script)

if __name__ == '__main__':
    run()
