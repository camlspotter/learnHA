from .breach import *
from hybridlearner.simulation.input import SignalType
from hybridlearner.types import Range
from hybridlearner import matlab

opts = find_counter_examples_options(
    time_horizon=20,
    sampling_time=0.01,
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
    skip_already_tried_parameters=True,
)

falsifier = Falsifier()

rng = random.Random()

trjs = falsifier.find_counter_examples(
    rng, opts, 'data/models/bball_learned_HA0.slx', 0
)

print(trjs)
