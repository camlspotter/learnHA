from infer_ha.utils.trajectories_parser import parse_trajectories
from infer_ha.utils.commandline_parser import process_type_annotation_parameters, Options

def load_trajectories_and_fix_parameters(parameters):
    '''
    Load the trajectories then fix the parameters.  Return the trajectories and the fixed parameters.
    '''
    input_filename = parameters['input_filename']
    trajs = parse_trajectories(input_filename)

    parameters['stepsize'] = trajs.stepsize

    annotations = {}  # structure that holds [var_index, var_name, var_type, pool_values]
    if len(parameters['variable_types']) >= 1:  # if user supply annotation arguments
        annotations = process_type_annotation_parameters(parameters, trajs.dimension)
    parameters['annotations'] = annotations

    ops = Options(**parameters)

    return (trajs.trajectories, ops)
