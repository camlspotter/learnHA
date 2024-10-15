import os
import random
import matlab
from typing import Protocol
from hybridlearner import matlab
from hybridlearner.simulation.input import Simulation_input, generate_simulation_input
from hybridlearner.simulation.script import generate_simulation_script
import hybridlearner.utils.io as utils_io

from typing import Optional
from hybridlearner.types import Invariant
from hybridlearner.simulation.input import SignalType


def simulate1(
    script_file: str,
    output_file: str,
    input_variables: list[str],
    output_variables: list[str],
    input: Simulation_input,
) -> None:
    """
    Simulation of 1 input.

    - script_file: simulation MATLAB script file name, made by hybridlearner.simulation.script
    - output_file: trajectory output destination file name
    - input_variables: list of the input variables
    - output_variables: list of the output variables
    - input: simulation parameters
    """
    assert os.path.isabs(output_file), (
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
    """
    Simulations of multiple inputs.

    - script_file: simulation MATLAB script file name, made by hybridlearner.simulation.script
    - output_file: trajectory output destination file name
    - input_variables: list of the input variables
    - output_variables: list of the output variables
    - inputs: simulation parameters
    """
    with utils_io.open_for_write(output_file) as oc:
        for i, input in enumerate(inputs):
            print("Simulating", i, input)
            # XXX Currently we need a dirty tempfile tech to prevent the Matlab script
            # from overwriting the output_file.
            # XXX We need ".txt" at the end of tmp_output_file since:
            # ファイル拡張子 '.0000' が認識されません。'FileType' パラメーターを使用してファイル タイプを指定してください。
            tmp_output_file = output_file + f".{i:04d}.txt"
            simulate1(
                script_file=script_file,
                output_file=tmp_output_file,
                input_variables=input_variables,
                output_variables=output_variables,
                input=input,
            )
            with open(tmp_output_file, 'r') as ic:
                for line in ic:
                    oc.write(line)


# Protocol for subtyping!
# Unfortunately I cannot inherit dataclasses and have to list all the fields here.
class simulate_options(Protocol):
    time_horizon: float  # total time of simulation
    sampling_time: float  # simulation frame time
    fixed_interval_data: bool
    invariant: Invariant
    number_of_cps: dict[str, int]
    signal_types: dict[str, SignalType]
    seed: Optional[int]
    input_variables: list[str]
    output_variables: list[str]
    output_directory: str


def simulate(
    rng: random.Random,
    opts: simulate_options,
    simulink_model_file: str,
    output_file: str,
    nsimulations: int,
) -> None:
    """
    1 stop simulation function

    - rng: RNG
    - opts: options
    - simulink_model_file: SLX model file name
    - output_file: trajectory destination file name
    - nsimulations: number of simulation runs
    """
    inputs = [
        generate_simulation_input(
            rng,
            time_horizon=opts.time_horizon,
            invariant=opts.invariant,
            number_of_cps=opts.number_of_cps,
            signal_types=opts.signal_types,
            input_variables=opts.input_variables,
            output_variables=opts.output_variables,
        )
        for _ in range(nsimulations)
    ]

    script_file = os.path.join(opts.output_directory, "simulate_model.m")

    with utils_io.open_for_write(script_file) as out:
        generate_simulation_script(
            out=out,
            title='Title',
            simulink_model_file=simulink_model_file,
            time_horizon=opts.time_horizon,
            sampling_time=opts.sampling_time,
            fixed_interval_data=opts.fixed_interval_data,
            input_variables=opts.input_variables,
            output_variables=opts.output_variables,
        )

    simulate_list(
        script_file=script_file,
        output_file=output_file,
        input_variables=opts.input_variables,
        output_variables=opts.output_variables,
        inputs=inputs,
    )
