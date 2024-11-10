import os
import random
import argparse
import textwrap
import numpy as np
from typeguard import typechecked
from pydantic.dataclasses import dataclass
import json
from dataclasses import asdict
import shutil
import subprocess

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
from hybridlearner.plot import plot_timeseries_multi


def report(
    output_directory: str,
    model_name: str,
    iteration: int,
    ha: HybridAutomaton,
    counter_examples: list[tuple[Trajectory, Trajectory, float]],
    input_variables: list[str],
    output_variables: list[str],
) -> None:
    """
    Counter example plot. Show both the original and learned for visual comparison.

    - output_directory: where to produce the report and images
    - model_name: used in the title
    - iteration: used in the title
    - ha : hybrid automaton
    - counter_examples: counter examples found for ha
    - input_variables: the names of the input variables
    - output_variables: the names of the output variables
    """
    log_filename = os.path.join(output_directory, f'report{iteration:02d}.md')
    with utils_io.open_for_write(log_filename) as log:
        log.write(f"# {model_name} inference {iteration}\n\n")
        log.write(f"## Automaton\n\n")
        log.write("```\n")
        ha.hum_print(log)
        log.write("```\n")
        log.write("\n")

        # inplace sort by dist
        counter_examples.sort(key=lambda x: -x[2])

        counter_examples_top_10 = counter_examples[:10]

        header = (
            ['time']
            + input_variables
            + [f"original:{k}" for k in output_variables]
            + [f"learned:{k}" for k in output_variables]
        )

        trs = [
            (
                f"Trajectory {i} (dist: {dist:.2f})",  # title
                (
                    ot[0],  # time
                    np.hstack((ot[1], lt[1][:, -len(output_variables) :])),  # values
                ),
            )
            for (i, (ot, lt, dist)) in enumerate(counter_examples_top_10)
        ]

        if len(trs) != 0:
            base = f"counter_examples{iteration:02d}.svg"
            counter_example_file = os.path.join(output_directory, base)

            plot_timeseries_multi(
                counter_example_file,
                'Counter examples',
                header[1:],  # drop 'time'
                trs,
            )

            log.write(
                f"## Counter examples (Top {len(counter_examples_top_10)} of {len(counter_examples)})\n\n"
            )
            log.write(f"![]({base})\n\n")
        else:
            log.write(f"## Counter examples\n\n")
            log.write(f"None!\n\n")

    if shutil.which('pandoc'):
        subprocess.run(f'pandoc {log_filename} -o {log_filename}.html', shell=True)


def report_no_comparison(
    output_directory: str,
    model_name: str,
    iteration: int,
    ha: HybridAutomaton,
    counter_examples: list[tuple[Trajectory, float]],
    input_variables: list[str],
    output_variables: list[str],
) -> None:
    """
    Counter example plot. Show both the original and learned for visual comparison.

    - output_directory: where to produce the report and images
    - model_name: used in the title
    - iteration: used in the title
    - ha : hybrid automaton
    - counter_examples: counter examples found for ha
    - input_variables: the names of the input variables
    - output_variables: the names of the output variables
    """
    log_filename = os.path.join(output_directory, f'report{iteration:02d}.md')
    with utils_io.open_for_write(log_filename) as log:
        log.write(f"# {model_name} inference {iteration}\n\n")
        log.write(f"## Automaton\n\n")
        log.write("```\n")
        ha.hum_print(log)
        log.write("```\n")
        log.write("\n")

        # inplace sort by dist
        counter_examples.sort(key=lambda x: -x[1])

        counter_examples_top_10 = counter_examples[:10]

        header = ['time'] + input_variables + [f"learned:{k}" for k in output_variables]

        trs = [
            (
                f"Trajectory {i} (dist: {dist:.2f})",  # title
                (
                    lt[0],  # time
                    lt[1],  # values
                ),
            )
            for (i, (lt, dist)) in enumerate(counter_examples_top_10)
        ]

        if len(trs) != 0:
            base = f"counter_examples{iteration:02d}.svg"
            counter_example_file = os.path.join(output_directory, base)

            plot_timeseries_multi(
                counter_example_file,
                'Counter examples',
                header[1:],  # drop 'time'
                trs,
            )

            log.write(
                f"## Counter examples (Top {len(counter_examples_top_10)} of {len(counter_examples)})\n\n"
            )
            log.write(f"![]({base})\n\n")
        else:
            log.write(f"## Counter examples\n\n")
            log.write(f"None!\n\n")

    if shutil.which('pandoc'):
        subprocess.run(f'pandoc {log_filename} -o {log_filename}.html', shell=True)
