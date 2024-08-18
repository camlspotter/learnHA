import unittest

import filecmp
import warnings
warnings.filterwarnings('ignore')   # disables FutureWarning in the use of clf.fit()

from infer_ha.infer_HA import infer_model
from infer_ha.model_printer.print_HA import print_HA
from infer_ha.parameters import load_trajectories_and_fix_parameters
from utils.parse_parameters import parse_trajectories
from utils.commandline_parser import process_type_annotation_parameters
import os

# To execute this test from the project folder "learnHA" type the command
# amit@amit-Alienware-m15-R4:~/MyPythonProjects/learningHA/learnHA$ python -m unittest discover -v


class TestLearnHA(unittest.TestCase):

    def test_runLearnHA_osci_withoutAnnotate(self):

        parameters = {}
        print("Running test runLearnHA module")

        parameters['input_filename'] = "data/test_data/simu_oscillator_2.txt"
        parameters['output_directory'] = "_test/oscillator_2_withoutAnnotate"

        parameters['clustering_method'] = 1
        parameters['methods'] = "dtw"

        parameters['ode_degree'] = 1
        parameters['modes'] = 4
        parameters['guard_degree'] = 1
        parameters['segmentation_error_tol'] = 0.1
        parameters['segmentation_fine_error_tol'] = 0.1
        parameters['threshold_distance'] = 1.0
        parameters['threshold_correlation'] = 0.89
        parameters['dbscan_eps_dist'] = 0.01  # default value
        parameters['dbscan_min_samples'] = 2  # default value
        parameters['size_input_variable'] = 0
        parameters['size_output_variable'] = 2
        parameters['variable_types'] = ''
        parameters['pool_values'] = ''
        parameters['ode_speedup'] = 50
        parameters['is_invariant'] = 0
        parameters['stepsize'] = 0.01
        parameters['filter_last_segment'] = 1
        parameters['lmm_step_size'] = 5

        (list_of_trajectories, parameters) = load_trajectories_and_fix_parameters(parameters)

        P, G, mode_inv, transitions, position, initial_location = infer_model(list_of_trajectories, parameters)
        # print("Number of modes learned = ", len(P))
        print_HA(P, G, mode_inv, transitions, position, parameters, initial_location)  # prints an HA model file

        backup_file = "data/test_output/oscillator_2_without_annotation.txt"
        test_generated_file = os.path.join(parameters['output_directory'], 'learn_HA.txt')

        # shallow mode comparison: where only metadata of the files are compared like the size, date modified, etc.
        # result = filecmp.cmp(backup_file, test_generated_file)
        # print(result)
        # deep mode comparison: where the content of the files are compared.
        result = filecmp.cmp(backup_file, test_generated_file, shallow=False)
        print(result)
        # self.assertTrue(result) # Fails if the output generated is not equal to the file stored in the data/test_output


    def test_runLearnHA_osci_withAnnotate(self):

        parameters = {}
        print("Running test runLearnHA module with Oscillator model with type annotation")

        parameters['input_filename'] = "data/test_data/simu_oscillator_2.txt"
        parameters['output_directory'] = "_test/oscillator_2_withAnnotate"

        parameters['clustering_method'] = 1
        parameters['methods'] = "dtw"

        parameters['ode_degree'] = 1
        parameters['modes'] = 4
        parameters['guard_degree'] = 1
        parameters['segmentation_error_tol'] = 0.1
        parameters['segmentation_fine_error_tol'] = 0.1
        parameters['threshold_distance'] = 1.0
        parameters['threshold_correlation'] = 0.89
        parameters['dbscan_eps_dist'] = 0.01  # default value
        parameters['dbscan_min_samples'] = 2  # default value
        parameters['size_input_variable'] = 0
        parameters['size_output_variable'] = 2
        parameters['variable_types'] = 'x0=t1,x1=t1'
        parameters['pool_values'] = ''
        parameters['constant_value'] = ''
        parameters['ode_speedup'] = 50
        parameters['is_invariant'] = 0
        parameters['stepsize'] = 0.01
        parameters['filter_last_segment'] = 1
        parameters['lmm_step_size'] = 5

        (list_of_trajectories, parameters) = load_trajectories_and_fix_parameters(parameters)

        P, G, mode_inv, transitions, position, initial_location = infer_model(list_of_trajectories, parameters)
        # print("Number of modes learned = ", len(P))
        print_HA(P, G, mode_inv, transitions, position, parameters, initial_location) # prints an HA model file

        backup_file = "data/test_output/oscillator_2_with_annotation.txt"
        test_generated_file = os.path.join(parameters['output_directory'], 'learn_HA.txt')

        # shallow mode comparison: where only metadata of the files are compared like the size, date modified, etc.
        # result = filecmp.cmp(backup_file, test_generated_file)
        # print(result)
        # deep mode comparison: where the content of the files are compared.
        result = filecmp.cmp(backup_file, test_generated_file, shallow=False)
        print(result)
        # self.assertTrue(result) # Fails if the output generated is not equal to the file stored in the data/test_output

    def test_runLearnHA_bball_withAnnotate(self):

        parameters = {}
        print("Running test runLearnHA module with Bouncing Ball model with type annotation")
        # python3 run.py --input-filename data/test_data/simu_bball_4.txt --output-filename bball_4.txt --modes 1 --clustering-method 1 --ode-degree 1 --guard-degree 1 --segmentation-error-tol 0.1 --segmentation-fine-error-tol 0.9 --filter-last-segment 1 --threshold-correlation 0.8 --threshold-distance 9.0 --size-input-variable 1 --size-output-variable 2 --variable-types 'x0=t1,x1=t1' --pool-values '' --ode-speedup 50 --is-invariant 2

        parameters['input_filename'] = "data/test_data/simu_bball_4.txt"
        parameters['output_directory'] = "_test/bball_4"

        parameters['clustering_method'] = 1
        parameters['methods'] = "dtw"

        parameters['ode_degree'] = 1
        parameters['modes'] = 1
        parameters['guard_degree'] = 1
        parameters['segmentation_error_tol'] = 0.1
        parameters['segmentation_fine_error_tol'] = 0.9
        parameters['threshold_distance'] = 9.0
        parameters['threshold_correlation'] = 0.8
        parameters['dbscan_eps_dist'] = 0.01  # default value
        parameters['dbscan_min_samples'] = 2  # default value
        parameters['size_input_variable'] = 1
        parameters['size_output_variable'] = 2
        parameters['variable_types'] = 'x0=t1,x1=t3'
        parameters['constant_value'] = 'x1=0'
        parameters['lmm_step_size'] = 5
        parameters['pool_values'] = ''
        parameters['ode_speedup'] = 50
        parameters['is_invariant'] = 2
        parameters['stepsize'] = 0.01
        parameters['filter_last_segment'] = 1

        (list_of_trajectories, parameters) = load_trajectories_and_fix_parameters(parameters)

        P, G, mode_inv, transitions, position, initial_location = infer_model(list_of_trajectories, parameters)
        # print("Number of modes learned = ", len(P))
        print_HA(P, G, mode_inv, transitions, position, parameters, initial_location) # prints an HA model file

        backup_file = "data/test_output/bball_4.txt"
        test_generated_file = os.path.join(parameters['output_directory'], 'learn_HA.txt')

        # shallow mode comparison: where only metadata of the files are compared like the size, date modified, etc.
        # result = filecmp.cmp(backup_file, test_generated_file)
        # print(result)
        # deep mode comparison: where the content of the files are compared.
        result = filecmp.cmp(backup_file, test_generated_file, shallow=False)
        print(result)
        # self.assertTrue(result) # Fails if the output generated is not equal to the file stored in the data/test_output

if __name__ == '__main__':
    unittest.main()
