import os
import random
from typing import Protocol
from pydantic.dataclasses import dataclass
from hybridlearner.types import Invariant
from hybridlearner.simulation.input import SignalType
from hybridlearner.simulation import simulate
from hybridlearner.trajectory import Trajectory, load_trajectories_files
from hybridlearner.trajectory.distance import trajectory_dtw_distance


# Protocol for subtyping!
# Unfortunately I cannot inherit dataclasses and have to list all the fields here.
class find_counter_examples_protocol(Protocol):
    time_horizon: float  # total time of simulation
    sampling_time: float  # simulation frame time
    fixed_interval_data: bool
    invariant: Invariant
    number_of_cps: dict[str, int]
    signal_types: dict[str, SignalType]
    input_variables: list[str]
    output_variables: list[str]
    output_directory: str
    simulink_model_file: str
    nsimulations: int
    counter_example_threshold: float


@dataclass
class find_counter_examples_options:
    time_horizon: float  # total time of simulation
    sampling_time: float  # simulation frame time
    fixed_interval_data: bool
    invariant: Invariant
    number_of_cps: dict[str, int]
    signal_types: dict[str, SignalType]
    input_variables: list[str]
    output_variables: list[str]
    output_directory: str
    simulink_model_file: str
    nsimulations: int
    counter_example_threshold: float


def find_counter_examples(
    rng: random.Random,
    opts: find_counter_examples_protocol,
    output_slx_file: str,
    i: int,
) -> list[Trajectory]:
    # Simulation of the original model

    rng_state = rng.getstate()

    original_trajectories_file = os.path.join(
        opts.output_directory, f"original_simulation{i}.txt"
    )

    simulate(
        rng,
        opts,
        opts.simulink_model_file,
        original_trajectories_file,
        opts.nsimulations,
    )

    # Simulation of the learned model with the same RNG seed

    rng.setstate(rng_state)

    learned_trajectories_file = os.path.join(
        opts.output_directory, f"learned_simulation{i}.txt"
    )

    simulate(rng, opts, output_slx_file, learned_trajectories_file, opts.nsimulations)

    # Find counter examples

    original_trajectories = load_trajectories_files([original_trajectories_file])
    learned_trajectories = load_trajectories_files([learned_trajectories_file])

    counter_examples = []
    for ot, lt in zip(original_trajectories, learned_trajectories):
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

    return counter_examples
