import unittest

import os
import random
import filecmp
import hybridlearner.utils.io as utils_io
from hybridlearner.types import Range
from hybridlearner.simulation.input import generate_simulation_input, SignalType
from hybridlearner.simulation.script import generate_simulation_script
from hybridlearner.simulation import simulate_list

class Test(unittest.TestCase):

    def test_simulate(self):

        # pipenv run python simulate.py --simulink-model-file  --time-horizon 13.0 --sampling-time 0.001 --fixed-interval-data False --input-variables 'u' --output-variables 'x,v' --invariant '-9.9 <= u && u <= -9.5 && 10.2 <= x && x <= 10.5 && 15 <= v && v <= 15' --number-of-cps 'u:4' --signal-types 'u:linear' -o model_simulation.txt -S 0 -n 64

        script_file= "_test/simulate_model.m"
        simulink_model_file= os.path.abspath("../../src/test_cases/engine/learn_ha_loop/ex_sldemo_bounce_Input.slx")
        output_file= os.path.abspath("_test/test_simulate.txt")
        time_horizon= 13.0
        sampling_time= 0.001
        fixed_interval_data= False
        input_variables= ['u']
        output_variables= ['x','v']
        invariant={'u': Range(-9.9, -9.5),
                   'x': Range(10.2, 10.5),
                   'v': Range(15, 15)}
        number_of_cps={'u': 4}
        signal_types={'u': SignalType.LINEAR} 
        nsimulations=4

        with utils_io.open_for_write(script_file) as out:
            generate_simulation_script(out= out,
                                       title= 'Title',
                                       simulink_model_file= simulink_model_file,
                                       time_horizon= time_horizon,
                                       sampling_time= sampling_time,
                                       fixed_interval_data= fixed_interval_data,
                                       input_variables= input_variables,
                                       output_variables = output_variables)

        rng= random.Random(0)

        inputs = [ generate_simulation_input(rng,
                                             time_horizon= time_horizon,
                                             invariant= invariant,
                                             number_of_cps= number_of_cps,
                                             signal_types= signal_types,
                                             input_variables= input_variables,
                                             output_variables= output_variables)
                   for _ in range(nsimulations) ]

        simulate_list( script_file= script_file,
                       output_file= output_file,
                       input_variables= input_variables,
                       output_variables= output_variables,
                       inputs= inputs )

        assert filecmp.cmp("data/test_simulate.txt", output_file, shallow=False)
