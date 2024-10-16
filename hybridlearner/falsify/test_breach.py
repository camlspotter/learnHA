from .breach import *
from hybridlearner.simulation.input import SignalType
from hybridlearner.types import Range
from hybridlearner.falsify import find_counter_examples_options

opts = find_counter_examples_options(
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
    input_variables=['u'],
    output_variables=['x', 'v'],
    output_directory="_out",
    simulink_model_file='data/models/ex_sldemo_bounce_Input.slx',
    nsimulations=20,
    counter_example_threshold=0.1,
)

build_script(opts, '_out/falsify.m', 'data/models/bball_learned_HA0.slx')

trjs = find_counter_examples(opts, 'data/models/bball_learned_HA0.slx')

print(trjs)
