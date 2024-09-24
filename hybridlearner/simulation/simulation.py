from os import path
import matlab
from hybridlearner import matlab
from hybridlearner.simulation.input import Simulation_input
import hybridlearner.utils.io as utils_io


def simulate(
    script_file: str,
    output_file: str,
    input_variables: list[str],
    output_variables: list[str],
    input: Simulation_input,
) -> None:
    assert path.isabs(output_file), (
        "simulate: output_file cannot be relative: " + output_file
    )

    variable_index: dict[str, int] = {
        v: i for (i, v) in enumerate(input_variables + output_variables)
    }

    # XXX We should retrieve data directly from the engine
    matlab.engine.setvar("result_filename", output_file)

    for var, v in input.initial_output_values.items():
        matlab.engine.setvar(f"a{variable_index[var]}", v)

    for var, ts in input.input_value_ts.items():
        vs = matlab.double([v for (_, v) in ts])
        matlab.engine.setvar(f"{var}_input", vs)

        ts = matlab.double([t for (t, _) in ts])
        matlab.engine.setvar(f"{var}_time", ts)

    matlab.engine.run(script_file)


def simulate_list(
    script_file: str,
    output_file: str,
    input_variables: list[str],
    output_variables: list[str],
    inputs: list[Simulation_input],
) -> None:
    with utils_io.open_for_write(output_file) as oc:
        for i, input in enumerate(inputs):
            print("Simulating", i, input)
            # XXX Currently we need a dirty tempfile tech to prevent the Matlab script
            # from overwriting the output_file.
            # XXX We need ".txt" at the end of tmp_output_file since:
            # ファイル拡張子 '.0000' が認識されません。'FileType' パラメーターを使用してファイル タイプを指定してください。
            tmp_output_file = output_file + f".{i:04d}.txt"
            simulate(
                script_file=script_file,
                output_file=tmp_output_file,
                input_variables=input_variables,
                output_variables=output_variables,
                input=input,
            )
            with open(tmp_output_file, 'r') as ic:
                for line in ic:
                    oc.write(line)
