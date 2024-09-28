# Example: having _out/learned_HA.json,
# pipenv run python compile_ha.py --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 _out/learned_HA.json
from os import path
import json
import argparse
from dataclasses import dataclass
from typeguard import typechecked
import hybridlearner.utils.io as utils_io
from hybridlearner.slx_compiler import compile
from hybridlearner.slx_compiler import options as compiler_options
from hybridlearner.automaton import HybridAutomaton
from hybridlearner import matlab


@dataclass
class Options(compiler_options.Options):
    ha_json_file: str  # aaa/bbb/learned_ha.json
    output_matlab_script: str  # aaa/bbb/learned_ha_compile.m
    simulink_model_name: str  # aaa/bbb/learned_ha


@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="Hybrid Automaton to SLX compiler")
    compiler_options.add_argument_group(parser)
    parser.add_argument(
        'ha_json_file',
        metavar='ha.json',
        type=str,
        help='Hybrid Automaton definition JSON path',
    )
    parser.add_argument(
        '--output-file',
        "-o",
        metavar='ha.slx',
        help='Output SLX model path',
        type=str,
        default='',
        required=False,
    )

    args = vars(parser.parse_args())

    assert (
        path.splitext(args['ha_json_file'])[1] == ".json"
    ), f"Hybrid Automaton definition path must have extension .json: {args['ha_json_file']}"
    args['output_file'] = (
        path.splitext(args['ha_json_file'])[0] + ".slx"
        if args['output_file'] == ""
        else args['output_file']
    )
    output_file_body_ext = path.splitext(args['output_file'])
    assert (
        output_file_body_ext[1] == ".slx"
    ), "Output SLX model path must have extension .slx"
    args['output_matlab_script'] = output_file_body_ext[0] + "_compile.m"
    args['simulink_model_name'] = path.basename(output_file_body_ext[0])
    del args['output_file']

    return Options(**args)


def run() -> None:
    opt = get_options()

    with open(opt.ha_json_file, 'r', encoding='utf-8') as file:
        ha = HybridAutomaton(**json.load(file))

    with utils_io.open_for_write(opt.output_matlab_script) as out:
        compile(
            out,
            ha,
            opt.ode_solver_type,
            opt.ode_solver,
            opt.simulink_model_name,
            opt.invariant_mode,
        )

    matlab.engine.run(opt.output_matlab_script)


if __name__ == '__main__':
    run()
