# Calculate distances of 2 sets of trajectories
#
# ex.
# pipenv run python distance.py --output-variables 'x,y' _out/bball0.txt _out/learned0.txt

import numpy as np
import argparse
from typing import Optional, cast
from typeguard import typechecked
from pydantic.dataclasses import dataclass
from hybridlearner.trajectory.distance import trajectory_dtw_distance
from hybridlearner.trajectory import parse_trajectories
import hybridlearner.parser
import hybridlearner.utils.io as utils_io

@dataclass
class Options:
    file_a : str
    file_b : str
    output_variables : list[str]

@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="Timeseries distance")
    parser.add_argument('file_a', help='Timeseries file A', type=str)
    parser.add_argument('file_b', help='Timeseries file B', type=str)
    parser.add_argument('--output-variables',
                        help='Output variable names separated by commas',
                        type=hybridlearner.parser.comma_separated_variables, required=True)
    args = vars(parser.parse_args())
    return Options(**args)

opts = get_options()

a = parse_trajectories(opts.file_a)
b = parse_trajectories(opts.file_b)

assert a.stepsize == b.stepsize, f"Non equal stepsizes: {a.stepsize}, {b.stepsize}"
assert len(a.trajectories) == len(b.trajectories), f"Non equal number of trajectories: {len(a.trajectories)} {len(b.trajectories)}"

a_nvars = a.trajectories[0][1].shape[1]
b_nvars = b.trajectories[0][1].shape[1]
assert a_nvars == b_nvars, f"Non equal number of variables: {a_nvars}, {b_nvars}"

for (at, bt) in zip(a.trajectories, b.trajectories):
    assert len(at[0]) == len(bt[0]), f"Non equal number of samples for a trajectory"
    aovs = at[1][:,-len(opts.output_variables):]
    bovs = bt[1][:,-len(opts.output_variables):]
    print("Comparing")
    print(aovs)
    print(bovs)
    dist = trajectory_dtw_distance(at, bt, ["u"], ["x", "y"])
    print(dist)
