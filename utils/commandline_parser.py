import argparse


def read_commandline_arguments():
    """
    This function calls Python's built-in class ArgumentParser to read command line arguments that are necessary for our
    HA learning algorithm.
    To find the complete list of arguments and their functions. Type the --help option in the command terminal.

    :return:
        A dictionary data type of arguments, args supplied by the user in the command terminal.
        For example, to access the value of the argument --ode-degree use
         degree = args['ode_degree']

    """

    parser = argparse.ArgumentParser(description='Learns HA model from input--output trajectories')
    parser.add_argument('-i', '--input-filename', help='input FileName containing trajectories', type=str, required=True)
    parser.add_argument('-o', '--output-filename', help='output FileName with the learned HA model', default='out.txt',
                        required=False)
    parser.add_argument('-c', '--clustering-method', help='Clustering Algorithm. Options are: 1: DTW  2: DBSCAN  3: piecelinear', type=int,
                        choices=[1, 2, 3], default=1, required=False)
    parser.add_argument('-d', '--ode-degree', help='Degree of polynomial in ODE', type=int, default=1, required=False)
    parser.add_argument('-m', '--modes', help='Number of modes. Used only in piecelinear clustering algorithm',
                        type=int, default=1, required=False)
    parser.add_argument('-b', '--guard-degree', help='Degree of polynomial inequalities for Guards', type=int,
                        default=1, required=False)
    parser.add_argument('--segmentation-error-tol', help='Maximal error tolerated during segmentation', type=float,
                        default=0.01, required=False)
    parser.add_argument('--threshold-distance', help='Maximal threshold for distance in DTW clustering algorithm',
                        type=float, default=0.1, required=False)
    parser.add_argument('--threshold-correlation', help='Maximal threshold for correlation value in DTW clustering algorithm',
                        type=float, default=0.8, required=False)
    parser.add_argument('--dbscan-eps-dist', help='Maximal threshold for distance in DBSCAN clustering algorithm',
                        type=float, default=0.01, required=False)
    parser.add_argument('--dbscan-min-samples', help='Maximal threshold for min-samples in DBSCAN clustering algorithm',
                        type=int, default=2, required=False)
    parser.add_argument('--size-input-variable', help='Number of input variables in the trajectories', type=int, required=True)
    parser.add_argument('--size-output-variable', help='Number of output variables in the trajectories', type=int, required=True)
    parser.add_argument('--variable-types', help='Type Annotation for variables. Options are t1: continuous variables'
                        ' t2: constant pool of values. Syntax: --variable-types "x0=t1, x1=t2, x2=t1"',
                        type=str, default='', required=False)
    parser.add_argument('--pool-values', help='set the values of type=t2. Syntax: --pool-values "x1={10, 20, 30, 40}"',
                        type=str, default='', required=False)
    parser.add_argument('--ode-speedup', help='Maximum number of segments to include for ODE computation',
                        type=int, default=10, required=False)
    parser.add_argument('--is-invariant', help='Options are: 0/1/2. Values 0 and 1 ignores invariant and 2 enables computation',
                        type=int, choices=[0, 1, 2], default=0, required=False)
    parser.add_argument('--stepsize', help='Fixed sampling time step-size of the input trajectories',
                        type=float, default=0.01, required=False)

    args = vars(parser.parse_args())    #  create a dict structure of the arguments
    # note the key name replaces with '_' for all '-' in the arguments
    '''
    print("input =", args['input_filename'])
    print("output =", args['output_filename'])
    print("clustering-method =", args['clustering_method'])
    print("ode-degree =", args['ode_degree'])
    print("modes =", args['modes'])
    print("guard-degree =", args['guard_degree'])
    print("segmentation_error_tol =", args['segmentation_error_tol'])
    print("threshold_distance =", args['threshold_distance'])
    print("threshold_correlation =", args['threshold_correlation'])
    print("dbscan_eps_dist =", args['dbscan_eps_dist'])
    print("dbscan_min_samples =", args['dbscan_min_samples'])
    print("size_input_variable =", args['size_input_variable'])
    print("size_output_variable =", args['size_output_variable'])    
    print("variable-types =", args['variable_types'])
    print("pool_values =", args['pool_values'])
    print("ode_speedup =", args['ode_speedup'])
    print("is_invariant =", args['is_invariant'])
    print("stepsize =", args['stepsize'])
    
    '''

    print("variable-types =", args['variable_types'])
    print("pool_values =", args['pool_values'])

    if args['clustering_method'] == 1:
        args['methods'] = "dtw"
    elif args['clustering_method'] == 2:
        args['methods'] = "dbscan"
    elif args['clustering_method'] == 3:
        args['methods'] = "piecelinear"

    return args


def process_type_annotation_parameters(parameters, system_dim):
    """
    :param
        parameters: is a dictionary data structure having the list of commandline arguments passed by the user for the
        learning algorithm. This function uses the arguments 'variable_types' and 'pool_values' supplied by the user
        to construct a specific data-structure named 'variableType_datastruct' which is used in the learning algorithm.
    :param
        system_dim: is the dimension (input + output variables) of the system whose trajectory is taken as input.

    :return:
        variableType_datastruct: a specific data-structure used in the learning algorithm.

    """

    # ******** Parsing the command line argument variable-type and pool-values into a list *****************
    variable_types = parameters['variable_types'] # Eg.: "x0=t4, x1=t3, x2=t4, x3=t1, x4=t2"
    pool_values = parameters['pool_values']   # Eg.:  "x2={10,20,30,40} & x4={14.7,12.5}"
    # ******** ******** ******** ******** ******** ******** ******** ******** ********
    variableType_datastruct = []  # structure that holds [var_index, var_name, var_type, pool_values]
    for i in range(0, system_dim):  # create and initialize the datastruct
        variableType_datastruct.append([i, "x" + str(i), "", ""])
    # print ("data = ", variableType_datastruct)
    # print("v_type:",variable_types, "and pool_val:",pool_values,"end")
    # print("Length of v_type:",len(variable_types), "and Length of pool_val:",len(pool_values),"end")

    if len(variable_types) >= 1:  # parse only when values are supplied from command line
        str_var_types = variable_types.split(",")
        # str_var_types = variable_types.split(",")
        # print("Length of str_var_types:")
        # print(len(str_var_types))
        for i in str_var_types:
            str_i_values = i.split("=")
            varName = str_i_values[0].strip()  # trim or remove whitespaces
            varType = str_i_values[1]
            # print("Var Name: ", varName, " var type: ", varType)
            for val in variableType_datastruct:
                if varName in val:
                    index = val[0]
                    variableType_datastruct[index][2] = varType
                    # print("Index=", val[0])
    # print ("data again = ", variableType_datastruct)

    if len(pool_values) >= 1:  # parse only when values are supplied from command line
        str_pool_values = pool_values.split(" & ")  # Eg.:  "x2={10,20,30,40} & x4={14.7,12.5}"
        # print("Pool values:", str_pool_values)
        for i in str_pool_values:  # Eg.:  "x2={10,20,30,40}"
            str_i_values = i.split("=")  # Eg.:  "['x2', '{10,20,30,40}']"
            varName = str_i_values[0]
            varValues = str_i_values[1]  # Eg.:  '{10,20,30,40}'
            size = len(varValues)
            varValues = varValues[1:size - 1]
            # print("Var Name: ", varName, " var Values: ", varValues)
            varValues = [float(x) for x in varValues.split(",")]
            for val in variableType_datastruct:
                if varName in val:
                    index = val[0]
                    variableType_datastruct[index][3] = varValues

    # print ("data again = ", variableType_datastruct)

    '''
    See the example output after parsing variable_types ="x0=t4, x1=t3, x2=t2, x3=t1, x4=t2" and pool_values="x2={10,20,30,40} & x4={14.7,12.5}"
    variableType_datastruct =  [[0, 'x0', 't4', ''], [1, 'x1', 't3', ''], [2, 'x2', 't2', [10.0, 20.0, 30.0]], [3, 'x3', 't1', ''], [4, 'x4', 't2', [14.7, 12.5]]]
    '''
    # The structure variableType_datastruct will be empty is no argument is supplied
    # ******** Parsing argument variable-type and pool-values into a list *****************

    return variableType_datastruct

if __name__ == '__main__':
    read_commandline_arguments()