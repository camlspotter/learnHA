import os
import json
from dataclasses import asdict

from hybridlearner.inference import infer_model
from hybridlearner.obsolete.model_printer.print_HA import print_HA
from hybridlearner import HA
from hybridlearner.inference.options import get_options
from hybridlearner.trajectory import parse_trajectories_files
import hybridlearner.utils.io as utils_io
from hybridlearner.slx_compiler import compile, OdeSolverType, InvariantMode

def runLearnHA() -> None:  # Calling the implementation from project BBC4CPS
    '''
    Hints:
        To analysis the segmentation output: in the file "learnHA/hybridlearner.inference.py" uncomment the line 24 having "plot_segmentation_new(segmented_traj, L_y, t_list, Y, stepM)"
        To analysis the clustering output: in the file "learnHA/hybridlearner.inference.py" uncomment the line 136 having "plot_after_clustering(t_list, L_y, P_modes, Y, stepM)"
    @return:
    '''
    opts = get_options()

    list_of_trajectories = parse_trajectories_files(opts.input_filenames)

    raw = infer_model(list_of_trajectories, opts)

    outputfilename = os.path.join(opts.output_directory, "learned_HA.txt")
    with utils_io.open_for_write(outputfilename) as f_out:
        print_HA(f_out, raw)

    ha = HA.build(raw)
    outputfilename = os.path.join(opts.output_directory, "learned_HA.json")
    with utils_io.open_for_write(outputfilename) as f_out:
        f_out.write(json.dumps(asdict(ha), indent=2))

if __name__ == '__main__':
    runLearnHA()
