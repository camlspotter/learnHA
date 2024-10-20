#!/usr/bin/env pipenv-shebang

import os
import random
import argparse
import textwrap
import numpy as np
from typeguard import typechecked
from pydantic.dataclasses import dataclass
import json
from dataclasses import asdict

import hybridlearner.utils.io as utils_io

from hybridlearner.common import options as common_options
from hybridlearner.simulation import options as simulation_options
from hybridlearner.inference import options as inference_options
from hybridlearner.slx import compiler_options

from hybridlearner.simulation import simulate
from hybridlearner.trajectory import (
    load_trajectories_files,
    Trajectories,
    Trajectory,
    save_trajectories,
)
from hybridlearner.inference import infer_model
from hybridlearner import automaton
from hybridlearner.automaton import HybridAutomaton
from hybridlearner.slx import compiler
from hybridlearner import matlab
from hybridlearner.falsify import find_counter_examples
from hybridlearner.plot import plot_timeseries_multi


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


def inference(opts: Options, trajectories_files: list[str]) -> HybridAutomaton:
    _header, list_of_trajectories = load_trajectories_files(trajectories_files)

    print(f"Loaded {len(list_of_trajectories)} trajectories")

    raw = infer_model(
        list_of_trajectories, opts.input_variables, opts.output_variables, opts
    )
    return automaton.build(raw)


def compile(opts: Options, learned_model_file: str) -> str:
    learned_model_name = os.path.splitext(learned_model_file)[0]
    output_matlab_script = learned_model_name + "_compile.m"
    simulink_model_name = os.path.basename(learned_model_name)
    output_slx_file = learned_model_name + ".slx"

    with open(learned_model_file, 'r', encoding='utf-8') as file:
        ha = HybridAutomaton(**json.load(file))

    with utils_io.open_for_write(output_matlab_script) as out:
        compiler.compile(
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

initial_simulation_file = os.path.join(opts.output_directory, "learning00.txt")
simulate(rng, opts, opts.simulink_model_file, initial_simulation_file, 1)  # start small

trajectories_files = [initial_simulation_file]

for i in range(1, opts.max_nloops + 1):
    # Inference

    logfile = os.path.join(opts.output_directory, f"report{i:02d}.md")
    with utils_io.open_for_write(logfile) as log:
        print("Inferring...")
        ha = inference(opts, trajectories_files)

        learned_model_file = os.path.join(
            opts.output_directory, f"learned_HA{i:02d}.json"
        )
        ha.save(learned_model_file)

        log.write(f"# {os.path.basename(opts.simulink_model_file)} inference {i}\n\n")
        log.write(f"## Automaton\n\n")
        log.write("```\n")
        ha.hum_print(log)
        log.write("```\n")
        log.write("\n")

        # Compile

        output_slx_file = compile(opts, learned_model_file)

        # Find counter examples

        original, learned = find_counter_examples(rng, opts, output_slx_file, i)

        header = ['time'] + opts.input_variables + opts.output_variables

        learning_file = os.path.join(opts.output_directory, f"learning{i:02d}.txt")
        # Add the original trajectories which could not be reproduced well
        # by the learned model.
        save_trajectories(learning_file, header, original)

        # Counter example plot. Show both the original and learned for visual comparison

        header = (
            ['time']
            + opts.input_variables
            + [f"original:{k}" for k in opts.output_variables]
            + [f"learned:{k}" for k in opts.output_variables]
        )

        counter_examples = [
            (ot[0], np.hstack((ot[1], lt[1][:, -len(opts.output_variables) :])))
            for (ot, lt) in zip(original, learned)
        ]

        base = f"counter_examples{i:02d}.svg"
        counter_example_file = os.path.join(opts.output_directory, base)

        plot_timeseries_multi(
            counter_example_file,
            'Counter examples found',
            header[1:],  # drop 'time'
            counter_examples,
        )

        log.write(f"## Counter examples\n\n")
        log.write(f"![]({base})\n\n")

        # Loop or not

        if len(original) == 0:
            print("No counter example found")
            exit(0)
        else:
            print(f"Counter examples: {len(original)}")

        trajectories_files.append(learning_file)

print(f"Even after {i} inference iterations, we did not see a fixedpoint")
