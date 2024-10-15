from .breach import *
from .options import Options
from .input import SignalType
from hybridlearner.types import Range

opts = Options(
    time_horizon=20,
    sampling_time=0.01,
    fixed_interval_data=False,
    invariant={
        'u': Range(min=-11, max=-9),
        'x': Range(min=10, max=20),
        'v': Range(min=5, max=15),
    },
    number_of_cps={'u': 3},
    signal_types={'u': SignalType.FIXED_STEP},
    seed=3,
)

simulate(
    opts,
    '_out/breach_simulate.m',
    '../data/models/ex_sldemo_bounce_Input.slx',  # from _out/ directory
    ['u'],
    ['x', 'v'],
    10,
)
