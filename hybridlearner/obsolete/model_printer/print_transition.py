from hybridlearner.obsolete.model_printer.print_guard import *
from hybridlearner.obsolete.model_printer.print_assignment import *
from hybridlearner.utils import math as myUtil


def print_transition(f_out, transitions, system_dim, boundary_order):
    """
    :param f_out: file pointer where the output is printed.
    :param transitions: is a list. Each item of the list P contain list of values which are positions of points of a trajectories.
           The size of the list P is equal to the number of clusters or modes of the learned hybrid automaton (HA).
    :param system_dim: system dimension.
    :param boundary_order: degree of the polynomial concerning the guard's equation.

    """

    # I have to loop through transitions to access all the transitions
    # **** Computing the polynomial expression for guard ****
    # same formula as in getcoeff Function in SVM
    coeff_expansion = myUtil.multinomial(system_dim + 1, boundary_order)
    gExp = [""] * int(len(coeff_expansion))
    # gExp = [""] * int(len(coeff_expansion)+1)   #todo testing
    coef_index = 0
    for coeff, term_ in coeff_expansion:
        # The original author used hetero list and we recover it here !!!!!!!!!!!!
        # Awful but no point to fix it since this printer is obsolete.
        term = [coeff] + term_
        number_of_var_per_term = 0
        term_index = 0
        aa = ""
        # Ignoring the 1st element which is the computed coefficient, Also, last term is 1
        for each_var_power in term:
            if (term_index != 0) and (term_index != (len(term) - 1)):
                # if (term_index != 0) and (term_index != (len(gExp) - 1)):  # todo: testing
                if each_var_power != 0.0:
                    if number_of_var_per_term > 0:
                        aa += "* "

                    if each_var_power > 1:
                        # -1 since variable indices begins with x0, x1, etc
                        aa += (
                            "(x"
                            + str(term_index - 1)
                            + ")^"
                            + str(each_var_power)
                            + " "
                        )
                    else:
                        aa += "x" + str(term_index - 1) + " "

                    number_of_var_per_term += 1

            term_index += 1

        gExp[coef_index] = aa
        coef_index += 1

    # print("Expression is ", gExp)
    # The last coeff is in fact the intercept
    gExp[len(coeff_expansion) - 1] = "1"
    # print("Expression is ", gExp)

    for (tr, (src, dest, guard_coeff, assignment)) in enumerate(transitions):

        trans_detail = "Transition-ID " + str(tr) + "\n"
        trans_detail += "Trans-Src-Dest " + str(src + 1) + " => " + str(dest + 1) + "\n"
        f_out.write(trans_detail)

        # **** Printing Guard and Assignment *****
        print_guard(f_out, guard_coeff, gExp)
        print_assignment(f_out, assignment)
