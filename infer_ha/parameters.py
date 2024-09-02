from infer_ha.utils.trajectories_parser import parse_trajectories
from infer_ha.utils.commandline_parser import process_type_annotation_parameters, Options

def load_trajectories_and_fix_parameters(parameters):
    '''
    Load the trajectories then fix the parameters.  Return the trajectories and the fixed parameters.
    '''
    input_filename = parameters['input_filename']
    list_of_trajectories, stepsize_of_traj, system_dimension = parse_trajectories(input_filename)

    if stepsize_of_traj != parameters['stepsize']:
        print(f"Warning: --stepsize {parameters['stepsize']} is different from the stepsize of trajectories {stepsize_of_traj}. Use the one in the file")
        parameters['stepsize'] = stepsize_of_traj

    variableType_datastruct = []  # structure that holds [var_index, var_name, var_type, pool_values]
    if len(parameters['variable_types']) >= 1:  # if user supply annotation arguments
        variableType_datastruct = process_type_annotation_parameters(parameters, system_dimension)
    parameters['variableType_datastruct'] = variableType_datastruct

    ops = Options(**parameters)

    return (list_of_trajectories, ops)
