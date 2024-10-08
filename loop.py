#!/usr/bin/env pipenv-shebang

import os
import random
import argparse
from typeguard import typechecked
from pydantic.dataclasses import dataclass

import hybridlearner.utils.io as utils_io
# from hybridlearner.types import Invariant

from hybridlearner.common import options as common_options
from hybridlearner.simulation import options as simulation_options
from hybridlearner.inference import options as inference_options
from hybridlearner.slx_compiler import options as compiler_options

from hybridlearner.simulation import simulate_list
from hybridlearner.simulation.input import generate_simulation_input
from hybridlearner.simulation.script import generate_simulation_script

from hybridlearner.trajectory import load_trajectories_files, Trajectories
from hybridlearner.inference import infer_model
from hybridlearner import automaton
from hybridlearner.automaton import HybridAutomaton
import json
from dataclasses import asdict

from hybridlearner import slx_compiler
from hybridlearner import matlab

from hybridlearner.trajectory.distance import trajectory_dtw_distance


@dataclass
class Options(
    common_options.Options,
    simulation_options.Options,
    inference_options.Options,
    compiler_options.Options,
):
    simulink_model_file: str
    counter_example_threshold: float
    nsimulations: int
    max_nloops: int


@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="Hybrid Automaton inference loop")
    parser.add_argument(
        '--simulink-model-file',
        help='SLX model file',
        type=os.path.abspath,
        required=True,
    )
    parser.add_argument(
        '--counter-example-threshold',
        help='Distance threshold for counter examples',
        type=float,
        required=True,
    )
    parser.add_argument(
        '-n',
        '--nsimulations',
        help='Number of simulations per inference iteration',
        type=int,
        default=1,
        required=False,
    )
    parser.add_argument(
        '--max-nloops',
        help='Max number of inference loops',
        type=int,
        default=10,
        required=False,
    )
    common_options.add_argument_group(parser)
    simulation_options.add_argument_group(parser)
    inference_options.add_argument_group(parser)
    compiler_options.add_argument_group(parser)

    return Options(**vars(parser.parse_args()))


opts = get_options()


def simulate(
    rng: random.Random,
    opts: Options,
    simulink_model_file: str,
    output_file: str,
    nsimulations: int,
) -> None:
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


def inference(
    opts: Options, trajectories_files: list[str], outputfilename: str
) -> None:
    list_of_trajectories = load_trajectories_files(trajectories_files)

    print(f"Loaded {len(list_of_trajectories.trajectories)} trajectories")

    raw = infer_model(
        list_of_trajectories, opts.input_variables, opts.output_variables, opts
    )
    ha = automaton.build(raw)
    # outputfilename = os.path.join(opts.output_directory, "learned_HA.json")
    with utils_io.open_for_write(outputfilename) as f_out:
        f_out.write(json.dumps(asdict(ha), indent=2))


def compile(opts: Options, learned_model_file: str) -> str:
    learned_model_name = os.path.splitext(learned_model_file)[0]
    output_matlab_script = learned_model_name + "_compile.m"
    simulink_model_name = os.path.basename(learned_model_name)
    output_slx_file = learned_model_name + ".slx"

    with open(learned_model_file, 'r', encoding='utf-8') as file:
        ha = HybridAutomaton(**json.load(file))

    with utils_io.open_for_write(output_matlab_script) as out:
        slx_compiler.compile(
            out,
            ha,
            opts.ode_solver_type,
            opts.ode_solver,
            simulink_model_name,
            opts.invariant_mode,
        )

    matlab.engine.run(output_matlab_script)

    return output_slx_file


# Random seed

print("Random seed", opts.seed)
rng = random.Random() if opts.seed is None else random.Random(opts.seed)

# Initial simulation set

initial_simulation_file = os.path.join(opts.output_directory, "original_simulation.txt")
simulate(rng, opts, opts.simulink_model_file, initial_simulation_file, 1)  # start small

trajectories_files = [initial_simulation_file]

for i in range(0, opts.max_nloops):
    # Inference

    print("Inferring...")
    learned_model_file = os.path.join(opts.output_directory, f"learned_HA{i}.json")
    inference(opts, trajectories_files, learned_model_file)

    # Compile

    output_slx_file = compile(opts, learned_model_file)

    # Simulation

    original_trajectories_file = os.path.join(
        opts.output_directory, f"original_simulation{i}.txt"
    )
    learned_trajectories_file = os.path.join(
        opts.output_directory, f"learned_simulation{i}.txt"
    )

    rng_state = rng.getstate()
    simulate(
        rng,
        opts,
        opts.simulink_model_file,
        original_trajectories_file,
        opts.nsimulations,
    )

    rng.setstate(rng_state)
    simulate(rng, opts, output_slx_file, learned_trajectories_file, opts.nsimulations)

    # Find counter examples

    original_trajectories = load_trajectories_files([original_trajectories_file])
    learned_trajectories = load_trajectories_files([learned_trajectories_file])

    counter_examples = []
    for ot, lt in zip(
        original_trajectories.trajectories, learned_trajectories.trajectories
    ):
        assert len(ot[0]) == len(lt[0]), "Non equal number of samples for a trajectory"
        ot_ovs = ot[1][:, -len(opts.output_variables) :]
        lt_ovs = lt[1][:, -len(opts.output_variables) :]
        print("Comparing")
        print(ot_ovs)
        print(lt_ovs)
        dist = trajectory_dtw_distance(
            ot, lt, opts.input_variables, opts.output_variables
        )
        print(dist)
        if opts.counter_example_threshold < dist:
            counter_examples.append(ot)

    counter_example_file = os.path.join(
        opts.output_directory, f"counter_example{i}.txt"
    )
    with utils_io.open_for_write(counter_example_file) as oc:
        Trajectories(counter_examples, original_trajectories.stepsize).output(oc)

    if len(counter_examples) == 0:
        print("No counter example found")
        exit(0)
    else:
        print(f"Counter examples: {len(counter_examples)}")

    trajectories_files.append(counter_example_file)

print(f"Even after {i+1} inference iterations, we did not see a fixedpoint")
