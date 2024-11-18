import os
import random
import matlab
from typing import Protocol
import numpy as np
from pydantic.dataclasses import dataclass
from hybridlearner import matlab
from hybridlearner.simulation.input import Simulation_input, generate_simulation_input
from hybridlearner.simulation.script import generate_simulation_script
import hybridlearner.utils.io as utils_io
from hybridlearner.types import Invariant, MATRIX
from hybridlearner.simulation.input import SignalType
from hybridlearner.trajectory import (
    Trajectory,
    write_trajectory,
    load_trajectories,
    Trajectories,
    make_nan_trajectory,
)


def simulate1(
    script_file: str,
    input_variables: list[str],
    output_variables: list[str],
    sampling_time: float,
    input: Simulation_input,
) -> Trajectory:
    """
    Simulation of 1 input.

    - script_file: simulation MATLAB script file name, made by hybridlearner.simulation.script
    - output_file: trajectory output destination file name
    - input_variables: list of the input variables
    - output_variables: list of the output variables
    - input: simulation parameters

    Simulation may fail if Simulink engine raises a DerivNotFinite exception.
    In that case simulate1 returns a nan-trajectory. (See trajectory.make_nan_trajectory for details)
    """
    variable_index: dict[str, int] = {
        v: i for (i, v) in enumerate(input_variables + output_variables)
    }

    matlab.engine.eval0('clear;')
    matlab.engine.eval0('bdclose all;')

    for var, v in input.initial_output_values.items():
        print(f'initial {var} : a{variable_index[var]} = {v}')
        matlab.engine.setvar(f"a{variable_index[var]}", v)

    for var, ts in input.input_value_ts.items():
        vs = matlab.double([v for (_, v) in ts])
        matlab.engine.setvar(f"{var}_input", vs)

        ts = matlab.double([t for (t, _) in ts])
        matlab.engine.setvar(f"{var}_time", ts)

    matlab.engine.run(script_file)

    simulation_error: list[str] = matlab.engine.getvar("simulation_error")

    match simulation_error:
        case []:  # no error
            pass
        case ['Simulink:Engine:DerivNotFinite', message]:
            print(f'Simulation failed because of infinite derivative: {message}')
            return make_nan_trajectory(sampling_time)
        case _:
            assert True, f"Simulation failure: {simulation_error}"

    result_matrix: MATRIX = np.array(matlab.engine.getvar("result_matrix"))
    times = result_matrix[:, 0]
    values = result_matrix[:, 1:]

    # Check the first values of the output variables are really
    # those specified in the input.
    # If different, the model does not follow the assumption of HybridLearner
    for i, var in enumerate(output_variables):
        i = i + len(input_variables)
        assert (
            values[0, i] == input.initial_output_values[var]
        ), f"The first output value of {var} {values[0,i]} is different from the specified {input.initial_output_values[var]}"

    return (times, values)


def simulate_list_aux(
    script_file: str,
    output_file: str,
    input_variables: list[str],
    output_variables: list[str],
    sampling_time: float,
    inputs: list[Simulation_input],
) -> Trajectories:
    """
    Simulations of multiple inputs.

    - script_file: simulation MATLAB script file name, made by hybridlearner.simulation.script
    - output_file: trajectory output destination file name
    - input_variables: list of the input variables
    - output_variables: list of the output variables
    - inputs: simulation parameters
    """
    with utils_io.open_for_write(output_file) as oc:
        oc.write('\t'.join(['time'] + input_variables + output_variables) + '\n')
        for i, input in enumerate(inputs):
            print("Simulating", i)
            # XXX Currently we need a dirty tempfile tech to prevent the Matlab script
            # from overwriting the output_file.
            # XXX We need ".txt" at the end of tmp_output_file since:
            # ファイル拡張子 '.0000' が認識されません。'FileType' パラメーターを使用してファイル タイプを指定してください。
            tr = simulate1(
                script_file=script_file,
                input_variables=input_variables,
                output_variables=output_variables,
                sampling_time=sampling_time,
                input=input,
            )
            write_trajectory(oc, tr)

    (_, trajs) = load_trajectories(output_file)
    return trajs


@dataclass
class simulate_options:
    time_horizon: float
    sampling_time: float
    fixed_interval_data: bool
    invariant: Invariant
    number_of_cps: dict[str, int]
    signal_types: dict[str, SignalType]
    input_variables: list[str]
    output_variables: list[str]
    output_directory: str


# Protocol for subtyping!
# Unfortunately I cannot inherit dataclasses and have to list all the fields here.
class simulate_protocol(Protocol):
    time_horizon: float
    sampling_time: float
    fixed_interval_data: bool
    invariant: Invariant
    number_of_cps: dict[str, int]
    signal_types: dict[str, SignalType]
    input_variables: list[str]
    output_variables: list[str]
    output_directory: str


class variables_protocol(Protocol):
    invariant: Invariant
    number_of_cps: dict[str, int]
    signal_types: dict[str, SignalType]
    input_variables: list[str]
    output_variables: list[str]


def check_variables(opts: variables_protocol) -> None:
    for k in opts.input_variables + opts.output_variables:
        assert (
            k in opts.invariant.keys()
        ), f"Error: variable {k} must be declared in invariants"
    for k in opts.invariant.keys():
        assert (
            k in opts.input_variables + opts.output_variables
        ), f"Error: {k} in invariant is neither an input nor output variables"
    for k in opts.number_of_cps.keys():
        assert (
            k in opts.input_variables
        ), f"Error: {k} in number_of_cps is not an input variable"
    for k in opts.input_variables:
        assert (
            k in opts.number_of_cps
        ), f"Error: input variable {k} must be declared in number_of_cps"
    for k in opts.signal_types.keys():
        assert (
            k in opts.input_variables
        ), f"Error: {k} in signal_types is not an input variable"
    for k in opts.input_variables:
        assert (
            k in opts.signal_types
        ), f"Error: input variable {k} must be declared in signal_types"


def simulate_list(
    opts: simulate_protocol,
    simulink_model_file: str,
    output_file: str,
    inputs: list[Simulation_input],
) -> Trajectories:
    check_variables(opts)
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

    return simulate_list_aux(
        script_file=script_file,
        output_file=output_file,
        input_variables=opts.input_variables,
        output_variables=opts.output_variables,
        sampling_time=opts.sampling_time,
        inputs=inputs,
    )


def simulate(
    rng: random.Random,
    opts: simulate_protocol,
    simulink_model_file: str,
    output_file: str,
    nsimulations: int,
) -> Trajectories:
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

    return simulate_list(opts, simulink_model_file, output_file, inputs)
