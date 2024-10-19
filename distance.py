#!/usr/bin/env pipenv-shebang

# Calculate distances of 2 sets of trajectories
#
# ex.
# pipenv run python distance.py --output-variables 'x,y' _out/bball0.txt _out/learned0.txt

import argparse
from typeguard import typechecked
from pydantic.dataclasses import dataclass
from hybridlearner.trajectory.distance import trajectory_dtw_distance
from hybridlearner.trajectory import load_trajectories, trajectory_stepsize
from hybridlearner.common import options as common_options


@dataclass
class Options(common_options.Options):
    file_a: str
    file_b: str


@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="Timeseries distance")
    common_options.add_argument_group(parser)
    parser.add_argument('file_a', help='Timeseries file A', type=str)
    parser.add_argument('file_b', help='Timeseries file B', type=str)
    return Options(**vars(parser.parse_args()))


opts = get_options()

a = load_trajectories(opts.file_a)
b = load_trajectories(opts.file_b)

assert trajectory_stepsize(a[0]) == trajectory_stepsize(
    b[0]
), f"Non equal stepsizes: {trajectory_stepsize(a[0]), trajectory_stepsize(b[0])}"
assert len(a) == len(b), f"Non equal number of trajectories: {len(a)} {len(b)}"

a_nvars = a[0][1].shape[1]
b_nvars = b[0][1].shape[1]
assert a_nvars == b_nvars, f"Non equal number of variables: {a_nvars}, {b_nvars}"

for at, bt in zip(a, b):
    assert len(at[0]) == len(bt[0]), "Non equal number of samples for a trajectory"
    aovs = at[1][:, -len(opts.output_variables) :]
    bovs = bt[1][:, -len(opts.output_variables) :]
    print("Comparing")
    print(aovs)
    print(bovs)
    dist = trajectory_dtw_distance(at, bt, ["u"], ["x", "y"])
    print(dist)
