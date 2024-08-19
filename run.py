from infer_ha import infer_HA as learnHA     #infer_model, svm_classify
from infer_ha.model_printer.print_HA import print_HA
from infer_ha import HA
from infer_ha.parameters import load_trajectories_and_fix_parameters
from infer_ha.utils.trajectories_parser import parse_trajectories
from infer_ha.utils.commandline_parser import read_commandline_arguments, process_type_annotation_parameters

def runLearnHA():  # Calling the implementation from project BBC4CPS
    '''
    Hints:
        To analysis the segmentation output: in the file "learnHA/infer_ha/infer_HA.py" uncomment the line 24 having "plot_segmentation_new(segmented_traj, L_y, t_list, Y, stepM)"
        To analysis the clustering output: in the file "learnHA/infer_ha/infer_HA.py" uncomment the line 136 having "plot_after_clustering(t_list, L_y, P_modes, Y, stepM)"
    @return:
    '''
    # input_filename, output_filename, list_of_trajectories, learning_parameters = read_command_line(sys.argv)
    parameters = read_commandline_arguments()   # reads the command line values also can use -h to see help on usages

    (list_of_trajectories, parameters) = load_trajectories_and_fix_parameters(parameters)

    P_modes, G, mode_inv, transitions, position, init_location = learnHA.infer_model(list_of_trajectories, parameters)

    print_HA(P_modes, G, mode_inv, transitions, position, parameters, init_location)

if __name__ == '__main__':
    runLearnHA()
