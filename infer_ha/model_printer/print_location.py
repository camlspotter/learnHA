from infer_ha.model_printer.print_invariant import *
from infer_ha.model_printer.print_flow import *

def print_location(f_out, G, mode_inv, Exp, initial_location):
    r"""
    :param f_out: file pointer where the output is printed.
    :param G: is a list. Each item of the list G is a list that holds the coefficients (obtained using linear regression)
           of the ODE of a mode of the learned HA.
    :param mode_inv: is a list with items of type [mode-id, invariant-constraints]. Where mode-id is the location number
                  and invariant-constraints holds the bounds (min, max) of each variable in the corresponding mode-id.
    :param Exp: is the polynomial expression obtained from the mapping \Phi function.

    """
    # ****** Writing the initial mode before so that Automaton gets the initial location ID. ******

    initVal = "Initial-mode " + str(initial_location + 1) + "\n"    # Old implementation writing only a single
                            # initial location. The mode in which the 1st/starting trajecotry lies.
    # In the later version we will determine all initial modes and print them here. Accordingly, the interface/syntax
    # of the output model-file will also change. Then, the calling project (BBC4CPS will have to change the model-parser
    # module.)
    f_out.write(initVal)

    # ****** Writing the mode ODE. ******
    for modeID in range(0, len(G)):  # for each mode ODE
        modelabel = "mode " + str(modeID + 1) + "\n"  # printing mode starting from 1, since dReach has issue for mode=0
        f_out.write(modelabel)
        # print(modelabel)
        print_invariant(f_out, mode_inv, modeID)
        print_flow_dynamics(f_out, G, modeID, Exp)
