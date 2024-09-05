from infer_ha.utils.trajectories_parser import parse_trajectories
from infer_ha.utils.commandline_parser import process_type_annotation_parameters, Options

def load_trajectories_and_fix_parameters(opts):
    '''
    Load the trajectories then fix the opts.  Return the trajectories and the fixed opts.
    '''
    input_filename = opts['input_filename']
    trajs = parse_trajectories(input_filename)

    opts['stepsize'] = trajs.stepsize

    annotations = {}  # structure that holds [var_index, var_name, var_type, pool_values]
    if len(opts['variable_types']) >= 1:  # if user supply annotation arguments
        annotations = process_type_annotation_parameters(opts, trajs.dimension)
    opts['annotations'] = annotations

    ops = Options(**opts)

    return (trajs.trajectories, ops)
