# Breach tools

import re
import numpy as np
from hybridlearner.types import MATRIX
from hybridlearner.matlab import engine
from hybridlearner.trajectory import Trajectories
from hybridlearner.slx.info import get_IOports


# 😡😡😡
# Usually, if multiple ncounter examples found,
#   np.shape(signals_matlab) = (n, 3, 1001)
# (1001 is the number of the frames)
#
# However, if only 1 counter example found, np.shape(signals_matlab) = (3, 1001)
def fix_signals(signals: MATRIX) -> MATRIX:
    match np.shape(signals):
        case (_, _, _):
            return signals
        case (_, _):
            print('Fixing the dimension of singals')
            return signals[np.newaxis, :]
        case _:
            assert False


def get_time(var: str) -> MATRIX:
    """
    Get 1xn double matlab matrix and return 1 dimension array
    """
    return engine.getvar_matrix(var)[0]


def get_signals(var: str) -> MATRIX:
    """
    Get n*1 cell of nports*frames doubles when more than 1 sets of signals
    or nports*frame doubles when only 1 set of signals
    """
    return fix_signals(engine.getvar_matrix(var))


def signals_to_trajectories(time: MATRIX, signals: MATRIX) -> Trajectories:
    return list(map(lambda sig: (time, np.transpose(np.array(sig))), signals))


def get_obj_false(pb: str) -> MATRIX:
    # scores can be empty! when only 1 counter example is found
    scores = np.array(engine.eval1(pb + '.obj_false'))
    if scores.size == 0:
        print('Strange obj_false:', scores, 'Fixing its dimension')
        scores = np.array([0])
    else:
        scores = scores[0]
    return scores


def get_port_dicts(
    simulink_model_file: str, input_variables: list[str], output_variables: list[str]
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Returns dictionaries of input/output variable names
    to input/output port names
    """
    inports, outports = get_IOports(simulink_model_file)

    inport_dict = dict(
        zip(input_variables, [re.sub(r'^[^/]+/', '', n) for n in inports])
    )
    outport_dict = dict(
        zip(output_variables, [re.sub(r'^[^/]+/', '', n) for n in outports])
    )
    for iv, ip in inport_dict.items():
        print(f'Input variable {iv} has port {ip}')
    for ov, op in outport_dict.items():
        print(f'Output variable {ov} has port {op}')

    return (inport_dict, outport_dict)
