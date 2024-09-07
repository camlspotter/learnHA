from enum import Enum
import argparse
from typing import Optional, Any
from pydantic.dataclasses import dataclass
from typeguard import typechecked
from infer_ha.utils.argparse_bool import argparse_bool
from infer_ha.annotation import Continuous, Pool, Constant, Annotation, AnnotationTbl, parse_annotation_tbl
import infer_ha.parser 

# @dataclass # We cannot use @dataclass with Enum: @dataclass overrides __eq__
class ClusteringMethod(Enum):
    DTW = "dtw"
    DBSCAN = "dbscan"
    PIECELINEAR = "piecelinear"
   
@dataclass
class Options:
    input_filename : str
    output_directory : str
    ode_degree : int # default=1
    modes : int # default=1
    guard_degree : int # default=1
    segmentation_error_tol : float # default=0.01
    segmentation_fine_error_tol : float # default=0.01
    threshold_distance : float # default=0.1
    threshold_correlation : float # default=0.8
    dbscan_eps_dist : float # default=0.01
    dbscan_min_samples : int # default=2
    annotations : AnnotationTbl
    ode_speedup : int # , default=10
    is_invariant : bool # default=True
    filter_last_segment : bool # default=False
    lmm_step_size : int # choices=[2, 3, 4, 5, 6], default=5
    clustering_method : ClusteringMethod # dtw/dbscan/piecelinear

    input_variables : list[str]
    output_variables : list[str]

@typechecked
def check_options(d : dict[str,Any]) -> Options:
    return Options(**d)

def read_commandline_arguments() -> Options:
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
    parser.add_argument('--output-directory', help='output directory', required=True)
    parser.add_argument('-c', '--clustering-method', help='Clustering Algorithm. Options are: dtw (default), dbscan, piecelinear', type=str, choices=['dtw', 'dbscan', 'piecelinear'], default='dtw', required=False)
    parser.add_argument('-d', '--ode-degree', help='Degree of polynomial in ODE. Set to 1 by default', type=int, default=1, required=False)
    parser.add_argument('-m', '--modes', help='Number of modes. Used only in piecelinear clustering algorithm. Set to 1 by default',
                        type=int, default=1, required=False)
    parser.add_argument('-b', '--guard-degree', help='Degree of polynomial inequalities for Guards. Set to 1 by default', type=int,
                        default=1, required=False)
    parser.add_argument('--segmentation-error-tol', help='Maximal relative-difference (FwdBwd) error tolerated during segmentation. Set to 0.01 by default', type=float,
                        default=0.01, required=False)
    parser.add_argument('--segmentation-fine-error-tol', help='Maximal relative-difference (Bwd) fine-error tolerated during segmentation. Set to 0.01 by default', type=float,
                        default=0.01, required=False)
    parser.add_argument('--threshold-distance', help='Maximal threshold for distance in DTW clustering algorithm. Set to 0.1 by default',
                        type=float, default=0.1, required=False)
    parser.add_argument('--threshold-correlation', help='Maximal threshold for correlation value in DTW clustering algorithm. Set to 0.8 by default',
                        type=float, default=0.8, required=False)
    parser.add_argument('--dbscan-eps-dist', help='Maximal threshold for distance in DBSCAN clustering algorithm. Set to 0.01 by default',
                        type=float, default=0.01, required=False)
    parser.add_argument('--dbscan-min-samples', help='Maximal threshold for min-samples in DBSCAN clustering algorithm. Set to 2 by default',
                        type=int, default=2, required=False)
    parser.add_argument('--annotations', help='Variable annotations',
                        type=str, default='', required= False)
    parser.add_argument('--ode-speedup', help='Maximum number of segments to include for ODE computation. Set to 10 by default',
                        type=int, default=10, required=False)
    # Beware! argparse's type=bool is broken
    parser.add_argument('--is-invariant', help='Values True (default) computes invariant and False disables computation',
                        type=argparse_bool, default=True, required=False)
    # Beware! argparse's type=bool is broken
    parser.add_argument('--filter-last-segment',
                        help='True to enable and False to disable (default) filtering out the last segment from a trajectory during segmentation', type=argparse_bool, default=False, required=False)
    parser.add_argument('--lmm-step-size',
                        help='Options are: 2/3/4/5/6. Higher values computes more accurate derivatives. 5 is set default',
                        type=int, choices=[2, 3, 4, 5, 6], default=5, required=False)

    parser.add_argument('--input-variables',
                        help='Input variable names separated by commas',
                        type=infer_ha.parser.comma_separated_variables, required=True)
    parser.add_argument('--output-variables',
                        help='Output variable names separated by commas',
                        type=infer_ha.parser.comma_separated_variables, required=True)

    args = vars(parser.parse_args())    #  create a dict structure of the arguments

    # print("pool_values =", args['pool_values'])

    args['clustering_method'] = ClusteringMethod(args['clustering_method'])
    
    args['size_input_variable'] = len(args['input_variables'])
    args['size_output_variable'] = len(args['output_variables'])

    # annotations
    args['annotations'] = parse_annotation_tbl(args['input_variables'], args['output_variables'], args['annotations'])

    return Options(**args)

# This must be repaced!
def process_type_annotation_parameters(parameters : dict[str,Any]) -> AnnotationTbl:
    """
    :param
        parameters: is a dictionary data structure having the list of commandline arguments passed by the user for the
        learning algorithm. This function uses the arguments 'variable_types' and 'pool_values' supplied by the user
        to construct a specific data-structure named 'annotations' which is used in the learning algorithm.
    :param
        system_dim: is the dimension (input + output variables) of the system whose trajectory is taken as input.

    :return:
        annotations: a specific data-structure used in the learning algorithm.

    """

    system_dim = len(parameters['input_variables']) + len(parameters['output_variables']) 

    # ******** Parsing the command line argument variable-type and pool-values into a list *****************
    variable_types = parameters['variable_types'] # Eg.: "x0=t4, x1=t3, x2=t4, x3=t1, x4=t2"
    pool_values = parameters['pool_values']   # Eg.:  "x2={10,20,30,40} & x4={14.7,12.5}"
    constant_value = parameters['constant_value']  # Eg.:  "x1=47.7 & others"; x1 is t3 type variable and jump reset is 47.7
    # ******** ******** ******** ******** ******** ******** ******** ******** ********

    # structure that holds [var_index, var_name, var_type, pool_values, constant_value]
    raw_annotations : list[list[Any]] = [ [i, "x" + str(i), "", [], 0.0] for i in range(0, system_dim) ]

    if variable_types != "":  # parse only when values are supplied from command line
        for s in variable_types.split(","):
            str_i_values = s.split("=")
            varName = str_i_values[0].strip()  # trim or remove whitespaces
            varType = str_i_values[1]
            # print("Var Name: ", varName, " var type: ", varType)
            for val in raw_annotations:
                if varName == val[1]:
                    index = val[0]
                    raw_annotations[index][2] = varType

    if pool_values != "":  # parse only when values are supplied from command line
        for poolValue in pool_values.split(" & "):  # Eg.:  "x2={10,20,30,40}"
            str_poolValue_values = poolValue.split("=")  # Eg.:  "['x2', '{10,20,30,40}']"
            varName = str_poolValue_values[0]
            varValues = str_poolValue_values[1]  # Eg.:  '{10,20,30,40}'
            size = len(varValues)
            varValues = varValues[1:size - 1]   # discarding parenthesis { and }
            varValues = [float(x) for x in varValues.split(",")] # created a list of the pool of values
            for val in raw_annotations:
                if varName == val[1]:
                    index = val[0]
                    raw_annotations[index][3] = varValues


    if constant_value != "":  # parse only when values are supplied from command line
        for constValue in constant_value.split(" & "):
            str_const_each_element = constValue.split("=")  # Eg.:  "['x1', '0']"
            varName = str_const_each_element[0]  # Eg.:  'x1'
            varValue = str_const_each_element[1]  # Eg.:  '0'
            for val in raw_annotations:
                if varName == val[1]:
                    index = val[0]
                    raw_annotations[index][4] = float(varValue)

    '''
    See the example output after parsing variable_types ="x0=t4, x1=t3, x2=t2, x3=t1, x4=t2" and pool_values="x2={10,20,30,40} & x4={14.7,12.5}"
    annotations =  [[0, 'x0', 't4', ''], [1, 'x1', 't3', ''], [2, 'x2', 't2', [10.0, 20.0, 30.0]], [3, 'x3', 't1', ''], [4, 'x4', 't2', [14.7, 12.5]]]
    '''
    # The structure annotations will be empty is no argument is supplied
    # ******** Parsing argument variable-type and pool-values into a list *****************

    def convert_( x : list[Any]) -> tuple[int, Annotation]:
        [i, _var, ty, fs, f] = x
        match ty:
            case "t1":
                return (i, Continuous())
            case "t2":
                return (i, Pool(fs))
            case "t3":
                return (i, Constant(f))
            case _:
                assert False
                
    @typechecked
    def convert() -> AnnotationTbl:
        return dict([ convert_(x)
                      for x in raw_annotations
                      if x[2] != "" ]) # x[2] is ty

    return convert()

if __name__ == '__main__':
    read_commandline_arguments()
