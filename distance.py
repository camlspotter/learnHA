# ex.
#
# pipenv run python simulate.py --simulink-model-file ../../src/test_cases/engine/learn_ha_loop/ex_sldemo_bounce_Input.slx --time-horizon 13.0 --sampling-time 0.001 --fixed-interval-data False --input-variables 'u' --output-variables 'x,v' --invariant '-9.9 <= u && u <= -9.5 && 10.2 <= x && x <= 10.5 && 15 <= v && v <= 15' --number-of-cps 'u:4' --signal-types 'u:linear' -o model_simulation.txt -S 0 -n 64

import numpy as np
import argparse
from typing import Optional, cast
from typeguard import typechecked
from pydantic.dataclasses import dataclass
from infer_ha.distance import dtw_distance
from infer_ha.trajectories import parse_trajectories
import infer_ha.parser
import infer_ha.utils.io as utils_io

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
                        type=infer_ha.parser.comma_separated_variables, required=True)
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
    avs = at[1]
    aovs = avs[:,-len(opts.output_variables):]
    bvs = bt[1]
    bovs = bvs[:,-len(opts.output_variables):]
    print("Comparing")
    print(aovs)
    print(bovs)
    dist = dtw_distance(aovs, bovs)
    print(dist)
