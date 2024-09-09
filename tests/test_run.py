import unittest

import filecmp
import os
import json
from dataclasses import asdict

from infer_ha.infer_HA import infer_model
from infer_ha import HA
from infer_ha.model_printer.print_HA import print_HA
from infer_ha.utils.commandline_parser import ClusteringMethod, Options
from infer_ha.trajectories import parse_trajectories
import infer_ha.utils.io as utils_io
from infer_ha.annotation import Continuous, Constant

# To execute this test from the project folder "learnHA" type the command
# amit@amit-Alienware-m15-R4:~/MyPythonProjects/learningHA/learnHA$ python -m unittest discover -v


def write_HA(opts, raw):
    outputfilename = os.path.join(opts.output_directory, "learned_HA.txt")
    with utils_io.open_for_write(outputfilename) as f_out:
        print_HA(f_out, raw)

    ha = HA.build(raw)
    outputfilename = os.path.join(opts.output_directory, "learned_HA.json")
    with utils_io.open_for_write(outputfilename) as f_out:
        f_out.write(json.dumps(asdict(ha), indent=2))

class TestLearnHA(unittest.TestCase):

    def test_runLearnHA_osci_withoutAnnotate(self):

        ps = {}
        print("Running test runLearnHA module")

        ps['input_filename'] = "data/test_data/simu_oscillator_2.txt"
        ps['output_directory'] = "_test/oscillator_2_withoutAnnotate"

        ps['clustering_method'] = ClusteringMethod.DTW

        ps['ode_degree'] = 1
        ps['modes'] = 4
        ps['guard_degree'] = 1
        ps['segmentation_error_tol'] = 0.1
        ps['segmentation_fine_error_tol'] = 0.1
        ps['threshold_distance'] = 1.0
        ps['threshold_correlation'] = 0.89
        ps['dbscan_eps_dist'] = 0.01  # default value
        ps['dbscan_min_samples'] = 2  # default value
        ps['input_variables'] = []
        ps['output_variables'] = ['x0', 'x1']
        ps['size_input_variable'] = 0
        ps['size_output_variable'] = 2
        ps['ode_speedup'] = 50
        ps['is_invariant'] = True
        ps['filter_last_segment'] = True
        ps['lmm_step_size'] = 5
        ps['annotations'] = {}

        opts = Options(**ps)

        list_of_trajectories = parse_trajectories(opts.input_filename)
        
        raw = infer_model(list_of_trajectories, opts)
        write_HA(opts, raw)  # prints an HA model file

        backup_file = "data/test_output/oscillator_2_without_annotation.txt"
        test_generated_file = os.path.join(opts.output_directory, 'learned_HA.txt')

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

        ps['clustering_method'] = ClusteringMethod.DTW

        ps['ode_degree'] = 1
        ps['modes'] = 4
        ps['guard_degree'] = 1
        ps['segmentation_error_tol'] = 0.1
        ps['segmentation_fine_error_tol'] = 0.1
        ps['threshold_distance'] = 1.0
        ps['threshold_correlation'] = 0.89
        ps['dbscan_eps_dist'] = 0.01  # default value
        ps['dbscan_min_samples'] = 2  # default value
        ps['input_variables'] = []
        ps['output_variables'] = ['x0', 'x1']
        ps['size_input_variable'] = 0
        ps['size_output_variable'] = 2
        ps['ode_speedup'] = 50
        ps['is_invariant'] = True
        ps['filter_last_segment'] = True
        ps['lmm_step_size'] = 5
        ps['annotations'] = {0: Continuous(), 1: Continuous()}

        opts = Options(**ps)

        list_of_trajectories = parse_trajectories(opts.input_filename)

        raw = infer_model(list_of_trajectories, opts)
        write_HA(opts, raw) # prints an HA model file

        backup_file = "data/test_output/oscillator_2_with_annotation.txt"
        test_generated_file = os.path.join(opts.output_directory, 'learned_HA.txt')

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
        # python3 run.py --input-filename data/test_data/simu_bball_4.txt --output-filename bball_4.txt --modes 1 --clustering-method dtw --ode-degree 1 --guard-degree 1 --segmentation-error-tol 0.1 --segmentation-fine-error-tol 0.9 --filter-last-segment 1 --threshold-correlation 0.8 --threshold-distance 9.0 --size-input-variable 1 --size-output-variable 2 --variable-types 'x0=t1,x1=t1' --pool-values '' --ode-speedup 50 --is-invariant False

        ps['input_filename'] = "data/test_data/simu_bball_4.txt"
        ps['output_directory'] = "_test/bball_4"

        ps['clustering_method'] = ClusteringMethod.DTW

        ps['ode_degree'] = 1
        ps['modes'] = 1
        ps['guard_degree'] = 1
        ps['segmentation_error_tol'] = 0.1
        ps['segmentation_fine_error_tol'] = 0.9
        ps['threshold_distance'] = 9.0
        ps['threshold_correlation'] = 0.8
        ps['dbscan_eps_dist'] = 0.01  # default value
        ps['dbscan_min_samples'] = 2  # default value
        ps['input_variables'] = ['x0']
        ps['output_variables'] = ['x1', 'x2']
        ps['size_input_variable'] = 1
        ps['size_output_variable'] = 2
        ps['lmm_step_size'] = 5
        ps['pool_values'] = ''
        ps['ode_speedup'] = 50
        ps['is_invariant'] = False
        ps['filter_last_segment'] = True
        ps['annotations'] = {0: Continuous(), 1: Constant(0)}

        opts = Options(**ps)

        list_of_trajectories = parse_trajectories(opts.input_filename)

        raw = infer_model(list_of_trajectories, opts)
        write_HA(opts, raw)

        backup_file = "data/test_output/bball_4.txt"
        test_generated_file = os.path.join(opts.output_directory, 'learned_HA.txt')

        # shallow mode comparison: where only metadata of the files are compared like the size, date modified, etc.
        # result = filecmp.cmp(backup_file, test_generated_file)
        # print(result)
        # deep mode comparison: where the content of the files are compared.
        result = filecmp.cmp(backup_file, test_generated_file, shallow=False)
        print(result)
        # self.assertTrue(result) # Fails if the output generated is not equal to the file stored in the data/test_output

if __name__ == '__main__':
    unittest.main()
