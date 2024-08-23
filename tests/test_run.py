import unittest

import filecmp
import warnings
import os
import json
from dataclasses import asdict

from infer_ha.infer_HA import infer_model
from infer_ha import HA
from infer_ha.model_printer.print_HA import print_HA
from infer_ha.parameters import load_trajectories_and_fix_parameters
from infer_ha.utils.trajectories_parser import parse_trajectories
from infer_ha.utils.commandline_parser import process_type_annotation_parameters, ClusteringMethod
import infer_ha.utils.io as utils_io

# To execute this test from the project folder "learnHA" type the command
# amit@amit-Alienware-m15-R4:~/MyPythonProjects/learningHA/learnHA$ python -m unittest discover -v


def write_HA(parameters, raw):
    outputfilename = os.path.join(parameters.output_directory, "learned_HA.txt")
    with utils_io.open_for_write(outputfilename) as f_out:
        print_HA(f_out, raw)

    ha = HA.build(raw)
    outputfilename = os.path.join(parameters.output_directory, "learned_HA.json")
    with utils_io.open_for_write(outputfilename) as f_out:
        f_out.write(json.dumps(asdict(ha), indent=2))

class TestLearnHA(unittest.TestCase):

    def test_runLearnHA_osci_withoutAnnotate(self):

        ps = {}
        print("Running test runLearnHA module")

        ps['input_filename'] = "data/test_data/simu_oscillator_2.txt"
        ps['output_directory'] = "_test/oscillator_2_withoutAnnotate"

        ps['methods'] = ClusteringMethod.DTW

        ps['ode_degree'] = 1
        ps['modes'] = 4
        ps['guard_degree'] = 1
        ps['segmentation_error_tol'] = 0.1
        ps['segmentation_fine_error_tol'] = 0.1
        ps['threshold_distance'] = 1.0
        ps['threshold_correlation'] = 0.89
        ps['dbscan_eps_dist'] = 0.01  # default value
        ps['dbscan_min_samples'] = 2  # default value
        ps['size_input_variable'] = 0
        ps['size_output_variable'] = 2
        ps['variable_types'] = ''
        ps['pool_values'] = ''
        ps['constant_value'] = ''
        ps['ode_speedup'] = 50
        ps['is_invariant'] = True
        ps['stepsize'] = 0.01
        ps['filter_last_segment'] = True
        ps['lmm_step_size'] = 5
        ps['input_variables'] = []
        ps['output_variables'] = []

        (list_of_trajectories, parameters) = load_trajectories_and_fix_parameters(ps)

        raw = infer_model(list_of_trajectories, parameters)
        write_HA(parameters, raw)  # prints an HA model file

        backup_file = "data/test_output/oscillator_2_without_annotation.txt"
        test_generated_file = os.path.join(parameters.output_directory, 'learn_HA.txt')

        # shallow mode comparison: where only metadata of the files are compared like the size, date modified, etc.
        # result = filecmp.cmp(backup_file, test_generated_file)
        # print(result)
        # deep mode comparison: where the content of the files are compared.
        result = filecmp.cmp(backup_file, test_generated_file, shallow=False)
        print(result)
        # self.assertTrue(result) # Fails if the output generated is not equal to the file stored in the data/test_output


    def test_runLearnHA_osci_withAnnotate(self):

        ps = {}
        print("Running test runLearnHA module with Oscillator model with type annotation")

        ps['input_filename'] = "data/test_data/simu_oscillator_2.txt"
        ps['output_directory'] = "_test/oscillator_2_withAnnotate"

        ps['methods'] = ClusteringMethod.DTW

        ps['ode_degree'] = 1
        ps['modes'] = 4
        ps['guard_degree'] = 1
        ps['segmentation_error_tol'] = 0.1
        ps['segmentation_fine_error_tol'] = 0.1
        ps['threshold_distance'] = 1.0
        ps['threshold_correlation'] = 0.89
        ps['dbscan_eps_dist'] = 0.01  # default value
        ps['dbscan_min_samples'] = 2  # default value
        ps['size_input_variable'] = 0
        ps['size_output_variable'] = 2
        ps['variable_types'] = 'x0=t1,x1=t1'
        ps['pool_values'] = ''
        ps['constant_value'] = ''
        ps['ode_speedup'] = 50
        ps['is_invariant'] = True
        ps['stepsize'] = 0.01
        ps['filter_last_segment'] = True
        ps['lmm_step_size'] = 5
        ps['input_variables'] = []
        ps['output_variables'] = []

        (list_of_trajectories, parameters) = load_trajectories_and_fix_parameters(ps)

        raw = infer_model(list_of_trajectories, parameters)
        write_HA(parameters, raw) # prints an HA model file

        backup_file = "data/test_output/oscillator_2_with_annotation.txt"
        test_generated_file = os.path.join(parameters.output_directory, 'learn_HA.txt')

        # shallow mode comparison: where only metadata of the files are compared like the size, date modified, etc.
        # result = filecmp.cmp(backup_file, test_generated_file)
        # print(result)
        # deep mode comparison: where the content of the files are compared.
        result = filecmp.cmp(backup_file, test_generated_file, shallow=False)
        print(result)
        # self.assertTrue(result) # Fails if the output generated is not equal to the file stored in the data/test_output

    def test_runLearnHA_bball_withAnnotate(self):

        ps = {}
        print("Running test runLearnHA module with Bouncing Ball model with type annotation")
        # python3 run.py --input-filename data/test_data/simu_bball_4.txt --output-filename bball_4.txt --modes 1 --clustering-method 1 --ode-degree 1 --guard-degree 1 --segmentation-error-tol 0.1 --segmentation-fine-error-tol 0.9 --filter-last-segment 1 --threshold-correlation 0.8 --threshold-distance 9.0 --size-input-variable 1 --size-output-variable 2 --variable-types 'x0=t1,x1=t1' --pool-values '' --ode-speedup 50 --is-invariant False

        ps['input_filename'] = "data/test_data/simu_bball_4.txt"
        ps['output_directory'] = "_test/bball_4"

        ps['methods'] = ClusteringMethod.DTW

        ps['ode_degree'] = 1
        ps['modes'] = 1
        ps['guard_degree'] = 1
        ps['segmentation_error_tol'] = 0.1
        ps['segmentation_fine_error_tol'] = 0.9
        ps['threshold_distance'] = 9.0
        ps['threshold_correlation'] = 0.8
        ps['dbscan_eps_dist'] = 0.01  # default value
        ps['dbscan_min_samples'] = 2  # default value
        ps['size_input_variable'] = 1
        ps['size_output_variable'] = 2
        ps['variable_types'] = 'x0=t1,x1=t3'
        ps['constant_value'] = 'x1=0'
        ps['lmm_step_size'] = 5
        ps['pool_values'] = ''
        ps['ode_speedup'] = 50
        ps['is_invariant'] = False
        ps['stepsize'] = 0.01
        ps['filter_last_segment'] = True
        ps['input_variables'] = []
        ps['output_variables'] = []

        (list_of_trajectories, parameters) = load_trajectories_and_fix_parameters(ps)

        raw = infer_model(list_of_trajectories, parameters)
        write_HA(parameters, raw)

        backup_file = "data/test_output/bball_4.txt"
        test_generated_file = os.path.join(parameters.output_directory, 'learn_HA.txt')

        # shallow mode comparison: where only metadata of the files are compared like the size, date modified, etc.
        # result = filecmp.cmp(backup_file, test_generated_file)
        # print(result)
        # deep mode comparison: where the content of the files are compared.
        result = filecmp.cmp(backup_file, test_generated_file, shallow=False)
        print(result)
        # self.assertTrue(result) # Fails if the output generated is not equal to the file stored in the data/test_output

if __name__ == '__main__':
    unittest.main()
