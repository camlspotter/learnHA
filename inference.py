import os
import json
from dataclasses import asdict
import argparse

from hybridlearner.inference import infer_model
from hybridlearner.obsolete.model_printer.print_HA import print_HA
from hybridlearner import automaton
from hybridlearner.common import options as common_options
from hybridlearner.inference import options as inference_options
from hybridlearner.trajectory import load_trajectories_files
import hybridlearner.utils.io as utils_io
from hybridlearner.slx_compiler import compile, OdeSolverType, InvariantMode

from pydantic.dataclasses import dataclass
from typeguard import typechecked


@dataclass
class Options(common_options.Options, inference_options.Options):
    input_filenames: list[str]


@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="Hybrid Automaton inference")
    inference_options.add_argument_group(parser)
    common_options.add_argument_group(parser)
    parser.add_argument(
        '-i',
        '--input-filename',
        help='input trajectory filename (OBSOLETE)',
        type=str,
        required=False,
    )
    parser.add_argument(
        'input-filenames', help='Input trajectory filenames', type=list[str], nargs='*'
    )

    args = vars(parser.parse_args())

    # input_filenames
    if 'input_filename' in args and 'input_filenames' in args:
        assert False, "--input-filename and input-filenames cannot coexist"

    if 'input_filename' in args:
        args['input_filenames'] = [args['input_filename']]
        del args['input_filename']

    if not 'input_filenames' in args:
        assert False, "At least one input filename must be given"

    return Options(**args)


def runLearnHA() -> None:  # Calling the implementation from project BBC4CPS
    '''
    Hints:
        To analysis the segmentation output: in the file "learnHA/hybridlearner.inference.py" uncomment the line 24 having "plot_segmentation_new(segmented_traj, L_y, t_list, Y, stepM)"
        To analysis the clustering output: in the file "learnHA/hybridlearner.inference.py" uncomment the line 136 having "plot_after_clustering(t_list, L_y, P_modes, Y, stepM)"
    @return:
    '''
    opts = get_options()

    list_of_trajectories = load_trajectories_files(opts.input_filenames)

    raw = infer_model(
        list_of_trajectories, opts.input_variables, opts.output_variables, opts
    )

    outputfilename = os.path.join(opts.output_directory, "learned_HA.txt")
    with utils_io.open_for_write(outputfilename) as f_out:
        print_HA(f_out, raw)

    ha = automaton.build(raw)
    outputfilename = os.path.join(opts.output_directory, "learned_HA.json")
    with utils_io.open_for_write(outputfilename) as f_out:
        f_out.write(json.dumps(asdict(ha), indent=2))


if __name__ == '__main__':
    runLearnHA()
