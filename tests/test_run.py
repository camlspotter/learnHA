import unittest

import filecmp
import os
import json
from dataclasses import asdict

from hybridlearner.inference import infer_model
from hybridlearner import automaton
from hybridlearner.obsolete.model_printer.print_HA import print_HA
from hybridlearner.inference.options import ClusteringMethod, Options
from hybridlearner.trajectory import load_trajectories
import hybridlearner.utils.io as utils_io
from hybridlearner.inference.annotation import Continuous, Constant

# To execute this test from the project folder "learnHA" type the command
# amit@amit-Alienware-m15-R4:~/MyPythonProjects/learningHA/learnHA$ python -m unittest discover -v


def write_HA(opts, raw):
    outputfilename = os.path.join(opts.output_directory, "learned_HA.txt")
    with utils_io.open_for_write(outputfilename) as f_out:
        print_HA(f_out, raw)

    ha = automaton.build(raw)
    outputfilename = os.path.join(opts.output_directory, "learned_HA.json")
    with utils_io.open_for_write(outputfilename) as f_out:
        f_out.write(json.dumps(asdict(ha), indent=2))


class TestLearnHA(unittest.TestCase):
    def doit(self, ps, golden_dir):
        opts = Options(**ps)

        list_of_trajectories = load_trajectories(opts.input_filename)

        raw = infer_model(list_of_trajectories, opts)
        write_HA(opts, raw)  # prints an HA model file

        backup_file = os.path.join(golden_dir, "learned_HA.txt")
        test_generated_file = os.path.join(opts.output_directory, 'learned_HA.txt')
        assert filecmp.cmp(backup_file, test_generated_file, shallow=False)

        backup_file = os.path.join(golden_dir, "learned_HA.json")
        test_generated_file = os.path.join(opts.output_directory, 'learned_HA.json')
        assert filecmp.cmp(
            backup_file, test_generated_file, shallow=False
        ), f"Golden test fails: golden: {backup_file} generated: {test_generated_file}"

    def test_runLearnHA_osci_withoutAnnotate(self):
        print("Running test runLearnHA module")
        ps = {}
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

        self.doit(ps, "data/test_output/oscillator_2_withoutAnnotate")

    def test_runLearnHA_osci_withAnnotate(self):
        print(
            "Running test runLearnHA module with Oscillator model with type annotation"
        )
        ps = {}
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
        ps['annotations'] = {'x0': Continuous(), 'x1': Continuous()}

        self.doit(ps, "data/test_output/oscillator_2_withAnnotate")

    def test_runLearnHA_bball_withAnnotate(self):
        print(
            "Running test runLearnHA module with Bouncing Ball model with type annotation"
        )
        ps = {}
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
        ps['annotations'] = {'x0': Continuous(), 'x1': Constant(0)}

        self.doit(ps, "data/test_output/bball_4")


if __name__ == '__main__':
    unittest.main()
