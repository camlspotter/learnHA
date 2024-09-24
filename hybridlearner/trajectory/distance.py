from fastdtw import fastdtw  # https://pypi.org/project/fastdtw/
from hybridlearner.types import MATRIX
from hybridlearner.trajectory import Trajectory


def dtw_distance(
    a: MATRIX,  # output variable timeseries A, 2D  a[time][var]
    b: MATRIX,  # output variable timeseries B, 2D  b[time][var]
) -> float:
    radius = 5
    dist = None  # p-norm
    return fastdtw(a, b, radius, dist)[0]  # not intersted in the path


def trajectory_dtw_distance(
    at: Trajectory,  # output variable timeseries A, 2D  a[time][var]
    bt: Trajectory,  # output variable timeseries B, 2D  b[time][var]
    input_variables: list[str],
    output_variables: list[str],
) -> float:
    assert at[1].shape[1] == len(input_variables) + len(output_variables)
    assert bt[1].shape[1] == len(input_variables) + len(output_variables)
    return dtw_distance(
        at[1][:, len(output_variables)], bt[1][:, len(output_variables)]
    )
